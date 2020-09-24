from datetime import datetime
import pytest

from ce.api import multimeta


@pytest.mark.parametrize("model", ("BNU-ESM", "",))
@pytest.mark.parametrize(
    "unique_id",
    (
        "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
        "tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
    ),
)
@pytest.mark.parametrize("extras", (None, "", "filepath", "filepath,obviouslywrong"))
def test_multimeta(populateddb, model, unique_id, extras):
    sesh = populateddb.session
    # Multimeta is wrapped for caching. Call the wrapped function
    rv = multimeta(sesh, ensemble_name="ce", model=model, extras=extras)
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
        "timescale",
        "multi_year_mean",
        "start_date",
        "end_date",
        "modtime",
    ]:
        assert key in file_metadata

    # times are not included in the /multimeta response
    assert "times" not in file_metadata

    if extras is not None and "filepath" in extras:
        assert f"{unique_id}.nc" in file_metadata["filepath"]

    assert file_metadata["model_id"] == "BNU-ESM"
    assert isinstance(file_metadata["modtime"], datetime)
