'''module for requesting unique_ids from ensemble or model short name
'''

from modelmeta import Ensemble

def lister(sesh, ensemble_name='ce', model=None):

    '''
    Args
        sesh (sqlalchemy.orm.session.Session): A database Session object
        ensemble (str): Some named ensemble
        model (str): Short name for some climate model (e.g "CGCM3")

    Returns:
        list of all unique_ids within that ensemble and/or model.

        For example:
            ensemble = default, model = PRISM (assuming PRISM group is in 'ce' ensemble)
            [
                tmax_monClim_PRISM_historical_run1_198101-201012,
                tmin_monClim_PRISM_historical_run1_198101-201012,
                pr_monClim_PRISM_historical_run1_198101-201012
            ]
    '''

    ensemble = sesh.query(Ensemble).filter(Ensemble.name == ensemble_name).first()

    if not ensemble: # Result does not contain any row therefore ensemble does not exist
        return []

    if model:
        model = model.replace(' ', '+')
        return [ dfv.file.unique_id for dfv in ensemble.data_file_variables if dfv.file.run.model.short_name == model ]

    return [ dfv.file.unique_id for dfv in ensemble.data_file_variables ]
