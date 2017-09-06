'''module for requesting metadata on multiple stations at a time'''

import json

def multistation(sesh, ensemble_name='ce', model=''):
    '''Retrieve metadata about all files describing real or modeled 
    data stations.
    
    Currently, just a mock-up to aid front-end development, no real 
    database or netCDF interaction.
    
    Parallel to multimeta, returns metadata about each file, including
    model, watershed, latlong of station, emissions scenario, variable,
    and start and end dates. 
    
    Somewhat arbitrarily assumes that the files will at some point in the
    future be named according to CMIP5 filename encoding standards.
    (http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf)
    
    Example output:
        {
            "flow_day_ACCESS1-0_historical+rcp45_r1i1p1_19500101-21001231_BCHLJ": {
                "watershed": "BCHLJ",
                "start_date": "1950-01-01T00:00:00Z",
                "model_name": "",
                "institution": "PCIC",
                "longitude": -122.9062,
                "latitude": 50.84375,
                "experiment": "historical+rcp45",
                "model_id": "ACCESS1-0",
                "variables": {
                  "flow": "Streamflow at outlet grid cell"
                },
                "ensemble_member": "r1i1p1",
                "end_date": "2100-12-31T00:00:00Z"
            },
            "flow_day_CanESM2_historical+rcp45_r1i1p1_19500101-21001231_CAYOO": {
                ...
            },
            ...
        }
    '''
    
    models = ['ACCESS1-0', 'CanESM2', 'CCSM4', 'CNRM-CM5', 'HadGEM2-ES', 'MPI-ESM-LR']
    emissions = ['historical+rcp45', 'historical+rcp85']
    watersheds = ['BCHAL', 'BCHLJ', 'BCHSF', 'BCHST', 'BCHTR', 'BCHWL', 'CAYOO']
    coords = [
        [49.28125, -122.4688],
        [50.84375, -122.9062],
        [49.21875, -122.3438],
        [50.71875, -122.0312],
        [50.78125, -122.2188],
        [50.28125, -118.7812],
        [50.65625, -122.0312]
        ]
    
    output = {}
    
    for model in models:
        for emission in emissions:
            for i in range(0, 7):
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
                meta["outlets"] = {}
                meta["outlets"]["p-0"] = outlet
                
                filename = 'flow_day_{}_{}_r1i1p1_19500101-21001231_{}'.format(model, emission, watersheds[i])
                output[filename] = meta
    
    return output
    