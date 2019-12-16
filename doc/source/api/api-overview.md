Documentation for each API endpoint is automatically generated from the code and docstring for that API's main function and may not be entirely user-friendly. There are some very minor differences between arguments for each API function and the parameters needed for a web query.

1. Web queries do not supply a `sesh` (database session) as an argument; that will be automatically done by the query parser.
2. Parameters supplied in a query url should be web-encoded.