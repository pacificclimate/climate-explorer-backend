'''
Health endpoint - returns information about the service, and
the services it depends on.

Right now, the service isn't fully integrated with the database, so the only
database information it checks is whether it has a valid database connection, 
as well as available memory and filestore info.

Example output:
{
  "status": "warning", 
  "output": "WARNING: Directory contains misformatted netCDF files: ['results.nc']", 
  "notes": "0 failures and 1 warnings from sub-services", 
  "version": "0.0.1",
  "details": {
    "result_files": {
      "output": "", 
      "status": "pass", 
      "metricUnit": "files", 
      "metricValue": 5, 
      "componentType": "datastore", 
      "time": "2018-08-13T11:39:40.482048"
    }, 
    "hydromodel_output_files": {
      "output": "WARNING: Directory contains misformatted netCDF files: ['results.nc']", 
      "status": "warning", 
      "metricUnit": "files", 
      "metricValue": 1, 
      "componentType": "datastore", 
      "time": "2018-08-13T11:39:40.628266"
    }, 
    "memory": {
      "output": "", 
      "status": "pass", 
      "metricUnit": "MB", 
      "metricValue": 959.225856, 
      "componentType": "system", 
      "time": "2018-08-13T11:39:40.684203"
    }
    "database": {
      "metricName": "connections",
      "componentType": "datastore",
      "status": "pass",
      "output": "",
      "time": "2018-08-13T11:39:40.303659",
      "metricValue": 1,
    }
  } 
}

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
        if len(not_openable) > 0 or len(not_nc) > 0 or len(nc_files) == 0:
            status["status"] = "warning"
            output = []
            if len(nc_files) == 0:
                output.append("WARNING: Directory contains no valid netCDF files")
            if len(not_openable) > 0:
                output.append("WARNING: Directory contains misformatted netCDF files: {}".format(not_openable))
            if len(not_nc) > 0:
                output.append("WARNING: Directory contains non-netCDF files: {}".format(not_nc))
            status["output"] = '\n'.join(output)
            
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
def result_files(session):
    return check_ncdf_datastore('/storage/data/projects/comp_support/climate_explorer_data_prep/hydro/sample_data/set5/results')
    
#check to make sure that the hydromodel output directory exists and 
#files in it can be opened. (Will be replaced by a database check)    
def hydromodel_output_files(session):
    return check_ncdf_datastore('/storage/data/projects/comp_support/climate_explorer_data_prep/hydro/sample_data/set5/hydromodel_output')

#check to see that there's enough memory available to open a typical
#file.
def memory(session):
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
        status["status"] = "warning"
        status["output"] = "WARNING: Available memory low"
    else:
        status["status"] = "fail"
        status["output"] = "ERROR: not enough memory to open netCDF files"
    
    return status

def database(session):
    status = {}
    status["componentType"] = "datastore"
    status["metricName"] = "connections"
    status["time"] = datetime.datetime.now().isoformat()
    db_connected = True
    try:
        result = session.execute("select 1 as test_select")
        result.close()
    except Exception:
        db_connected = False

    if db_connected:
        status["status"] = "pass"
        status["metricValue"] = 1 #not actually try, but not sure how to get actual number
        status["output"] = ""
    else:
        status["status"] = "fail"
        status["output"] = "ERROR: No database connections available"
        status["metricValue"] = 0
    return status

components = [result_files, hydromodel_output_files, memory, database]

def health(session):
    status = {}
    details = {}
    notes = []
    warnings = []
    fails = []
    for c in components:
        comp_status = c(session)
        if comp_status["status"] == "warning":
            warnings.append(comp_status["output"])
        elif comp_status["status"] == "fail":
            fails.append(comp_status["output"])
        details[c.__name__] = comp_status

    if len(fails) > 0:
        status["status"] = "fail"
        status["output"] = '\n'.join(fails)
    elif len(warnings) > 0:
        status["status"] = "warning"
        status["output"] = '\n'.join(warnings)
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
