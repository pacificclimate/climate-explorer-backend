import pytest
import numpy
from ce.geo_data_grid_2d.vic import VicDataGrid
from test_utils import np_array, N, E, SE, S, SW, W, O


# Longitudes


@pytest.fixture
def longitudes_1():
    return numpy.linspace(0.1, 0.3, num=3)


# Latitudes


@pytest.fixture
def latitudes_1():
    return numpy.linspace(50.2, 50.8, num=4)


# Data grids


@pytest.fixture
def flow_direction_1(longitudes_1, latitudes_1):
    return VicDataGrid(
        longitudes=longitudes_1,  # len = 3
        latitudes=latitudes_1,  # len = 4
        values=np_array(((SE, S, SW), (W, S, W), (N, SW, S), (O, E, E),)),
    )


@pytest.fixture
def elevation_1(longitudes_1, latitudes_1):
    return VicDataGrid(
        longitudes=longitudes_1,  # len = 3
        latitudes=latitudes_1,  # len = 4
        values=np_array(((3, 4, 3), (2, 2, 3), (3, 1, 3), (0, 3, 2),)),
        units="m",
    )


@pytest.fixture
def area_1(longitudes_1, latitudes_1):
    return VicDataGrid(
        longitudes=longitudes_1,  # len = 3
        latitudes=latitudes_1,  # len = 4
        values=numpy.ones((4, 3)),
        units="m2",
    )
