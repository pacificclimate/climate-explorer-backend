"""module for requesting information on the downstream watershed that drains
from a specified point.

CAUTION: This code juggles two sets of coordinates: spatial coordinates, and
data indexes. Spatial coordinates (such as the WKT parameter input, or the
geoJSON output) are lon-lat order. But inside the netCDF files, data is
arranged in lat-lon order.

Spatial coordinates variables are named lat and lon. Data indexes variables
are named x and y, and correspond, in the data file arrangement, to x <-> lat
and y <-> lon, the opposite of the usual geographic convention.

Functions `lonlat_to_xy()` and `xy_to_lonlat()`, which translate from a
spatial tuple to a data index tuple and vice versa, also switch the
dimension order accordingly.
"""
from contexttimer import Timer

from flask import abort
from shapely.geometry import Point
from shapely.errors import WKTReadingError

from ce.api.geospatial import (
    geojson_feature,
    path_line,
)
from ce.api.util import is_valid_index, vec_add, neighbours
from ce.geo_data_grid_2d import GeoDataGrid2DIndexError
from ce.geo_data_grid_2d.vic import VicDataGrid

from ce.api.streamflow.shared import (
    setup,
    VIC_direction_matrix,
    get_time_invariant_variable_dataset,
)


def downstream(sesh, station, ensemble_name):
    """Return the downstream watershed that drains from a specifiedpoint.

    :param sesh: (sqlalchemy.orm.session.Session) A database Session object
    :param station: (string) Location of start point, WKT POINT format
    :param ensemble_name: (string) Name of the ensemble containing data files backing
        providing data for this request.
    :return: dict representation for JSON response object with the following
        attributes:
            shape: A GeoJSON object representing the downstream watershed.
    This function is primarily responsible for finding the relevant data files
    and converting their contents to `VicDataGrid` objects for consumption by
    `downstream_worker`, which as its name suggests, does most of the work.
    """
    
    station_lonlat = setup(station)

    with get_time_invariant_variable_dataset(
        sesh, ensemble_name, "flow_direction"
    ) as flow_direction_ds:
        try:
            return downstream_worker(
                station_lonlat,
                flow_direction=VicDataGrid.from_nc_dataset(
                    flow_direction_ds, "flow_direction"
                ),
            )
        except GeoDataGrid2DIndexError:
            abort(
                404,
                description="Station lon-lat coordinates are not within the area "
                "for which we have data.",
            )


def downstream_worker(
    station_lonlat, flow_direction,
):
    """Compute the watershed.

    This function exists to make these computations more easily testable.
    (Specifically, data *files* are not required, only the relevant contents
    of those files passed as `VicDataGrid` objects. `VicDataGrid`s are much easier to
    construct for tests.)

    :param station_lonlat: (tuple) Location of start point, (lon, lat)
    :param flow_direction: (VicDataGrid) Flow direction grid
    :return: (dict) representation for JSON response object; see downstream() for details
    """

    # Compute lonlats of watershed whose starting point is `station`
    direction_matrix = VIC_direction_matrix(
        flow_direction.lat_step, flow_direction.lon_step
    )

    with Timer() as watershed_time:
        watershed_xys = build_downstream_watershed(
            flow_direction.lonlat_to_xy(station_lonlat),
            flow_direction.values,
            direction_matrix,
            debug=True,
        )

    watershed_lonlats = [flow_direction.xy_to_lonlat(xy) for xy in watershed_xys]

    # Compute outline of watershed as a GeoJSON feature
    outline = path_line(watershed_lonlats)

    return {
        "boundary": geojson_feature(
            outline,
            properties={
                "starting point": geojson_feature(
                    Point(
                        flow_direction.xy_to_lonlat(
                            flow_direction.lonlat_to_xy(station_lonlat)
                        )
                    ),
                )
            },
        ),
    }


def build_downstream_watershed(target, routing, direction_map, debug=False):
    """
    Return set of all cells (including target) that drain from `target`.

    :param target: An xy index representing the cell of interest.
    :param routing: A numpy array representing water flow using VIC direction
        codes (0 - 9). These codes may be integers or floats.
    :param direction_map: Maps VIC direction codes into offsets in cell indices.
        Necessary because, depending on whether lon and lat dimensions
        increase or decrease with increasing index, a move north or east is
        represented by an offset of +1 or -1, respectively.
    :param debug: Boolean indicating whether this function should compute
        and return debug information.
    :return: Set of cells (cell indices) that drain from `target`.

    Notes:

    - In this function, a cell is represented by an (x, y) index pair.

    - Routing graphs can and in practice do contain cycles. Variable `visited`
    is used to determine whether a cell has already been visited during the
    traversal of the routing graph, i.e., whether we are cycling, and if so
    not to repeat that subgraph.
    """
    visited = set()

    def is_downstream(neighbour, cell):
        """Return a boolean indicating whether `neighbour` is downstream of `cell`
        according to the routing matrix and direction map."""
        # Eliminate invalid cases
        if not is_valid_index(neighbour, routing.shape):
            return False
        cell_routing = routing[cell]
        # `neighbour` is downstream of `cell` if `cell`'s routing points at `neighbour`
        return vec_add(cell, direction_map[int(cell_routing)]) == neighbour

    def downstream(cell):
        """Return all cells downstream of `cell`.
        This is the closure of downstream over cell neighbours.
        """
        nonlocal visited
        visited |= {cell}
        return {cell}.union(
            *(
                downstream(neighbour)
                for neighbour in neighbours(cell)
                if neighbour not in visited and is_downstream(neighbour, cell)
            )
        )

    return downstream(target)