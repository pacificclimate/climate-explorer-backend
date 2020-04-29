This API provides a list of all files from which data for a region has been precalculated, along with the status of the source datafile. The precomputed data is used by the `percentileanomaly` API, as calculated the data at runtime proved too slow. 

Each datafile is identified by its `unique_id` and the `modtime` at the time the data was calculated, along with one of four possible statuses:

1. **current**: the source file has not been updated since the stored data was calculated; everything is up to date
2. **outdated**: the source file has been updated since the stored data was calculated
3. **removed**: the source file from which stored data was calculated is no longer listed in the database
4. **conflicted**: stored data has been calculated from multiple conflicting versions of the source file

The `regions` API shows an overview for all regions with a count of the number of files in each status instead of a list of individual files.