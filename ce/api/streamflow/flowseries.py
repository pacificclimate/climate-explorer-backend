'''module for requesting an unstructured timeseries from a single station in a file'''

import json
import random

def flowseries(sesh, id_, station):
    '''Generates a static streamflow timeseries from a single file.

    Opens the data file specified by the id_ parameter and returns the
    data values associated with station at each timestep in the file.

    Currently, just a mock-up to aid front-end development, no actual 
    database or netCDF interaction. Returns a random timeseries seeded with
    the file id.
        Example:
            {
                'id': 'flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_BRI',
                'station': 'p-0',
                'units': 'm3/s',
                'data':
                {
                    '1985-01-15T00:00:00Z': 1.5,
                    '1985-02-15T00:00:00Z': 2.5,
                    '1985-03-15T00:00:00Z': 5.5,
                    '1985-04-15T00:00:00Z': 10.2,
                    ...
                }
            }
    '''

    output = {}
    dates = []
    
    for y in range(1980,2001):
        for m in range(1,12):
            dates.append("{}-{:02d}-15T00:00:00Z".format(y, m))
    
    output["id"] = id_
    output["units"] = "m3/s"
    output["station"] = "p-0"
    data = {}
    
    random.seed(id_)
    
    for date in dates:
        data[date] = random.uniform(1.0, 50.0)
    
    output["data"] = data    
    return output