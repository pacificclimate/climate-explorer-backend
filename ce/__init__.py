import os

from flask import Flask
from flask.ext.cors import CORS
from flask.ext.cache import Cache

cache = Cache(config={'CACHE_TYPE': 'simple'})

from ce.views import add_routes

def get_app():
    app = Flask(__name__)
    CORS(app)
    cache.init_app(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'MDDB_DSN', 'postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta')
    add_routes(app)
    return app
