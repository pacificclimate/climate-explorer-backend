"""module for requesting metadata from multiple files based on model or ensemble
"""

from modelmeta import DataFile, Model, Emission, Run
from modelmeta import DataFileVariable, VariableAlias, TimeSet
from modelmeta import EnsembleDataFileVariables, Ensemble


def multimeta(sesh, ensemble_name="ce_files", model=""):
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

    Returns:
        A dictionary keyed by unique_id for all unique_ids in the
        requested model/ensemble. The value is delegated to the metadata call

        For example::

          {
          pr_day_BCCAQ-ANUSPLIN300-MRI-CGCM3_historical-rcp45_r1i1p1_19500101-21001231:
              {
              institution: "PCIC",
              model_id: "BCCAQ+ANUSPLIN300+MRI-CGCM3",
              model_name: "",
              experiment: "historical+rcp45",
              variables:
                  {
                  "pr": "Precipitation"
                  },
              ensemble_member: "r1i1p1",
              timescale: "monthly",
              multi_year_mean: false,
              start_date: datetime.datetime(1950, 1, 1, 0, 0),
              end_date: datetime.datetime(2100, 12, 31, 0, 0),
              modtime: datetime.datetime(2010, 1, 1, 17, 30, 4)
              },
          unique_id2:
              ...
          }

    """

    q = (
        sesh.query(
            DataFile.unique_id,
            Model.organization,
            Model.short_name,
            Model.long_name,
            Emission.short_name,
            Run.name,
            DataFileVariable.netcdf_variable_name,
            VariableAlias.long_name,
            TimeSet.time_resolution,
            TimeSet.multi_year_mean,
            TimeSet.start_date,
            TimeSet.end_date,
            DataFile.index_time,
        )
        .join(Run, Run.id == DataFile.run_id)
        .join(Model)
        .join(Emission)
        .join(DataFileVariable, DataFileVariable.data_file_id == DataFile.id)
        .join(EnsembleDataFileVariables)
        .join(Ensemble)
        .join(VariableAlias, VariableAlias.id == DataFileVariable.variable_alias_id)
        .join(TimeSet, TimeSet.id == DataFile.time_set_id)
        .filter(Ensemble.name == ensemble_name)
    )

    if model:
        q = q.filter(Model.short_name == model)

    rv = {}
    results = q.all()

    # FIXME: aggregation of the variables can be done in database with the
    # array_agg() function. Change this when SQLAlchemy supports it
    # circa release 1.1
    for (
        id_,
        org,
        model_short,
        model_long,
        emission,
        run,
        var,
        long_var,
        timescale,
        multi_year_mean,
        start_date,
        end_date,
        modtime,
    ) in results:
        if id_ not in rv:
            rv[id_] = {
                "institution": org,
                "model_id": model_short,
                "model_name": model_long,
                "experiment": emission,
                "variables": {var: long_var},
                "ensemble_member": run,
                "timescale": timescale,
                "multi_year_mean": multi_year_mean,
                "start_date": start_date,
                "end_date": end_date,
                "modtime": modtime,
            }
        else:
            rv[id_]["variables"][var] = long_var

    return rv
