''' Result metadata endpoint - detailed metadata on a single result
datafile. Describes the spatial and temporal extent of the results and
provides links to data access endpoints (annual mean, annual max, and annual
cycle).

Example output:
{
  "start": "1950-01-01T00:00:00", 
  "cell_y": 167, 
  "links": [
    {
      "uri": "http://127.0.0.1:8000/api/routed_streamflow/result/0", "r
      el": "self"
    }, 
    {
      "uri": "http://127.0.0.1:8000/api/routed_streamflow/result/0/annualmean", 
      "rel": "annual mean"
    }, 
    {
      "uri": "http://127.0.0.1:8000/api/routed_streamflow/result/0/annualmax", 
      "rel": "annual max"
    }, 
    {
      "uri": "http://127.0.0.1:8000/api/routed_streamflow/result/0/annualcycle", 
      "rel": "annual cycle"
    }, 
    {
      "uri": "http://127.0.0.1:8000/api/routed_streamflow/hydromodel_output/0", 
      "rel": "hydromodel_output"
    }
  ], 
  "stop": "2100-01-01T00:00:00", 
  "status": "ready", 
  "cell_x": 120, 
  "latitude": 51.46875, 
  "timestep": "1 day", 
  "longitude": -117.46875
}    
'''

from modelmeta import DataFile
from ce.api.util import open_nc
from ce.api.routed_streamflow.streamflow_helpers import result_file_list
from ce.api.routed_streamflow.streamflow_helpers import base_api_url
from ce.api.routed_streamflow.streamflow_helpers import base_streamflow_url

from flask import request

#todo: check inputs, sanitize id.
def result_metadata(sesh, id):

    result_file = result_file_list()[int(id)]
    
    result = {}
    with open_nc(result_file) as nc:
        result["status"] = "ready"
        result["cell_x"] = int(nc.variables["outlet_x_ind"][0])
        result["cell_y"] = int(nc.variables["outlet_y_ind"][0])
        result["longitude"] = float(nc.variables["lon"][0])
        result["latitude"] = float(nc.variables["lat"][0])
        
        #no valid time info in sample netCDFs, so just faking that for now.
        result["start"] = "1950-01-01T00:00:00"
        result["stop"] = "2100-01-01T00:00:00"
        result["timestep"] = "1 day"
                
        links = []
        links.append({
            "rel": "self",
            "uri": request.url
            })
        links.append({
            "rel": "annual mean",
            "uri": request.url + "/annualmean"
            })
        links.append({
            "rel": "annual max",
            "uri": request.url + "/annualmax"
            })
        links.append({
            "rel": "annual cycle",
            "uri": request.url + "/annualcycle"
            })
        links.append({
            "rel": "hydromodel_output",
            "uri": base_streamflow_url() + "/hydromodel_output/0"})
        
        result["links"] = links
        
    return result