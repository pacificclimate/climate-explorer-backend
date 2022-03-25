import pytest
from ce.api.streamflow.downstream import downstream_worker
from test_utils import check_dict_subset


@pytest.mark.parametrize(
    "lon, lat, expected",
    (
        (
            0.3,
            50.8,
            {
                "boundary": {
                    "type": "Feature",
                    "properties": {
                        "starting point": {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": (0.3, 50.8)},
                        }
                    },
                },
            },
        ),
        (
            0.19,
            50.78,
            {
                "boundary": {
                    "type": "Feature",
                    "properties": {
                        "starting point": {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": (0.2, 50.8)},
                        }
                    },
                },
            },
        ),
        (
            0.3,
            50.6,
            {
                "boundary": {
                    "type": "Feature",
                    "properties": {
                        "starting point": {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": (0.3, 50.6)},
                        }
                    },
                },
            },
        ),
    ),
)
def test_downstream_worker(
    lon, lat, expected, flow_direction_1,
):
    result = downstream_worker((lon, lat), flow_direction_1,)
    check_dict_subset(expected, result)
