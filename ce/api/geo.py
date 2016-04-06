import logging
import collections
import sys
import math
from collections import OrderedDict
from threading import RLock

from netCDF4 import Dataset
import numpy as np
from shapely.wkt import loads
from shapely.affinity import translate
import rasterio
from rasterio.features import rasterize

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
    def inner(obj, _seen_ids = set()):
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

        fname, wkt = args

        key = (fname, wkt)
        log.debug('Checking cache for key {}'.format(key))

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
def wktToMask(filename, wkt):
    poly = loads(wkt)
    return polygonToMask(filename, poly)

def polygonToMask(filename, poly):

    nc = Dataset(filename, 'r')
    nclons = nc.variables['lon'][:]
    if np.any(nclons > 180):
        poly = translate(poly, xoff=180)
    nc.close()

    raster = rasterio.open(filename, 'r', driver='NetCDF')
    mask = rasterize((poly,), out_shape=raster.shape, transform=raster.affine, all_touched=True)
    return mask == 0
