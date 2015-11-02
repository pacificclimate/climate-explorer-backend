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

from modelmeta import DataFile

from ce.api.util import get_array, get_units_from_netcdf_file

def stats(sesh, id_, time, area, variable):
    '''
    '''
    try:
        fname, = sesh.query(DataFile.filename).filter(DataFile.unique_id == id_).one()
    except NoResultFound:
        return {}

    array = get_array(fname, time, area, variable)
    stats = array_stats(array)
    stats['units'] = get_units_from_netcdf_file(fname, variable)
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
