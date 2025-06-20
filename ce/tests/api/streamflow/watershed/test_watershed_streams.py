import pytest
from ce.api.streamflow.watershed_streams import worker
from test_utils import check_dict_subset


@pytest.mark.parametrize(
    "lon, lat, expected",
    (
        (
            0.1,
            50.6,
            {
                "streams": {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": (((0.1, 50.6), (0.1, 50.4)),),
                    },
                },
            },
        ),
        (
            0.1,
            50.8,
            {
                "streams": {
                    "type": "Feature",
                    "geometry": {
                        "coordinates": (),
                        "type": "MultiLineString",
                    },
                },
            },
        ),
        (
            0.11,
            50.25,
            {
                "streams": {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": (
                            ((0.1, 50.2), (0.2, 50.4), (0.2, 50.6), (0.3, 50.6)),
                            ((0.2, 50.6), (0.3, 50.8)),
                            ((0.2, 50.6), (0.1, 50.8)),
                            ((0.2, 50.6), (0.2, 50.8)),
                        ),
                    },
                },
            },
        ),
        (
            0.19,
            50.47,
            {
                "streams": {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": (
                            ((0.2, 50.4), (0.2, 50.6), (0.3, 50.6)),
                            ((0.2, 50.6), (0.3, 50.8)),
                            ((0.2, 50.6), (0.1, 50.8)),
                            ((0.2, 50.6), (0.2, 50.8)),
                        ),
                    },
                },
            },
        ),
        (
            0.3,
            50.2,
            {
                "streams": {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": (
                            ((0.3, 50.2), (0.3, 50.4)),
                            ((0.3, 50.2), (0.2, 50.2)),
                        ),
                    },
                },
            },
        ),
    ),
)
def test_worker(
    lon,
    lat,
    expected,
    flow_direction_1,
):
    result = worker(
        (lon, lat),
        flow_direction_1,
    )
    check_dict_subset(expected, result)
