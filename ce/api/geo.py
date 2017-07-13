import logging
import sys
import math
from collections import OrderedDict
from threading import RLock

from netCDF4 import Dataset
import numpy as np
from shapely.wkt import loads
from shapely.affinity import translate
from shapely.geometry import mapping # convert a Shapely Geom to GeoJSON
import rasterio
from rasterio.mask import mask as rio_mask

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

class memoize_mask(object):
    '''
    Decorator. Caches wktToMask keyed to model_id and the WKT string
    '''
    def __init__(self, func, maxsize=50):
        '''
        Args:
            func: the function to wrap
            maxsize (int): Max size of cache (in MB)
        '''

        self.hits = self.misses = 0
        self.func = func
        self.maxsize = maxsize
        self.cache = OrderedDict()

    def __call__(self, *args):

        nc, fname, wkt, varname = args
        # If we have no key, automatic cache miss
        if (not hasattr(nc, 'model_id')):
            log.debug('Cache MISS (attribute \'model_id\' not found)')
            return self.func(*args)

        # Set key to model_id and wkt polygon
        key = (nc.model_id, wkt)
        log.debug('Checking cache for key %s', key)

        with cache_lock:
            try:
                result = self.cache[key]
                self.cache.move_to_end(key) # record recent use of this key
                self.hits += 1
                log.debug('Cache HIT')
                return result
            except KeyError:
                pass

        log.debug('Cache MISS')
        result = self.func(*args)

        with cache_lock:
            self.cache[key] = result
            self.misses += 1
            while getsize(self.cache) > self.maxsize * 1024 * 1024: # convert to MB
                self.cache.popitem(0) # Purge least recently used cache entry

        return result

    def cache_clear(self):
        with cache_lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

@memoize_mask
def wkt_to_masked_array(nc, fname, wkt, variable):
    poly = loads(wkt)
    return polygon_to_masked_array(nc, fname, poly, variable)


def polygon_to_masked_array(nc, fname, poly, variable):

    nclons = nc.variables['lon'][:]
    if np.any(nclons > 180):
        poly = translate(poly, xoff=180)

    dst_name = 'NETCDF:"{}":{}'.format(fname, variable)
    with rasterio.open(dst_name, 'r', driver='NetCDF') as raster:

        if raster.affine == rasterio.Affine.identity():
            raise Exception("Unable to determine projection parameters for GDAL "
                            "dataset {}".format(dst_name))

        the_array, _ = rio_mask(raster, [mapping(poly)], crop=False, all_touched=True)

    # Weirdly rasterio's mask operation sets, but doesn't respect the
    # Fill_Value, scale_factor, or add_offset
    var = nc.variables[variable]
    the_array.mask = the_array==the_array.fill_value
    scale_factor = getattr(var, 'scale_factor', 1.0)
    add_offset = getattr(var, 'add_offset', 0.0)

    the_array = the_array * scale_factor + add_offset
    return the_array
