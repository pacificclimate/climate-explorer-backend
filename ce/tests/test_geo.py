import time

import pytest

from ce.api.geo import wktToMask, polygonToMask
from shapely.wkt import loads

test_polygons = [
    'POLYGON ((-125 50, -116 50, -116 60, -125 60, -125 50))',
    'POLYGON ((-125 55, -116 55, -116 60, -125 60, -125 55))'
]

def test_cache(netcdf_file):
    f = wktToMask
    f.cache_clear()
    f(netcdf_file, test_polygons[0])
    assert f.hits == 0, f.misses == 1
    f(netcdf_file, test_polygons[0])
    assert f.hits == 1, f.misses == 1
    f(netcdf_file, test_polygons[1])
    assert f.hits == 1, f.misses == 2
    f(netcdf_file, test_polygons[1])
    assert f.hits == 2, f.misses == 2
    f(netcdf_file, test_polygons[1])
    assert f.hits == 3, f.misses == 2

def test_clip_speed(big_nc_file, polygon):
    try:
        poly = loads(polygon)
    except:
        pytest.skip("Invalid polygon, so speed test is irrellevant")
    t0 = time.time()
    polygonToMask(big_nc_file, poly)
    t = time.time() - t0
    # Ensure that we can clip our largest polygons in under 100ms
    assert t < .1
