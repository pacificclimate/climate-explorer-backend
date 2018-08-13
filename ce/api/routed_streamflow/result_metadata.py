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