'''module for requesting metadata from multiple files based on model or ensemble
'''

import modelmeta as mm

def multimeta(sesh, ensemble_name='ce', model=''):
    '''Retrieve metadata for all data files in an ensemble

    The ``multimeta`` API call is available to retrieve summarized
    metadata from all data files in a given ensemble, optionally
    filtered by the name of some model.

    Unlike the ``metadata`` API call, ``multimeta`` omits information
    about the timesteps which are available. To discover this
    information, one is required to make a follow-up all to
    ``metadata`` for the specific unique_id in question.

    The ``model`` argument is optional. If it is omitted, all models
    are included in the results.

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
              variables:
                  {
                  "pr": "Precipitation"
                  }
              ensemble_member: "r1i1p1",
              timescale: "monthly"
              },
          unique_id2:
              ...
          }

    '''

    q = sesh.query(mm.DataFile.unique_id, mm.Model.organization,
            mm.Model.short_name, mm.Model.long_name, mm.Emission.short_name,
            mm.Run.name, mm.DataFileVariable.netcdf_variable_name,
            mm.VariableAlias.long_name, mm.TimeSet.time_resolution)\
            .join(mm.Run).join(mm.Model).join(mm.Emission)\
            .join(mm.DataFileVariable).join(mm.EnsembleDataFileVariables)\
            .join(mm.Ensemble).join(mm.VariableAlias).join(mm.TimeSet)\
            .filter(mm.Ensemble.name == ensemble_name)

    if model:
        q = q.filter(mm.Model.short_name == model)

    rv = {}
    results = q.all()

    # FIXME: aggregation of the variables can be done in database with the
    # array_agg() function. Change this when SQLAlchemy supports it
    # circa release 1.1
    for id_, org, model_short, model_long, emission, run, var, long_var, \
            timescale in results:
        if id_ not in rv:
            rv[id_] = {
                'institution': org,
                'model_id': model_short,
                'model_name': model_long,
                'experiment': emission,
                'variables': {var: long_var},
                'ensemble_member': run,
                'timescale': timescale
            }
        else:
            rv[id_]['variables'][var] = long_var

    return rv
