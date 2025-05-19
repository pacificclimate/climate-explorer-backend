from datetime import datetime
from dateutil.parser import parse
import pytest

from ce.api import data


@pytest.mark.parametrize(
    ("model", "scenario"), (("", ""), (None, None), ("cgcm19", "rcp45"))
)
def test_data_bad_model_scenario(populateddb_session, model, scenario):
    rv = data(populateddb_session, model, scenario, 1, None, "tasmax")
    assert rv == {}


def test_data_bad_time(populateddb_session):
    with pytest.raises(Exception) as exc:
        data(populateddb_session, "", "", "time-not-an-int", "", "")
    assert 'time parameter "time-not-an-int" not convertable to an integer.' == str(
        exc.value
    )


@pytest.mark.online
@pytest.mark.parametrize(
    "variable,climatological_statistic",
    (
        ("tasmax", "standard_deviation"),
        ("tasmin", "mean"),
    ),
)
@pytest.mark.parametrize(
    "timescale, time_idx, expected_ymd",
    (
        ("monthly", 8, (1985, 9, 15)),
        ("seasonal", 2, (1985, 7, 15)),
        ("yearly", 0, (1985, 7, 2)),
    ),
)
def test_data_single_file(
    populateddb_session,
    mock_thredds_url_root,
    variable,
    climatological_statistic,
    timescale,
    time_idx,
    expected_ymd,
):
    rv = data(
        populateddb_session,
        model="BNU-ESM",
        emission="historical",
        area=None,
        variable=variable,
        timescale=timescale,
        time=time_idx,
        ensemble_name="ce",
        climatological_statistic=climatological_statistic,
    )

    assert len(rv) == 1
    expected_run = "r1i1p1"
    assert expected_run in rv
    assert "data" in rv[expected_run]

    for run_id, run_value in rv.items():
        assert len(run_value["data"]) >= 1
        for time_str, value in run_value["data"].items():
            time = parse(time_str)
            assert (time.year, time.month, time.day) == expected_ymd
            assert 173 <= value <= 373  # -100 to +100 C, in K
        # FIXME: Or, fix something: units are wrong! Its K, not C.
        assert run_value["units"] == "degC"
        assert isinstance(run_value["modtime"], datetime)


def test_data_multiple_times(multitimedb_session):
    rv = data(
        multitimedb_session,
        model="BNU-ESM",
        emission="rcp45",
        time=0,
        area=None,
        variable="tasmax",
        timescale="other",
        ensemble_name="ce",
    )
    assert len(rv) > 1
    for run in rv.values():
        assert len(run["data"]) > 1
        assert isinstance(run["modtime"], datetime)
