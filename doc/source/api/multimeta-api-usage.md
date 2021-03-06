This API endpoint provides a list of all the datasets available in a given 
ensemble. Datasets are identified with a unique identification string. 
Additional metadata describing the contents of each dataset is provided.

This endpoint is intended to provide an overview of all available datasets 
to enable a caller to decide which datasets are of further interest for 
numerical data or mapping. It does not return detailed temporal metadata 
or any spatial metadata; see the `grid` and `metadata` endpoints for more 
detailed metadata about temporal or spatial extent of a dataset.

## Metadata attributes
* `institution`: The research institution that created this dataset
* `model_id`: A short abbreviation for the General Circulation Model, Regional 
Climate Model, or interpolation algorithm that output this dataset
* `model_name`: The full name of the model that created this dataset
* `experiment`: The emissions scenario used to model this data. 
Emissions scenarios represent a range of possible future projections for 
greenhouse gas concentration in the atmosphere, typically one of the 
Representative Concentration Pathways (RCP). May be "historical" for 
datasets based on historical data
* `variables`: A list of variables in this dataset, with name and a short 
description. Variables are the numerical quantities being measured or 
projected, such as maximum temperature, precipitation, or derived indices.
* `ensemble_member`: A model may be run multiple times with different 
initialization conditions; data from these runs is distinguished by the 
ensemble_member attribute
* `timescale`: The temporal resolution of the data. `monthly`, `seasonal`, 
or `yearly`
* `multi_year_mean`: Whether or not this datafile is a climatological 
aggregate. In a climatological aggregate dataset, the value at each timestamp 
represents a combination of values at that timestamp across multiple years. 
For example, a 1961-1990 climatological mean would have one value for January 
that represented the mean value of January 1961, January 1962, etc. 
* `start_date`: The start of the temporal interval described by this dataset 
* `end_date`: The end of the temporal interval described by this dataset
* `modtime`: The most recent data this dataset was updated. Useful for 
determining whether to cache data.
* `filepath`: (optional) The filepath of the data file in the local storage
 system. This is used in requests to ncWMS servers configured to provide
 dynamic datasets. PCIC's ncWMS server is so configured after about 2020 Aug 15.
To include the filepath of the file in the response, add the query parameter
`extras=filepath` to the request.