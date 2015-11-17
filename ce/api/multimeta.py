'''module for requesting metadata from multiple files based on model or ensemble
'''

from modelmeta import Ensemble

from ce.api.metadata import metadata

def multimeta(sesh, ensemble_name='ce', model=''):
    '''
    Args
        sesh (sqlalchemy.orm.session.Session): A database Session object
        ensemble (str): Some named ensemble
        model (str): Short name for some climate model (e.g "CGCM3")

    Returns:
        A dictionary keyed by unique_id for all unique_ids in the requested model/ensemble.
        The value is delegated to the metadata call

        For example:

        {
        pr_day_BCCAQ-ANUSPLIN300-MRI-CGCM3_historical-rcp45_r1i1p1_19500101-21001231:
            {
            institute_id: "PCIC",
            institution: "Pacific Climate Impacts Consortium (PCIC), Victoria, BC, www.pacificclimate.org",
            model_id: "BCCAQ+ANUSPLIN300+MRI-CGCM3",
            model_name: "",
            experiment: "historical+rcp45",
            variables: "pr",
            ensemble_member: "r1i1p1"
            },
        unique_id2:
            ...
        }
    '''

    ensemble = sesh.query(Ensemble).filter(Ensemble.name == ensemble_name).first()

    rv = {}
    if not ensemble: # Result does not contain any row therefore ensemble does not exist
        return rv

    if model:
        model = model.replace(' ', '+')
        unique_ids = [ dfv.file.unique_id for dfv in ensemble.data_file_variables if dfv.file.run.model.short_name == model ]
    else:
        unique_ids =  [ dfv.file.unique_id for dfv in ensemble.data_file_variables ]

    for id_ in unique_ids:
        rv.update(metadata(sesh, id_))
    return rv
