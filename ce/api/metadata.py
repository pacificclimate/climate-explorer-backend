'''module for requesting metadata for one single file through the API
'''

from modelmeta import DataFile
from sqlalchemy.orm.exc import NoResultFound

def metadata(sesh, model_id):
    '''Delegate for performing a metadata lookup for one single file

    The `metadata` call is intended for the client to retrieve
    attributes, model information and organizational information. In
    also includes variable/measured quantity names as well as the time
    values for which data exists. The `metadata` call uses information
    from the `modelmeta` database exclusively and does not hit any data
    files on disk.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        model_id (str): Unique id which is a key to the data file requested

    Returns:
        dict: Empty dictionary if model_id is not found in the database.

        Otherwise returns a single dict with the key of the file's
        unique_id and the value being a nested dict with keys:
        'institution', 'model_id', 'model_name', 'experiment',
        'ensemble_member' (run_name?), and 'variables'.

        'variables' is a nested dict of netcdf variable name, long
        variable description pars.

        For example::

            {
                'tmax_monClim_PRISM_historical_run1_198101-201012':
                {
                    'institution': 'Pacific Climate Impacts Consortium',
                    'model_id': 'BCSD+ANUSPLIN300+CCSM4',
                    'model_name': 'CCSM4 GCM data downscaled to '
                                  'ANUSPLINE grid using BCSD',
                    'experiment': 'historical+rcp45',
                    'ensemble_member': 'r1i1p1',
                    'variables':
                    {
                        'tasmax': 'Maximum daily temperature',
                        'tasmin': 'Minimum daily temperature',
                    },
                    'timescale': 'monthly',
                    'times':
                    {
                        0: '1985-01-15T00:00:00Z',
                        1: '1985-02-15T00:00:00Z',
                        2: '1985-03-15T00:00:00Z',
                        3: '1985-04-15T00:00:00Z'
                    }
                }
            }

    Raises:
        None?

    '''
    try:
        file_ = sesh.query(DataFile).filter(DataFile.unique_id == model_id).one()
    except NoResultFound:
        return {}

    vars_ = {
            dfv.netcdf_variable_name: a.long_name
                for a, dfv in [
                        (dfv.variable_alias, dfv) for dfv in file_.data_file_variables
                ]
    }

    times = {
        time.time_idx: time.timestep.strftime('%Y-%m-%dT%H:%M:%SZ')
                for time in file_.timeset.times
    } if file_.timeset else {}
    timescale = file_.timeset.time_resolution if file_.timeset else 'other'

    run = file_.run
    model = run.model
    return {
        model_id: {
            'institution': model.organization,
            'model_id': model.short_name,
            'model_name': model.long_name,
            'experiment': run.emission.short_name,
            'variables': vars_,
            'ensemble_member': run.name,
            'times': times,
            'timescale': timescale
        }
    }
