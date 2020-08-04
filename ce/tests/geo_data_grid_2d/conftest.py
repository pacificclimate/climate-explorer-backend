import pytest
import numpy
from ce.geo_data_grid_2d import GeoDataGrid2D


@pytest.fixture
def longitudes_1():
    return numpy.linspace(0.1, 0.3, num=3)


@pytest.fixture
def latitudes_1():
    return numpy.linspace(50.2, 50.8, num=4)


@pytest.fixture
def data_grid_1(longitudes_1, latitudes_1):
    return GeoDataGrid2D(
        longitudes=longitudes_1,
        latitudes=latitudes_1,
        values=numpy.arange(12).reshape((4, 3)),
        units="units",
    )
