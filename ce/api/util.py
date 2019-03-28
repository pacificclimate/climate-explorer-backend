import os
from contextlib import contextmanager
from datetime import datetime, timezone
import re

import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset
import modelmeta as mm

from ce.api.geo import wkt_to_masked_array

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
        a = wkt_to_masked_array(nc, fname, area, variable)
        a = time_slice_array(a, time, nc, fname, variable)
    else:
        a = time_slice_array(a, time, nc, fname, variable)
        a = ma.masked_array(a)

    return a

# FIXME: Assumes 3d data... doesn't support levels
#Reduces a 3-dimensional array to a two-dimensional array by
#returning the timeidxth slice, IFF time is defined and time
#is a dimension in the netCDF. Otherwise return array unchanged.
def time_slice_array(a, timeidx, nc, fname, variable):
    if timeidx or timeidx == 0:
        if 'time' not in nc.variables[variable].dimensions:
            raise Exception(
                "File {} does not have a time dimension".format(fname)
                )
        a = a[timeidx,:,:]
    return a

def mean_datetime(datetimes):
    timestamps = [
        dt.replace(tzinfo=timezone.utc).timestamp()
        for dt in datetimes
    ]
    mean = np.mean(timestamps)
    return datetime.fromtimestamp(mean, tz=timezone.utc)

def validate_cell_method(cell_method):
    return cell_method in ('mean', 'standard_deviation')

def search_for_unique_ids(sesh, ensemble_name='ce', model='', emission='',
                          variable='', time=0, timescale='', cell_method='mean'):
    if not validate_cell_method(cell_method):
        raise Exception('Unsupported cell_method: {}'.format(cell_method))

    cell_methods = sesh.query(mm.DataFileVariable.variable_cell_methods)\
                    .distinct(mm.DataFileVariable.variable_cell_methods).all()
    pattern = {
        'standard_deviation': r'time:[a-z\s]*time:\s+standard_deviation\s+over\s+days',
        'mean': r'time:[a-z\s]*\s+(time:\s+mean\s+over\s+days)?'
    }[cell_method]

    matching_cell_methods = [r[0] for r in cell_methods if re.match(pattern, r[0])]

    query = sesh.query(mm.DataFile.unique_id)\
            .distinct(mm.DataFile.unique_id)\
            .join(mm.DataFileVariable, mm.EnsembleDataFileVariables, mm.Ensemble,
                  mm.Run, mm.Model, mm.Emission, mm.TimeSet, mm.Time)\
            .filter(mm.Ensemble.name == ensemble_name)\
            .filter(mm.DataFileVariable.netcdf_variable_name == variable)\
            .filter(mm.DataFileVariable.variable_cell_methods.in_(matching_cell_methods))\
            .filter(mm.Time.time_idx == time)

    if model:
        query = query.filter(mm.Model.short_name == model)

    if emission:
        query = query.filter(mm.Emission.short_name == emission)

    if timescale:
        query = query.filter(mm.TimeSet.time_resolution == timescale)

    return ( r[0] for r in query.all() )
