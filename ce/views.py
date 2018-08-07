from flask_sqlalchemy import SQLAlchemy

import ce.api
import ce.api.routed_streamflow

def add_routes(app):

    db = SQLAlchemy(app)

    @app.route("/api/<request_type>")
    def api_request(*args, **kwargs):
        return ce.api.call(db.session, *args, **kwargs)
    
    @app.route("/api/routed_streamflow/result", methods=['GET'])
    @app.route("/api/routed_streamflow/result/<id>", methods=['GET'])
    @app.route("/api/routed_streamflow/result/<id>/<data_type>", methods=['GET'])
    @app.route("/api/routed_streamflow/result/<id>/<data_type>&<params>", methods=['GET'])
    def routed_streamflow_result(id=None, data_type=None, params=None):
        return ce.api.routed_streamflow.call(db.session, "result", id, data_type, params)
    
    @app.route("/api/routed_streamflow/hydromodel_output", methods=['GET'])
    @app.route("/api/routed_streamflow/hydromodel_output/<id>", methods=['GET'])
    def routed_streamflow_hydromodel_output(id=None):
        return ce.api.routed_streamflow.call(db.session, "hydromodel_output", id)
    
    @app.route("/api/relations/<relation_type>", methods=['GET'])
    def routed_streamflow_relations(relation_type=None):
        return "Relation pages aren't implemented yet"

    @app.after_request
    def add_header(response):
        response.cache_control.public = True
        response.cache_control.max_age = 86400
        return response
