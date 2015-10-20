from flask import Flask

from ce.views import add_routes

def get_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite:///'
    add_routes(app)
    return app
