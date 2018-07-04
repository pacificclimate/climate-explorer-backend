'''module to request the watershed that feeds a given station location'''

import json
from netCDF4 import Dataset
from shapely.geometry import Polygon, mapping
from shapely.ops import cascaded_union
import operator
import numpy as np
import os



def watershed(sesh, id_, station):
    '''returns a geoJSON Feature object representing the polygon drained by a 
    given station.
    
    Currently, a mix of calculated and canned data. The watershed is actually
    computed, but station metadata is canned. 
    
    NOTE: GeoJSON coordinates are longitude-first, unlike Leaflet or Google Maps.
    
        Example:
            {
                'type': 'Feature',
                'geometry': {
                    "coordinates": [
                        [
                            [-117.4688, 51.46875], 
                            [-117.4688, 51.96875], 
                            [-117.9688, 51.96875], 
                            [-117.9688, 51.46875], 
                            [-117.4688, 51.46875]
                        ]
                    ], 
                  "type": "Polygon"
                }
                'properties':{
                    'station': 'p-0',
                    'latitude': 52.09375,
                    'longitude': -118.5312,
                    'watershed': 'ColumbiaRouting.nc'
                    }
            }
    '''
    output = {}
    output['type'] = 'Feature'
    
    properties = {}
    properties['station'] = 'p-0'
    properties['watershed'] = 'ColumbiaRouting.nc'
     
    files = ["flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_BEAVE", 
              "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_BRI",
              "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_CRNIC",
              "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_DONAL",
              "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_KICHO",
              "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_MCD"]
    
    coords = [
        [51.46875, -117.4688],
        [49.40625, -117.5312],
        [51.21875, -116.9062],
        [51.46875, -117.1562],
        [51.28125, -116.9062],
        [52.09375, -118.5312]
        ]
        
    index = files.index(id_)
    
    lat = coords[index][0]
    lon = coords[index][1]
    properties['latitude'] = lat
    properties['longitude'] = lon
    
    routing_file = "ce/api/streamflow/routing-data/ColumbiaRouting.nc"
    output['properties'] = properties
    output['geometry'] = watershed_geoJSON((lat, lon), routing_file)
    
    return output





#TODO: caching, this is sloooow.
def watershed_geoJSON(station_latlon, netcdf_filename):
    '''
    Given a netCDF routing file and coordinates of a station, returns a GeoJSON polygon
    representing all grid squares that drain to that station.
    Note that the routing netCDF file provides coordinates latitude-first, while GeoJSON
    requires longitude-first. The ncindex_to_grid_square function swaps the order.
    '''
    
    #Determine which way directions go in this file and build a translation matrix.
    routes =  Dataset(netcdf_filename, "r", format="NETCDF4")
    directions = build_VIC_direction_matrix(routes)

    #Find the starting point
    station_index = latlon_to_ncindex(station_latlon, routes)
    watershed = build_watershed(station_index, directions, routes.variables["Flow_Direction"], 0)
    
    #Switches from latitude-first to longitude-first here.
    polygons = list(map(lambda index: ncindex_to_grid_square(index, routes), watershed ))
    
    geoJSON = cascaded_union(polygons)
    print(json.dumps(mapping(geoJSON)))
    return mapping(geoJSON)
        
def build_watershed(mouth, directions, routing, depth):
    '''
    Depth-first recursive function takes a netCDF variable containing VIC-style
    drainage mapping, a netCDF direction matrix, and an index representing
    the mouth of the drainage system. It returns a python set containing 
    the coordinates of every point upstream.
    As the sample routing files include some "looped" routes where water flows
    from cell A into cell B and from cell B into cell A, recursion is hard-limited
    to 200 cells deep.
    '''
    watershed = []
    watershed.append(mouth)
    if depth > 200:
        return watershed
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            source = add_tuples(mouth, (i, j))
            if (i != 0 or j != 0 ) and \
                valid_netcdf_variable_index(source, routing) and \
                not routing[source[0]][source[1]] is np.ma.masked:
                direction = int(routing[source[0]][source[1]]) 
                #if the routing direction "points" back toward 0,0, this source drains into the mouth
                if(add_tuples(directions[direction], (i, j)) == (0,0)):
                    watershed.extend(build_watershed(source, directions, routing, depth + 1))
                
    return watershed


def build_VIC_direction_matrix(nc):
    '''
    Takes a netCDF files with latitude and longitude dimensions and returns
    an array mapping VIC's routing conventions (1 = North, 2 = Northeast, etc)
    to netCDF index deltas. Assumes latitude-first coordinates. 
    '''
    latinc = nc_dimension_increment(nc, "lat")
    latinc = int(latinc / abs(latinc))
    
    loninc = nc_dimension_increment(nc, "lon")
    loninc = int(loninc / abs(loninc))

    directions = [[0,0]] #filler
    directions.append([latinc, 0]) #1 = north
    directions.append([latinc, loninc]) #2 = northeast
    directions.append([0, loninc]) #3 = east
    directions.append([-1 * latinc, loninc]) #4 = southeast
    directions.append([-1 * latinc, 0]) #5 = south
    directions.append([-1 * latinc, -1 * loninc]) #6 = southwest
    directions.append([0, -1 * latinc]) #7 = west
    directions.append([latinc, -1 * loninc]) # 8 = northwest
    directions.append([0, 0]) #9 = outlet
    
    return directions
    

def latlon_to_ncindex(coords, nc):
    """netCDF index corresponding to grid square containing the coordinate"""
    x = (coords[0] - nc.variables["lat"][0]) / nc_dimension_increment(nc, "lat")
    y = (coords[1] - nc.variables["lon"][0]) / nc_dimension_increment(nc, "lon")
    return (int(round(x)), int(round(y)))

def ncindex_to_latlon(index, nc):
    """Latlong of the center of the indexed netCDF grid square"""
    return (nc.variables["lat"][index[0]], nc.variables["lon"][index[1]])

def nc_dimension_increment(nc, dimension):
    """Assuming regular grid, returns increment of the dimension in the netCDF file."""
    return nc.variables[dimension][1] - nc.variables[dimension][0]

def valid_netcdf_variable_index(index, var):
    """True if this index is valid for this netCDF variable"""
    return index[0] >= 0 and index[0] < var.shape[0] and \
        index[1] >= 0 and index[1] < var.shape[1]
    

def ncindex_to_grid_square(index, nc):
    '''
    Returns a shapely Polygon corresponding to the netCDF grid square represented
    by the index. Switches from latitude-first coordinates (netCDF) to longitude-first 
    (shapely & geoJSON).
    '''
    points = []
    center = ncindex_to_latlon(index, nc)
    height = nc_dimension_increment(nc, "lat")
    width = nc_dimension_increment(nc, "lon")
    
    #switch coordinate order.
    points.append((center[1] + width / 2, center[0] - height / 2))
    points.append((center[1] + width / 2, center[0] + height / 2))
    points.append((center[1] - width / 2, center[0] + height / 2))
    points.append((center[1] - width / 2, center[0] - height / 2))
        
    return Polygon(points)

def add_tuples(a, b):
    """numPy-style addition for builtin tuples: (1, 1) + (2, 3) = (3, 4)"""
    return tuple(map(operator.add, a, b))





