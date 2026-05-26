import hashlib
import json
import os
from datetime import datetime
from threading import Lock
from urllib.parse import urlencode

from flask import current_app
from werkzeug.wrappers import Response


DEFAULT_MULTIMETA_PARAMS = {
    "ensemble_name": "ce_files",
    "model": "",
    "extras": "",
    "climatological_statistic": "mean",
    "percentile": None,
}
DEFAULT_PRELOAD_MULTIMETA_PARAMS = [
    {"ensemble_name": "extreme_precipitation", "extras": "filepath"},
    {"ensemble_name": "ce_files", "extras": "filepath"},
    {"ensemble_name": "ce_cmip6_mbcn", "extras": "filepath"},
    {
        "ensemble_name": "fraser_peace_columbia",
        "climatological_statistic": "percentile",
        "extras": "filepath",
    },
]
cache_lock = Lock()


def is_multimeta_cache_enabled():
    return current_app.config.get("MULTIMETA_CACHE_ENABLED", True)


def _cache_dir():
    return current_app.config["MULTIMETA_CACHE_DIR"]


def _normalize_params(params):
    normalized = DEFAULT_MULTIMETA_PARAMS.copy()
    normalized.update(params)
    return {
        key: value
        for key, value in sorted(normalized.items())
        if value is not None and value != ""
    }


def _cache_path(params):
    query_string = urlencode(_normalize_params(params))
    digest = hashlib.sha256(query_string.encode("utf-8")).hexdigest()[:16]
    ensemble = _normalize_params(params).get("ensemble_name", "multimeta")
    return os.path.join(_cache_dir(), "{}-{}.json".format(ensemble, digest))


def get_cached_multimeta_response(params):
    if not is_multimeta_cache_enabled():
        return None

    path = _cache_path(params)
    with cache_lock:
        if not os.path.exists(path):
            return None

        with open(path) as infile:
            cached = json.load(infile)

    response = Response(cached["body"], content_type="application/json")
    if cached.get("last_modified"):
        response.last_modified = datetime.fromisoformat(cached["last_modified"])
    return response


def cache_multimeta_response(params, response):
    if not is_multimeta_cache_enabled():
        return

    path = _cache_path(params)
    with cache_lock:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        cached = {
            "body": response.get_data(as_text=True),
            "last_modified": (
                response.last_modified.isoformat() if response.last_modified else None
            ),
        }

        temp_path = "{}.tmp".format(path)
        with open(temp_path, "w") as outfile:
            json.dump(cached, outfile)
        os.replace(temp_path, path)


def preload_multimeta_cache(app):
    if app.config.get("TESTING"):
        return
    if not app.config.get("PRELOAD_MULTIMETA_CACHE", True):
        return

    with app.test_client() as client:
        for params in app.config.get(
            "MULTIMETA_PRELOAD_PARAMS", DEFAULT_PRELOAD_MULTIMETA_PARAMS
        ):
            client.get("/api/multimeta", query_string=params)
