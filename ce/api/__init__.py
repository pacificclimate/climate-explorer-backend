"""PCIC Climate Explorer backend API module

.. moduleauthor:: James Hiebert <hiebert@uvic.ca>

"""

import inspect
from datetime import datetime

from json import dumps
from werkzeug.wrappers import Response
from flask import request

from ce.api.stats import stats
from ce.api.multistats import multistats
from ce.api.data import data
from ce.api.timeseries import timeseries
from ce.api.models import models
from ce.api.metadata import metadata
from ce.api.multimeta import multimeta
from ce.api.lister import lister
from ce.api.grid import grid
from ce.api.percentileanomaly import percentileanomaly
from ce.api.streamflow.watershed import watershed
from ce.api.streamflow.watershed_streams import watershed_streams
from ce.api.streamflow.downstream import downstream
from ce.api.health.regions import regions


methods = {
    "stats": stats,
    "multistats": multistats,
    "data": data,
    "models": models,
    "metadata": metadata,
    "multimeta": multimeta,
    "timeseries": timeseries,
    "lister": lister,
    "grid": grid,
    "percentileanomaly": percentileanomaly,
    "watershed": watershed,
    "watershed_streams": watershed_streams,
    "downstream": downstream,
    "regions": regions,
}

__all__ = list(methods.keys()) + ["call"]


def call(session, request_type, item=None):
    """Extracts request query parameters, checks for required arguments
    and delegates to helper functions to fetch the results from
    storage

    Args:
       session (sqlalchemy.orm.session.Session): A database Session object
       request_type(str): name of the API endpoint to call
       item(str): name of an individual item for a REST API

    Returns:
       werkzeug.wrappers.Response.  A JSON encoded response object
    """

    try:
        func = methods[request_type]
    except KeyError:
        return Response("Invalid API Endpoint", status=400)

    # Check that required args are included in the query params, excluding the
    # REST item, if there is one
    if item:
        required_params = set(get_required_args(func)).difference(["sesh", "item"])
    else:
        required_params = set(get_required_args(func)).difference(["sesh"])

    optional_params = set(get_keyword_args(func))

    # Clients may submit parameters either encoded in the URL string
    # for GET methods, or in the body of a POST request.
    # Clients should use GET when possible, to take
    # advantage of caching, and produce links that can be shared.
    # However, in some cases, the 'area' parameter, which is a WKT
    # string describing the polygon the client requests data describing,
    # is too long to fit in the unofficial standard URL length of
    # 4096 characters. Clients may send a POST request in this case.

    # flask.request's "values" attribute contains dictionaries of
    # both URL and body parameters; we can use it to build the list
    # of function arguments whether the request is a POST or GET.

    provided_params = set(request.values.keys())
    missing = required_params.difference(provided_params)
    if missing:
        return Response(
            "Missing query param{}: {}".format(
                "s" if len(missing) > 1 else "", ", ".join(missing)
            ),
            status=400,
        )

    # FIXME: Sanitize input
    args = {key: request.values.get(key) for key in required_params}
    kwargs = {
        key: request.values.get(key)
        for key in optional_params
        if request.values.get(key) is not None
    }

    args.update(kwargs)
    # Note: all arguments to the delegate functions are necessarily strings
    # at this point, since they're all coming through the URL query
    # parameters
    if item:
        rv = func(session, item, **args)
    else:
        rv = func(session, **args)
    modtime = find_modtime(rv)
    resp = Response(dumps(format_dates(rv)), content_type="application/json")
    resp.last_modified = modtime
    return resp


# from http://stackoverflow.com/q/196960/
def get_required_args(func):
    args, _, _, defaults, _, _, _ = inspect.getfullargspec(func)
    if defaults:
        args = args[: -len(defaults)]
    return args  # *args and **kwargs are not required, so ignore them.


def get_keyword_args(func):
    args, _, _, defaults, _, _, _ = inspect.getfullargspec(func)
    if defaults:
        return args[-len(defaults) :]
    else:
        return []


def find_modtime(obj):
    """Find the maximum modtime in an object

    Recursively search a dictionary, returning the maximum value found
    in all keys named 'modtime
    """
    if not isinstance(obj, dict):
        return None

    candidates = [find_modtime(val) for val in obj.values() if isinstance(val, dict)]
    if "modtime" in obj and isinstance(obj["modtime"], datetime):
        candidates.append(obj["modtime"])
    candidates = [x for x in candidates if isinstance(x, datetime)]
    if candidates:
        return max(candidates)


def format_dates(obj):
    """Recursively format datetimes to strings

    json.dumps doesn't properly convert datetimes to their
    representative format. It simply using the __repr__ of the datetime
    object (which is not what we want).

    This method recursively searches a dict, formatting all datetime
    objects, and leaving everything else unchanged. The formatted object
    is returned.
    """
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    if not isinstance(obj, dict):
        return obj
    return {
        key: (
            val.strftime(time_format)
            if isinstance(val, datetime)
            else format_dates(val)
        )
        for key, val in obj.items()
    }
