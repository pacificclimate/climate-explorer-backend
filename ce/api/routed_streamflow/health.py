'''
Health endpoint - returns information about the service, and
the services it depends on.

Right now, the service isn't hooked up to most of its pieces, (database,
queue, etc) so it just returns information aboit available memory and
files.
'''
from json import dumps
from werkzeug.wrappers import Response
import psutil as psu
import datetime
import os
from netCDF4 import Dataset

#checks a directory containing netCDF datafiles. Issues an error if the 
#directory doesn't exist, and a warning if it contains non-netCDF files or
#misformatted netCDF files.
def check_ncdf_datastore(directory):
    status = {}
    status["componentType"] = "datastore"
    status["metricUnit"] = "files"
    status["time"] = datetime.datetime.now().isoformat()
    if os.path.isdir(directory):
        nc_files = []
        not_openable = []
        not_nc = []
        files = sorted(os.listdir(directory))
        for f in files:
            if f.find(".nc") != 0:
                try:
                    d = Dataset(directory + '/' + f)
                    d.close()
                    nc_files.append(f)
                except Exception:
                    not_openable.append(f)
            else:
                not_nc.append(f)
            
        status["metricValue"] = len(nc_files)    
        if len(not_openable) > 0 or len(not_nc) > 0:
            status["status"] = "warning"
            output = []
            if len(not_openable) > 0:
                output.append("WARNING: Directory contains misformatted netCDF files: {}".format(not_openable))
            if len(nc_files) > 0:
                output.append("WARNING: Directory contains non-netCDF files: {}".format(not_nc))
            status["output"] = output
            
        else:
            status["status"] = "pass"
            status["output"] = ""
    else:
        status["status"] = "fail"
        status["metricValue"] = 0
        status["output"] = "ERROR: dataset directory does not exist"
    return status
    
#check to make sure the result file directory exists and files in it
#can be opened. (Will someday be replaced by a database connection check)   
def result_files():
    return check_ncdf_datastore('/storage/data/projects/comp_support/climate_explorer_data_prep/hydro/sample_data/set5/results')
    
#check to make sure that the hydromodel output directory exists and 
#files in it can be opened. (Will be replaced by a database check)    
def hydromodel_output_files():
    return check_ncdf_datastore('/storage/data/projects/comp_support/climate_explorer_data_prep/hydro/sample_data/set5/hydromodel_output')


#check to see that there's enough memory available to open a typical
#file.
def memory():
    status = {}
    available_memory = psu.virtual_memory()[1]
    status["metricValue"] = available_memory / 1000000
    status["metricUnit"] = "MB"
    status["componentType"] = "system"
    status["time"] = datetime.datetime.now().isoformat()
    
    #pass if >300M memory available, warn if >1M, error if <1MB
    if status["metricValue"] > 300:
        status["status"] = "pass"
        status["output"] = ""
    elif status["metricValue"] > 1:
        status["status"] = "warn"
        status["output"] = "WARNING: Available memory low"
    else:
        status["status"] = "fail"
        status["output"] = "ERROR: not enough memory to open netCDF files"
    
    return status

components = [result_files, hydromodel_output_files, memory]

def health():
    status = {}
    details = {}
    notes = []
    warnings = []
    fails = []
    for c in components:
        comp_status = c()
        if comp_status["status"] == "warn":
            warnings.append(comp_status["output"])
        elif comp_status["status"] == "fail":
            fails.append(comp_status["output"])
        details[c.__name__] = comp_status

    if len(fails) > 0:
        status["status"] = "fail"
        status["output"] = fails
    elif len(warnings) > 0:
        status["status"] = "warning"
        status["output"] = warnings
    else:
        status["status"] = "pass"
        status["output"] = ""

    status["details"] = details
    status["version"] = "0.0.1"
    status["notes"] = "{} failures and {} warnings from sub-services".format(len(fails), len(warnings))
    
    http_status = 500 if status["status"] == "fail" else 200
    
    resp = Response(
      dumps(status),
      content_type='application/json',
      status=http_status
      )
    
    
    return resp
