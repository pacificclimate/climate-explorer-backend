import time

import pytest

from ce.api.geo import wkt_to_masked_array, polygon_to_masked_array
from geomet import wkt as wkt_parser

test_polygons = [
    'POLYGON ((-125 50, -116 50, -116 60, -125 60, -125 50))',
    'POLYGON ((-125 55, -116 55, -116 60, -125 60, -125 55))'
]


def test_cache(netcdf_file):
    f = wkt_to_masked_array
    var = 'tasmax'
    netcdf_file, fname = netcdf_file
    f.cache_clear()
    f(netcdf_file, fname, test_polygons[0], var)
    assert f.hits == 0, f.misses == 1
    f(netcdf_file, fname, test_polygons[0], var)
    assert f.hits == 1, f.misses == 1
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.hits == 1, f.misses == 2
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.hits == 2, f.misses == 2
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.hits == 3, f.misses == 2


def test_clip_speed(ncobject, polygon):
    ncobject, fname = ncobject
    try:
        poly = wkt_parser.loads(polygon)
    except ValueError:
        pytest.skip("Invalid polygon, so speed test is irrellevant")
    t0 = time.time()
    polygon_to_masked_array(ncobject, fname, poly, 'tasmax')
    t = time.time() - t0
    # Ensure that we can clip our largest polygons in under 100ms
    assert t < .1
