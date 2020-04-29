This API endpoint provides an overview of the state of the precvalculated and stored `stats` queries used by the `percentileanomaly` API. It checks to see whether the source files from which the stored `stats` calls where calculate have been updated since the time of calculation. For each of the defined plan2adapt regions, it reports on how many of the source files are in each of four states:

1. **current**: the source file has not been updated since the stored data was calculated; everything is up to date
2. **outdated**: the source file has been updated since the stored data was calculated
3. **removed**: the source file from which stored data was calculated is no longer listed in the database
4. **conflicted**: stored data has been calculated from multiple conflicting versions of the source file

This API opens all the stored datasets, a fairly demanding process, and should not be run too often nor at times when heavy traffic is anticipated.

To see exactly which source files have been updated since a region's stored data was calculated, use the `region` API.