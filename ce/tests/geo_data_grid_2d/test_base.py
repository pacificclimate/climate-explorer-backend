import pytest


def test_properties(data_grid_1):
    assert len(data_grid_1.longitudes) == 3
    assert len(data_grid_1.latitudes) == 4
    assert data_grid_1.values.shape == (4, 3)
    assert data_grid_1.units == 'units'


