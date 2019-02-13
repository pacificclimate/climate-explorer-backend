'''module for requesting data across multiple files through the API
'''

import numpy as np

from modelmeta import Run, Emission, Model, TimeSet, DataFile
from modelmeta import DataFileVariable, EnsembleDataFileVariables, Ensemble
from ce.api.util import get_array, get_units_from_run_object, open_nc

def data(sesh, model, emission, time, area, variable, timescale='other',
         ensemble_name='ce_files'):
    '''Delegate for performing data lookups across climatological files

    Searches the database for all files from a given model and
    emission scenario with the indicated variable, time resolution (timescale),
    and belonging to the indicated ensemble,
    and returns the data value for the requested timestep
    (e.g., August [7], summer [2], or year [0])
    from each matching file.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        model (str): Short name for some climate model (e.g "CGCM3")
        emission (str): Short name for some emission scenario (e.g.
            "historical+rcp85")
        time (int): Timestep index (0-based) representing the time of year;
            0-11 for monthly, 0-3 for seasonal, 0 for annual datasets.
        area (str): WKT polygon of selected area
        variable (str): Short name of the variable to be returned
        timescale (str): Description of the resolution of time to be
            returned (e.g. "monthly" or "yearly")
        ensemble_name (str): Name of ensemble

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

    '''
    # Validate arguments

    try:
        time = int(time)
    except ValueError:
        raise Exception('time parameter "{}" not convertable to an integer.'
                        .format(time))

    def get_spatially_averaged_data(data_file, time_idx):
        """
        From the NetCDF data file pointed at by `data_file`,
        get the spatial average over the area specified by `area`
        of the data for variable `variable`
        at time index `time_idx`.

        :param data_file (modelmeta.DataFile): source data file
        :param time_idx (int): index of time of interest
        :return: float
        """
        with open_nc(data_file.filename) as nc:
            a = get_array(nc, data_file.filename, time_idx, area, variable)
        return np.asscalar(np.mean(a))

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
        raise Exception('Timeset has no time with index value {}'
                        .format(time_idx))

    query = (
        sesh.query(DataFileVariable)
        .filter(DataFileVariable.netcdf_variable_name == variable)

        .join(DataFileVariable.file)
        .join(DataFile.run)

        .join(Run.model)
        .filter(Model.short_name == model)

        .join(Run.emission)
        .filter(Emission.short_name == emission)

        .join(DataFile.timeset)
        .filter(TimeSet.time_resolution == timescale)
        .filter(TimeSet.multi_year_mean == True)

        .filter(DataFileVariable.ensembles.any(Ensemble.name == ensemble_name))
    )
    data_file_variables = query.all()

    result = {}
    for data_file_variable in data_file_variables:
        try:
            run_result = result[data_file_variable.file.run.name]
        except KeyError:
            run_result = result[data_file_variable.file.run.name] = {
                'data': {},
                'units': get_units_from_run_object(
                    data_file_variable.file.run, variable),
                'modtime': data_file_variable.file.index_time
            }
        time_key = (
            get_time_value(data_file_variable.file.timeset, time)
                .strftime('%Y-%m-%dT%H:%M:%SZ'))
        value = get_spatially_averaged_data(data_file_variable.file, time)
        run_result['data'][time_key] = value
        run_result['modtime'] = max(run_result['modtime'],\
                                    data_file_variable.file.index_time)

    return result
