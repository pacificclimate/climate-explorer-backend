import os
from typing import Any

from flask import Flask
from flask_cors import CORS
from sqlalchemy.pool import NullPool

from ce.api.multimeta_cache import (
    DEFAULT_PRELOAD_MULTIMETA_PARAMS,
    preload_multimeta_cache,
)

from ce.views import add_routes


def _build_engine_options():
    """Build SQLAlchemy engine options from environment variables.

    Set SQLALCHEMY_POOL_CLASS=null to use NullPool (recommended when deploying
    behind pgbouncer). Optional pool tuning via SQLALCHEMY_POOL_SIZE,
    SQLALCHEMY_MAX_OVERFLOW, SQLALCHEMY_POOL_TIMEOUT, SQLALCHEMY_POOL_RECYCLE.
    """
    if os.getenv("SQLALCHEMY_POOL_CLASS", "").lower() == "null":
        return {"poolclass": NullPool}

    options: dict[str, Any] = {"pool_pre_ping": True}

    for env_var, key, cast in [
        ("SQLALCHEMY_POOL_SIZE", "pool_size", int),
        ("SQLALCHEMY_MAX_OVERFLOW", "max_overflow", int),
        ("SQLALCHEMY_POOL_TIMEOUT", "pool_timeout", float),
        ("SQLALCHEMY_POOL_RECYCLE", "pool_recycle", float),
    ]:
        val = os.getenv(env_var)
        if val is not None:
            options[key] = cast(val)

    return options


def get_app(config=None):
    app = Flask(__name__)
    CORS(app)

    default_config = {
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "MDDB_DSN", "postgresql://httpd_meta@db.pcic.uvic.ca/pcic_meta"
        ),
        "SQLALCHEMY_ENGINE_OPTIONS": _build_engine_options(),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "MULTIMETA_CACHE_DIR": os.getenv("MULTIMETA_CACHE_DIR", "/tmp/multimeta-cache"),
        "MULTIMETA_CACHE_ENABLED": True,
        "MULTIMETA_PRELOAD_PARAMS": DEFAULT_PRELOAD_MULTIMETA_PARAMS,
        "PRELOAD_MULTIMETA_CACHE": True,
    }
    app.config.update(default_config)

    if config:
        app.config.update(config)

    add_routes(app)
    preload_multimeta_cache(app)
    return app
