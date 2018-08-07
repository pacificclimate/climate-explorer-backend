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
        result["hydromodel_output_metadata_id"] = 4
        result["cell_x"] = int(nc.variables["outlet_x_ind"][0])
        result["cell_y"] = int(nc.variables["outlet_y_ind"][0])
                
        links = []
        #todo: have rel be links, like in Rod's documents        
        links.append({
            "rel": "self",
            "uri": request.url
            })
        links.append({
            "rel": base_api_url() + "/relations/timeseries",
            "uri": request.url + "/timeseries"
            })
        links.append({
            "rel": "deprecate",
            "uri": request.url + "/deprecate"
            })
        links.append({
            "rel": base_api_url() + "/relations/hydromodel_output",
            "uri": base_streamflow_url() + "/hydromodel_output/0"})
        
        result["links"] = links
        
    return result