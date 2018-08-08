'''Endpoint that aggregates daily streamflow values into a timeseries with
one value per year. Any of the num.py statistical functions 
( https://docs.scipy.org/doc/numpy-1.14.0/reference/routines.statistics.html )
could be used for aggregation.

Returns a JSON object with separate arrays of timestamps and values:
{
  "id": "0", 
  "startTime": "Jan 1 1950", 
  "times": [
    1950, 
    1951, 
    1952, 
    1953, 
    1954
  ], 
  "timeIncrement": "1 year", 
  "values": [
    164.50233459472656, 
    261.9129943847656, 
    170.32029724121094, 
    183.456787109375, 
    253.8182830810547
  ], 
  "aggregator": "maximum"
}

'''

from modelmeta import DataFile
from ce.api.util import open_nc
from ce.api.routed_streamflow.streamflow_helpers import result_file_list
import numpy as np
import datetime

def result_annual_means(sesh, id):
    series = annual_series(result_file_list()[int(id)], np.mean)
    series["id"] = id
    series["aggregator"] = "mean"
    return series
                                              

def result_annual_max(sesh, id):
    series = annual_series(result_file_list()[int(id)], np.nanmax)
    series["id"] = id
    series["aggregator"] = "maximum"
    return series

def annual_series(file, aggregate):
    
    series = {}
    series["startTime"] = datetime.datetime(1950, 1, 1).isoformat()
    series["timeIncrement"] = "1 year"

    values = []
    times = []
    with(open_nc(file)) as nc:
        streamflow = nc.variables["streamflow"]
        year = 1950
        cursor = 0
        while year < 2100:
            days = days_per_year(year)
            values.append(float(aggregate(streamflow[cursor:cursor + days:1])))
            times.append(datetime.datetime(year, 7, 2).isoformat())
            cursor += days
            year += 1       
    series["values"] = values
    series["times"] = times
    
    return series

def days_per_year(year):
    if year % 4 != 0:
        return 365
    elif year % 100 == 0 and year % 400 != 0:
        return 365
    else:
        return 366