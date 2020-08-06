from datetime import datetime
from json import loads
from dateutil.parser import parse
import re
import pytest

from ce.api import find_modtime
from test_utils import check_dict_subset


@pytest.mark.parametrize(
    "endpoint, query_params, expected",
    [
        (
            "stats",
            {"id_": "", "time": "", "area": "", "variable": ""},
            {},
        ),
        (
            "data",
            {"model": "", "emission": "", "time": "0", "area": "", "variable": ""},
            {},
        ),
        (
            "timeseries",
            {"id_": "", "area": "", "variable": ""},
            {},
        ),
        (
            "models",
            {},
            {},
        ),
        (
            "metadata",
            {
                "model_id": "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
            },
            {
                "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230": {
                    "institution": "BNU",
                    "model_id": "BNU-ESM",
                    "experiment": "historical",
                    "variables": {
                        "tasmax": "Daily Maximum Temperature"
                    },
                    "ensemble_member": "r1i1p1",
                    "times": {
                        "0": "1985-01-15T00:00:00Z",
                        "1": "1985-02-15T00:00:00Z",
                        "2": "1985-03-15T00:00:00Z",
                        "3": "1985-04-15T00:00:00Z",
                        "4": "1985-05-15T00:00:00Z",
                        "5": "1985-06-15T00:00:00Z",
                        "6": "1985-07-15T00:00:00Z",
                        "7": "1985-08-15T00:00:00Z",
                        "8": "1985-09-15T00:00:00Z",
                        "9": "1985-10-15T00:00:00Z",
                        "10": "1985-11-15T00:00:00Z",
                        "11": "1985-12-15T00:00:00Z"
                    },
                    "timescale": "monthly",
                    "multi_year_mean": True,
                    "start_date": "1971-01-01T00:00:00Z",
                    "end_date": "2000-12-31T00:00:00Z"
                },
            },
        ),
        (
            "metadata",
            {
                "model_id": "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
                "extras": "filepath",
            },
            {
                "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230": {
                    "institution": "BNU",
                    "filepath": re.compile(
                        r"tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230\.nc"
                    ),
                },
            },
        ),
        (
            "multimeta",
            {"ensemble_name": "ce", "model": ""},
            {
                "CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc": {
                    "institution": "CCCMA",
                    "model_id": "CanESM2",
                    "experiment": "rcp85",
                    "ensemble_member": "r1i1p1",
                    "timescale": "monthly",
                    "multi_year_mean": True,
                    "start_date": "1971-01-01T00:00:00Z",
                    "end_date": "2000-12-31T00:00:00Z",
                    "variables": {
                        "tasmax": "Daily Maximum Temperature",
                    },
                },
            },
        ),
        (
            "multimeta",
            {"ensemble_name": "ce", "model": "", "extras": "filepath"},
            {
                "CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc": {
                    "filepath": re.compile(r"CanESM2-rcp85-tasmax-r1i1p1-2010-2039\.nc"),
                    "institution": "CCCMA",
                },
            },
        ),
        (
            "lister",
            {"model": ""},
            {},
        ),
        (
            "grid",
            {"id_": ""},
            {},
        ),
    ],
)
@pytest.mark.usefixtures("populateddb")
def test_api_endpoint_calls(
    test_client,
    endpoint,
    query_params,
    expected,
):
    url = "/api/" + endpoint
    response = test_client.get(url, query_string=query_params)
    assert response.status_code == 200
    assert response.cache_control.public is True
    assert response.cache_control.max_age > 0
    if endpoint not in ("models", "lister"):
        assert response.last_modified is not None
    check_dict_subset(expected, response.get_json())


def test_dates_are_formatted(test_client, populateddb):
    url = "/api/metadata"
    query_params = {
        "model_id": "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    }
    response = test_client.get(url, query_string=query_params)
    assert response.status_code == 200
    content = loads(response.data.decode(response.charset))

    one_date = parse(content[query_params["model_id"]]["times"]["0"])
    assert isinstance(one_date, datetime)
    another_date = parse(content[query_params["model_id"]]["modtime"])
    assert isinstance(another_date, datetime)


@pytest.mark.parametrize(
    ("endpoint", "missing_params"),
    [
        ("/api/metadata", ["model_id"]),
        ("/api/data", ("model", "emission", "time", "area", "variable")),
    ],
)
def test_missing_query_param(test_client, cleandb, endpoint, missing_params):
    response = test_client.get(endpoint)
    assert response.status_code == 400
    content = response.data.decode(response.charset)
    assert re.search("Missing query params?:", content)
    for param in missing_params:
        assert param in content


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ({}, None),
        ("", None),
        (None, None),
        ({"foo": "bar", "blah": "stuff"}, None),
        ({"foo": {}, "bar": {}}, None),
        ({"foo": {"modtime": datetime(2018, 1, 1)}, "bar": {}}, datetime(2018, 1, 1)),
        ({"modtime": datetime(2018, 1, 1)}, datetime(2018, 1, 1)),
        (
            {
                "modtime": datetime(2018, 1, 1),
                "foo": {"modtime": datetime(2018, 1, 10)},
            },
            datetime(2018, 1, 10),
        ),
        (
            {
                "foo": {"modtime": datetime(2018, 1, 1)},
                "bar": {"modtime": datetime(2018, 1, 10)},
            },
            datetime(2018, 1, 10),
        ),
    ],
)
def test_find_modtime(obj, expected):
    assert find_modtime(obj) == expected
