''' PCIC Climate Explorer streamflow API module'''

from datetime import datetime

from json import dumps
from werkzeug.wrappers import Response
from flask import request

from ce.api.routed_streamflow.result_list import result_list
from ce.api.routed_streamflow.result_metadata import result_metadata
from ce.api.routed_streamflow.result_annual_series import result_annual_means
from ce.api.routed_streamflow.result_annual_series import result_annual_max
from ce.api.routed_streamflow.result_annual_cycle import result_annual_cycle
from ce.api.routed_streamflow.hydromodel_output import hydromodel_output
from ce.api.routed_streamflow.health import health

def call(session, resource, *args):
    rv = ""

    if resource == "result":
        if not args[0]:
            rv = result_list(session)
        
        if args[0] and not args[1]:
            rv = result_metadata(session, args[0])
        
        if args[1]:
            if args[1] == "annualmean":
                rv = result_annual_means(session, args[0])
            elif args[1] == "annualmax":
                rv = result_annual_max(session, args[0])
            elif args[1] == "annualcycle":
                rv = result_annual_cycle(session, args[0], args[2])
            else:
                rv = "unrecognized data request: {}".format(args[1])
    elif resource == "hydromodel_output":
        if not args[0]:
            rv = hydromodel_output(session)
        else:
            return "Individual hydromodel pages are not implemented yet"
    elif resource == "health":
        return health() #this endpoint sets its own HTTP code.
    else:
        rv = "Unrecognized resource: {}" #need to 400 or something here.
            
    resp = Response(
      dumps(rv),
      content_type='application/json'
      )
    
    #do we need modtime?
    return resp
