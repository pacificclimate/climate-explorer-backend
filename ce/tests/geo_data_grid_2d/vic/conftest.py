import pytest
import numpy
from ce.geo_data_grid_2d.vic import VicDataGrid


# Longitudes


@pytest.fixture
def vic_longitudes_1():
    return numpy.linspace(0.1, 0.3, num=3)


@pytest.fixture
def vic_longitudes_2():
    return numpy.linspace(0.5, 0.6, num=2)


@pytest.fixture
def vic_longitudes_3():
    return numpy.linspace(0.5, 0.6, num=4)


# Latitudes


@pytest.fixture
def vic_latitudes_1():
    return numpy.linspace(50.2, 50.8, num=4)


@pytest.fixture
def vic_latitudes_2():
    return numpy.linspace(51.2, 51.8, num=4)


@pytest.fixture
def vic_data_grid_1(vic_longitudes_1, vic_latitudes_1):
    return VicDataGrid(
        longitudes=vic_longitudes_1,
        latitudes=vic_latitudes_1,
        values=numpy.arange(12).reshape((4, 3)),
        units="units",
    )


@pytest.fixture
def vic_data_grid_2(vic_longitudes_2, vic_latitudes_2):
    return VicDataGrid(
        longitudes=vic_longitudes_2,
        latitudes=vic_latitudes_2,
        values=numpy.ones((4, 2)),
        units="units",
    )


@pytest.fixture
def vic_data_grid_3(vic_longitudes_3, vic_latitudes_1):
    return VicDataGrid(
        longitudes=vic_longitudes_3,
        latitudes=vic_latitudes_1,
        values=numpy.ones((4, 2)),
        units="units",
    )
