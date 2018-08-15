''' PCIC Climate Explorer routed streamflow API module: a RESTful API 
that serves modeled streamflow data.

Resources:
  * /hydromodel_output - datasets containing baseflow and runoff that can be 
    to generated routed streamflow
  * /result - a dataset containing routed streamflow data
      - annual mean - annual-resolution timeseries with the mean streamflow for each year  
      - annual max - annual-resolution timeseries with the max streamflow for each year
      - annual cycle - returns average daily streamflow for each month over the selected period
  * /health - reports on whether all parts of the system are working
'''

from datetime import datetime
from json import dumps
from werkzeug.wrappers import Response
from flask import request

from ce.api.routed_streamflow.result_list import result_list
from ce.api.routed_streamflow.result_metadata import result_metadata
from ce.api.routed_streamflow.result_annual_series import result_annual_means
from ce.api.routed_streamflow.result_annual_series import result_annual_max
from ce.api.routed_streamflow.result_annual_cycle import result_annual_cycle
from ce.api.routed_streamflow.hydromodel_output_list import hydromodel_output_list
from ce.api.routed_streamflow.hydromodel_output_metadata import hydromodel_output_metadata
from ce.api.routed_streamflow.health import health

def call(session, resource, *args):
    rv = ""
    status = 200

    #todo: handle the case where a nonexistant member of a valid resource type
    #is specified, like /result/banana or the like.
    #todo: handle cases where extra arguments are supplied (but not 
    #needed or checked for)
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
                rv = "Unrecognized data type: {}".format(args[1])
                status = 404
    elif resource == "hydromodel_output":
        if not args[0]:
            rv = hydromodel_output_list(session)
        elif args[0] and len(args) < 2:
            rv = hydromodel_output_metadata(session, args[0])
        else:
            rv = "Unrecognized hydromodel output request: {}"
            status = 404
    elif resource == "health":
        return health(session) #this endpoint sets its own HTTP code.
    else:
        rv = "Unrecognized resource: {}"
        status = 404
            
    resp = Response(
      dumps(rv),
      content_type='application/json',
      status = status
      )
    
    #do we need modtime?
    return resp
