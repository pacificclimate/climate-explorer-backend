from ce.api import models


def test_models(populateddb_session):
    rv = models(populateddb_session, "ce")
    assert rv
