This API offers a snapshot of the functioning of the API.

## Stored Regional Queries
Checks the CSV files containing stored calls to the `/stats` API for outdated data. When the queries are calculated, the `modtime` and `unique_id` of each source dataset are stored along with the query results. This API checks the stored `modtimes` against the current database, and if any datasets have been modified or deleted, they will be listed.

As it opens all the stored datasets, it is a fairly demanding query, and should not be run too often nor at times when heavy traffic is anticipated.