'''module for requesting stats from multiple files based on model or ensemble
'''

from ce.api.stats import stats
from ce.api.util import search_for_unique_ids

def multistats(sesh, ensemble_name='ce', model='', emission='', time=0,
               area=None, variable='', timescale=''):
    '''Request and calculate statistics for multiple models or scenarios

    There are some cases for which one may want to get a set of
    summary statistics for multiple models and scenarios (e.g. to
    produce a table comparing several different emission
    scenarios. This request will do that.

    It starts by searching for all of the data files for the provided
    variable and will filter according to the model and emission
    parameters.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        ensemble_name (str): The name of the application-level ensemble
            (e.g. "ce")
        model (str): Short name for some climate model (e.g "CGCM3") to
            be used as a filter
        emission (str): Short name for some emission scenario (e.g.
            "historical+rcp85") to be used as a filter
        time (int): Timestep integer (1-17) representing the time of year
        area (str): WKT polygon of selected area
        variable (str): Short name of the variable to be returned

    Returns:
        dict: Empty dictionary if no unique_ids matched the search.

        Otherwise, returns a single dict with one key for each
        unique_id and the value being the result of the stats() API
        call (a dictionary with the following attributes: 'mean',
        'stdev', 'min', 'max', 'median', 'ncells', 'units', 'time').

        For example ::

            {'file0':
                {
                    'mean': 303.97227647569446,
                    'stdev': 8.428096450998078,
                    'min': 288.71807861328125,
                    'max': 318.9695739746094,
                    'median': 301.61065673828125,
                    'ncells': 72,
                    'units': 'K',
                    'time': datetime.datetime(1985, 6, 30, 12, 0, 0),
                    'modtime': datetime.datetime(2010, 1, 1, 17, 30, 4),
                }
             'file1':
                {
                    'mean': 305,
                    'stdev': 8.7,
                    'min': 299.0,
                    'max': 311.0,
                    'median': 42.1,
                    'ncells': 72,
                    'units': 'K',
                    'time': datetime.datetime(1985, 6, 30, 12, 0, 0),
                    'modtime': datetime.datetime(2010, 1, 1, 17, 30, 4),
                }
            }
    '''

    ids = search_for_unique_ids(sesh, ensemble_name, model, emission, variable,
                                time, timescale)
    return {
        id_: stats(sesh, id_, time, area, variable)[id_]
        for id_ in ids
    }
