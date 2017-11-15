'''module for requesting sinlge-file data through the API
'''

import datetime
import numpy as np
from sqlalchemy.orm.exc import NoResultFound
from collections import OrderedDict

from modelmeta import DataFile
from ce.api.util import get_array, get_units_from_netcdf_file, open_nc

def timeseries(sesh, id_, area, variable):
    '''Delegate for performing data lookups within a single file

    Opens the data file specified by the id_ parameter and returns the
    data values at each timestep in the file.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        id_ (str): Unique id which is a key to the data file requested
        area (str): WKT polygon of selected area
        variable (str): Short name of the variable to be returned

    Returns:
        dict: Empty dictionary if id_ is not found in the database.

        Otherwise returns a single dict with keys `id`, `units` and
        `data`. The value for `data` is another dictionary where keys
        correspond to the time values (formatted as
        '%Y-%m-%dT%H:%M:%SZ') and values correspond to the data values
        themselves. The value for `id` is the unique_id for the file
        and the value for `units` is the unit string of the data
        values.

        For example::

            {
                'id': 'tmax_monClim_PRISM_historical_run1_198101-201012',
                'units': 'degC',
                'data':
                {
                    '1985-01-15T00:00:00Z': 1.5,
                    '1985-02-15T00:00:00Z': 2.5,
                    '1985-03-15T00:00:00Z': 5.5,
                    '1985-04-15T00:00:00Z': 10.2,
                    ...
                    '1985-12-15T00:00:00Z': 2.5,
                }
            }

    Raises:
        None?

    '''
    try:
        file_ = sesh.query(DataFile).filter(DataFile.unique_id == id_).one()
    except NoResultFound:
        return {}

    # Get all time indexes for this file
    ti = [ (time.timestep, time.time_idx) for time in file_.timeset.times ]
    ti.sort(key=lambda x: x[1])
    
    with open_nc(file_.filename) as nc:

        data = OrderedDict([(
            timeval.strftime('%Y-%m-%dT%H:%M:%SZ'),
            np.asscalar(np.mean(get_array(nc, file_.filename, idx, area, variable)))
        )
            #for timeval, idx in shortlist
            for timeval, idx in ti
        ])
        units = get_units_from_netcdf_file(nc, variable)

    return {
        'id': id_,
        'data': data,
        'units': units
    }
