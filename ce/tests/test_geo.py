import time

import pytest

from ce.api.geo import wkt_to_masked_array, polygon_to_masked_array, polygon_to_mask
from shapely.wkt import loads
from shapely.errors import ReadingError

test_polygons = [
    'POLYGON ((-125 50, -116 50, -116 60, -125 60, -125 50))',
    'POLYGON ((-125 55, -116 55, -116 60, -125 60, -125 55))'
]


def test_data_cache(netcdf_file):
    f = wkt_to_masked_array
    var = 'tasmax'
    netcdf_file, fname = netcdf_file
    f.cache_clear()
    f(netcdf_file, fname, test_polygons[0], var)
    assert f.get_hits() == 0, f.get_misses() == 1
    f(netcdf_file, fname, test_polygons[0], var)
    assert f.get_hits() == 1, f.get_misses() == 1
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.get_hits() == 1, f.get_misses() == 2
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.get_hits() == 2, f.get_misses() == 2
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.get_hits() == 3, f.get_misses() == 2

def test_mask_cache(netcdf_file):
    f = polygon_to_mask
    var = 'tasmax'
    nc, fname = netcdf_file
    f.cache_clear()
    gj0 = wkt_parser.loads(test_polygons[0])
    gj1 = wkt_parser.loads(test_polygons[1])
    f(nc, fname, gj0, var)
    assert f.get_hits() == 0, f.get_misses() == 1
    assert f.get_length() == 1
    f(nc, fname, gj0, var)
    assert f.get_hits() == 1, f.get_misses() == 1
    assert f.get_length() == 1
    f(nc, fname, gj1, var)
    assert f.get_hits() == 1, f.get_misses() == 2
    assert f.get_length() == 2
    f(nc, fname, gj0, var)
    assert f.get_hits() == 2, f.get_misses() == 2
    assert f.get_length() == 2
    f(nc, fname, gj1, var)
    assert f.get_hits() == 3, f.get_misses() == 2
    assert f.get_length() == 2


def test_clip_speed(ncobject, polygon):
    ncobject, fname = ncobject
    try:
        poly = loads(polygon)
    except ReadingError:
        pytest.skip("Invalid polygon, so speed test is irrellevant")
    t0 = time.time()
    polygon_to_masked_array(ncobject, fname, poly, 'tasmax')
    t = time.time() - t0
    # Ensure that we can clip our largest polygons in under 100ms
    assert t < .1
