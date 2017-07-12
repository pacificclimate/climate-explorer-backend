import os
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset
import modelmeta as mm

from ce.api.geo import wktToMask

def get_files_from_run_variable(run, variable):
    return [file_ for file_ in run.files if variable in
                [dfv.netcdf_variable_name for dfv in file_.data_file_variables]
           ]

def get_units_from_netcdf_file(nc, variable):
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

def get_grid_from_netcdf_file(nc):
    return {
        'latitudes': np.ndarray.tolist(nc.variables['lat'][:]),
        'longitudes': np.ndarray.tolist(nc.variables['lon'][:])
    }

@contextmanager
def open_nc(fname):
    if not os.path.exists(fname):
        raise Exception(
            "The metadata database is out of sync with the filesystem. "
            "I was told to open the file {}, but it does not exist."
            .format(fname)
        )

    try:
        nc = Dataset(fname, 'r')
        yield nc
    finally:
        nc.close()

def get_array(nc, fname, time, area, variable):

    if variable not in nc.variables:
        raise Exception(
            "File {} does not have variable {}."
            .format(fname, variable)
        )

    a = nc.variables[variable]

    if area:
        # Mask out data that isn't inside the input polygon
        a = wktToMask(nc, fname, area, variable)

    # FIXME: Assumes 3d data... doesn't support levels
    if time or time == 0:
        assert 'time' in nc.variables[variable].dimensions
        a = a[time,:,:]
    else:
        a = a[:,:,:]

    return a

def mean_datetime(datetimes):
    timestamps = [
        dt.replace(tzinfo=timezone.utc).timestamp()
        for dt in datetimes
    ]
    mean = np.mean(timestamps)
    return datetime.fromtimestamp(mean, tz=timezone.utc)

def search_for_unique_ids(sesh, ensemble_name='ce', model='', emission='',
                          variable='', time=0):
    query = sesh.query(mm.DataFile.unique_id)\
            .distinct(mm.DataFile.unique_id)\
            .join(mm.DataFileVariable, mm.EnsembleDataFileVariables, mm.Ensemble,
                  mm.Run, mm.Model, mm.Emission, mm.TimeSet, mm.Time)\
            .filter(mm.Ensemble.name == ensemble_name)\
            .filter(mm.DataFileVariable.netcdf_variable_name == variable)\
            .filter(mm.Time.time_idx == time)

    if model:
        query = query.filter(mm.Model.short_name == model)

    if emission:
        query = query.filter(mm.Emission.short_name == emission)

    return ( r[0] for r in query.all() )
