import os

from flask import Flask

from ce.views import add_routes

def get_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'MDDB_DSN', 'postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta')
    add_routes(app)
    return app
