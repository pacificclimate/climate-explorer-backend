.. Documentation on metadata endpoint is split over three locations: the function's docstring,
   metadata-api-usage.md, which explains the general usage of the endpoint, and this file, which
   takes advantage of the sphinx RST "warning" functionality to post a warning about parameter names.

metadata
========
.. mdinclude:: metadata-api-usage.md

.. mdinclude:: sesh-not-needed.md

.. warning::
     Parameter names for this endpoint are not consistent with parameter names for the other
     endpoints. Every other endpoint uses the word "model" to refer to the General Circulation
     Model (GCM) or Regional Climate Model (RCM) that produced a particular dataset.
     
     This endpoint uses the "model_id" parameter to reger to a dataset's unique identification
     string, which is called "id_" in every other endpoint.
     
     This is a holdover from a much older data design when all data from each model was
     in a single file.


------

.. autofunction:: ce.api.metadata