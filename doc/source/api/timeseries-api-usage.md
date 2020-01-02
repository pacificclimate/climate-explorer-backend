This API returns the mean value of each timestamp in the selected datafile, as indicated by that file's unique identification string. Almost all files available to this endpoint represent climatologies; in these cases, this endpoint returns an annual cycle, with 12 entries (monthly), 4 entries (seasonal), or 1 entry (annual), depending on the resolution of the requested dataset.

While generating annual cycle data from climatologies is the expected use case of this endpoint, it can also return timestamped data from non-climatological files. One value per timestamp will be returned.

To see how the value of a variable at a particular timestamp changes over the long term, instead of the course of a year, use the `data` endpoint.