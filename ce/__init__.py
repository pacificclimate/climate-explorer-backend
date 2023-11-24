import os

from flask import Flask
from flask_cors import CORS


from ce.views import add_routes


def get_app(test_config=None):
    app = Flask(__name__)
    CORS(app)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "MDDB_DSN", "postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta"
        ),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    add_routes(app)
    return app
