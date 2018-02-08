from flask_sqlalchemy import SQLAlchemy

import ce.api

def add_routes(app):

    db = SQLAlchemy(app)

    @app.route("/api/<request_type>")
    def api_request(*args, **kwargs):
        return ce.api.call(db.session, *args, **kwargs)

    @app.after_request
    def add_header(response):
        response.cache_control.public = True
        response.cache_control.max_age = 86400
        return response
