"""module for requesting information on the watershed that drains
to a specified point.

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
from netCDF4 import Dataset
import numpy as np
import math
from contexttimer import Timer

from flask import abort
from sqlalchemy import distinct
from shapely.geometry import Point
from shapely.errors import WKTReadingError
from pint import UnitRegistry

from ce.api.geospatial import (
    geojson_feature,
    outline_cell_rect,
    WKT_point_to_lonlat,
    GeospatialTypeError,
)
from ce.api.util import is_valid_index, vec_add, neighbours
from ce.geo_data_grid_2d import GeoDataGrid2DIndexError
from ce.geo_data_grid_2d.vic import VicDataGrid
from modelmeta import (
    DataFile,
    DataFileVariableGridded,
    Ensemble,
    EnsembleDataFileVariables,
)


def watershed(sesh, station, ensemble_name):
    """Return information describing the watershed that drains to a specified
    point.

    :param sesh: (sqlalchemy.orm.session.Session) A database Session object
    :param station: (string) Location of drainage point, WKT POINT format
    :param ensemble_name: (string) Name of the ensemble containing data files backing
        providing data for this request.
    :return: dict representation for JSON response object with the following
        attributes:
            area: Area of the watershed

            elevation: Minimum and maximum elevations

            shape: A GeoJSON object representing the outline of the watershed;
                a concave hull of the cell rectangles.

            hypsometric_curve: Elevation-area histogram of the watershed

    This function is primarily responsible for finding the relevant data files
    and converting their contents to `VicDataGrid` objects for consumption by
    `worker`, which as its name suggests, does most of the work.
    """
    try:
        station_lonlat = WKT_point_to_lonlat(station)
    except WKTReadingError:
        abort(400, description="Station lon-lat coordinates are not valid WKT syntax")
        return
    except GeospatialTypeError as e:
        print("##### GeospatialTypeError")
        abort(400, description="Station must be a WKT POINT: {}".format(e.message))

    with get_time_invariant_variable_dataset(
        sesh, ensemble_name, "flow_direction"
    ) as flow_direction_ds, get_time_invariant_variable_dataset(
        sesh, ensemble_name, "elev"
    ) as elevation_ds, get_time_invariant_variable_dataset(
        sesh, ensemble_name, "elevmin"
    ) as elevation_min_ds, get_time_invariant_variable_dataset(
        sesh, ensemble_name, "elevmax"
    ) as elevation_max_ds, get_time_invariant_variable_dataset(
        sesh, ensemble_name, "area"
    ) as area_ds:
        try:
            return worker(
                station_lonlat,
                flow_direction=VicDataGrid.from_nc_dataset(
                    flow_direction_ds, "flow_direction"
                ),
                elevation_mean=VicDataGrid.from_nc_dataset(elevation_ds, "elev"),
                elevation_max=VicDataGrid.from_nc_dataset(elevation_max_ds, "elevmax"),
                elevation_min=VicDataGrid.from_nc_dataset(elevation_min_ds, "elevmin"),
                area=VicDataGrid.from_nc_dataset(area_ds, "area"),
            )
        except GeoDataGrid2DIndexError:
            abort(
                404,
                description="Station lon-lat coordinates are not within the area "
                "for which we have data.",
            )


def worker(
    station_lonlat,
    flow_direction,
    elevation_mean,
    elevation_max,
    elevation_min,
    area,
    hypso_params=None,
):
    """Compute the watershed endpoint response.

    This function exists to make these computations more easily testable.
    (Specifically, data *files* are not required, only the relevant contents
    of those files passed as `VicDataGrid` objects. `VicDataGrid`s are much easier to
    construct for tests.)

    :param station_lonlat: (tuple) Location of drainage point, (lon, lat)
    :param flow_direction: (VicDataGrid) Flow direction grid
    :param elevation_mean: (VicDataGrid) Mean elevation per grid cell, used for hypsometry
    :param elevation_max: (VicDataGrid) Maximum elevation per grid cell, used for Melton Ratio
    :param elevation_min: (VicDataGrid) Minimum elevation per grid cell, used for Melton Ratio
    :param area: (VicDataGrid) Area grid
    :return: (dict) representation for JSON response object; see watershed() for details
    """
    if hypso_params is None:
        # Default parameters cover total range of BC elevations from
        # sea level to highest point, Mt. Fairweather, at 4,663 m.
        hypso_params = {
            "bin_start": 0,
            "bin_width": 100,
            "num_bins": 46,
        }
    ureg = UnitRegistry()

    # check that all grids match
    if not flow_direction.is_compatible(elevation_mean):
        raise ValueError("Flow direction and elevation do not have compatible grids")
    if not flow_direction.is_compatible(area):
        raise ValueError("Flow direction and area do not have compatible grids")
    if not flow_direction.is_compatible(elevation_max):
        raise ValueError(
            "Flow direction and elevation maximum do not have compatible grids"
        )
    if not flow_direction.is_compatible(elevation_min):
        raise ValueError(
            "Flow direction and elevation minimum do not have compatible grids"
        )

    # check that datasets have compatible units
    if not ureg(elevation_mean.units).check("[length]"):
        raise ValueError(
            "Elevation units not recognized: {}".format(elevation_mean.units)
        )
    if not ureg(elevation_max.units).check("[length]"):
        raise ValueError(
            "Elevation maximum units not recognized: {}".format(elevation_max.units)
        )
    if not ureg(elevation_min.units).check("[length]"):
        raise ValueError(
            "Elevation units not recognized: {}".format(elevation_min.units)
        )
    if not ureg(area.units).check("[length] [length]"):
        raise ValueError("Area units not recognized: {}".format(elevation.units))

    # Compute lonlats of watershed whose mouth is at `station`
    # TODO: Refactor to accept a VicDataGrid?
    direction_matrix = VIC_direction_matrix(
        flow_direction.lat_step, flow_direction.lon_step
    )

    with Timer() as watershed_time:
        watershed_xys = build_watershed(
            flow_direction.lonlat_to_xy(station_lonlat),
            flow_direction.values,
            direction_matrix,
            debug=True,
        )

    # `watershed_lonlats`, `elevations`, and `areas` must all be ordered
    # collections (not sets) because it is required (at minimum) that the
    # coordinates (lonlats) for `elevations[i]` and `areas[i]` be equal for
    # all `i`.
    watershed_lonlats = [flow_direction.xy_to_lonlat(xy) for xy in watershed_xys]

    #  Compute elevations at each lonlat of watershed
    ws_elevations = elevation_mean.get_values_at_lonlats(watershed_lonlats)

    #  Compute area of each cell in watershed
    ws_areas = area.get_values_at_lonlats(watershed_lonlats)

    #  Get the maximum and minimum elevation of each cell
    ws_elevation_maximums = elevation_max.get_values_at_lonlats(watershed_lonlats)
    ws_elevation_minimums = elevation_min.get_values_at_lonlats(watershed_lonlats)

    # Compute the elevation/area curve
    cumulative_areas = hypsometry(ws_elevations, ws_areas, **hypso_params)

    # Compute outline of watershed as a GeoJSON feature
    outline = outline_cell_rect(
        watershed_lonlats, flow_direction.lat_step, flow_direction.lon_step
    )

    outlet_elevation = min(ws_elevation_minimums)
    source_elevation = max(ws_elevation_maximums)
    total_area = sum(ws_areas)
    m_ratio = compute_melton_ratio(
        source_elevation,
        elevation_max.units,
        outlet_elevation,
        elevation_min.units,
        total_area,
        area.units,
    )

    return {
        "elevation": {
            "units": elevation_mean.units,
            "minimum": outlet_elevation,
            "maximum": source_elevation,
        },
        "area": {"units": area.units, "value": total_area},
        "hypsometric_curve": {
            "elevation_bin_start": hypso_params["bin_start"],
            "elevation_bin_width": hypso_params["bin_width"],
            "elevation_num_bins": hypso_params["num_bins"],
            "cumulative_areas": cumulative_areas,
            "elevation_units": elevation_mean.units,
            "area_units": area.units,
        },
        "melton_ratio": {"units": "km/km", "value": m_ratio,},
        "boundary": geojson_feature(
            outline,
            properties={
                "mouth": geojson_feature(
                    Point(
                        flow_direction.xy_to_lonlat(
                            flow_direction.lonlat_to_xy(station_lonlat)
                        )
                    ),
                )
            },
        ),
        "debug/test": {
            "watershed": {
                "cell_count": len(watershed_xys),
                "time": watershed_time.elapsed,
            }
        },
    }


def build_watershed(target, routing, direction_map, debug=False):
    """
    Return set of all cells (including target) that drain into `target`.

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
    :return: Set of cells (cell indices) that drain into `target`.

    Algorithm is operator closure of "upstream" over cell neighbours.

    Notes:

    - In this function, a cell is represented by an (x, y) index pair.

    - Routing graphs can and in practice do contain cycles. Variable `visited`
    is used to determine whether a cell has already been visited during the
    traversal of the routing graph, i.e., whether we are cycling, and if so
    not to repeat that subgraph.
    """
    visited = set()

    def is_upstream(neighbour, cell):
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

    def upstream(cell):
        """Return all cells upstream of `cell`.
        This is the closure of upstream over cell neighbours.
        """
        nonlocal visited
        visited |= {cell}
        return {cell}.union(
            *(
                upstream(neighbour)
                for neighbour in neighbours(cell)
                if neighbour not in visited and is_upstream(neighbour, cell)
            )
        )

    return upstream(target)


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


def hypsometry(elevations, areas, bin_start=0, bin_width=100, num_bins=46):
    """
    Computes a hypsometric curve as a histogram of areas by elevation.

    :param elevations: list of elevations; location is not specified but
        must be consistent with locations of areas
    :param areas: list of areas; location is not specified but
        must be consistent with locations of elevations
    :param bin_start: lowest elevation; lower bound of elevation bin 0
    :param bin_width: width of elevation bins
    :param num_bins: number of elevation bins
    :return: list of total areas in each elevation bin;
            indexed same as bin_centres

    Binning is "clipped": Any elevation below bin_start is placed in bin 0;
    any elevation above (bin_start + num_bins * bin_width) is placed in bin
    (num_bins - 1).
    """

    if len(elevations) != len(areas):
        raise IndexError(
            "elevations ({}) and areas ({}) do not have same lengths".format(
                len(elevations), len(areas)
            )
        )

    cumulative_areas = [0] * num_bins

    def clip(index):
        return max(0, min(num_bins - 1, index))

    for elevation, area in zip(elevations, areas):
        bin = clip(math.floor((elevation - bin_start) / bin_width))
        cumulative_areas[bin] += area

    return cumulative_areas


def compute_melton_ratio(
    elevation_max,
    elevation_max_units,
    elevation_min,
    elevation_min_units,
    area,
    area_units,
):
    """The change in elevation over a watershed divided by the square root of the watershed area"""
    ureg = UnitRegistry()
    elev_delta = elevation_max * ureg(elevation_max_units) - elevation_min * ureg(
        elevation_min_units
    )
    area_sqrt = (area * ureg(area_units)) ** 0.5
    melton_ratio = elev_delta / area_sqrt
    if melton_ratio.check("[]"):  # ensure dimensionlessness
        return melton_ratio.magnitude
    raise ValueError(
        "Area and elevation units are not compatible: {}, {}, and {}".format(
            elevation_max_units, elevation_min_units, area_units
        )
    )
