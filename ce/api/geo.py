import logging
import sys
import math
from collections import OrderedDict
from threading import RLock

import datetime
from netCDF4 import Dataset
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from geomet import wkt as wkt_parser

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
    Decorator. Caches wkt_to_masked_array keyed to filename and the WKT string
    '''
    def __init__(self, func, maxsize=100):
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

        # Set key to file and wkt polygon
        key = (fname, wkt)
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
                if len(self.cache) == 1:
                    print("Single item too large for cache, size {}".format(getsize(self.cache)))
                self.cache.popitem(0) # Purge least recently used cache entry

        return result

    def cache_clear(self):
        with cache_lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

@memoize_mask
def wkt_to_masked_array(nc, fname, wkt, variable):
    poly = wkt_parser.loads(wkt)
    return polygon_to_masked_array(nc, fname, poly, variable)


def polygon_to_masked_array(nc, fname, poly, variable):

    nclons = nc.variables['lon'][:]
    if np.any(nclons > 180):
        poly = translate_polygon_longitudes(poly, 180) if poly['type'] == 'Polygon' else translate_multipolygon_longitudes(poly, 180)

    dst_name = 'NETCDF:"{}":{}'.format(fname, variable)
    with rasterio.open(dst_name, 'r', driver='NetCDF') as raster:

        if raster.transform == rasterio.Affine.identity():
            raise Exception("Unable to determine projection parameters for GDAL "
                            "dataset {}".format(dst_name))

        the_array, _ = rio_mask(raster, [poly], crop=False, all_touched=True, filled=False)

    return the_array

def translate_polygon_longitudes (poly, offset):
    """Takes a geoJSON POLYGON-like object, adds offset to each point's longitude"""
    coords = []
    for point in poly['coordinates'][0]: #assumes a single ring
        coords.append([point[0] + offset % 360, point[1]])
    return dict(type='Polygon', coordinates=[coords])

def translate_multipolygon_longitudes (multi, offset):
    """Takes a geoJSON MULTIPOLYGON-like object, adds offset of each point's longitude"""
    rings = []
    for ring in multi['coordinates'][0]:
        coords = []
        for point in ring:
            coords.append([point[0] + offset % 360, point[1]])
        rings.append(coords)
    return dict(type='MultiPolygon', coordinates=[rings])