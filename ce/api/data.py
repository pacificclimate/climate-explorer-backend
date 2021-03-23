"""module for requesting data across multiple files through the API
"""

import numpy as np
import os

from modelmeta import Run, Emission, Model, TimeSet, DataFile
from modelmeta import DataFileVariableGridded, Ensemble
from ce.api.util import (
    get_array,
    get_units_from_run_object,
    open_nc,
    check_climatological_statistic,
    is_valid_clim_stat_param,
)
from distutils.util import strtobool


def data(
    sesh,
    model,
    emission,
    time,
    area,
    variable,
    timescale="other",
    ensemble_name="ce_files",
    climatological_statistic="mean",
    percentile=None,
    is_thredds=False,
):
    """Delegate for performing data lookups across climatological files

    Searches the database for all files from a given model and
    emission scenario with the indicated variable, time resolution (timescale),
    and belonging to the indicated ensemble,
    and returns the data value for the requested timestep
    (e.g., August [7], summer [2], or year [0])
    from each matching file.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object

        model (str): Short name for some climate model (e.g "CGCM3")

        emission (str): Short name for some emission scenario
            (e.g."historical+rcp85")

        time (int): Timestep index (0-based) representing the time of year;
            0-11 for monthly, 0-3 for seasonal, 0 for annual datasets.

        area (str): WKT polygon of selected area

        variable (str): Short name of the variable to be returned

        timescale (str): Description of the resolution of time to be
            returned (e.g. "monthly" or "yearly")

        ensemble_name (str): Name of ensemble

        climatological_statistic (str): Statistical operation applied to variable in a
            climatological dataset (e.g "mean", "standard_deviation",
            "percentile). Defaulted to "mean".
        
        percentile (float): if climatological_statistic is "percentile", specifies what
            percentile value to use. A percentile value must be provided if the 
            climatological_statistic is "percentile".

        is_thredds (bool): If set to `True` the filepath will be searched for
            on THREDDS server. This flag is not needed when running the backend
            as a server as the files are accessed over the web.

    Returns:
        dict:
            Empty dictionary if there exist no files matching the provided
            model and emissions scenario.

        Otherwise returns a single dict keyed on the run id for all
        runs that match the model and emissions scenario. values are a
        dict with keys `data` and `units`. The `data` dictionary
        contains keys corresponding to the time values (formatted as
        '%Y-%m-%dT%H:%M:%SZ') and values corresponding to the data
        values themselves.

        For example::

            {
                'r1i1p1':
                {
                    'data':
                    {
                        '1985-1-15T00:00:00Z': 5.1,
                        '2015-1-15T00:00:00Z': 7.2,
                        '2045-1-15T00:00:00Z': 10.3,
                        '2075-1-15T00:00:00Z': 12.4,
                    }
                    'units': 'degC',
                    'modtime': datetime.datetime(2010, 1, 1, 17, 30, 4)
                }
                'r2i1p1':
                {
                    'data':
                    {
                        '1985-1-15T00:00:00Z': 5.2,
                        '2015-1-15T00:00:00Z': 7.3,
                        '2045-1-15T00:00:00Z': 10.4,
                        '2075-1-15T00:00:00Z': 12.5,
                    }
                    'units': 'degC',
                    'modtime': datetime.datetime(2010, 1, 1, 17, 30, 4)
                }
            }

    Raises:
        Exception: If `time` parameter cannot be converted to an integer

    """
    # Validate arguments
    try:
        time = int(time)
    except ValueError:
        raise Exception(
            'time parameter "{}" not convertable to an integer.'.format(time)
        )
    if not is_valid_clim_stat_param(climatological_statistic):
        raise Exception(
            "Unsupported climatological_statistic parameter: {}".format(
                climatological_statistic
            )
        )
    if percentile is not None:
        try:
            percentile = float(percentile)
        except ValueError:
            raise Exception(
                "Percentile parameter {} not convertable to a number".format(percentile)
            )
    if climatological_statistic == "percentile" and not percentile:
        raise Exception(
            "Percentile parameters must be specified to access percentile data"
        )
    if climatological_statistic != "percentile" and percentile:
        raise Exception(
            "Percentile parameter is only meaningful for percentile climatologies"
        )

    def get_spatially_averaged_data(data_file, time_idx, is_thredds):
        """
        From the NetCDF data file pointed at by `data_file`,
        get the spatial average over the area specified by `area`
        of the data for variable `variable`
        at time index `time_idx`.

        :param data_file (modelmeta.DataFile): source data file
        :param time_idx (int): index of time of interest
        :param is_thredds (bool): whether data target is on thredds server
        :return: float
        """
        if isinstance(is_thredds, str):
            is_thredds = strtobool(is_thredds)

        if is_thredds:
            data_filename = os.getenv("THREDDS_URL_ROOT") + data_file.filename
        else:
            data_filename = data_file.filename

        with open_nc(data_filename) as nc:
            a = get_array(nc, data_filename, time_idx, area, variable)
        return np.mean(a).item()

    def get_time_value(timeset, time_idx):
        """
        Get the time value associated with time index `time_idx`
        from the time set `timeset`.

        :param timeset (modelmeta.TimeSet): time set
        :param time_idx (int): index of time of interest
        :return: (str)
        """
        for time in timeset.times:
            if time.time_idx == time_idx:
                return time.timestep
        raise Exception("Timeset has no time with index value {}".format(time_idx))

    query = (
        sesh.query(DataFileVariableGridded)
        .filter(DataFileVariableGridded.netcdf_variable_name == variable)
        .join(DataFileVariableGridded.file)
        .join(DataFile.run)
        .join(Run.model)
        .filter(Model.short_name == model)
        .join(Run.emission)
        .filter(Emission.short_name == emission)
        .join(DataFile.timeset)
        .filter(TimeSet.time_resolution == timescale)
        .filter(TimeSet.multi_year_mean)
        .filter(DataFileVariableGridded.ensembles.any(Ensemble.name == ensemble_name))
    )
    data_file_variables = query.all()

    # filter by cell methods parameter
    data_file_variables = [
        dfv
        for dfv in data_file_variables
        if check_climatological_statistic(
            dfv.variable_cell_methods,
            climatological_statistic,
            default_to_mean=True,
            match_percentile=percentile,
        )
    ]

    result = {}
    for data_file_variable in data_file_variables:

        try:
            run_result = result[data_file_variable.file.run.name]
        except KeyError:
            run_result = result[data_file_variable.file.run.name] = {
                "data": {},
                "units": get_units_from_run_object(
                    sesh, data_file_variable.file.run, variable, ensemble_name
                ),
                "modtime": data_file_variable.file.index_time,
            }
        time_key = get_time_value(data_file_variable.file.timeset, time).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        value = get_spatially_averaged_data(data_file_variable.file, time, is_thredds)
        run_result["data"][time_key] = value
        run_result["modtime"] = max(
            run_result["modtime"], data_file_variable.file.index_time
        )

    return result
