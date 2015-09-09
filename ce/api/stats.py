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
from sqlalchemy.orm.exc import NoResultFound

def stats(sesh, id_, time, area, variable):
    '''
    '''
    try:
        fname, = sesh.query(DataFile.filename).filter(DataFile.unique_id == id_).one()
    except NoResultFound:
        return {}

    return {
        'model_id1':
        {
            'min': 0.0,
            'max': 2.0,
            'mean': 1.0,
            'median': 1.0,
            'stdev': 1.0,
            'units': 'degC'
        },
    }

