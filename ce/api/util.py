import os
from datetime import datetime, timezone

import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset
from shapely.wkt import loads
from modelmeta import *

from ce.api.geo import polygonToMask

def get_files_from_run_variable(run, variable):
    return [file_ for file_ in run.files if variable in
                [dfv.netcdf_variable_name for dfv in file_.data_file_variables]
           ]

def get_units_from_netcdf_file(fname, variable):
    nc = Dataset(fname)
    return nc.variables[variable].units

def get_units_from_file_object(file_, varname):
    for dfv in file_.data_file_variables:
        if dfv.netcdf_variable_name == varname:
            return dfv.variable_alias.units
    raise Exception("Variable {} is not indexed for file {}".format(varname, file_.filename))

def get_units_from_run_object(run, varname):
    files = get_files_from_run_variable(run, varname)
    units = { get_units_from_file_object(file_, varname) for file_ in files }

    if len(units) != 1:
        raise Exception("File list {} does not have consistent units {}".format(run.files, units))

    return units.pop()

def get_grid_from_netcdf_file(fname):
    nc = Dataset(fname)
    return {
        'latitudes': nc.variables['lat'][:],
        'longitudes': nc.variables['lon'][:]
    }

def get_array(fname, time, area, variable):
    if not os.path.exists(fname):
        raise Exception(
            "The meatadata database is out of sync with the filesystem. "
            "I was told to open the file {}, but it does not exist."
            .format(fname)
        )

    nc = Dataset(fname)

    if variable not in nc.variables:
        raise Exception(
            "File {} does not have variable {}."
            .format(fname, variable)
        )

    a = nc.variables[variable]

    # FIXME: Assumes 3d data... doesn't support levels
    if time:
        assert 'time' in nc.variables[variable].dimensions
        a = a[time,:,:]
    else:
        a = a[:,:,:]

    if area:
        polygon = loads(area)

        # Mask out data that isn't inside the input polygon
        mask = polygonToMask(nc, polygon)

        # Extend the mask into the time dimension (if it exists)
        mask = np.repeat(mask, a.size / mask.size).reshape(a.shape)
    else:
        mask = False

    # We may or may not have received a masked array from the NetCDF file
    if hasattr(a, 'mask'):
        mask = a.mask | mask
        return ma.masked_array(a.data, mask)
    else:
        return ma.masked_array(a, mask)

def mean_datetime(datetimes):
    timestamps = [ dt.replace(tzinfo=timezone.utc).timestamp() for dt in datetimes ]
    mean = np.mean(timestamps)
    return datetime.fromtimestamp(mean, tz=timezone.utc)

def search_for_unique_ids(sesh, ensemble_name='ce', model='', emission='', variable='', time=0):
    query = sesh.query(DataFile.unique_id).distinct(DataFile.unique_id)\
                  .join(DataFileVariable, EnsembleDataFileVariables, Ensemble, Run, Model, Emission, TimeSet, Time)\
                  .filter(Ensemble.name == ensemble_name)\
                  .filter(DataFileVariable.netcdf_variable_name == variable)\
                  .filter(Time.time_idx == time)\
                  .filter(TimeSet.multi_year_mean == True)

    if model:
        query = query.filter(Model.short_name == model)

    if emission:
        query = query.filter(Emission.short_name == emission)

    return ( r[0] for r in query.all() )
