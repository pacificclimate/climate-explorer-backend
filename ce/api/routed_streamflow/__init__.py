''' PCIC Climate Explorer streamflow API module'''

from datetime import datetime

from json import dumps
from werkzeug.wrappers import Response
from flask import request

from ce.api.routed_streamflow.result_list import result_list
from ce.api.routed_streamflow.result_metadata import result_metadata
from ce.api.routed_streamflow.result_timeseries import result_timeseries
from ce.api.routed_streamflow.hydromodel_output import hydromodel_output

def call(session, resource, *args):
    rv = ""

    if resource == "result":
        if not args[0]:
            rv = result_list(session)
        
        if args[0] and not args[1]:
            rv = result_metadata(session, args[0])
        
        if args[1]:
            if args[1] == "timeseries":
                rv = result_timeseries(session, args[0])
            elif args[1] == "long_term_average":
                rv = result_long_term_average(session, args[0])
            else:
                rv = "unrecognized data request: {}".format(args[1])
    
    if resource == "hydromodel_output":
        if not args[0]:
            rv = hydromodel_output(session)
        else:
            return "Individual hydromodel pages are not implemented yet"
            
    resp = Response(
      dumps(rv),
      content_type='application/json'
      )
    
    #do we need modtime?
    return resp
