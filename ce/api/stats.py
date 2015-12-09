'''
Query Params

id: Model ID
time: Climatological period (0-17)
area: WKT of selected area
variable: Variable requested

Returns JSON statistics for each model:

{
model_id1:
    {
    min: <float>,
    max: <float>,
    mean: <float>,
    median: <float>,
    stdev: <float>,
    units: <string>
    },
model_id2:
    ...}
'''

import numpy as np
import numpy.ma as ma
from sqlalchemy.orm.exc import NoResultFound

from modelmeta import DataFile, Time

from ce.api.util import get_array, get_units_from_netcdf_file, mean_datetime

def stats(sesh, id_, time, area, variable):
    '''
    '''
    try:
        df = sesh.query(DataFile).filter(DataFile.unique_id == id_).one()
        fname = df.filename
    except NoResultFound:
        return {}

    array = get_array(fname, time, area, variable)
    stats = array_stats(array)

    query = sesh.query(Time.timestep).filter(Time.time_set_id == df.timeset.id)
    if time:
        query.filter(Time.time_idx == time)
    timevals = [ t for t, in query.all() ]
    timeval = mean_datetime(timevals)

    stats.update({
        'units': get_units_from_netcdf_file(fname, variable),
        'time': timeval.strftime('%Y-%m-%dT%H:%M:%SZ')
    })
    return {id_: stats}

def array_stats(array):
    '''Return the min, max, mean, median, standard deviation and number
       of cells of a 3d data grid (numpy.ma.MaskedArray)
    '''
    return {
        'min': np.asscalar(np.min(array)),
        'max': np.asscalar(np.max(array)),
        'mean': np.asscalar(np.mean(array)),
        'median': np.asscalar(ma.median(array)),
        'stdev': np.asscalar(np.std(array)),
        'ncells': array.compressed().size
    }
