This API endpoint provides information on the state of the precalculated and stored `stats` queries used by the `percentileanomaly` API. It checks to see whether the source files from which the stored `stats` calls were calculated have been updated since the time of calculation. 

Stored data can be in one of four states relative to its source files:

1. **current**: the source file has not been updated since the stored data was calculated; the stored data is up to date
2. **outdated**: the source file has been updated since the stored data was calculated
3. **removed**: the source file from which stored data was calculated is no longer listed in the database
4. **conflicted**: stored data has been calculated from multiple conflicting versions of the source file

This endpoint may be called for a specific region (`/health/regions/region_name`), in which case it will return a list of the files used to calculate stored data for that region and their individual status. Each file is identified by its `unique_id`.

Alternately, it may be called without specifying a region (`health/regions`), in which case it will provide a summary of the status of stored data for all regions. This opens all the stored datasets, a fairly demanding process, and should not be run too often nor at times when heavy traffic is anticipated.
