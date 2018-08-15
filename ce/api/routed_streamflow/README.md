#PCIC Climate Explorer Streamflow API

##Hydromodel outputs
A hydromodel output is a gridded dataset containing modeled hydrological data, which can be used to generate streamflow data results. Hydromodel outputs may vary in their spatial converage, temporal coverage, or which General Climate Model or emissions scenario was used to provide temperature and precipitation inputs to generate them. 

###Collection resource
A list of all available hydromodel outputs can be accessed with GET via the collection resource `routed_streamflow/hydromodel_outputs`. Summary information is provided about the hydrological model used to generate the output and the GCM used to generate inputs to the hydrological model.

Example output:
```json
[
  {
    "hydromodel_output_metadata_id": 0, 
    "uri": "BASE_URL/api/routed_streamflow/hydromodel_output/0"
    "climate_input": {
      "scenario": "historical+rcp45", 
      "run": "r1i1p1", 
      "model": "ACCESS1-0"
    }, 
    "model_definition": {
      "name": "VIC (Built from source: v0.0.2-142-g981d56a1bb).", 
      "description": "Variable Infiltration Capacity Model GL with glacier dynamics"
    }
  },
  {
    "hydromodel_output_metadata_id": 1,
    ...
  }
]
```

###Document resource
Information on a specific hydromodel output, including hydrological model data, GCM model data, and temporal and spatial coverage can be accessed with GET via the document resource `routed_streamflow/hydromodel_output/{id}`.

Example output:
```json
{
  "hydromodel_output_metadata_id": 0, 
  "time": {
    "start": "1950-01-01T00:00:00", 
    "increment": "1 day", 
    "stop": "2100-01-01T00:00:00"
  }, 
  "model_definition": {
    "description": "Variable Infiltration Capacity Model GL with glacier dynamics", 
    "name": "VIC (Built from source: v0.0.2-142-g981d56a1bb)."
  }, 
  "climate_input": {
    "run": "r1i1p1", 
    "scenario": "historical+rcp45", 
    "model": "ACCESS1-0"
  }, 
  "grid": {
    "latstep": 0.0625, 
    "longitude": [-124.96875, -109.71875], 
    "latitude": [41.03125, 53.15625], 
    "lonstep": 0.0625
  }
}
```

##Results
A result is a station-based dataset containing modeled data describing streamflow at a particular location. Results are generated from specific hydromodel inputs for a particular location and timespan.

###Collection resource
A list of all available results can be access with GET via `routed_streamflow/result/`. Summary information including the relative location of the result and which hydromodel output was used to generate it are provided.

Example output:
```json
[
  {
    "cell_y": 167, 
    "status": "ready", 
    "cell_x": 120, 
    "hydromodel_output_metadata": "BASE_URL/api/routed_streamflow/hydromodel_output/0", 
    "uri": "BASE_URL/api/routed_streamflow/result/0"
  }, 
  {
    "cell_y": 163, 
    "status": "ready", 
    "cell_x": 129, 
    "hydromodel_output_metadata": "BASE_URL/api/routed_streamflow/hydromodel_output/0", 
    "uri": "BASE_URL/api/routed_streamflow/result/1"
  }, 
  ...
]
```

###Document resource
More detailed metadata on an individual result file, including absolute location and time coordinates of the result can be accessed with GET via `routed_streamflow/result/{id}`. This resource also provides links to data derived from the result.

Example output:
```json
{
  "start": "1950-01-01T00:00:00", 
  "cell_y": 167, 
  "links": [
    {
      "uri": "BASE_URL/api/routed_streamflow/result/0", "r
      el": "self"
    }, 
    {
      "uri": "BASE_URL/api/routed_streamflow/result/0/annualmean", 
      "rel": "annual mean"
    }, 
    {
      "uri": "BASE_URL/api/routed_streamflow/result/0/annualmax", 
      "rel": "annual max"
    }, 
    {
      "uri": "BASE_URL/api/routed_streamflow/result/0/annualcycle", 
      "rel": "annual cycle"
    }, 
    {
      "uri": "BASE_URL/api/routed_streamflow/hydromodel_output/0", 
      "rel": "hydromodel_output"
    }
  ], 
  "stop": "2100-01-01T00:00:00", 
  "status": "ready", 
  "cell_x": 120, 
  "latitude": 51.46875, 
  "timestep": "1 day", 
  "longitude": -117.46875
}
```

###Data document resources

####Annual Mean
Accessed with GET via `routead_streamflow/result/{id}/annualmean`. An array of timestamps, one for July 2 of each year present in the timeseries, and an array containing the mean streamflow value for the entire year.

####Annual Maximum
Accessed with GET via `routed_streamflow/result/{id}/annualmax`. Similar to the annual mean resource, returns an object containing an array of timestamps, one for each year, and an array with the maximum streamflow value recorded for that year.

####Annual Cycle
Accessed with GET via `routed_streamflow/result/{id}/annualcycle`. Parameters for the calculation may be provided in three ways:
* `routed_streamflow/result/{id}/annualcycle` - returns annual cycle data aggregated over the entire time period spanned by the result dataset.
* `routed_streamflow/result/{id}/annualcycle/{year}` - returns annual cycle data aggregated over a single year
* `routed_streamflow/result/{id}/annualcycle/{year1}-{year2}` - returns annyal cycle data aggregated over the interval from year1 to year2 inclusive.

Returns an array of twelve timestamps, one for the fifteenth day of each month of the Gregorian calendar for the central year of the interval, and an array of twelve values, each of which is the mean of all days of that month across the entire interval.

##Health
The `routed_streamflow/health` endpoint reports on the health of the entire climate explorer routed streamflow system. 

It has no additional hierarchical resources. 

It returns a JSON object following the draft IETF health check format. The overall status of the system will be one of PASS, WARNING, or FAIL; PASS and WARNING will return 200 OK headers; fail will return 500 Internal Server Error headers. The details attribute will return information on each sub-system.

Example output:
```json
{
  "version": "0.0.1",
  "notes": "0 failures and 1 warnings from sub-services",
  "status": "warning",
  "output": "WARNING: Directory contains misformatted netCDF files: ['results.nc']"
  "details": {
    "hydromodel_output_files": {
      "metricValue": 1,
      "time": "2018-08-14T15:52:34.425320",
      "metricUnit": "files",
      "status": "warning",
      "componentType": "datastore",
      "output": "WARNING: Directory contains misformatted netCDF files: ['results.nc']"
    },
    "memory": {
      "metricValue": 3492.74112,
      "time": "2018-08-14T15:52:34.475261",
      "componentType": "system",
      "status": "pass",
      "metricUnit": "MB",
      "output": ""
    },
    "result_files": {
      "metricValue": 5,
      "time": "2018-08-14T15:52:34.196140",
      "metricUnit": "files",
      "status": "pass",
      "componentType": "datastore",
      "output": ""
    },
    "database": {
      "metricValue": 1,
      "time": "2018-08-14T15:52:34.475285",
      "componentType": "datastore",
      "status": "pass",
      "output": "",
      "metricName": "connections"
    }
  },
}

```