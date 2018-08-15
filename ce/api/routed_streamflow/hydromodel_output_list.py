''' Hydromodel_output endpoint: provides a list of available hydromodel
outputs with metadata about the climate model and hydro model used to generate
each one.

Example output:
[
  {
    "hydromodel_output_metadata_id": 0, 
    "uri": "http://127.0.0.1:8000/api/routed_streamflow/hydromodel_output/0"
    "climate_input": {
      "scenario": "historical+rcp45", 
      "run": "r1i1p1", 
      "model": "ACCESS1-0"
    }, 
    "model_definition": {
      "name": "VIC (Built from source: v0.0.2-142-g981d56a1bb).", 
      "description": "Variable Infiltration Capacity Model GL with glacier dynamics"
    }
  },
  {
    "hydromodel_output_metadata_id": 1,
    ...
  }
]

'''

from modelmeta import DataFile
from flask import request

#The final version of this query will get all its information
#from a modelmeta database, but the database hasn't been updated yet.

#The shimmed version of this query will get its information from 
#inspecting netCDF files, but the files in question have gotten corrupted
#somehow. So for now, it's 100% canned data. :/

def hydromodel_output_list(sesh):
    
    #results.nc has gotten corrupted somehow (?) so return canned answers
    model_definition = {}
    model_definition["name"] = "VIC (Built from source: v0.0.2-142-g981d56a1bb)."
    model_definition["description"] = "Variable Infiltration Capacity Model GL with glacier dynamics"
    climate_input = {}
    climate_input["model"] = "ACCESS1-0"
    climate_input["scenario"] = "historical+rcp45"
    climate_input["run"] = "r1i1p1"
    
    outputs_list = [
        {
          "hydromodel_output_metadata_id": 0,
          "uri": "{}/0".format(request.url),
          "model_definition": model_definition,
          "climate_input": climate_input
        }
      ]
    
    return outputs_list