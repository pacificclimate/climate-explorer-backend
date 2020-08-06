"""module for requesting metadata for one single file through the API
"""
from sqlalchemy.orm.exc import NoResultFound

from modelmeta import DataFile


def metadata(sesh, model_id, extras=""):
    """Delegate for performing a metadata lookup for one single file

    The `metadata` call is intended for the client to retrieve
    attributes, model information and organizational information. In
    also includes variable/measured quantity names as well as the time
    values for which data exists. The `metadata` call uses information
    from the `modelmeta` database exclusively and does not hit any data
    files on disk.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object

        model_id (str): Unique id which is a key to the data file requested

        extras (str): Comma-separated list of extra fields to be included in
            response. Currently responds to fields:
                "filepath": in each dictionary item, filepath of data file
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
                    'filepath': '/storage/data/projects/blah/blah/tmax_monClim_PRISM_historical_run1_198101-201012.nc',
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
                        0: datetime.datetime(1985, 1, 15, 0, 0),
                        1: datetime.datetime(1985, 2, 15, 0, 0),
                        2: datetime.datetime(1985, 3, 15, 0, 0),
                        3: datetime.datetime(1985, 4, 15, 0, 0),
                    }
                    'multi_year_mean': False,
                    'start_date': 'datetime.datetime(1985, 1, 15, 0, 0),
                    'end_date': datetime.datetime(1985, 4, 15, 0, 0),
                    'modtime': datetime.datetime(2010, 1, 1, 17, 30, 4)
                }
            }

    Raises:
        ValueError

    """
    try:
        data_file = sesh.query(DataFile).filter(DataFile.unique_id == model_id).one()
    except NoResultFound:
        return {}

    variables = {
        dfv.netcdf_variable_name: dfv.variable_alias.long_name
        for dfv in data_file.data_file_variables
    }
    run = data_file.run
    model = run.model

    # These values are always returned
    base_values = {
        "institution": model.organization,
        "model_id": model.short_name,
        "model_name": model.long_name,
        "experiment": run.emission.short_name,
        "variables": variables,
        "ensemble_member": run.name,
        "modtime": data_file.index_time,
    }

    # A subset of these values is returned, depending on what is requested
    # by `extras` param
    all_extra_values = {
        "filepath": data_file.filename,
    }
    requested_extra_values = {
        key: value
        for key, value in all_extra_values.items()
        if key in (extras or "").split(",")
    }

    # Time are given null values if timeset is absent.
    timeset = data_file.timeset
    time_values = {
        "times": {
            time.time_idx: time.timestep for time in timeset.times
        },
        "timescale": timeset.time_resolution,
        "multi_year_mean": timeset.multi_year_mean,
        "start_date": timeset.start_date,
        "end_date": timeset.end_date,
    } if timeset else {
        "times": {},
        "timescale": None,
        "multi_year_mean": None,
        "start_date": None,
        "end_date": None,
    }

    return {
        model_id: {
            **base_values,
            **requested_extra_values,
            **time_values,
        }
    }
