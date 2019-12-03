import pytest
import numpy
from ce.api.streamflow.watershed import DataGrid
from test_utils import np_array, \
    N, NE, E, SE, S, SW, W, NW, O


# Longitudes

@pytest.fixture
def longitudes_1():
    return numpy.linspace(0.1, 0.3, num=3)


@pytest.fixture
def longitudes_2():
    return numpy.linspace(0.5, 0.6, num=2)


@pytest.fixture
def longitudes_3():
    return numpy.linspace(0.5, 0.6, num=4)


# Latitudes

@pytest.fixture
def latitudes_1():
    return numpy.linspace(50.2, 50.8, num=4)


@pytest.fixture
def latitudes_2():
    return numpy.linspace(51.2, 51.8, num=4)


# Data grids

@pytest.fixture
def data_grid_1(longitudes_1, latitudes_1):
    return DataGrid(
        longitudes=longitudes_1,
        latitudes=latitudes_1,
        values=numpy.arange(12).reshape((4, 3)),
        units='units'
    )


@pytest.fixture
def data_grid_2(longitudes_2, latitudes_2):
    return DataGrid(
        longitudes=longitudes_2,
        latitudes=latitudes_2,
        values=numpy.ones((4, 2)),
        units='units'
    )


@pytest.fixture
def data_grid_3(longitudes_3, latitudes_1):
    return DataGrid(
        longitudes=longitudes_3,
        latitudes=latitudes_1,
        values=numpy.ones((4, 2)),
        units='units'
    )


@pytest.fixture
def flow_direction_1(longitudes_1, latitudes_1):
    return DataGrid(
        longitudes=longitudes_1,  # len = 3
        latitudes=latitudes_1,    # len = 4
        values=np_array((
            (SE,  S, SW),
            ( W,  S,  W),
            ( N, SW,  S),
            ( O,  E,  E),
        ))
    )


@pytest.fixture
def elevation_1(longitudes_1, latitudes_1):
    return DataGrid(
        longitudes=longitudes_1,  # len = 3
        latitudes=latitudes_1,    # len = 4
        values=np_array((
            (3, 4, 3),
            (2, 2, 3),
            (3, 1, 3),
            (0, 3, 2),
        )),
        units='m'
    )


@pytest.fixture
def area_1(longitudes_1, latitudes_1):
    return DataGrid(
        longitudes=longitudes_1,  # len = 3
        latitudes=latitudes_1,    # len = 4
        values=numpy.ones((4, 3)),
        units='m2'
    )
