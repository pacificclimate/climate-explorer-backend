'''module for requesting metadata on multiple stations at a time'''

import json

def multistation(sesh, ensemble_name='streamflow', model=''):
    '''Retrieve metadata about all files describing real or modeled 
    data stations.
    
    Currently, just a mock-up to aid front-end development, no actual 
    database or netCDF interaction. Returns canned data about stations
    in the Columbia watershed, matching sample data from Markus.
    
    Parallel to multimeta, returns metadata about each file, including
    model, watershed, latlong of station, emissions scenario, variable,
    and start and end dates. 
    
    Somewhat arbitrarily assumes that the files will at some point in the
    future be named according to CMIP5 filename encoding standards.
    (http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf)
    
    Example output:
    
    {
    "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_MCD": {
        "watershed": "MCD",
        "end_date": "2100-12-31T00:00:00Z",
        "routing": "ColumbiaRouting.nc",
        "ensemble_member": "r1i1p1",
        "start_date": "1950-01-01T00:00:00Z",
        "model_name": "",
        "experiment": "historical+rcp45",
        "outlets": {
            "p-0": {
                "latitude": 52.09375,
                "longitude": -118.5312
            }
        },
        "model_id": "ACCESS1-0",
        "institution": "PCIC",
        "variables": {
            "flow": "Streamflow at outlet grid cell"
        }
    },
    "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_DONAL": {
        ...
    }
    '''
    
    models = ['ACCESS1-0']
    emissions = ['historical+rcp45']
    watersheds = ['BEAVE', 'BRI', 'CRNIC', 'DONAL', 'KICHO', 'MCD']
    stations = [
        'Beaver River', 
        'Brilliant Dam',
        'Unknown Station', 
        'Columbia River at Donald',
        'Kicking Horse River',
        'Mica Dam'
        ]
    coords = [
        [51.46875, -117.4688],
        [49.40625, -117.5312],
        [51.21875, -116.9062],
        [51.46875, -117.1562],
        [51.28125, -116.9062],
        [52.09375, -118.5312]
        ]
    
    output = {}
    
    for model in models:
        for emission in emissions:
            for i in range(0, 6):
                meta = {}
                variables = {}
                outlet = {}
                variables["flow"] = "Streamflow at outlet grid cell"
                meta["model_id"] = model
                meta["experiment"] = emission
                meta["variables"] = variables
                meta["watershed"] = watersheds[i]
                meta["start_date"] = "1950-01-01T00:00:00Z"
                meta["end_date"] = "2100-12-31T00:00:00Z"
                meta["ensemble_member"] = "r1i1p1"
                meta["institution"] = "PCIC"
                meta["model_name"] = ""
                outlet["latitude"] = coords[i][0]
                outlet["longitude"] = coords[i][1]
                outlet["name"] = stations[i]
                meta["outlets"] = {}
                meta["outlets"]["p-0"] = outlet
                meta["routing"] = "ColumbiaRouting.nc"
                meta["timescale"] = "monthly"
                meta["multi_year_mean"] = False
                
                filename = 'flow_day_{}_{}_r1i1p1_19500101-21001231_{}'.format(model, emission, watersheds[i])
                output[filename] = meta
    
    return output
    