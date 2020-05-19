from pkg_resources import resource_filename
from datetime import timezone

from time import time

import pytest
import numpy as np
from numpy.ma import MaskedArray
from dateutil.parser import parse
from netCDF4 import Dataset

from ce.api.util import get_array, mean_datetime


@pytest.fixture(
    params=(
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc", "tasmax"),
        ("tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc", "tasmin"),
        ("prism_pr_small.nc", "pr"),  # a file with masked values
    ),
    ids=("bnu-tasmax", "bnu-tasmin", "prism_pr_small"),
    scope="function",
)
def ncfilevar(request):
    fname, varname = request.param
    return (resource_filename("ce", "tests/data/" + fname), varname)


@pytest.fixture(scope="function")
def nctuple(request, ncfilevar):
    fname, varname = ncfilevar
    nc = Dataset(fname)

    def fin():
        print("teardown netcdf_file")
        nc.close()

    request.addfinalizer(fin)
    return nc, fname, varname


def test_get_array(request, nctuple, polygon):
    nc, fname, var = nctuple
    t0 = time()
    x = get_array(nc, fname, 0, polygon, var)
    t = time() - t0
    print(t)
    assert t < 0.1
    assert type(x) == MaskedArray
    assert hasattr(x, "mask")
    assert np.mean(x) > 0 or np.all(x.mask)


utc = timezone.utc


@pytest.mark.parametrize(
    ("input_", "output"),
    (
        (["2001-01-01T00:00:00Z"], "2001-01-01T00:00:00Z"),
        (["2001-01-01T00:00:00Z", "2001-01-04T00:00:00Z"], "2001-01-02T12:00:00Z"),
        (
            ["2001-01-01T00:00:00Z", "2001-01-04T00:00:00Z", "2001-01-07T00:00:00Z"],
            "2001-01-04T00:00:00Z",
        ),
    ),
)
def test_mean_datetime(input_, output):
    x = [parse(t).replace(tzinfo=utc) for t in input_]
    assert mean_datetime(x) == parse(output).replace(tzinfo=utc)
