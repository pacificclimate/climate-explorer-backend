import numpy as np
import numpy.ma as ma
from shapely.geometry import Polygon, Point, CAP_STYLE

def pointInPoly(x, y, poly):
    if x is ma.masked or y is ma.masked:
        return ma.masked

    cell = Point(x, y).buffer(2, cap_style=CAP_STYLE.square)
    if poly.intersects(cell):
        return not ma.masked
    else:
        return ma.masked

pointsInPoly = np.vectorize(pointInPoly)

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
