import pytest


@pytest.mark.parametrize('lon, y', (
    (0.051, 0),
    (0.1, 0),
    (0.149, 0),
    (0.151, 1),
    (0.2, 1),
    (0.249, 1),
))
@pytest.mark.parametrize('lat, x', (
    (50.11, 0),
    (50.2, 0),
    (50.29, 0),
    (50.31, 1),
    (50.4, 1),
    (50.49, 1),
))
def test_lonlat_to_xy(lon, lat, x, y, vic_data_grid_1):
    assert vic_data_grid_1.lonlat_to_xy((lon, lat)) == (x, y)


@pytest.mark.parametrize('y, lon', (
    (0, 0.1),
    (1, 0.2),
    (2, 0.3),
))
@pytest.mark.parametrize('x, lat', (
    (0, 50.2),
    (1, 50.4),
    (3, 50.8),
))
def test_xy_to_lonlat(x, y, lon, lat, vic_data_grid_1):
    assert vic_data_grid_1.xy_to_lonlat((x, y)) == (lon, lat)


def test_get_values_at_lonlats(vic_data_grid_1):
    assert vic_data_grid_1.get_values_at_lonlats(((0.1, 50.2), (0.2, 50.4), (0.3, 50.8))) == \
           [0, 4, 11]


def test_is_compatible(vic_data_grid_1, vic_data_grid_2, vic_data_grid_3):
    assert vic_data_grid_1.is_compatible(vic_data_grid_2)
    assert not vic_data_grid_1.is_compatible(vic_data_grid_3)


