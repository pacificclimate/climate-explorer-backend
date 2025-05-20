import os

from flask import Flask
from flask_cors import CORS


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
    }
    app.config.update(default_config)

    if config:
        app.config.update(config)

    add_routes(app)
    return app
