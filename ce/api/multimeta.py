'''module for requesting metadata from multiple files based on model or ensemble
'''

from modelmeta import *

from ce.api.metadata import metadata
from ce import cache

@cache.memoize(timeout=86400)
def multimeta(sesh, ensemble_name='ce', model=''):
    '''
    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        ensemble (str): Some named ensemble
        model (str): Short name for some climate model (e.g "CGCM3")

    Returns:
        A dictionary keyed by unique_id for all unique_ids in the requested model/ensemble.
        The value is delegated to the metadata call

        For example::

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

    q = sesh.query(DataFile.unique_id, Model.organization, Model.short_name,
            Model.long_name, Emission.short_name, Run.name,
            DataFileVariable.netcdf_variable_name, VariableAlias.long_name)\
            .join(Run).join(Model).join(Emission).join(DataFileVariable)\
            .join(EnsembleDataFileVariables).join(Ensemble)\
            .join(VariableAlias).filter(Ensemble.name == ensemble_name)

    rv = {}
    results = q.all()

    # FIXME: aggregation of the variables can be done in database with the
    # array_agg() function. Change this when SQLAlchemy supports it
    # circa release 1.1
    for id_, org, model_short, model_long, emission, run, var, long_var in results:
        if id_ not in rv:
            rv[id_] = {
                'institution': org,
                'model_id': model_short,
                'model_name': model_long,
                'experiment': emission,
                'variables': {var: long_var},
                'ensemble_member': run,
            }
        else:
            rv[id_]['variables'][var] = long_var

    return rv
