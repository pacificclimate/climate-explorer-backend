from pkg_resources import resource_filename
from datetime import timezone

from os import getenv
from time import time

import pytest
import numpy as np
from numpy.ma import MaskedArray
from dateutil.parser import parse
from netCDF4 import Dataset

from ce.api.util import (
    get_array,
    mean_datetime,
    open_nc,
    check_climatological_statistic,
    get_climatological_statistic,
    get_units_from_run_object,
)

from modelmeta.v2 import Run


@pytest.fixture(
    params=(
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc", "tasmax"),
        ("tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc", "tasmin"),
        ("prism_pr_small.nc", "pr"),  # a file with masked values
        ("anuspline_na.nc", "tasmax"),
        ("CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc", "tasmax"),
    ),
    ids=("bnu-tasmax", "bnu-tasmin", "prism_pr_small", "anuspline", "canesm",),
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
    if "prism_pr_small.nc" in fname and getenv("GITHUB_ACTIONS"):
        pytest.skip(
            "Test does not work with GitHub Actions CI. See issue 206: https://github.com/pacificclimate/climate-explorer-backend/issues/206"
        )
    t0 = time()
    x = get_array(nc, fname, 0, polygon, var)
    t = time() - t0
    print(t)
    assert t < 0.2
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


@pytest.mark.online
@pytest.mark.parametrize(
    ("local", "online"),
    [
        (
            "/storage/data/projects/comp_support/daccs/test-data/fdd_seasonal_CanESM2_rcp85_r1i1p1_1951-2100.nc",
            "https://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/catalog/datasets/storage/data/projects/comp_support/daccs/test-data/fdd_seasonal_CanESM2_rcp85_r1i1p1_1951-2100.nc",
        )
    ],
)
def test_open_nc(local, online):
    with open_nc(local) as nc_local, open_nc(online) as nc_online:
        for key in nc_local.dimensions.keys():
            assert nc_local.dimensions[key].name == nc_online.dimensions[key].name
            assert nc_local.dimensions[key].size == nc_online.dimensions[key].size


@pytest.mark.online
@pytest.mark.parametrize(("bad_path"), [("/bad/path/to/file.nc")])
def test_open_nc_exception(bad_path):
    with pytest.raises(Exception):
        with open_nc(bad_path) as nc:
            # Test won't make it this far, but in case we do, let's fail the test
            assert False


@pytest.mark.parametrize(
    ("run_name", "var_name", "ensemble_name", "expected_units"),
    [
        ("run1", "tasmax", "ce", "degC"),
        ("r1i1p1", "tasmin", "ce", "degC"),
        ("r1i1p1", "pr", "ce", "kg d-1 m-2"),
    ],
)
def test_get_units_from_run_object(
    populateddb_session, run_name, var_name, ensemble_name, expected_units
):
    run_object = Run(name=run_name)
    units = get_units_from_run_object(populateddb_session, Run, var_name, ensemble_name)
    assert units == expected_units


@pytest.mark.parametrize(
    ("cell_methods", "climatological_statistic", "default_to_mean", "expected"),
    (
        # standard_deviation dataset
        (
            "time: minimum time: standard_deviation over days",
            "standard_deviation",
            True,
            True,
        ),
        (
            "time: minimum time: standard_deviation over days",
            "standard_deviation",
            False,
            True,
        ),
        ("time: minimum time: standard_deviation over days", "mean", True, False),
        ("time: minimum time: standard_deviation over days", "mean", False, False),
        ("time: minimum time: standard_deviation over days", "percentile", True, False),
        (
            "time: minimum time: standard_deviation over days",
            "percentile",
            False,
            False,
        ),
        # percentile dataset
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "standard_deviation",
            True,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "standard_deviation",
            False,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "percentile",
            True,
            True,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "percentile",
            False,
            True,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "mean",
            True,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "mean",
            False,
            False,
        ),
        # mean dataset - climatology - strict
        ("time: maximum time: mean over days", "standard_deviation", True, False),
        ("time: maximum time: mean over days", "standard_deviation", False, False),
        ("time: maximum time: mean over days", "mean", True, True),
        ("time: maximum time: mean over days", "mean", False, True),
        ("time: maximum time: mean over days", "percentile", True, False),
        ("time: maximum time: mean over days", "percentile", False, False),
        # mean dataset - ensemble mean - strict
        (
            "time: maximum time: mean over days models: mean",
            "standard_deviation",
            True,
            False,
        ),
        (
            "time: maximum time: mean over days models: mean",
            "standard_deviation",
            False,
            False,
        ),
        ("time: maximum time: mean over days models: mean", "mean", True, True),
        ("time: maximum time: mean over days models: mean", "mean", False, True),
        ("time: maximum time: mean over days models: mean", "percentile", True, False),
        ("time: maximum time: mean over days models: mean", "percentile", False, False),
        # mean dataset - incorrect
        (
            "time: minimum within days time: count within years where > 25 C",
            "standard_deviation",
            True,
            False,
        ),
        (
            "time: minimum within days time: count within years where > 25 C",
            "standard_deviation",
            False,
            False,
        ),
        (
            "time: minimum within days time: count within years where > 25 C",
            "mean",
            True,
            True,
        ),
        (
            "time: minimum within days time: count within years where > 25 C",
            "mean",
            False,
            False,
        ),
        (
            "time: minimum within days time: count within years where > 25 C",
            "percentile",
            True,
            False,
        ),
        (
            "time: minimum within days time: count within years where > 25 C",
            "percentile",
            False,
            False,
        ),
        # mean dataset - unparseable
        ("unspecified", "standard_deviation", True, False),
        ("unspecified", "standard_deviation", False, False),
        ("unspecified", "mean", True, True),
        ("unspecified", "mean", False, False),
        ("unspecified", "percentile", True, False),
        ("unspecified", "percentile", False, False),
        # mean dataset - mean of stdevs (we don't have any data like this, but could be possible)
        (
            "time: standard_deviation over days time: mean over days",
            "standard_deviation",
            True,
            False,
        ),
        (
            "time: standard_deviation over days time: mean over days",
            "standard_deviation",
            False,
            False,
        ),
        ("time: standard_deviation over days time: mean over days", "mean", True, True),
        (
            "time: standard_deviation over days time: mean over days",
            "mean",
            False,
            True,
        ),
        (
            "time: standard_deviation over days time: mean over days",
            "percentile",
            True,
            False,
        ),
        (
            "time: standard_deviation over days time: mean over days",
            "percentile",
            False,
            False,
        ),
    ),
)
def test_check_climatological_statistic(
    cell_methods, climatological_statistic, default_to_mean, expected
):
    assert (
        check_climatological_statistic(
            cell_methods, climatological_statistic, default_to_mean
        )
        == expected
    )


@pytest.mark.parametrize(
    ("cell_methods, climatological_statistic, match_percentile, expected"),
    (
        (
            "time: minimum time: standard_deviation over days",
            "standard_deviation",
            None,
            True,
        ),
        ("time: minimum time: standard_deviation over days", "percentile", None, False),
        ("time: minimum time: standard_deviation over days", "percentile", 5, False),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "standard_deviation",
            None,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "standard_deviation",
            5,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "percentile",
            None,
            True,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "percentile",
            5,
            True,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            "percentile",
            95,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            "standard_deviation",
            None,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            "standard_deviation",
            5,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            "percentile",
            None,
            True,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            "percentile",
            5,
            False,
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            "percentile",
            95,
            True,
        ),
        ("time: minimum time: standard_deviation over days[5]", "percentile", 5, False),
        ("time: minimum time: standard_deviation[5] over days", "percentile", 5, False),
    ),
)
def test_check_climatological_statistic_percentiles(
    cell_methods, climatological_statistic, match_percentile, expected
):
    assert (
        check_climatological_statistic(
            cell_methods,
            climatological_statistic,
            default_to_mean=True,
            match_percentile=match_percentile,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("cell_methods", "default_to_mean", "expected"),
    (
        (
            "time: minimum time: standard_deviation over days",
            True,
            "standard_deviation",
        ),
        (
            "time: minimum time: standard_deviation over days",
            False,
            "standard_deviation",
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            True,
            "percentile[5.0]",
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[5]",
            False,
            "percentile[5.0]",
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            True,
            "percentile[95.0]",
        ),
        (
            "time: mean within days time: max over days time: mean over days models: percentile[95]",
            False,
            "percentile[95.0]",
        ),
        ("time: maximum time: mean over days", True, "mean",),
        ("time: maximum time: mean over days", False, "mean"),
        ("time: maximum time: mean over days models: mean", True, "mean",),
        ("time: maximum time: mean over days models: mean", False, "mean",),
        (
            "time: minimum within days time: count within years where > 25 C",
            True,
            "mean",
        ),
        (
            "time: minimum within days time: count within years where > 25 C",
            False,
            False,
        ),
        ("unspecified", True, "mean",),
        ("unspecified", False, False,),
        ("time: standard_deviation over days time: mean over days", True, "mean",),
        ("time: standard_deviation over days time: mean over days", False, "mean",),
    ),
)
def test_get_climatological_statistic(cell_methods, default_to_mean, expected):
    assert get_climatological_statistic(cell_methods, default_to_mean) == expected
