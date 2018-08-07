#this file contains temporary functions that will be replaced as other
#parts of the ecosystem et up and running.
import os
import re
from flask import request

#returns the url of the routed_streamflow base, something like:
#http://127.0.0.1:8000/api/routed_streamflow.
def base_streamflow_url():
    urlMatch = re.match(r'(.*routed_streamflow)', request.url)
    return urlMatch.group(1)
    

    
#returns the url of the the api base, something like:
#127.0.0.1:8000/api    
def base_api_url():
    urlMatch = re.match(r'(.*api)', request.url)
    return urlMatch.group(1)
    
    
#this is a shim that will eventually be replaced with a call to the
#modelmeta database. It returns a sorted array of all files in the
#results directory
#discrete geometry data can't yet be indexed into modelmeta     
def result_file_list():
        result_dir = '/storage/data/projects/comp_support/climate_explorer_data_prep/hydro/sample_data/set5/results'
        return list(map(lambda f: result_dir + '/' + f, sorted(os.listdir(result_dir))))
