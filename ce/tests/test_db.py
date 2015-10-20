import pytest
from flask.ext.sqlalchemy import SQLAlchemy
from modelmeta import *

def test_can_query_db(cleandb):
    sesh = cleandb.session
    results = sesh.query(Ensemble.name).all()


def test_db_is_populated(populateddb):
    sesh = populateddb.session
    assert sesh.query(Ensemble).count() > 0
