# Typical Workflows

## List Available Datasets

Datafiles are organized into ensembles, which collect all data needed for a specific purpose. To view a list of all datasets in a particular ensemble, query the `multimeta` API. The `multimeta` API gives each datafile as a unique identifier string and a collection of attributes describing the data contained within that file. After a datafile of interest has been determined from its metadata attributes, its unique identifier string may be used to request the data.

The `multi_year_mean` attribute is an important attribute of datafiles. Datafiles with `multi_year_mean` equal to `true` represent climatological means. Each individual value in these files represents a mean taken across years. For example, a monthly climatological mean might cover a span of thirty years, 1961-1990, but feature only twelve timestamps. The January timestamp is the mean of the value for January 1961, January 1962, and so on up to January 1990. The February timestamp is the mean of the values for February 1961, February 1962, and so on. Climatological means may be monthly, seasonal, or annual. This API primarily supports analysis of climatological datasets, and more analysis options are available for them.

Datasets with `multi_year_mean` equal to `false` represent nominal time datasets; no aggregation has been done between years. A monthly dataset covering 1961-1990 would feature 360 timestamps.

## Request Numerical Data From A Climatological Mean Datafile

The `timeseries` endpoint returns a timeseries with the mean value of every timestamp in the datafile. It requires a datafile's unique identification string, and optionally a spatial area of interest defined as a Well Known Text (WKT) Polygon or Point. For a climatological mean datafile, the resulting timeseries represents an average annual cycle over the period described by the dataset. The annual cycle may have twelve monthly values, four seasonal values, or a single annual value.

The `stats` endpoint returns statistical measures (`mean`, `stdev`, `min`, `max`, and `median`) of a single dataset identified by its unique identification string, a temporal index, and optionally a spatial area of interest defined as a WKT Polygon or Point.  

You may wish to compare the statistical measure of this particular climatological mean datafile against the statistical measure of climatological means of other timespans to observe change over time. For example, if the file of interest is a climatological mean across the years 1961-1990, there may also be datafiles representing the same data for 1971-2000, 1981-2010, or other spans available. The `multistats` query may be called with parameters that describe a set of datasets by specifying all parameters except the start and end dates, as well as a time index and optional spatial area of interest. It responds with the same information as the `stats` query, but for every datafile that matches the parameters.

Similarly, the `data` API is also queried by submitting parameters that describe a set of datafiles by specifying all parameters except the start and end dates, as well as a time index and optional spatial area of interest. It returns a timeseries constructed from all climatological mean files that meet the parameters. For example, it would return the January value for the 1961-1990 climatology, the January value for the 1971-2000 climatology, etc, to make a timeseries showing projected long-term change over time of the mean value for January.

## Request A Non-Climatological Timeseries

Fewer options are available for datafiles with the `multi_year_mean` attribute of `false`, which have no guarenteed temporal structure or organization. The `timeseries` API endpoint requires a datafile's unique identification string and optionally a spatial area of interest. It responds with a timeseries consisting of the average values over the area of interest, one for each timestamp in the datafile. The timestamps need not be evenly spaced.

## Request a Map 

In order to request a data map image from PCIC's ncWMS server, two piece of information are requred. Firstly, the identification string of the file is required. The identification string of the file of interest can be determined from the `multimeta` query, which lists all files available in a collection.

A timestamp is also needed for ncWMS. The `metadata` API endpoint can be accessed with the datafile's unique identification string, and provides a list of timestamps available in the file, which would be usable by ncWMS.