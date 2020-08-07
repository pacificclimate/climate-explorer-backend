# Typical Workflows

## List Available Datasets

Datafiles are organized into ensembles containing all data needed for a 
specific purpose. (The term "ensemble" is a misnomer in this usage; a more 
appropriate term would be "collection." For historical reasons the term 
"ensemble" is embedded in the code and it is not easily changed at this point.)

To view a list of all datasets in a particular ensemble, query the 
`multimeta` API. The `multimeta` API gives each datafile as a unique identifier 
string and a collection of attributes describing the data contained within that 
file. After a datafile of interest has been determined from its metadata 
attributes, its unique identifier string may be used to request the data.

The `multi_year_mean` attribute is an important attribute of datafiles. 
Datafiles with `multi_year_mean` equal to `true` represent climatological 
aggregates. Each individual value in these files represents a mean or stanard 
deviation calculated across multiple years, typically thirty years, which is 
standard in climate science. For example, a monthly climatological mean might 
cover 1961-1990, but feature only twelve timestamps. The January timestamp is 
the mean of the value for January 1961, January 1962, and so on up to January 
1990. The February timestamp is the mean of the values for February 1961, 
February 1962, and so on. Climatological means may be monthly, seasonal, 
or annual. This API primarily supports analysis of climatological datasets, 
and more analysis options are available for them.

Datasets with `multi_year_mean` equal to `false` represent nominal time 
datasets; no aggregation has been done between years. A monthly dataset 
covering 1961-1990 would feature 360 timestamps.

## Request Numerical Data From A Climatological Aggregate Datafile

The `timeseries` endpoint returns a timeseries with the mean value for each 
timestamp in the datafile. It requires a datafile's unique identification 
string, and optionally a spatial area of interest defined as a Well Known 
Text (WKT) Polygon or Point. For a climatological aggregate datafile, the 
resulting timeseries represents an average annual cycle over the period 
described by the dataset. The annual cycle may have twelve monthly values, 
four seasonal values, or a single annual value.

The `stats` endpoint returns statistical measures (`mean`, `stdev`, `min`, 
`max`, and `median`) of a single dataset identified by its unique 
identification string. The timestep of interest is defined by a temporal index. 
An optional spatial area of interest may be defined as a WKT Polygon or Point. 
The statistical measures will be calculated over the time and space extent 
within the dataset.

You may wish to compare the statistical measures of a related set of 
climatological aggregate datafiles. The `multistats` query functions 
similarly to the `stats` query, but on several files that share common 
parameters at once. The `multistats` query may be called with parameters 
that describe a set of datasets by specifying all parameters except the start 
and end dates, as well as a time index and optional spatial area of interest. 
It responds with the same information as the `stats` query, but for every 
datafile that matches the parameters.

Similarly, the `data` API is also queried by submitting parameters that 
describe a set of datafiles by specifying all parameters except the start 
and end dates, as well as a time index and optional spatial area of interest. 
It returns a timeseries constructed from all climatological aggregate files 
that meet the parameters. For example, it would return the January value for 
the 1961-1990 climatology, the January value for the 1971-2000 climatology, 
etc, to make a timeseries showing projected long-term change over time of the 
mean value for January.

### Request Streamflow Data From A Climatological Aggregate Datafile

The typical use case for streamflow data is to determine flow at a single 
point corresponding to a location on a river or stream. Average streamflow 
over an area is not useful in most cases. The `timeseries`, `data` and 
`multistats` API endpoints accept WKT Points for the `area` parameter and 
may be used to request annual timeseries, long term data, or summary statistics 
for streamflow at a given point, similar to any other climatological aggregate 
dataset. 

While this is subject to change, all streamflow data are available in the 
ensemble named `bc_moti`, with variable name equal to `streamflow`.

When requesting streamflow data from a point, please be cautious and aware 
of potential differences in precision. Note that while you may supply a point
 with arbitrarily precise longitude and latitude values to the API, the 
 streamflow data is a gridded dataset and has only one value available per 
 grid cell. If you supply the coordinates of a small creek inside the same 
 grid cell as a river, the data you receive is for the total flow through 
 that grid cell; it is primarily influenced by the river. Accordingly, 
 this dataset is more accurate for larger streams, and should not be 
 considered accurate for streams that drain watersheds of less than 200 
 kilometers area. Information on the grid corresponding to a dataset can 
 be obtained from the `grid` API, which will provide a list of the longitudes 
 and latitudes corresponding to the centroids of each grid cell.

To get contextual information on the watershed that drains to the streamflow 
location of interest, the `watershed` API can be invoked with the same 
WKT Point used to request streamflow data. This API provides information on 
the topology and extent of the watershed that drains to the grid cell 
containing the specified point. The outline of the watershed is provided as a 
GeoJSON object. This outline, like the streamflow data itself, has a 
resolution determined by the size of a grid cell.

The GeoJSON watershed polygon can furthermore be used to request data on 
processes across the entire watershed that drains to a point, such as 
average precipitation across the watershed. If the polygon is converted to 
WKT format, it can be passed as the `area` argument to the `timeseries`, 
`data`, or `multistats` API endpoints to request climate data across the 
watershed for the same time period and model.


## Request A Non-Climatological Timeseries

Fewer options are available for datafiles with the `multi_year_mean` 
attribute of `false`, which have no guarenteed temporal structure or 
organization. The `timeseries` API endpoint requires a datafile's unique 
identification string and optionally a spatial area of interest. It responds 
with a timeseries consisting of the average values over the area of interest, 
one for each timestamp in the datafile. The timestamps need not be evenly 
spaced.

## Request a Map 

In order to request a data map image from PCIC's ncWMS server, two pieces of 
information are required, the dataset identifier and the timestamp.

### Dataset identifier

The PCIC ncWMS server has been configured to use two different methods of 
identifying a dataset:

- By unique id (before approximately Aug 15, 2020): 
  `layers=<unique_id>/<variable>`
- By filepath (after)
  `layers=<prefix>/<filepath>/<variable>`


Both `unique_id` and `filepath` are obtained from the 
`/multimeta` or `/metadata` query, which provide metadata for, respectively, 
all datasets in a collection or a single specific dataset. 

Attribute `unique_id` is included in all responses, as the top-level key to 
the dictionary of values returned.

To include `filepath` in the response, the metadata query should include
the query parameter `extras=filepath`.
For example, `/multimeta?...&extras=filepath`. Each item in the dictionary
then includes a `filepath` attribute. 
This feature is only available in Climate Explorer backend since release 3.0.1.

### Timestamp

A timestamp is also needed for ncWMS. The `/metadata` API endpoint can be 
accessed with the datafile's unique identification string, and provides a 
list of timestamps available in the file, which would be usable by ncWMS.