'''module for requesting data across multiple files through the API
'''

import numpy as np

from modelmeta import Run, Time, Emission, Model, TimeSet, DataFile, DataFileVariable
from ce.api.util import get_array, get_units_from_run_object, get_files_from_run_variable

def data(sesh, model, emission, time, area, variable):
    '''Delegate for performing data lookups across climatological files

    Searches the database for all files from a given model and
    emission scenario and returns a data value for that particular
    timestep (e.g. January [1], summer [14] or annual [17]) in each
    file.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        model (str): Short name for some climate model (e.g "CGCM3")
        emission (str): Short name for some emission scenario (e.g.
            "historical+rcp85")
        time (int): Timestep integer (1-17) representing the time of year
        area (str): WKT polygon of selected area
        variable (str): Short name of the variable to be returned

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
                    'units': 'degC'
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
                    'units': 'degC'
                }
            }

    Raises:
        Exception: If `time` parameter cannot be converted to an integer

    '''
    try:
        time = int(time)
    except ValueError:
        raise Exception('time parameter "{}" not convertable to an integer.'.format(time))

    results = sesh.query(Run, Time.timestep)\
            .join(Model, Emission, DataFile, DataFileVariable, TimeSet, Time)\
            .filter(DataFileVariable.netcdf_variable_name == variable)\
            .filter(Emission.short_name == emission)\
            .filter(Model.short_name == model)\
            .filter(Time.time_idx == time)\
            .filter(TimeSet.multi_year_mean == True).all()

    if not results:
        return {}

    def getdata(file_):
        array = get_array(file_.filename, time, area, variable)
        return np.asscalar(np.mean(array))

    return {
        run.name: {
            'data': {
                timeval.strftime('%Y-%m-%dT%H:%M:%SZ'): getdata(file_) for file_ in get_files_from_run_variable(run, variable) },
            'units': get_units_from_run_object(run, variable)
        } for run, timeval in results
    }
