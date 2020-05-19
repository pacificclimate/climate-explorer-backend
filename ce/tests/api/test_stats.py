from datetime import datetime
import math
import pytest

from ce.api import stats


@pytest.mark.parametrize(
    "unique_id, var_name",
    [
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),
        ("tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),
        ("tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),
        ("tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin"),
        ("tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin"),
        ("tasmin_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin"),
    ],
)
def test_stats(populateddb, polygon, unique_id, var_name):
    sesh = populateddb.session
    rv = stats(sesh, unique_id, None, polygon, var_name)
    statistics = rv[unique_id]
    for attr in ("min", "max", "mean", "median", "stdev"):
        value = statistics[attr]
        assert type(value) == float, attr
        assert value >= 0, attr

    for attr in ("units", "time"):
        assert statistics[attr]

    assert type(statistics["ncells"]) == int
    assert isinstance(statistics["time"], datetime)
    assert isinstance(statistics["modtime"], datetime)


# stats() should return NaNs for the values
@pytest.mark.parametrize(
    ("unique_id", "var"),
    (
        # Variable does not exist in file
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "no_variable"),
        # File does not exist on the filesystem
        ("file1", "tasmax"),
    ),
)
def test_stats_bad_params(populateddb, unique_id, var):
    sesh = populateddb.session

    rv = stats(sesh, unique_id, None, None, var)
    assert math.isnan(rv[unique_id]["max"])
    assert "time" not in rv[unique_id]
    assert "units" not in rv[unique_id]
    assert "modtime" not in rv[unique_id]


def test_stats_bad_id(populateddb):
    rv = stats(populateddb.session, "id-does-not-exist", None, None, None)
    assert rv == {}
