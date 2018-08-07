
#eventually will dig up all needed info from the database, but for now is
#just getting it from files.

from modelmeta import DataFile
from ce.api.util import open_nc
from flask import request
from ce.api.routed_streamflow.streamflow_helpers import result_file_list

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
                "hydromodel_output_metadata_id": 0,
                "cell_x": cell_x,
                "cell_y": cell_y
                })
            inc += 1
    
    return results