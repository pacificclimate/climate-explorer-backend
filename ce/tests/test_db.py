from modelmeta.v2 import Ensemble


def test_can_query_db(cleandb_session):
    assert len(cleandb_session.query(Ensemble.name).all()) == 0


def test_db_is_populated(populateddb_session):
    assert populateddb_session.query(Ensemble).count() > 0
