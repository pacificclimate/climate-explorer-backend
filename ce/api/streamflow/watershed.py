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

import json
import re
from netCDF4 import Dataset
from shapely.geometry import Polygon, mapping
from shapely.ops import cascaded_union
import operator
import numpy as np
import os
import math

from sqlalchemy import distinct
from sqlalchemy.orm.exc import NoResultFound

from ce.api.util import WKT_point_to_lonlat
import modelmeta as mm
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

    start_xy = lonlat_to_xy([lon, lat], flow_direction_ds)

    direction_matrix = VIC_direction_matrix(
        nc_dimension_step(flow_direction_ds, 'lat'),
        nc_dimension_step(flow_direction_ds, 'lon')
    )
    watershed_xys = build_watershed(
        start_xy, 
        flow_direction_ds.variables['flow_direction'],
        direction_matrix
    )
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

    #  calculate geoJSON shape

    shape = geoJSON_shape(watershed_lonlats, flow_direction_ds)
    
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
        'shape': {
            **shape,
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


def build_watershed(mouth, routing, direction_map, depth=0):
    '''Depth-first recursive
    Arguments:
       routing: a netCDF variable representing water flow
       mouth: an xy index representing the starting location
       direction_map: maps RVIC's direction codes to movement in data index
       depth: recursion depth, for breaking out of loops.
    Returns a set of xy tuples representing the data indexes of locations
    that drain into mouth, including mouth itself.
    RVIC flow direction data occaisionally contains loops: two grid squares,
    each of which is marked as draining into the other - it always occurs
    along coastlines. Therefore recursion is limited to 200 cells deep.
    This may need to be increased if we start doing larger watersheds.
    '''
    watershed = []
    watershed.append(mouth)
    if depth > 200:
        return watershed
    # iterate through the nine cells around the mouth (including the mouth)
    # and check to see whether each one's flow_direction value points
    # toward the mouth.
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            upstream = add_tuples(mouth, (i, j))  # xy index of possible upstream cell
            # there are three constraints for a possible upstream cell:
            # - it's not the mouth (relative 0,0)
            # - it's actually in the flow_direction variable's extent
            # - it's not masked
            if (i != 0 or j != 0) and \
                valid_netcdf_variable_index(upstream, routing) and \
                not routing[upstream[0]][upstream[1]] is np.ma.masked:
                source_flow = int(routing[upstream[0]][upstream[1]])
                # if the flow direction from the possible source grid
                # points back to 0,0, the mouth, then this source drains
                # into the mouth and is part of the watershed,  as are
                # any further squares that drain into it.
                if(add_tuples(direction_map[source_flow], (i, j)) == (0, 0)):
                    watershed.extend(build_watershed(upstream,
                                                     routing,
                                                     direction_map,
                                                     depth + 1))

    return watershed


def valid_netcdf_variable_index(index, var):
    '''True if this variable has an item (masked or not) at this index'''
    for i in range(len(index)):
        if index[i] < 0 or index[i] > var.shape[i]:
            return False
    return True


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
    base = [
        [ 0,  0],   # filler - 0 is not used in the encoding
        [ 1,  0],   # 1 = north
        [ 1,  1],   # 2 = northeast
        [ 0,  1],   # 3 = east
        [-1,  1],   # 4 = southeast
        [-1,  0],   # 5 = south
        [-1, -1],   # 6 = southwest
        [ 0, -1],   # 7 = west
        [ 1, -1],   # 8 = northwest
        [ 0,  0],   # 9 = outlet
    ]
    lat_dir = int(math.copysign(1, lat_step))
    lon_dir = int(math.copysign(1, lon_step))
    # TODO: Make this a tuple of tuples (immutable)
    return [
        [lat_dir * lat_base, lon_dir * lon_base]
        for lat_base, lon_base in base
    ]


# TODO: Remove
def build_VIC_direction_matrix(flow_direction):
    '''Constructs mapping between RVIC's routing encoding (1 = North,
    2 = Northeast, etc) and the data layout in the flow direction file.
    Returns coordinates in latlong (data index) order.'''

    def dimension_direction(nc, dim):
        '''returns the sign (+1/-1) of the change between subsequent values
        in a 1-dimensional netCDF variable (assumes monotonicity)'''
        increment = nc_dimension_step(nc, dim)
        return int(increment / abs(increment))
    # determine the data index directions corresponding to *increasing*
    # lat and lon
    lat_dir = dimension_direction(flow_direction, "lat")
    lon_dir = dimension_direction(flow_direction, "lon")

    # use those directions to build a mapping saying which way to go
    # in the data index for each of RVIC's defined direction codes.

    directions = [[0, 0]]  # filler - 0 is not used in the encoding
    directions.append([lat_dir, 0])  # 1 = north
    directions.append([lat_dir, lon_dir])  # 2 = northeast
    directions.append([0, lon_dir])  # 3 = east
    directions.append([-1 * lat_dir, lon_dir])  # 4 = southeast
    directions.append([-1 * lat_dir, 0])  # 5 = south
    directions.append([-1 * lat_dir, -1 * lon_dir])  # 6 = southwest
    directions.append([0, -1 * lat_dir])  # 7 = west
    directions.append([lat_dir, -1 * lon_dir])  # 8 = northwest
    directions.append([0, 0])  # 9 = outlet
    return directions


def get_time_invariant_variable_dataset(sesh, ensemble_name, variable):
    '''This function locates and opens a time-invariant dataset.
    These datasets contain things like elevation or area of a grid cell -
    they're independent of time and there should be only one per ensemble.
    If more or less than one is found in the ensemble, it raises an error.'''
    # TODO: Should these be filtered for being time-invariant?
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


def add_tuples(a, b):
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


# TODO: Remove
def bin_values(values):
    '''Accepts a list of (elevation, area) tuples.
    returns a histogram dictionary of how much area is at each elevation. 
    For N values, sqrt(N) bins will be created.'''

    num_bins = math.ceil(math.sqrt(len(values)))

    area = []
    bins = []
    mn = min(values, key = lambda t: t[0])[0] - 5
    mx = max(values, key = lambda t: t[0])[0] + 5
    width = (mx - mn) / num_bins
    center = mn + (width / 2)
    for i in range(num_bins):
        area.append(0)
        bins.append(center)
        center += width

    for t in values:
        bin = math.floor((t[0] - mn) / width)
        area[bin] = area[bin] + t[1]
    hist = {
        "bin_width": width,
        "x_bin_centers": bins,
        "y_values": area
    }
    return hist


def geoJSON_shape(points, nc):
    '''Accepts a set of lon-lat points and a netCDF files containing a
    corresponding grid. Returns a geoJSON object representing the union
    of the grid squares centered at the points. Doesn't do anything clever,
    just takes the union of a while bunch of squares. Quite slow. Debugging use
    only, probably.'''
    width = nc_dimension_step(nc, "lon")
    height = nc_dimension_step(nc, "lat")

    def grid_square_from_point(point, width, height):
        '''makes shapely Polygon representing grid square centered at point'''
        corners = []
        corners.append((point[0] + width / 2, point[1] - height / 2))
        corners.append((point[0] + width / 2, point[1] + height / 2))
        corners.append((point[0] - width / 2, point[1] + height / 2))
        corners.append((point[0] - width / 2, point[1] - height / 2))
        return Polygon(corners)

    squares = list(map(lambda p: grid_square_from_point(p, width, height),
                       points))
    return {
        'type': 'Feature',
        'geometry': mapping(cascaded_union(squares))
    }