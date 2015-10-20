'''
Query Params

none

Returns list of all models available:

[
model_id1,
model_id2,
...
]
'''

from modelmeta import *

def models(sesh, ensemble_name='bcsd_downscale_canada'):
    '''
    '''
    try:
        ensemble = sesh.query(Ensemble).filter(Ensemble.name == ensemble_name).first()
    except:
        return []

    if not ensemble: # Result does not contain any row therefore ensemble does not exist
        return []

    return [ dfv.file.unique_id for dfv in ensemble.data_file_variables ]
