import pytest

from ce.api import multistats


@pytest.mark.parametrize(
    ("filters", "keys"),
    (
        (
            {"variable": "tasmax", "cell_methods": "standard_deviation"},
            ("CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc", "file2"),
        ),
        (
            {
                "variable": "tasmax",
                "model": "BNU-ESM",
                "cell_methods": "standard_deviation",
            },
            ["tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230"],
        ),
        (
            {
                "variable": "tasmax",
                "timescale": "seasonal",
                "cell_methods": "standard_deviation",
            },
            ["tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230"],
        ),
        (
            {"variable": "tasmin", "model": "BNU-ESM", "cell_methods": "mean"},
            ["tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230"],
        ),
        (
            {"variable": "pr", "model": "BNU-ESM", "cell_methods": "mean"},
            ["pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"],
        ),
    ),
)
def test_multistats(populateddb, filters, keys):
    sesh = populateddb.session
    rv = multistats(sesh, "ce", **filters)
    for key in keys:
        assert key in rv
