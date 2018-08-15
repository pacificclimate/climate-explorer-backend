''' Result metadata endpoint - provides basic metadata on all available 
result datasets: which hydromodel output they were generated with and 
their spatial location.

Sample output:
[
  {
    "cell_y": 167, 
    "status": "ready", 
    "cell_x": 120, 
    "hydromodel_output_metadata": "http://127.0.0.1:8000/api/routed_streamflow/hydromodel_output/0", 
    "uri": "http://127.0.0.1:8000/api/routed_streamflow/result/0"
  }, 
  {
    "cell_y": 163, 
    "status": "ready", 
    "cell_x": 129, 
    "hydromodel_output_metadata": "http://127.0.0.1:8000/api/routed_streamflow/hydromodel_output/0", 
    "uri": "http://127.0.0.1:8000/api/routed_streamflow/result/1"
  }, 
  ...
]

'''
#eventually will dig up all needed info from the database, but for now is
#just getting it from files directly.

from modelmeta import DataFile
from ce.api.util import open_nc
from flask import request
from ce.api.routed_streamflow.streamflow_helpers import result_file_list, base_streamflow_url

def result_list(sesh):
    results = []
    inc = 0    

    #since the files aren't in the database yet, just index in alphabetical order.
    for result in result_file_list():
        with open_nc(result) as nc:
            cell_x = int(nc.variables["outlet_x_ind"][0])
            cell_y = int(nc.variables["outlet_y_ind"][0])
            uri = "{}/{}".format(request.url, inc)
            results.append({
                "uri": uri,
                "status": "ready",
                "hydromodel_output_metadata": "{}/hydromodel_output/0".format(base_streamflow_url()),
                "cell_x": cell_x,
                "cell_y": cell_y
                })
            inc += 1
    
    return results