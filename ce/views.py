from flask_sqlalchemy import SQLAlchemy

import ce.api


def add_routes(app):

    db = SQLAlchemy(app)

    @app.route("/api/<request_type>", methods= ['GET', 'POST'])
    def api_request(*args, **kwargs):
        return ce.api.call(db.session, *args, **kwargs)

    @app.route("/api/streamflow/<request_type>")
    def streamflow_request(*args, **kwargs):
        return ce.api.call(db.session, *args, **kwargs)

    # RESTful collection url - behaves like a non-REST query
    @app.route("/api/health/<request_type>")
    def health_collection_request(*args, **kwargs):
        """A REST-style request for a collection - routed in the same
        was as any other request."""
        return ce.api.call(db.session, *args, **kwargs)

    # RESTful url with id for individual object
    @app.route("/api/health/<request_type>/<item>")
    def health_item_request(*args, **kwargs):
        """A REST-style request for an item within a collection.
        The item is specified in the URL, not as a &parameter."""
        return ce.api.call(db.session, *args, **kwargs)

    @app.after_request
    def add_header(response):
        response.cache_control.public = True
        response.cache_control.max_age = 86400
        return response
