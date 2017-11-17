import logging
import sys
import math
from collections import OrderedDict
from threading import RLock

from netCDF4 import Dataset
import numpy as np
from shapely.wkt import loads, dumps
from shapely.affinity import translate
from shapely.geometry import mapping # convert a Shapely Geom to GeoJSON
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.mask import raster_geometry_mask as rio_getmask

### From http://stackoverflow.com/a/30316760/597593
from numbers import Number
from collections import Set, Mapping, deque
try: # Python 2
    zero_depth_bases = (basestring, Number, xrange, bytearray)
    iteritems = 'iteritems'
except NameError: # Python 3
    zero_depth_bases = (str, bytes, Number, range, bytearray)
    iteritems = 'items'

def getsize(obj):
    """Recursively iterate to sum size of object & members."""
    def inner(obj, _seen_ids = None):
        if not _seen_ids:
            _seen_ids = set()
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, zero_depth_bases):
            pass # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
        # Now assume custom object instances
        elif hasattr(obj, '__slots__'):
            size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
        else:
            attr = getattr(obj, '__dict__', None)
            if attr is not None:
                size += inner(attr)
        return size
    return inner(obj)
### End from http://stackoverflow.com/a/30316760/597593

log = logging.getLogger(__name__)
cache_lock = RLock()

class memoize(object):
    '''
    Decorator to add caching to a function.
    Initialized with a key-generating function and maxsize. Caches up to maxsize
    MB worth of results from the decorated function using a key created from the
    decorated function's arguments by the key function.
    A key generator should have the same signature as the cached function.
    '''
    def __init__(self, keyfunc, maxsize=50):
        '''
        Args:
            keyfunc: used to generate keys for the cache hash
            maxsize (int): Max size of cache (in MB)
        '''
        self.keyfunc = keyfunc
        self.maxsize = maxsize

    def __call__(self, func):

        #Under normal circumstances, the callable object returned by this function (and
        #therefore the decorator as a whole) should be called as if it were a decorated
        #function.
        #As an object, it provides a few extra methods for testing and debugging cache
        #performance, but these aren't used in production and can generally be ignored.
        class CachedFunction(object):
            def __init__(self, maxsize, keyfunc, func):
                self.hits = self.misses = 0
                self.maxsize = maxsize
                self.keyfunc = keyfunc
                self.func = func
                self.func.__name__ = func.__name__
                self.cache = OrderedDict()
                self.MBconversion = 1024 * 1024


            def __call__(self, *args):
                key = self.keyfunc(*args)
                log.debug('Checking cache for key {}'.format(key))

                with cache_lock:
                    try:
                        result = self.cache[key]
                        self.cache.move_to_end(key)
                        self.hits += 1
                        log.debug("Cache Hit for {}".format(self.func))
                        return result
                    except KeyError:
                        pass

                    log.debug('Cache MISS for {}'.format(self.func))
                    result = self.func(*args)

                with cache_lock:
                    self.cache[key] = result
                    self.misses += 1
                    while getsize(self.cache) > self.maxsize * self.MBconversion:
                        if len(self.cache) == 1:
                            log.warning("Cache maxsize is set to {} MB ".format(self.maxsize),
                                        "but tried to cache a {} MB item".format(getsize(self.cache) / self.MBconversion))
                        self.cache.popitem(0)

                return result

            #cache testing / debugging functions
            def cache_clear(self):
                with cache_lock:
                    self.cache.clear()
                    self.hits = 0
                    self.misses = 0

            def get_hits(self): return self.hits

            def get_misses(self): return self.misses

            def get_size(self): return getsize(self.cache)

            def get_length(self): return len(self.cache)

        cf = CachedFunction(self.maxsize, self.keyfunc, func)
        return cf

def make_mask_grid_key(nc, fname, poly, variable):
    '''
    Generates a key for characterizing a numpy mask  meant to
    be applied to netCDF files: the polygon the mask is generated from
    and min / max / number of steps for both latitutde and longitude.
    Assumes a regular grid.
    '''
    latsteps = nc.variables['lat'].shape[0]
    latmin = nc.variables['lat'][0]
    latmax = nc.variables['lat'][latsteps - 1]
    lonsteps = nc.variables['lon'].shape[0]
    lonmin = nc.variables['lon'][0]
    lonmax = nc.variables['lon'][lonsteps - 1]
    wkt = dumps(poly) #dict-style geoJSON can't be hashed
    return (wkt, latmin, latmax, latsteps, lonmin, lonmax, lonsteps)

@memoize(make_mask_grid_key, 10)
def polygon_to_mask(nc, fname, poly, variable):
    """Generates a numpy mask from a polygon"""
    nclons = nc.variables['lon'][:]
    if np.any(nclons > 180):
        poly = translate(poly, xoff=180)

    dst_name = 'NETCDF:"{}":{}'.format(fname, variable)
    with rasterio.open(dst_name, 'r', driver='NetCDF') as raster:
        if raster.transform == rasterio.Affine.identity():
            raise Exception("Unable to determine projection parameters for GDAL "
                            "dataset {}".format(dst_name))
        mask, out_transform, window = rio_getmask(raster, [mapping(poly)], all_touched=True)

    return mask, out_transform, window

def make_masked_file_key(nc, fname, wkt, varname):
    """generates a key suitable for characterizing a masked netCDF file:
       filename and polygon"""
    return (fname, wkt)

@memoize(make_masked_file_key, 100)
def wkt_to_masked_array(nc, fname, wkt, variable):
    poly = loads(wkt)
    return polygon_to_masked_array(nc, fname, poly, variable)


def polygon_to_masked_array(nc, fname, poly, variable):
    """Applies a polygon mask to a variable read from a netCDF file,
    in addition to any masks specified in the file itself (_FillValue)
    Returns a numpy masked array with every time slice masked"""

    mask, out_transform, window  = polygon_to_mask(nc, fname, poly, variable)

    dst_name = 'NETCDF:"{}":{}'.format(fname, variable)
    with rasterio.open(dst_name, 'r', driver='NetCDF') as raster:
        #based on https://github.com/mapbox/rasterio/blob/master/rasterio/mask.py
        height, width = mask.shape
        out_shape = (raster.count, height, width)

        array = raster.read(window=window, out_shape=out_shape, masked=True)
        array.mask = array.mask | mask

    return array
