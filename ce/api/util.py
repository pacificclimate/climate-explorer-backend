import os
from contextlib import contextmanager
from datetime import datetime, timezone
from itertools import product
import operator
import re

import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset
import modelmeta as mm

from ce.api.geo import wkt_to_masked_array


def get_files_from_run_variable(run, variable):
    return [
        file_
        for file_ in run.files
        if variable in [dfv.netcdf_variable_name for dfv in file_.data_file_variables]
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


def get_units_from_run_object(run, varname):
    files = get_files_from_run_variable(run, varname)
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
def open_nc(fname):
    if not "http" in fname and not os.path.exists(fname):
        raise Exception(
            f"File name: {fname} is not valid, database not in sync with filesystem."
        )

    try:
        nc = Dataset(fname, "r")
        nc.set_always_mask(False)
        yield nc
    finally:
        nc.close()


def get_array(nc, fname, time, area, variable):

    if variable not in nc.variables:
        raise Exception("File {} does not have variable {}.".format(fname, variable))

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
# Reduces a 3-dimensional array to a two-dimensional array by
# returning the timeidxth slice, IFF time is defined and time
# is a dimension in the netCDF. Otherwise return array unchanged.
def time_slice_array(a, timeidx, nc, fname, variable):
    if timeidx or timeidx == 0:
        if "time" not in nc.variables[variable].dimensions:
            raise Exception("File {} does not have a time dimension".format(fname))
        a = a[timeidx, :, :]
    return a


def mean_datetime(datetimes):
    timestamps = [dt.replace(tzinfo=timezone.utc).timestamp() for dt in datetimes]
    mean = np.mean(timestamps)
    return datetime.fromtimestamp(mean, tz=timezone.utc)


def validate_cell_method(cell_method):
    return cell_method in ("mean", "standard_deviation")


def find_matching_cell_methods(cell_methods, target_method):
    def filter_on_method(cell_method, target_method):
        pattern = r"time:[a-z\s]*time:\s+{}\s+over\s+(days|years)".format(target_method)
        return re.fullmatch(pattern, cell_method)

    # Older data sets were all climatological means and therefore the
    # cell_method attribute never had to specify that they were such.  With the
    # introduction of climatological standard deviation data sets the
    # cell_method usage had to be updated such that we could differentiate
    # between the different the data operations.  Thus any cell_method that
    # doesn't match the updated version is considered to be a climatological
    # mean.
    #
    # The conventions that were followed to create these cell_method attributes
    # can be found here:
    # http://cfconventions.org/cf-conventions/cf-conventions.html#cell-methods
    if target_method == "mean":
        return [
            cell_method
            for cell_method in cell_methods
            if filter_on_method(cell_method, target_method)
            or (
                not filter_on_method(cell_method, target_method)
                and not filter_on_method(cell_method, "standard_deviation")
            )
        ]
    else:
        return [
            cell_method
            for cell_method in cell_methods
            if filter_on_method(cell_method, target_method)
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
    if not validate_cell_method(cell_method):
        raise Exception("Unsupported cell_method: {}".format(cell_method))

    cell_methods = (
        sesh.query(mm.DataFileVariableGridded.variable_cell_methods)
        .distinct(mm.DataFileVariableGridded.variable_cell_methods)
        .all()
    )

    matching_cell_methods = find_matching_cell_methods(
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


def apply_thredds_root(
    filename,
    root="https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds/dodsC/datasets",
):
    """Apply thredds root to filename

    PCIC's THREDDS data server stores files that follow the same filepath
    pattern found in `/storage`. To access it, we just want to add on the first
    section of the url, the rest will be the same.
    """
    return root + filename
