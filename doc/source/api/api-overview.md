Documentation for each API endpoint is automatically generated from the code and docstring for that API's main function and may not be entirely user-friendly. There are some minor differences between the internal workings of the API function and the process of querying them over the web.

The query URL is constructed from a base url ending in a slash, followed by the name of the endpoint, a question mark, and then one or more parameters of the form `attribute=value', seperated by ampersands. Parameters supplied via query URL should be web-encoded so that they will be correctly parsed.

The automatically generated API documentation describes a `sesh` (database session) argument to each API function. Database sessions are supplied by the query parser and does not need to be given in the query URL.

For example, the `multimeta` function has a signature of `ce.api.multimeta(sesh, ensemble_name='ce_files', model='')`

The query URL `https://base_url/multimeta?ensemble_name=ce_files&model=CanESM2` calls the `multimeta` endpoint and supplies two arguments for the `multimeta` function: `ensemble_name` is "ce_files" and `model` is CanESM2. `sesh` is not supplied in the query URL.

The API function return values are converted to JSON for the endpoint response.