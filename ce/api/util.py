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


def get_units_from_run_object(sesh, run, varname, ensemble_name):
    units = (
        sesh.query(mm.VariableAlias.units)
        .distinct(mm.VariableAlias.units)
        .join(
            mm.DataFileVariableGridded,
            mm.EnsembleDataFileVariables,
            mm.Ensemble,
            mm.DataFile,
            mm.Run,
        )
        .filter(mm.Ensemble.name == ensemble_name)
        .filter(mm.DataFileVariableGridded.netcdf_variable_name == varname)
        .filter(mm.Run.name == run.name)
    )

    if len(units.all()) != 1:
        raise Exception(
            "Run {} for variable {} does not have consistent units {}".format(
                run, varname, units.all()
            )
        )

    return units.scalar()


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


# valid climatological statistic method parameters for the API. Add new ones here as needed.
VALID_CLIM_STAT_PARAMETERS = ("mean", "standard_deviation", "percentile")


def is_valid_clim_stat_param(climatological_statistic):
    """Validate the climatological_statistic parameter supplied by caller"""
    return climatological_statistic in VALID_CLIM_STAT_PARAMETERS


def check_climatological_statistic(
    cell_methods, climatological_statistic, default_to_mean=True, match_percentile=None
):
    """Determines whether the final method in a cell methods string
    (corresponding to a statistical aggregation) matches the target
    climatological statistic.
    If default_to_mean is true, treats errors and unrecognized methods
    as though they are climatological means. This compensates for some
    noisy cell_methods attributes in our data, all of which are
    climatological means.
    If a "match_percentile" float is supplied, will only return true for
    percentile datasets that match that specific percentile. Otherwise
    will return true for any percentile dataset. match_percentile is
    ignored if climatological_statistic is not "percentile".
    """

    def final_method(p):
        """get the name of the final cell method, corresponding 
        to climatological aggregation (usually)"""
        return p[-1].method.name

    def final_params(p):
        """get the parameters of the final cell method, providing details
        of the climatological aggregation (ie, percentile value)"""
        return p[-1].method.params

    parsed = parse(cell_methods)

    if climatological_statistic == "mean" and default_to_mean:
        # determine means by process of elimination
        nonmeans = [m for m in VALID_CLIM_STAT_PARAMETERS if m != "mean"]
        return parsed is None or final_method(parsed) not in nonmeans
    elif (
        parsed is not None
        and climatological_statistic == "percentile"
        and match_percentile is not None
    ):
        return (
            final_method(parsed) == "percentile"
            and final_params(parsed)[0] == match_percentile
        )
    elif parsed is not None:
        return final_method(parsed) == climatological_statistic
    else:
        # unparsable cell methods string
        return False


def get_climatological_statistic(cell_methods, default_to_mean=True):
    """Given a cell_methods string, returns a description of the
    statistical process used to make the climatology, currently either
    'mean', 'standard_deviation', or 'percentile[number]'.
    If default_to_mean is true, unparsable and unrecognizable cell
    methods strings will be treated as means."""
    climatological_statistic = False
    for clim_stat in VALID_CLIM_STAT_PARAMETERS:
        if check_climatological_statistic(cell_methods, clim_stat, default_to_mean):
            climatological_statistic = clim_stat

    # return percentile number, if relevant
    if climatological_statistic == "percentile":
        cm_parsed = parse(cell_methods)
        percentile_num = cm_parsed[-1].method.params[0]
        climatological_statistic = "{}[{}]".format(
            climatological_statistic, percentile_num
        )

    return climatological_statistic


def filter_by_climatological_statistic(
    cell_methods, climatological_statistic, match_percentile=None
):
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
        cm
        for cm in cell_methods
        if check_climatological_statistic(
            cm,
            climatological_statistic,
            default_to_mean=True,
            match_percentile=match_percentile,
        )
    ]


def search_for_unique_ids(
    sesh,
    ensemble_name="ce_files",
    model="",
    emission="",
    variable="",
    time=0,
    timescale="",
    climatological_statistic="mean",
):
    if not is_valid_clim_stat_param(climatological_statistic):
        raise Exception(
            "Unsupported climatological_statistic parameter: {}".format(
                climatological_statistic
            )
        )

    cell_methods = (
        sesh.query(mm.DataFileVariableGridded.variable_cell_methods)
        .distinct(mm.DataFileVariableGridded.variable_cell_methods)
        .all()
    )

    matching_cell_methods = filter_by_climatological_statistic(
        [r[0] for r in cell_methods], climatological_statistic,
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
