import os

import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset
from shapely.wkt import loads

from ce.api.geo import polygonToMask

def get_units_from_netcdf_file(fname, variable):
    nc = Dataset(fname)
    return nc.variables[variable].units

def get_units_from_file_object(file_, varname):
    for dfv in file_.data_file_variables:
        if dfv.netcdf_variable_name == varname:
            return dfv.variable_alias.units
    raise Exception("Variable {} is not indexed for file {}".format(varname, file_.filename))

def get_units_from_run_object(run, varname):
    units = { get_units_from_file_object(file_, varname) for file_ in run.files }

    if len(units) != 1:
        raise Exception("File list {} does not have consistent units {}".format(run.files, units))

    return units.pop()


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

    data = nc.variables[variable]

    if time:
        assert 'time' in nc.variables[variable].dimensions
        data = data[time,:,:] # FIXME: Assumes 3d data... doesn't support levels

    if area:
        polygon = loads(area)

        # Mask out data that isn't inside the input polygon
        mask = polygonToMask(nc, polygon)

        # Extend the mask into the time dimension (if it exists)
        mask = np.repeat(mask, data.size / mask.size).reshape(data.shape)
        return ma.masked_array(data, mask=mask)
    else:
        return ma.masked_array(data, False)
