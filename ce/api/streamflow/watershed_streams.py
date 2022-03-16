"""module for requesting information on the streamflow connectivity
upstream of a point on the watershed

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
from shapely.geometry import MultiLineString
from shapely.errors import WKTReadingError

from ce.api.geospatial import geojson_feature
from ce.api.util import neighbours
from ce.geo_data_grid_2d import GeoDataGrid2DIndexError
from ce.geo_data_grid_2d.vic import VicDataGrid
from ce.api.streamflow.shared import (
    setup,
    is_upstream,
    VIC_direction_matrix,
    get_time_invariant_variable_dataset,
)


def watershed_streams(sesh, station, ensemble_name):
    """Return information describing the watershed that drains to a specified
    point.

    :param sesh: (sqlalchemy.orm.session.Session) A database Session object
    :param station: (string) Location of drainage point, WKT POINT format
    :param ensemble_name: (string) Name of the ensemble containing data files backing
        providing data for this request.
    :return: dict representation for JSON response object with the following
        attributes:
            Lines: A GeoJSON MultiLineString representing the streams of the watershed;

    This function is primarily responsible for finding the relevant data files
    and converting their contents to `VicDataGrid` objects for consumption by
    `worker`, which as its name suggests, does most of the work.
    """
    station_lonlat = setup(station)

    with get_time_invariant_variable_dataset(
        sesh, ensemble_name, "flow_direction"
    ) as flow_direction_ds:
        try:
            return worker(
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


def worker(
    station_lonlat, flow_direction,
):
    """Compute the watershed streamflow.

    This function exists to make these computations more easily testable.
    (Specifically, data *files* are not required, only the relevant contents
    of those files passed as `VicDataGrid` objects. `VicDataGrid`s are much easier to
    construct for tests.)

    :param station_lonlat: (tuple) Location of drainage point, (lon, lat)
    :param flow_direction: (VicDataGrid) Flow direction grid
    :return: (dict) representation for JSON response object; see watershed() for details
    """

    # Compute lonlats of watershed whose mouth is at `station`
    # TODO: Refactor to accept a VicDataGrid?
    direction_matrix = VIC_direction_matrix(
        flow_direction.lat_step, flow_direction.lon_step
    )

    with Timer() as watershed_time:
        watershed_xys = build_watershed_streams(
            flow_direction.lonlat_to_xy(station_lonlat),
            flow_direction.values,
            direction_matrix,
            debug=True,
        )

    # `watershed_lonlats` must be an ordered collection (not sets) because
    # a multi line string is an array (python list) of linestrings
    watershed_lonlats = [[]]
    counter = 0

    for frozen in watershed_xys:
        for xy in frozen:
            watershed_lonlats[counter].append(flow_direction.xy_to_lonlat(xy))
        counter += 1
        watershed_lonlats.append([])

    if watershed_lonlats[-1] == []:
        watershed_lonlats.remove([])

    lines = MultiLineString(watershed_lonlats)

    return {
        "streams": geojson_feature(lines,),
        "debug/test": {"watershed_streams": {"time": watershed_time.elapsed,}},
    }


def build_watershed_streams(target, routing, direction_map, debug=False):
    """
    Return set of all paths of cells that drain into `target`.

    :param target: An xy index representing the cell of interest.
    :param routing: A numpy array representing water flow using VIC direction
        codes (0 - 9). These codes may be integers or floats.
    :param direction_map: Maps VIC direction codes into offsets in cell indices.
        Necessary because, depending on whether lon and lat dimensions
        increase or decrease with increasing index, a move north or east is
        represented by an offset of +1 or -1, respectively.
        TODO: Compute this internally?
    :param debug: Boolean indicating whether this function should compute
        and return debug information.
    :return: Set of frozensets of cells (streams) that drain into `target`.

    Notes:

    - In this function, a cell is represented by an (x, y) index pair.

    - Routing graphs can and in practice do contain cycles. Variable `visited`
    is used to determine whether a cell has already been visited during the
    traversal of the routing graph, i.e., whether we are cycling, and if so
    not to repeat that subgraph.
    """
    visited = set()
    i = 0
    connection = [[]]

    def upstream(cell):
        """Return graph description of how the stream is connected
        by movement of water"""
        nonlocal visited
        nonlocal i
        nonlocal connection

        visited |= {cell}
        connection[i].append(cell)
        for neighbour in neighbours(cell):
            if neighbour not in visited and is_upstream(
                neighbour, cell, routing, direction_map
            ):
                upstream(neighbour)
                connection.append([])
                i += 1
                connection[i].append(cell)
        return connection

    connection = upstream(target)
    return set(frozenset(i) for i in connection if len(i) > 1)