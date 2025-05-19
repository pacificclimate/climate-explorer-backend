from datetime import datetime
import pytest

from ce.api import metadata


@pytest.mark.parametrize(
    "unique_id",
    (
        "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
        "tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
    ),
)
@pytest.mark.parametrize("extras", (None, "", "filepath", "filepath,obviouslywrong"))
def test_metadata(populateddb_session, unique_id, extras):
    sesh = populateddb_session
    rv = metadata(sesh, unique_id, extras=extras)
    assert unique_id in rv
    file_metadata = rv[unique_id]

    for key in [
        "institution",
        "model_id",
        "model_name",
        "experiment",
        "variables",
        "units",
        "ensemble_member",
        "times",
        "timescale",
        "multi_year_mean",
        "start_date",
        "end_date",
        "modtime",
    ]:
        assert key in file_metadata

    if extras is not None and "filepath" in extras:
        assert f"{unique_id}.nc" in file_metadata["filepath"]

    times = file_metadata["times"]
    assert len(times) > 0

    # Are the values proper datetimes?
    for val in times.values():
        assert isinstance(val, datetime)

    if file_metadata["multi_year_mean"] is True:
        assert isinstance(file_metadata["start_date"], datetime)
        assert isinstance(file_metadata["end_date"], datetime)
    else:
        assert file_metadata["start_date"] is None
        assert file_metadata["end_date"] is None

    assert isinstance(file_metadata["modtime"], datetime)


def test_metadata_no_times(populateddb_session):
    sesh = populateddb_session
    rv = metadata(sesh, "file1")
    assert rv["file1"]["times"] == {}


def test_metadata_empty(populateddb_session):
    sesh = populateddb_session
    assert metadata(sesh, None) == {}
