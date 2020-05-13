from datetime import datetime
from json import loads
from dateutil.parser import parse
import re
import pytest

from ce.api import find_modtime


@pytest.mark.parametrize(
    ("endpoint", "query_params"),
    [
        ("stats", {"id_": "", "time": "", "area": "", "variable": ""}),
        (
            "data",
            {"model": "", "emission": "", "time": "0", "area": "", "variable": ""},
        ),
        ("timeseries", {"id_": "", "area": "", "variable": ""}),
        ("models", {}),
        (
            "metadata",
            {"model_id": "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230"},
        ),
        ("multimeta", {"model": ""}),
        ("lister", {"model": ""}),
        ("grid", {"id_": ""}),
    ],
)
def test_api_endpoints_are_callable(test_client, cleandb, endpoint, query_params):
    url = "/api/" + endpoint
    response = test_client.get(url, query_string=query_params)
    assert response.status_code == 200
    assert response.cache_control.public is True
    assert response.cache_control.max_age > 0
    if endpoint not in ("models", "lister"):
        assert response.last_modified is not None


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
