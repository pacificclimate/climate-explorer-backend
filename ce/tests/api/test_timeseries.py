from datetime import datetime
from time import time
import pytest

from ce.api import timeseries


@pytest.mark.parametrize(
    ("unique_id", "var"),
    (("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),),
)
def test_timeseries(populateddb_session, polygon, unique_id, var):
    sesh = populateddb_session
    rv = timeseries(sesh, unique_id, polygon, var)
    for key in ("id", "data", "units"):
        assert key in rv
    assert rv["id"] == unique_id
    assert set(rv["data"].keys()) == {
        "1985-01-15T00:00:00Z",
        "1985-08-15T00:00:00Z",
        "1985-04-15T00:00:00Z",
        "1985-09-15T00:00:00Z",
        "1985-06-15T00:00:00Z",
        "1985-12-15T00:00:00Z",
        "1985-05-15T00:00:00Z",
        "1985-02-15T00:00:00Z",
        "1985-03-15T00:00:00Z",
        "1985-07-15T00:00:00Z",
        "1985-10-15T00:00:00Z",
        "1985-11-15T00:00:00Z",
    }
    for val in rv["data"].values():
        assert type(val) == float
    assert rv["units"] == "K"
    assert isinstance(rv["modtime"], datetime)


# verifies that different months or seasons of an annual timeseries
# have different values
@pytest.mark.parametrize(
    "unique_id,var",
    [
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),
        ("tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin"),
        ("tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),
        ("tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin"),
    ],
)
def test_timeseries_annual_variation(populateddb_session, unique_id, var):
    sesh = populateddb_session
    poly = """POLYGON((-265 65,-265 74,-276 74,-276 65,-265 65))"""
    rv = timeseries(sesh, unique_id, poly, var)
    values = set([])
    for val in rv["data"].values():
        assert val not in values
        values.add(val)


@pytest.mark.parametrize(("unique_id"), (None, "", "does-not-exist"))
def test_timeseries_bad_id(populateddb_session, unique_id):
    rv = timeseries(populateddb_session, unique_id, None, None)
    assert rv == {}


@pytest.mark.parametrize(
    ("unique_id", "var"),
    (
        ("tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmax"),
        ("tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", "tasmin"),
    ),
)
def test_timeseries_speed(populateddb_session, polygon, unique_id, var):
    sesh = populateddb_session
    t0 = time()
    timeseries(sesh, unique_id, polygon, var)
    t = time() - t0
    print(t)
    assert t < 3
