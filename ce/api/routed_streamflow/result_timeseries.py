from modelmeta import DataFile
from ce.api.util import open_nc
from ce.api.routed_streamflow.streamflow_helpers import result_file_list
import numpy as np


def result_timeseries(sesh, id):
    result_file = result_file_list()[int(id)]
    
    timeseries = {}
    timeseries["startTime"] = "Jan 1 1950"
    timeseries["timeIncrement"] = "1 year"

    values = []
    with(open_nc(result_file)) as nc:
        streamflow = nc.variables["streamflow"]
        year = 1950
        cursor = 0
        while year < 2100:
            days_per_year = 365 if year % 4 != 0 else 366
            if year % 100 == 0 and year % 400 != 0:
                days_per_year = 365 
            values.append(float(np.mean(streamflow[cursor:cursor + days_per_year:1])))
            cursor += days_per_year
            year += 1       
    timeseries["values"] = values
    
    
    return timeseries

