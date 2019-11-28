'''module for requesting information on the watershed that drains
to a specified point.

Arguments:
  * station, a WKT-formatted point
  * ensemble_name, the modelmeta ensemble containing the watershed data
      (an elevation netCDF, an area netCDF, a flow direction netCDF)

Returns a JSON object with the following attributes:
    area: area of the watershed, in square meters
    elevation: minimum and maximum elevations
    shape: a geoJSON object representing the lat-long contour
               of the watershed
    hypsometric_curve: a histogram of the watershed

CAUTION: This API juggles two sets of coordinates: spatial coordinates, and
data indexes. Spatial coordinates (such as the WKT parameter input, or the
geoJSON output) are lon-lat order. But inside the netCDF files, data is
arranged in lat-lon order.

Spatial coordinates are named lat and lon. Data coordinates are named x and y.

The functions lonlat_to_xy() and xy_to_lonlat(), which translate from a
spatial tuple to a data index tuple and vice versa, also switch the
dimension order.
'''

from netCDF4 import Dataset
import operator
import numpy as np
import math

from sqlalchemy import distinct

from ce.api.geospatial import geojson_feature, outline, WKT_point_to_lonlat
from modelmeta import \
    DataFile, DataFileVariable, Ensemble, EnsembleDataFileVariables


def watershed(sesh, station, ensemble_name):
    '''Documentation goes here --- what is the format?'''
    # Get the watershed, represented as a list of points

    lon, lat = WKT_point_to_lonlat(station)
    
    # Compute lonlats of watershed whose mouth is at `station`

    flow_direction_ds = get_time_invariant_variable_dataset(
        sesh, ensemble_name, 'flow_direction'
    )

    lat_step = nc_dimension_step(flow_direction_ds, 'lat')
    lon_step = nc_dimension_step(flow_direction_ds, 'lon')
    direction_matrix = VIC_direction_matrix(lat_step, lon_step)

    start_xy = lonlat_to_xy([lon, lat], flow_direction_ds)
    watershed_xys = build_watershed(
        start_xy, 
        flow_direction_ds.variables['flow_direction'],
        direction_matrix
    )

    # `watershed_lonlats`, `elevations`, and `areas` must all be ordered
    # collections (not sets) because it is required (at minimum) that the
    # coordinates (lonlats) for `elevations[i]` and `areas[i]` be equal for
    # all `i`.
    watershed_lonlats = list(
        map(lambda xy: xy_to_lonlat(xy, flow_direction_ds), watershed_xys)
    )

    # TODO: DRY up the following two computations

    #  Compute elevations at each lonlat of watershed
    
    elevation_ds = \
        get_time_invariant_variable_dataset(sesh, ensemble_name, 'elev')
    if not compatible_grids(flow_direction_ds, elevation_ds):
        raise ValueError(
            'Flow direction and elevation do not have the same grid')
    
    elevations = list(
        map(lambda lonlat: value_at_lonlat(lonlat, elevation_ds, "elev"),
            watershed_lonlats)
    )
    
    #  Compute area of each cell in watershed

    area_ds = get_time_invariant_variable_dataset(sesh, ensemble_name, "area")
    if not compatible_grids(flow_direction_ds, area_ds):
        raise Exception("Flow direction and area do not have the same grid")

    areas = list(
        map(lambda lonlat: value_at_lonlat(lonlat, area_ds, "area"),
            watershed_lonlats)
    )

    # Compute the elevation/area curve

    h_bin_width, h_bin_centres, h_cumulative_areas = \
        hypsometry(elevations, areas)

    # Compute outline of watershed as a GeoJSON feature

    geojson_outline = geojson_feature(
        outline(watershed_lonlats, lat_step, lon_step),
        properties=dict(mouth=dict(longitude=lon, latitude=lat))
    )
    
    # Compose response

    response = {
        'elevation': {
            'units': elevation_ds.variables['elev'].units,
            'minimum': min(elevations),
            'maximum': max(elevations),
        },
        'area': {
            'units': area_ds.variables['area'].units,
            'value': sum(areas),
        },
        'hypsometric_curve': {
            'bin_width': h_bin_width,
            'x_bin_centers': h_bin_centres,
            'y_values': h_cumulative_areas,
            'x_units': elevation_ds.variables['elev'].units,
            'y_units': area_ds.variables['area'].units,
        },
        'outline': {
            **geojson_outline,
            'properties': {
                'mouth_longitude': lon, 
                'mouth_latitude': lat
            },
        },
    }

    elevation_ds.close()
    flow_direction_ds.close()
    area_ds.close()

    return response


def build_watershed(target, routing, direction_map, max_depth=200, depth=0):
    '''Depth-first recursive
    Arguments:
       routing: a netCDF variable representing water flow
       target: an xy index representing the location of interest:
        what cells drain into this cell?
       direction_map: maps RVIC's direction codes to movement in data index
       depth: recursion depth, for breaking out of loops
       max_depth: break out of recursion at this depth
    Returns a list of xy tuples representing the data indexes of locations
    that drain into mouth, including mouth itself.
    RVIC flow direction data occasionally contains loops: two grid squares,
    each of which is marked as draining into the other - it always occurs
    along coastlines. Therefore recursion is limited to 200 cells deep.
    This may need to be increased if we start doing larger watersheds.
    '''
    watershed = {target}
    if depth >= max_depth:
        return watershed
    # iterate through the nine cells around the mouth (including the mouth)
    # and check to see whether each one's flow_direction value points
    # toward the mouth.
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            # xy index of possible upstream cell
            index = vec_add(target, (i, j))
            # there are three constraints for a possible upstream cell:
            # - it's not the mouth (relative 0,0)
            # - it's actually in the flow_direction variable's extent
            # - it's not masked
            if (i != 0 or j != 0) and \
                is_valid_index(index, routing.shape) and \
                not routing[index[0]][index[1]] is np.ma.masked:

                source_flow = int(routing[index[0]][index[1]])
                # if the flow direction from the possible source grid
                # points back to 0,0, the mouth, then this source drains
                # into the mouth and is part of the watershed,  as are
                # any further squares that drain into it.
                if vec_add(direction_map[source_flow], (i, j)) == (0, 0):
                    watershed = watershed | build_watershed(
                        index, routing, direction_map, max_depth, depth + 1
                    )

    return watershed


def is_valid_index(index, shape):
    """True if index is in valid range for an array of given shape"""
    return all(0 <= i < n for i, n in zip(index, shape))


def lonlat_to_xy(coords, nc):
    '''returns the x-y data index for a given lon-lat coordinate,
    switching the order of the coordinates. Does *not* check whether
    the returned index is actually within the file's extent.'''
    x = (coords[1] - nc.variables["lat"][0]) / nc_dimension_step(nc, "lat")
    y = (coords[0] - nc.variables["lon"][0]) / nc_dimension_step(nc, "lon")
    return (int(round(x)), int(round(y)))


def xy_to_lonlat(coords, nc):
    '''returns the lon-lat coordinate for a given xy data index,
    switching the order of the coordinates.'''
    return (nc.variables["lon"][coords[1]], nc.variables["lat"][coords[0]])


def nc_dimension_step(nc, dimension):
    '''for a regularly spaced variable (like lat, lon, or time),
    returns the interval between steps. Assumes all steps same size.'''
    return nc.variables[dimension][1] - nc.variables[dimension][0]

def compatible_grids(nc1, nc2):
    '''checks whether the two netCDF files have the same size grid.
    Does not check spatial extent.'''
    return (abs(nc_dimension_step(nc1, "lon")) == abs(nc_dimension_step(nc2, "lon")) and
        abs(nc_dimension_step(nc1, "lat")) == abs(nc_dimension_step(nc2, "lat")))


def VIC_direction_matrix(lat_step, lon_step):
    """Return a VIC direction matrix, which is a matrix indexed by the VIC
    streamflow direction codes 0...9, with the value at index i indicating
    the offsets from the data index (x, y) in a streamflow file required to
    step in that streamflow direction.
    The offsets must account for the sign of the step in the lat and lon
    dimensions in the streamflow file.
    For example, in a streamflow file with lat and lon both increasing with
    increasing index, the offset to step northeast is [1, 1].

    Note that argument order is latlon, not lonlat.
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
    '''This function locates and opens a time-invariant dataset.
    These datasets contain things like elevation or area of a grid cell -
    they're independent of time and there should be only one per ensemble.
    If more or less than one is found in the ensemble, it raises an error.'''
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


def vec_add(a, b):
    '''numpy-style addition for builtin tuples: (1,1)+(2,3) = (3,4)'''
    return tuple(map(operator.add, a, b))


def value_at_lonlat(lonlat, nc, var):
    '''value of a 2d netcdf variable at a particular lonlat coordinate'''
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
            [bin_centres[i] - bin_width, bin_centres[i] + bin_width)
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
