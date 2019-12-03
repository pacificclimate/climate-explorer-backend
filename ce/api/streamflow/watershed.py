"""module for requesting information on the watershed that drains
to a specified point.

CAUTION: This code juggles two sets of coordinates: spatial coordinates, and
data indexes. Spatial coordinates (such as the WKT parameter input, or the
geoJSON output) are lon-lat order. But inside the netCDF files, data is
arranged in lat-lon order.

Spatial coordinates are named lat and lon. Data indexes are named x and y,
and correspond to lat and lon.

The functions lonlat_to_xy() and xy_to_lonlat(), which translate from a
spatial tuple to a data index tuple and vice versa, also switch the
dimension order.
"""
from netCDF4 import Dataset
import numpy as np
import math
import time

from sqlalchemy import distinct

from ce.api.geospatial import \
    geojson_feature, outline_cell_rect, outline_point_buff, WKT_point_to_lonlat
from ce.api.util import is_valid_index, vec_add, neighbours
from modelmeta import \
    DataFile, DataFileVariable, Ensemble, EnsembleDataFileVariables


# TODO: Move to utils?
class DataGrid():
    def __init__(self, longitudes, latitudes, values, units=None):
        self.longitudes = longitudes
        self.latitudes = latitudes
        self.values = values
        self.units = units
        self.lon_step = longitudes[1] - longitudes[0]
        self.lat_step = latitudes[1] - latitudes[0]

    @staticmethod
    def from_nc_dataset(dataset, variable_name):
        """Factory method"""
        return DataGrid(
            dataset.variables['lon'],
            dataset.variables['lat'],
            dataset.variables[variable_name],
            dataset.variables[variable_name].units,
        )

    def is_compatible(self, other):
        return math.isclose(self.lon_step, other.lon_step) and \
               math.isclose(self.lat_step, other.lat_step)

    def lonlat_to_xy(self, lonlat):
        """Returns the (x, y) data index for a given lon-lat coordinate,
        switching the order of the coordinates. Checks that the index is
        valid for the grid; we must at minimum exclude negative index values,
        which are valid but wrong in this application."""
        x = int(round((lonlat[1] - self.latitudes[0]) / self.lat_step))
        y = int(round((lonlat[0] - self.longitudes[0]) / self.lon_step))
        if not is_valid_index((x, y), self.values.shape):
            raise ValueError('Foobar!')
        return x, y

    def xy_to_lonlat(self, xy):
        """Returns the lon-lat coordinate for a given xy data index,
        switching the order of the coordinates."""
        if not is_valid_index(xy, self.values.shape):
            raise ValueError('Foobar!')
        return self.longitudes[xy[1]], self.latitudes[xy[0]]

    def get_values_at_lonlats(self, lonlats):
        return [
            float(self.values[self.lonlat_to_xy(lonlat)]) for lonlat in lonlats
        ]


def watershed(sesh, station, ensemble_name):
    station_lonlat = WKT_point_to_lonlat(station)

    with get_time_invariant_variable_dataset(
        sesh, ensemble_name, 'flow_direction'
    ) as flow_direction_ds:
        with get_time_invariant_variable_dataset(
            sesh, ensemble_name, 'elev'
        ) as elevation_ds:
            with get_time_invariant_variable_dataset(
                sesh, ensemble_name, 'area'
            ) as area_ds:
                return worker(
                    station_lonlat,
                    flow_direction=DataGrid.from_nc_dataset(flow_direction_ds, 'flow_direction'),
                    elevation=DataGrid.from_nc_dataset(elevation_ds, 'elev'),
                    area=DataGrid.from_nc_dataset(area_ds, 'area'),
                )


def worker(station_lonlat, flow_direction, elevation, area):
    """

    :param station_lonlat: (tuple) Location of drainage point, (lon, lat)
    :param flow_direction: (DataGrid) Flow direction grid
    :param elevation: (DataGrid) Elevation grid
    :param area: (DataGrid) Area grid
    :return: dict representation for JSON response object with the following
        attributes:
            area: Area of the watershed
            elevation: Minimum and maximum elevations
            shape: A GeoJSON object representing the outline of the watershed;
                a concave hull of the cell rectangles.
            hypsometric_curve: Elevation-area histogram of the watershed
    """
    if not flow_direction.is_compatible(elevation):
        raise ValueError(
            'Flow direction and elevation do not have compatible grids')
    if not flow_direction.is_compatible(area):
        raise ValueError(
            'Flow direction and area do not have compatible grids')

    # Compute lonlats of watershed whose mouth is at `station`
    # TODO: Refactor to accept a DataGrid?
    direction_matrix = VIC_direction_matrix(
        flow_direction.lat_step, flow_direction.lon_step
    )

    watershed_xys, watershed_debug = build_watershed(
        flow_direction.lonlat_to_xy(station_lonlat),
        flow_direction.values,
        direction_matrix,
        debug=True
    )

    # `watershed_lonlats`, `elevations`, and `areas` must all be ordered
    # collections (not sets) because it is required (at minimum) that the
    # coordinates (lonlats) for `elevations[i]` and `areas[i]` be equal for
    # all `i`.
    watershed_lonlats = \
        [flow_direction.xy_to_lonlat(xy) for xy in watershed_xys]

    #  Compute elevations at each lonlat of watershed
    ws_elevations = elevation.get_values_at_lonlats(watershed_lonlats)

    #  Compute area of each cell in watershed
    ws_areas = area.get_values_at_lonlats(watershed_lonlats)

    # Compute the elevation/area curve
    elevation_bin_width, elevation_bin_centres, cumulative_areas = \
        hypsometry(ws_elevations, ws_areas)

    # Compute outline of watershed as a GeoJSON feature
    outline = outline_cell_rect(
        watershed_lonlats, flow_direction.lat_step, flow_direction.lon_step)

    return {
        'elevation': {
            'units': elevation.units,
            'minimum': min(ws_elevations),
            'maximum': max(ws_elevations),
        },
        'area': {
            'units': area.units,
            'value': sum(ws_areas),
        },
        'hypsometric_curve': {
            'elevation_bin_width': elevation_bin_width,
            'elevation_bin_centers': elevation_bin_centres,
            'cumulative_areas': cumulative_areas,
            'elevation_units': elevation.units,
            'area_units': area.units,
        },
        'shape': geojson_feature(
            outline,
            properties={
                # Represent as GeoJSON?
                'mouth': {
                    'longitude': station_lonlat[0],
                    'latitude': station_lonlat[1]
                }
            },
        ),
        'debug/test': {
            'watershed': {
                'cell_count': len(watershed_xys),
                **watershed_debug
            }
        }
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
    if debug:
        start_time = time.time()

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
            *(upstream(neighbour) for neighbour in neighbours(cell)
              if neighbour not in visited and is_upstream(neighbour, cell))
        )

    if debug:
        return upstream(target), {'time': time.time() - start_time}
    return upstream(target)


def lonlat_to_xy(coords, nc):
    """Returns the (x, y) data index for a given lon-lat coordinate,
    switching the order of the coordinates. Does *not* check whether
    the returned index is actually within the file's extent."""
    x = (coords[1] - nc.variables["lat"][0]) / nc_dimension_step(nc, "lat")
    y = (coords[0] - nc.variables["lon"][0]) / nc_dimension_step(nc, "lon")
    return (int(round(x)), int(round(y)))


def xy_to_lonlat(coords, nc):
    """Returns the lon-lat coordinate for a given xy data index,
    switching the order of the coordinates."""
    return (nc.variables["lon"][coords[1]], nc.variables["lat"][coords[0]])


def nc_dimension_step(nc, dimension):
    """Returns the interval between steps for a regularly spaced variable
    (e.g., lat, lon, time) in a netcdf file. Assumes all steps same size."""
    return nc.variables[dimension][1] - nc.variables[dimension][0]


def compatible_grids(nc1, nc2):
    """Checks whether the two netCDF files have the same size grid.
    Does not check spatial extent."""
    return (
        abs(nc_dimension_step(nc1, "lon")) ==
        abs(nc_dimension_step(nc2, "lon")) and
        abs(nc_dimension_step(nc1, "lat")) ==
        abs(nc_dimension_step(nc2, "lat"))
    )


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
        ( 0,  0),   # filler - 0 is not used in the encoding
        ( 1,  0),   # 1 = north
        ( 1,  1),   # 2 = northeast
        ( 0,  1),   # 3 = east
        (-1,  1),   # 4 = southeast
        (-1,  0),   # 5 = south
        (-1, -1),   # 6 = southwest
        ( 0, -1),   # 7 = west
        ( 1, -1),   # 8 = northwest
        ( 0,  0),   # 9 = outlet
    )
    lat_dir = int(math.copysign(1, lat_step))
    lon_dir = int(math.copysign(1, lon_step))
    return tuple(
        (lat_dir * lat_base, lon_dir * lon_base)
        for lat_base, lon_base in base
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
        sesh.query(distinct(DataFile.filename).label('filename'))
        .join(
            DataFileVariable,
            EnsembleDataFileVariables,
            Ensemble,
        )
        .filter(Ensemble.name == ensemble_name)
        .filter(DataFileVariable.netcdf_variable_name == variable)
        .filter(DataFile.time_set_id == None)
    )

    file = query.one()  # Raises exception if n != 1 results found
    return Dataset(file.filename, 'r')


def value_at_lonlat(lonlat, nc, var):
    """Return value of a 2D netcdf variable at a given lonlat coordinate"""
    return float(nc.variables[var][lonlat_to_xy(lonlat, nc)])


def hypsometry(elevations, areas, num_bins=None):
    """
    Computes a hypsometric curve as a histogram of areas by elevation.

    :param elevations: list of elevations; location is not specified but
        must be consistent with locations of areas
    :param areas: list of areas; location is not specified but
        must be consistent with locations of elevations
    :param num_bins: number of elevation bins; if None, the square root of
        the number of elevations is used
    :return: tuple (bin_width, bin_centres, cumulative_areas)
        bin_width: width of each elevation bin
        bin_centres: list of centre values of each elevation bin;
            elevation bin `i` spans semi-open interval
            [bin_centres[i] - bin_width/2, bin_centres[i] + bin_width/2)
        cumulative_areas: list of total areas in each elevation bin;
            indexed same as bin_centres
    """

    if len(elevations) != len(areas):
        raise IndexError(
            'elevations ({}) and areas ({}) do not have same lengths'.format(
                len(elevations), len(areas)))

    if num_bins is None:
        num_bins = math.ceil(math.sqrt(len(elevations)))
    bin_min = min(elevations) - 5
    bin_max = max(elevations) + 5
    bin_width = (bin_max - bin_min) / num_bins

    bin_centres = [bin_min + (i + 0.5) * bin_width for i in range(num_bins)]

    cumulative_areas = [0] * num_bins
    for elevation, area in zip(elevations, areas):
        bin = math.floor((elevation - bin_min) / bin_width)
        cumulative_areas[bin] += area

    return bin_width, bin_centres, cumulative_areas
