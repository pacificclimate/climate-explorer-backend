
import pytest

from ce.api.geo import wktToMask

test_polygons = [
    'POLYGON ((-125 50, -116 50, -116 60, -125 60, -125 50))',
    'POLYGON ((-125 55, -116 55, -116 60, -125 60, -125 55))'
]

def test_cache(netcdf_file):
    f = wktToMask
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
