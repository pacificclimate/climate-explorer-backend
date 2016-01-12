import logging
import collections
from collections import OrderedDict
from threading import RLock

import numpy as np
import numpy.ma as ma
from shapely.geometry import Polygon, Point, CAP_STYLE
from shapely.wkt import loads

log = logging.getLogger(__name__)
cache_lock = RLock()

class memoize_mask(object):
    '''
    Decorator. Caches wktToMask keyed to model_id and the WKT string
    '''
    def __init__(self, func, maxsize=100):
        '''
        Args:
            func: the function to wrap
            maxsize (int): Max number of function calls to cache
        '''

        self.hits = self.misses = 0
        self.func = func
        self.maxsize = maxsize
        self.cache = OrderedDict()

    def __call__(self, *args):
        # Set key to model_id and wkt polygon
        key = (args[0].model_id, args[1])
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
            if len(self.cache) > self.maxsize:
                self.cache.popitem(0) # Purge least recently used cache entry

        return result

def pointInPoly(x, y, poly):
    if x is ma.masked or y is ma.masked:
        return ma.masked

    cell = Point(x, y).buffer(2, cap_style=CAP_STYLE.square)
    if poly.intersects(cell):
        return not ma.masked
    else:
        return ma.masked

pointsInPoly = np.vectorize(pointInPoly)

@memoize_mask
def wktToMask(nc, wkt):
    poly = loads(wkt)
    return polygonToMask(nc, poly)

def polygonToMask(nc, poly):

    nclats = nc.variables['lat'][:]
    nclons = nc.variables['lon'][:]
    if np.any(nclons > 180):
        nclons -= 180

    lons, lats = np.meshgrid(nclons, nclats)
    lons = ma.masked_array(lons)
    lats = ma.masked_array(lats, mask=lons.mask)
    # The mask is now shared between both arrays, so you can mask one and the
    # other will be masked as well
    assert lons.sharedmask == True

    # Calculate the polygon extent
    minx, miny, maxx, maxy = poly.bounds

    min_width = np.min(np.diff(nclons))
    min_height = np.min(np.diff(nclons))
    min_cell_area = min_width * min_height
    if poly.area < min_cell_area:
        # We can't just naively mask based on grid centroids.
        # The polygon could actually fall completely between grid centroid
        minx -= min_width
        maxx += min_width
        miny -= min_height
        maxy += min_height

    lons = ma.masked_where((lons < minx) | (lons > maxx), lons, copy=False)
    lats = ma.masked_where((lats < miny) | (lats > maxy), lats, copy=False)

    polygon_mask = pointsInPoly(lons, lats, poly)

    return polygon_mask.mask
