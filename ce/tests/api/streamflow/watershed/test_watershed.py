import pytest
from ce.api.streamflow.watershed import worker
from test_utils import check_dict_subset


@pytest.mark.parametrize(
    "lon, lat, expected",
    (
        (
            0.11,
            50.25,
            {
                "elevation": {"units": "m", "minimum": 0, "maximum": 4.1},
                "area": {"units": "m^2", "value": 7},
                "hypsometric_curve": {
                    "elevation_bin_start": 0,
                    "elevation_bin_width": 100,
                    "elevation_num_bins": 46,
                    # 'cumulative_areas': ???,
                    "elevation_units": "m",
                    "area_units": "m^2",
                },
                "melton_ratio": {
                    "units": "km/km",
                    "value": 1.5496543393378315,
                },
                "boundary": {
                    # TODO: more here
                    "type": "Feature",
                    "properties": {
                        "mouth": {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": (0.1, 50.2)},
                        }
                    },
                },
                "debug/test": {"watershed": {"cell_count": 7}},
            },
        ),
        (
            0.19,
            50.47,
            {
                "elevation": {"units": "m", "minimum": 0.9, "maximum": 4.1},
                "area": {"units": "m^2", "value": 6},
                "hypsometric_curve": {
                    "elevation_bin_start": 0,
                    "elevation_bin_width": 100,
                    "elevation_num_bins": 46,
                    # 'cumulative_areas': ???,
                    "elevation_units": "m",
                    "area_units": "m^2",
                },
                "melton_ratio": {
                    "units": "km/km",
                    "value": 1.3063945294843617,
                },
                "boundary": {
                    # TODO: more here
                    "type": "Feature",
                    "properties": {
                        "mouth": {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": (0.2, 50.4)},
                        }
                    },
                },
                "debug/test": {"watershed": {"cell_count": 6}},
            },
        ),
        (
            0.3,
            50.2,
            {
                "elevation": {"units": "m", "minimum": 1.9, "maximum": 3.1},
                "area": {"units": "m^2", "value": 3},
                "hypsometric_curve": {
                    "elevation_bin_start": 0,
                    "elevation_bin_width": 100,
                    "elevation_num_bins": 46,
                    # 'cumulative_areas': ???,
                    "elevation_units": "m",
                    "area_units": "m^2",
                },
                "melton_ratio": {
                    "units": "km/km",
                    "value": 0.692820323027551,
                },
                "boundary": {
                    # TODO: more here
                    "type": "Feature",
                    "properties": {
                        "mouth": {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": (0.3, 50.2)},
                        }
                    },
                },
                "debug/test": {"watershed": {"cell_count": 3}},
            },
        ),
    ),
)
def test_worker(
    lon,
    lat,
    expected,
    flow_direction_1,
    elevation_1,
    elevation_max_1,
    elevation_min_1,
    area_1,
):
    result = worker(
        (lon, lat),
        flow_direction_1,
        elevation_mean=elevation_1,
        elevation_max=elevation_max_1,
        elevation_min=elevation_min_1,
        area=area_1,
    )
    check_dict_subset(expected, result)
