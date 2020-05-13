import inspect
import pytest
from ce.geo_data_grid_2d.vic import VicDataGrid, VicDataGridNonuniformCoordinateError


@pytest.mark.parametrize(
    "args, expected",
    [
        # Uniform coordinate steps
        (dict(longitudes=(0, 1, 2), latitudes=(0, 2, 4)), (1, 2),),
        # Nonuniform longitude steps
        (
            dict(longitudes=(0, 1, 3), latitudes=(0, 2, 4)),
            VicDataGridNonuniformCoordinateError,
        ),
        # Nonuniform latitude steps
        (
            dict(longitudes=(0, 1, 2), latitudes=(0, 2, 3)),
            VicDataGridNonuniformCoordinateError,
        ),
    ],
)
def test_coordinates(args, expected):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            grid = VicDataGrid(**args, values=None)
    else:
        grid = VicDataGrid(**args, values=None)
        assert grid.lon_step, grid.lat_step == expected


@pytest.mark.parametrize(
    "grid_1_args, grid_2_args, expected",
    [
        # Compatible cases
        # Identical grids
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            True,
        ),
        # Offset longitudes, coinciding
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(2, 3), latitudes=(0, 2)),
            True,
        ),
        # Offset latitudes, coinciding
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(0, 1), latitudes=(4, 6)),
            True,
        ),
        # Offset longitudes and latitudes, coinciding
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(2, 3), latitudes=(4, 6)),
            True,
        ),
        # Incompatible cases
        # Different longitude step size
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(0, 2), latitudes=(0, 2)),
            False,
        ),
        # Different latitude step size
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(0, 1), latitudes=(0, 1)),
            False,
        ),
        # Same step size, offset longitudes, not coinciding
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(2.1, 3.1), latitudes=(0, 2)),
            False,
        ),
        # Same step size, offset latitudes, not coinciding
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(0, 1), latitudes=(4.1, 6.1)),
            False,
        ),
        # Same step size, offset longitudes and latitudes, not coinciding
        (
            dict(longitudes=(0, 1), latitudes=(0, 2)),
            dict(longitudes=(2.1, 3.1), latitudes=(4.2, 6.2)),
            False,
        ),
    ],
)
def test_is_compatible(grid_1_args, grid_2_args, expected):
    grid_1 = VicDataGrid(**grid_1_args, values=None)
    grid_2 = VicDataGrid(**grid_2_args, values=None)
    assert grid_1.is_compatible(grid_2) == expected


@pytest.mark.parametrize(
    "lon, y", ((0.051, 0), (0.1, 0), (0.149, 0), (0.151, 1), (0.2, 1), (0.249, 1),)
)
@pytest.mark.parametrize(
    "lat, x", ((50.11, 0), (50.2, 0), (50.29, 0), (50.31, 1), (50.4, 1), (50.49, 1),)
)
def test_lonlat_to_xy(lon, lat, x, y, vic_data_grid_1):
    assert vic_data_grid_1.lonlat_to_xy((lon, lat)) == (x, y)


@pytest.mark.parametrize("y, lon", ((0, 0.1), (1, 0.2), (2, 0.3),))
@pytest.mark.parametrize("x, lat", ((0, 50.2), (1, 50.4), (3, 50.8),))
def test_xy_to_lonlat(x, y, lon, lat, vic_data_grid_1):
    assert vic_data_grid_1.xy_to_lonlat((x, y)) == (lon, lat)


def test_get_values_at_lonlats(vic_data_grid_1):
    assert vic_data_grid_1.get_values_at_lonlats(
        ((0.1, 50.2), (0.2, 50.4), (0.3, 50.8))
    ) == [0, 4, 11]
