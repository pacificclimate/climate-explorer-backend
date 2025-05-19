import time
import pytest

from ce.api.geo import wkt_to_masked_array, polygon_to_masked_array
from ce.api.geo import (
    polygon_to_mask,
    memoize,
    getsize,
    make_mask_grid_key,
    rasterio_thredds_helper,
)
from shapely.wkt import loads
from shapely.errors import ShapelyError
from collections import OrderedDict
import rasterio

test_polygons = [
    "POLYGON ((-125 50, -116 50, -116 60, -125 60, -125 50))",
    "POLYGON ((-125 55, -116 55, -116 60, -125 60, -125 55))",
]


def test_data_cache(netcdf_file):
    f = wkt_to_masked_array
    var = "tasmax"
    netcdf_file, fname = netcdf_file
    f.cache_clear()
    f(netcdf_file, fname, test_polygons[0], var)
    assert f.get_hits() == 0
    assert f.get_misses() == 1
    f(netcdf_file, fname, test_polygons[0], var)
    assert f.get_hits() == 1
    assert f.get_misses() == 1
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.get_hits() == 1
    assert f.get_misses() == 2
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.get_hits() == 2
    assert f.get_misses() == 2
    f(netcdf_file, fname, test_polygons[1], var)
    assert f.get_hits() == 3
    assert f.get_misses() == 2


def test_mask_cache(netcdf_file):
    f = polygon_to_mask
    var = "tasmax"
    nc, fname = netcdf_file
    f.cache_clear()
    gj0 = loads(test_polygons[0])
    gj1 = loads(test_polygons[1])
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


# because we don't have enough test netCDF data to fill up the 100MB data
# cache to trigger a delete, test cache clearing with a simple function
# and tiny cache instead.
def test_cache_delete():
    def make_fib_key(n):
        return n

    # determine the size of a ten-integer OrderedDict, then use that as the
    # cache size to ensure we see some item removal with twenty calls
    od = OrderedDict()
    for i in range(1, 10):
        od[i] = i

    mb_conversion = 1024 * 1024
    cache_size_mb = getsize(od) / mb_conversion

    @memoize(make_fib_key, cache_size_mb)
    def cached_fibonacci(n):
        if n < 3:
            return 1
        else:
            return cached_fibonacci(n - 1) + cached_fibonacci(n - 2)

    f = cached_fibonacci
    previous_cache = f.get_size()

    for n in range(1, 20):
        cached_fibonacci(n)
        assert (f.get_size() / mb_conversion) <= cache_size_mb
        if previous_cache >= f.get_size():
            return None
        previous_cache = f.get_size()

    # make sure cache has stayed the same size or shrunk at least once.
    assert 0, "Items were supposed to have been deleted from the cache, but none were"


def test_clip_speed(ncobject, polygon):
    ncobject, fname = ncobject
    try:
        poly = loads(polygon)
    except ShapelyError:
        pytest.skip("Invalid polygon, so speed test is irrellevant")
    t0 = time.time()
    polygon_to_masked_array(ncobject, fname, poly, "tasmax")
    t = time.time() - t0
    # Ensure that we can clip our largest polygons in under 100ms
    assert t < 0.1


def test_make_mask_grid_key(ncobject, polygon):
    ncobject, fname = ncobject
    try:
        poly = loads(polygon)
    except ShapelyError:
        pytest.skip("Invalid polygon, so speed test is irrellevant")

    result = make_mask_grid_key(ncobject, fname, poly, None)
    try:
        {result}
    except TypeError:
        assert False, "make_mask_grid_key() generated an unhashable key"


@pytest.mark.online
@pytest.mark.parametrize(
    "local, online",
    [
        (
            "ce/tests/data/tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc",
            "https://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/catalog/datasets/storage/data/projects/comp_support/daccs/test-data/tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230_test.nc",
        ),
        (
            "ce/tests/data/tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc",
            "https://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/catalog/datasets/storage/data/projects/comp_support/daccs/test-data/tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230_test.nc",
        ),
    ],
)
def test_rasterio_thredds_helper(local, online):
    with rasterio_thredds_helper(online) as temp_name:
        with rasterio.open(temp_name) as result, rasterio.open(local) as expected:
            assert result.profile == expected.profile
