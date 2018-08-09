'''Endpoint that yields mean daily streamflow values over the specified period into
monthly values representing an annual cycle. If no period is specified, all available
timesteps will be used. If only one value is given, that year will be used.

Example:
{
  "id": "0", 
  "means": [
    3.745572785408266, 
    3.3109089736397386, 
    3.8639955582157257, 
    12.629720865885417, 
    60.57380922379032, 
    123.0356640625, 
    152.55834173387098, 
    89.13258568548387, 
    48.619921875, 
    17.79250252016129, 
    5.428345133463542, 
    4.221193375126008
  ], 
  "end": "1999-12-31T00:00:00", 
  "start": "1990-01-01T00:00:00", 
  "dates": [
    "1995-01-15T00:00:00", 
    "1995-02-15T00:00:00", 
    "1995-03-15T00:00:00", 
    "1995-04-15T00:00:00", 
    "1995-05-15T00:00:00", 
    "1995-06-15T00:00:00", 
    "1995-07-15T00:00:00", 
    "1995-08-15T00:00:00", 
    "1995-09-15T00:00:00", 
    "1995-10-15T00:00:00", 
    "1995-11-15T00:00:00", 
    "1995-12-15T00:00:00"
  ]
}


'''

from modelmeta import DataFile
from ce.api.util import open_nc
from ce.api.routed_streamflow.streamflow_helpers import result_file_list, days_per_year
import numpy as np
import datetime
import math

def result_annual_cycle(sesh, id, args):
    file = result_file_list()[int(id)]
    if args:
        args = args.split("-")
        startyear = int(args[0])
        endyear = int(args[1]) if len(args) > 1 else startyear
    else:
        startyear = 1950
        endyear = 2100

    cycle = annual_cycle(file, startyear, endyear)
    cycle["id"] = id
    cycle["start"] = datetime.datetime(startyear, 1, 1).isoformat()
    cycle["end"] = datetime.datetime(endyear, 12, 31).isoformat()
    return cycle

def annual_cycle(file, startyear, endyear):
    #there's got to be a more efficient way to do this.
    cumulative = np.zeros((12, 2))
    file_start_date = datetime.date(1950, 1, 1)
    start_index = (datetime.date(startyear, 1, 1) - file_start_date).days
    end_index = (datetime.date(endyear, 12, 31) - file_start_date).days
    with open_nc(file) as nc:
        for d in range(start_index, end_index + 1):
            month = (file_start_date + datetime.timedelta(days=d)).month
            cumulative[month-1][0] += nc.variables["streamflow"][d]
            cumulative[month-1][1] += 1
    means = list(map(lambda m: float(m[0] / m[1]), cumulative))
    centeryear = math.ceil((startyear + endyear) / 2)
    dates = list(map(lambda m: datetime.datetime(centeryear, m+1, 15).isoformat(), range(12)))
            
    return {
        "means": means,
        "dates": dates
        }
