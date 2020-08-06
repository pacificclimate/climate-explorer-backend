"""module for requesting metadata from multiple files based on model or ensemble
"""

from modelmeta import DataFile, Model, Emission, Run
from modelmeta import DataFileVariableGridded, VariableAlias, TimeSet
from modelmeta import EnsembleDataFileVariables, Ensemble


def multimeta(sesh, ensemble_name="ce_files", model="", extras=""):
    """Retrieve metadata for all data files in an ensemble

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

        extras (str): Comma-separated list of extra fields to be included in
            response. Currently responds to fields:
                "filepath": in each dictionary item, filepath of data file

    Returns:
        A dictionary keyed by unique_id for all unique_ids in the
        requested model/ensemble. The value is delegated to the metadata call

        For example::

          {
              'pr_day_BCCAQ-ANUSPLIN300-MRI-CGCM3_historical-rcp45_r1i1p1_19500101-21001231': {
                  'filepath': '/storage/data/projects/blah/blah/pr_day_BCCAQ-ANUSPLIN300-MRI-CGCM3_historical-rcp45_r1i1p1_19500101-21001231.nc',
                  'institution': 'PCIC',
                  'model_id': 'BCCAQ+ANUSPLIN300+MRI-CGCM3',
                  'model_name': '',
                  'experiment': 'historical+rcp45',
                  'variables':
                      {
                        'pr': 'Precipitation'
                      },
                  'ensemble_member': 'r1i1p1',
                  'timescale': 'monthly',
                  'multi_year_mean': false,
                  'start_date': datetime.datetime(1950, 1, 1, 0, 0),
                  'end_date': datetime.datetime(2100, 12, 31, 0, 0),
                  'modtime': datetime.datetime(2010, 1, 1, 17, 30, 4)
              },
              'unique_id2': {
                  ...
              },
              ...
          }

    """

    q = (
        sesh.query(
            DataFile.unique_id.label("unique_id"),
            DataFile.filename.label("filepath"),
            Model.organization.label("institution"),
            Model.short_name.label("model_id"),
            Model.long_name.label("model_name"),
            Emission.short_name.label("experiment"),
            Run.name.label("ensemble_member"),
            DataFileVariableGridded.netcdf_variable_name.label("netcdf_variable_name"),
            VariableAlias.long_name.label("variable_long_name"),
            TimeSet.time_resolution.label("timescale"),
            TimeSet.multi_year_mean.label("multi_year_mean"),
            TimeSet.start_date.label("start_date"),
            TimeSet.end_date.label("end_date"),
            DataFile.index_time.label("modtime"),
        )
        .join(Run, Run.id == DataFile.run_id)
        .join(Model)
        .join(Emission)
        .join(
            DataFileVariableGridded, DataFileVariableGridded.data_file_id == DataFile.id
        )
        .join(EnsembleDataFileVariables)
        .join(Ensemble)
        .join(
            VariableAlias, VariableAlias.id == DataFileVariableGridded.variable_alias_id
        )
        .join(TimeSet, TimeSet.id == DataFile.time_set_id)
        .filter(Ensemble.name == ensemble_name)
    )

    if model:
        q = q.filter(Model.short_name == model)

    results = q.all()

    # FIXME: aggregation of the variables can be done in database with the
    # array_agg() function. Change this when SQLAlchemy supports it
    # circa release 1.1

    base_attribute_names = """
            institution
            model_id
            model_name
            experiment
            ensemble_member
            timescale
            multi_year_mean
            start_date
            end_date
            modtime        
        """.split()

    allowable_extra_attribute_names = """
            filepath
        """.split()
    extra_attribute_names = [
        name for name in extras.split(",") if name in allowable_extra_attribute_names
    ] if extras is not None and extras != "" else []

    simple_attribute_names = base_attribute_names + extra_attribute_names

    rv = {}
    for result in results:
        unique_id = result.unique_id
        if unique_id not in rv:
            rv[unique_id] = {
                name: getattr(result, name) for name in simple_attribute_names
            }
            rv[unique_id]["variables"] = {}
        rv[unique_id]["variables"][result.netcdf_variable_name] = \
            result.variable_long_name
        
    return rv
