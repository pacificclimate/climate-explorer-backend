from datetime import datetime
import math
import pytest

from ce.api import stats


@pytest.mark.online
@pytest.mark.parametrize(
    "unique_id, var_name, is_thredds",
    [
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax", False),
        ("tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax", False),
        ("tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax", False),
        ("tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin", False),
        ("tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin", "false"),
        ("tasmin_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin", "false"),
        (
            "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230_test",
            "tasmax",
            "true",
        ),
        (
            "tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230_test",
            "tasmin",
            True,
        ),
    ],
)
def test_stats(
    populateddb_session, polygon, mock_thredds_url_root, unique_id, var_name, is_thredds
):
    sesh = populateddb_session
    rv = stats(sesh, unique_id, None, polygon, var_name, is_thredds)
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
def test_stats_bad_params(populateddb_session, unique_id, var):
    sesh = populateddb_session

    rv = stats(sesh, unique_id, None, None, var)
    assert math.isnan(rv[unique_id]["max"])
    assert "time" not in rv[unique_id]
    assert "units" not in rv[unique_id]
    assert "modtime" not in rv[unique_id]


def test_stats_bad_id(populateddb_session):
    rv = stats(populateddb_session, "id-does-not-exist", None, None, None)
    assert rv == {}
