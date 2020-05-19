from modelmeta.v2 import Ensemble


def test_can_query_db(cleandb):
    sesh = cleandb.session
    assert len(sesh.query(Ensemble.name).all()) == 0


def test_db_is_populated(populateddb):
    sesh = populateddb.session
    assert sesh.query(Ensemble).count() > 0
