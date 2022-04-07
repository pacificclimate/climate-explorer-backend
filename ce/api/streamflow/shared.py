"""module for shared functions between watershed and watershed_streams"""

from netCDF4 import Dataset
import numpy as np
import math

from sqlalchemy import distinct
from shapely.errors import WKTReadingError

from flask import abort
from ce.api.geospatial import WKT_point_to_lonlat, GeospatialTypeError
from ce.api.util import is_valid_index, vec_add
from modelmeta import (
    DataFile,
    DataFileVariableGridded,
    Ensemble,
    EnsembleDataFileVariables,
)


def setup(station):
    try:
        station_lonlat = WKT_point_to_lonlat(station)
    except WKTReadingError:
        abort(400, description="Station lon-lat coordinates are not valid WKT syntax")
        return
    except GeospatialTypeError as e:
        print("##### GeospatialTypeError")
        abort(400, description="Station must be a WKT POINT: {}".format(e.message))
    return station_lonlat


def is_upstream(neighbour, cell, routing, direction_map):
    """Return a boolean indicating whether `neighbour` is upstream of `cell`
    according to the routing matrix and direction map."""
    # Eliminate invalid cases
    if not is_valid_index(neighbour, routing.shape):
        return False
    neighbour_routing = routing[neighbour]
    if neighbour_routing is np.ma.masked:
        return False
    # `neighbour` is upstream if its routing points back at `cell`
    return vec_add(neighbour, direction_map[int(neighbour_routing)]) == cell


def is_downstream(neighbour, cell, routing, direction_map):
    """Return a boolean indicating whether `neighbour` is downstream of `cell`
    according to the routing matrix and direction map."""
    # Eliminate invalid cases
    if not is_valid_index(neighbour, routing.shape):
        return False
    cell_routing = routing[cell]
    # `neighbour` is downstream of `cell` if `cell`'s routing points at `neighbour`
    return vec_add(cell, direction_map[int(cell_routing)]) == neighbour


def VIC_direction_matrix(lat_step, lon_step):
    """ Return a VIC direction matrix, which is a matrix indexed by the VIC
    streamflow direction codes 0...9, with the value at index `i` indicating
    the offsets from the data index in a streamflow file required to
    step in that streamflow direction.

    :param lat_step: Difference between two successive latitudes in streamflow
        file. (Only) sign matters.
    :param lon_step: Difference between two successive longitudes in streamflow
        file. (Only) sign matters.
    :return: tuple of offset pairs

    The offsets must account for the sign of the step in the lat and lon
    dimensions in the streamflow file.
    For example, in a streamflow file with lat and lon both increasing with
    increasing index, the offset to step northeast is [1, 1].

    Note that argument order is (lat, lon), not (lon, lat).
    """
    base = (
        (0, 0),  # filler - 0 is not used in the encoding
        (1, 0),  # 1 = north
        (1, 1),  # 2 = northeast
        (0, 1),  # 3 = east
        (-1, 1),  # 4 = southeast
        (-1, 0),  # 5 = south
        (-1, -1),  # 6 = southwest
        (0, -1),  # 7 = west
        (1, -1),  # 8 = northwest
        (0, 0),  # 9 = outlet
    )
    lat_dir = int(math.copysign(1, lat_step))
    lon_dir = int(math.copysign(1, lon_step))
    return tuple(
        (lat_dir * lat_base, lon_dir * lon_base) for lat_base, lon_base in base
    )


def get_time_invariant_variable_dataset(sesh, ensemble_name, variable):
    """Locates and opens a time-invariant dataset.
    These datasets contain things like elevation or area of a grid cell -
    they're independent of time and there should be only one per ensemble.
    If more or less than one is found in the ensemble, it raises an error

    :param sesh: (sqlalchemy.orm.session.Session) A database Session object
    :param ensemble_name: Name of the ensemble containing data files
    :param variable: Name of *variable* inside dataset. This is not the
        dataset filename or unique id.
    :return: (netcdf.Dataset) netcdf Dataset object representing the file.
    """
    query = (
        sesh.query(distinct(DataFile.filename).label("filename"))
        .join(DataFileVariableGridded, EnsembleDataFileVariables, Ensemble,)
        .filter(Ensemble.name == ensemble_name)
        .filter(DataFileVariableGridded.netcdf_variable_name == variable)
        .filter(DataFile.time_set_id.is_(None))
    )

    file = query.one()  # Raises exception if n != 1 results found
    return Dataset(file.filename, "r")
