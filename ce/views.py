from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

import ce.api

###
# TODO: For consideration, the /api url prefix could probably be dropped entirely and controlled by the
# deployment behaviour.
###


def add_routes(app):
    db = SQLAlchemy(app)

    @app.route("/api/readyz")
    def readyz():
        status = {"status": "ok"}
        http_status = 200
        if request.args.get("verbose", "").lower() in ("1", "true", "yes"):
            try:
                db.session.execute(text("SELECT 1"))
                status["db"] = "ok"
            except Exception as e:
                status["status"] = "error"
                status["db"] = str(e)
                http_status = 503
        response = jsonify(status)
        response.cache_control.no_store = True
        return response, http_status

    @app.route("/api/<request_type>", methods=["GET", "POST"])
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
        if request.endpoint != "readyz":
            response.cache_control.public = True
            response.cache_control.max_age = 86400
        return response
