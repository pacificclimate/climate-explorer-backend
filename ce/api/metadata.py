'''
Query Params

id: Model ID[s] (optional, null means all models)

Returns JSON model metadata:

{
model_id1:
    {
    institute_id: <string>,
    institution: <string>,
    model_id: <string>,
    model_name: <string>,
    experiment: <string>,
    variables: [<string:var1>, <string:var2>, ... ],
    ensemble_member: <string>
    },
model_id2:
    ...
}
'''

from modelmeta import *

def metadata(sesh, model_id=None):
    '''
    '''
    if not model_id:
        raise NotImplementedError("There will only ever be a single mddb"
                "Ensemble for the Climate Explorer, but there will be many"
                "more other things in the database, so we need to discuss what"
                "'return all models' actually means")

    files = sesh.query(DataFile).filter(DataFile.unique_id == model_id).all()

    rv = {}
    for f in files:
        vars = [ a.long_name for a in [ v.variable_alias for v in f.data_file_variables ] ]

        rv[f.unique_id] = {
            'institute_id': 'What is this?',
            'institution': f.run.model.organization,
            'model_id': f.run.model.short_name,
            'model_name': f.run.model.long_name,
            'experiment': f.run.emission.short_name,
            'variables': vars,
            'ensemble_member': 'What is this?'
        }
    return rv
