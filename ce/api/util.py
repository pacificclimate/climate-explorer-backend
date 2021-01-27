import os
from contextlib import contextmanager
from datetime import datetime, timezone
from itertools import product
from cf_cell_methods import parse
import operator
import re

import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset
import modelmeta as mm

from ce.api.geo import wkt_to_masked_array


def get_files_from_run_variable(run, variable, ensemble_name):
    return [
        file_
        for file_ in run.files
        if any(
            variable == dfv.netcdf_variable_name
            and any(ensemble.name == ensemble_name for ensemble in dfv.ensembles)
            for dfv in file_.data_file_variables
        )
    ]


def get_units_from_netcdf_file(nc, variable):
    return nc.variables[variable].units


def get_units_from_file_object(file_, varname):
    for dfv in file_.data_file_variables:
        if dfv.netcdf_variable_name == varname:
            return dfv.variable_alias.units
    raise Exception(
        "Variable {} is not indexed for file {}".format(varname, file_.filename)
    )


def get_units_from_run_object(run, varname, ensemble_name):
    files = get_files_from_run_variable(run, varname, ensemble_name)
    units = {get_units_from_file_object(file_, varname) for file_ in files}

    if len(units) != 1:
        raise Exception(
            "File list {} does not have consistent units {}".format(run.files, units)
        )

    return units.pop()


def get_grid_from_netcdf_file(nc):
    return {
        "latitudes": np.ndarray.tolist(nc.variables["lat"][:]),
        "longitudes": np.ndarray.tolist(nc.variables["lon"][:]),
    }


@contextmanager
def open_nc(resource):
    if not "http" in resource and not os.path.exists(resource):
        raise Exception(
            f"The metadata database is out of sync with the filesystem. I was told to open file with name {resource}, but it does not exist."
        )

    try:
        nc = Dataset(resource, "r")
        nc.set_always_mask(False)
        yield nc
    finally:
        nc.close()


def get_array(nc, resource, time, area, variable):

    if variable not in nc.variables:
        raise Exception(f"Resource {resource} does not have variable {variable}.")

    a = nc.variables[variable]

    if area:
        # Mask out data that isn't inside the input polygon
        a = wkt_to_masked_array(nc, resource, area, variable)
        a = time_slice_array(a, time, nc, resource, variable)
    else:
        a = time_slice_array(a, time, nc, resource, variable)
        a = ma.masked_array(a)

    return a


# FIXME: Assumes 3d data... doesn't support levels
# Reduces a 3-dimensional array to a two-dimensional array by
# returning the timeidxth slice, IFF time is defined and time
# is a dimension in the netCDF. Otherwise return array unchanged.
def time_slice_array(a, timeidx, nc, resource, variable):
    if timeidx or timeidx == 0:
        if "time" not in nc.variables[variable].dimensions:
            raise Exception(f"Resource {resource} does not have a time dimension")
        a = a[timeidx, :, :]
    return a


def mean_datetime(datetimes):
    timestamps = [dt.replace(tzinfo=timezone.utc).timestamp() for dt in datetimes]
    mean = np.mean(timestamps)
    return datetime.fromtimestamp(mean, tz=timezone.utc)


# valid cell method parameters for the API. Add new ones here as needed.
VALID_CELL_METHOD_PARAMETERS = ("mean", "standard_deviation", "percentile")


def is_valid_cell_method(cell_method):
    """Validate the cell_method parameter supplied by caller"""
    return cell_method in VALID_CELL_METHOD_PARAMETERS


def check_final_cell_method(cell_methods, target_method, default_to_mean=True):
    """Determines whether the final method in a cell methods string
    (corresponding to a statistical aggregation) matches the target.
    If default_to_mean is true, treats errors and unrecognized methods
    as though they are climatological means. This compensates for some
    noisy cell_methods attributes in our data, all of which are
    climatological means.
    """
    parsed = parse(cell_methods)
    if target_method == "mean" and default_to_mean:
        # determine means by process of elimination
        nonmeans = [m for m in VALID_CELL_METHOD_PARAMETERS if m != "mean"]
        return parsed is None or parsed[-1].method.name not in nonmeans
    elif parsed is not None:
        return parsed[-1].method.name == target_method
    else:
        # unparsable cell methods string
        return False


def filter_by_cell_method(cell_methods, target_method):
    """
    There are multiple types of statistical data available to the backend
    via the modelmeta database:
      * climatological means
      * climatological standard deviations
      * model ensemble means of climatological means
      * model ensemble percentiles of climatological means
      * time-invariant physical geography data
    A caller may specify whether they are interested in climatological means
    (including model ensemble means of climatological means), climatological
    standard deviations, or percentiles of climatological means. (Physical
    geography data should only be accessed by the /watershed API), and this
    function will filter returned data to the desired category based on
    its cell_method attribute.
    """

    return [
        cm for cm in cell_methods if check_final_cell_method(cm, target_method, True)
    ]


def search_for_unique_ids(
    sesh,
    ensemble_name="ce",
    model="",
    emission="",
    variable="",
    time=0,
    timescale="",
    cell_method="mean",
):
    if not is_valid_cell_method(cell_method):
        raise Exception("Unsupported cell_method: {}".format(cell_method))

    cell_methods = (
        sesh.query(mm.DataFileVariableGridded.variable_cell_methods)
        .distinct(mm.DataFileVariableGridded.variable_cell_methods)
        .all()
    )

    matching_cell_methods = filter_by_cell_method(
        [r[0] for r in cell_methods], cell_method
    )

    query = (
        sesh.query(mm.DataFile.unique_id)
        .distinct(mm.DataFile.unique_id)
        .join(
            mm.DataFileVariableGridded,
            mm.EnsembleDataFileVariables,
            mm.Ensemble,
            mm.Run,
            mm.Model,
            mm.Emission,
            mm.TimeSet,
            mm.Time,
        )
        .filter(mm.Ensemble.name == ensemble_name)
        .filter(mm.DataFileVariableGridded.netcdf_variable_name == variable)
        .filter(
            mm.DataFileVariableGridded.variable_cell_methods.in_(matching_cell_methods)
        )
        .filter(mm.Time.time_idx == time)
    )

    if model:
        query = query.filter(mm.Model.short_name == model)

    if emission:
        query = query.filter(mm.Emission.short_name == emission)

    if timescale:
        query = query.filter(mm.TimeSet.time_resolution == timescale)

    return (r[0] for r in query.all())


def index_set(m, n):
    """Return the set of all indices of a matrix with row and column index sets
    defined by `m` and `n`, respectively.
    `m` and `n` can be any valid argument vectors for `range`. For ease of use,
    non-tuple args are turned into singlet tuples."""

    def tuplify(x):
        return x if type(x) == tuple else (x,)

    return set(product(range(*tuplify(m)), range(*tuplify(n))))


def is_valid_index(index, shape):
    """True if index is in valid range for an array of given shape"""
    return all(0 <= i < n for i, n in zip(index, shape))


def vec_add(a, b):
    """numpy-style addition for builtin tuples: (1,1)+(2,3) = (3,4)"""
    return tuple(map(operator.add, a, b))


neighbour_offsets = index_set((-1, 2), (-1, 2)) - {(0, 0)}


def neighbours(cell):
    """Return all neighbours of `cell`: all cells with an x or y offset
    of +/-1"""
    return (vec_add(cell, offset) for offset in neighbour_offsets)


def apply_thredds_root(filename):
    """Apply thredds root to filename

    PCIC's THREDDS data server stores files that follow the same filepath
    pattern found in `/storage`. To access it, we just want to add on the first
    section of the url, the rest will be the same.
    """
    thredds_url_root = os.getenv("THREDDS_URL_ROOT")
    if not thredds_url_root:
        raise Exception(
            "You must set the THREDDS_URL_ROOT environment variable to use the server"
        )

    return thredds_url_root + filename
