import os

from flask import Flask
from flask_cors import CORS

from ce.api.multimeta_cache import (
    DEFAULT_PRELOAD_MULTIMETA_PARAMS,
    preload_multimeta_cache,
)

from ce.views import add_routes


def get_app(config=None):
    app = Flask(__name__)
    CORS(app)

    default_config = {
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "MDDB_DSN", "postgresql://httpd_meta@db.pcic.uvic.ca/pcic_meta"
        ),
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
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
