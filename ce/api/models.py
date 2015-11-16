'''module for requesting list of available models
'''

from sqlalchemy import distinct

from modelmeta import Ensemble

def models(sesh, ensemble_name='ce'):

    '''
    Args
        sesh (sqlalchemy.orm.session.Session): A database Session object

    Returns list of all models available:

    [
    model_short_name1,
    model_short_name2,
    ...
    ]
    '''

    ensemble = sesh.query(Ensemble).filter(Ensemble.name == ensemble_name).first()

    if not ensemble: # Result does not contain any row therefore ensemble does not exist
        return []

    return list(set([ dfv.file.run.model.short_name for dfv in ensemble.data_file_variables ]))
