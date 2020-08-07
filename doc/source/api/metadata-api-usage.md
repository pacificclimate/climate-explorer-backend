This endpoint returns detailed metadata on a single file. 
In addition to returning attributes describing the data in the file, 
it returns a list of all timestamps available within the file. 
This allows a user to request a map image from the map server 
corresponding to a specific timestamp.

To include the filepath of the file in the response, add the query parameter
`extras=filepath` to the request. This is used in requests to ncWMS servers 
configured to provide dynamic datasets. PCIC's ncWMS server is so configured 
after about 2020 Aug 15.