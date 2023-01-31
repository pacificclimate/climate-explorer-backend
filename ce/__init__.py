import os

from flask import Flask
from flask_cors import CORS


from ce.views import add_routes


def get_app():
    app = Flask(__name__)
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "MDDB_DSN", "postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    add_routes(app)
    return app
