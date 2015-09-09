'''
Query Params

id: Model ID
time: Climatological period (0-17)
area: WKT of selected area
variable: Variable requested

Returns JSON statistics for each model:

{
model_id1:
    {
    min: <float>,
    max: <float>,
    mean: <float>,
    median: <float>,
    stdev: <float>,
    units: <string>
    },
model_id2:
    ...}
'''

import os.path

from modelmeta import DataFile

import numpy as np
import numpy.ma as ma
from shapely.geometry import Polygon, Point, CAP_STYLE
from shapely.wkt import loads
from netCDF4 import Dataset
from sqlalchemy.orm.exc import NoResultFound

def stats(sesh, id_, time, area, variable):
    '''
    '''
    try:
        fname, = sesh.query(DataFile.filename).filter(DataFile.unique_id == id_).one()
    except NoResultFound:
        return {}

    assert os.path.exists(fname)

    nc = Dataset(fname)

    polygon = loads(area)

    # Mask out data that isn't inside the input polygon
    mask = polygonToMask(nc, polygon)

    assert variable in nc.variables

    data = nc.variables[variable]

    if time:
        assert 'time' in nc.variables[variable].dimensions
        data = data[time,:,:] # FIXME: Assumes 3d data... doesn't support levels

    # Extend the mask into the time dimension (if it exists)
    mask = np.repeat(mask, data.size / mask.size).reshape(data.shape)

    data = ma.masked_array(data, mask=mask)

    return {
        id_:
        {
            'min': np.min(data),
            'max': np.max(data),
            'mean': np.mean(data),
            'median': ma.median(data)[0],
            'stdev': np.std(data),
            'units': nc.variables[variable].units,
            'ncells': data.compressed().size
        },
    }


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
