from ce.api import models


def test_models(populateddb):
    sesh = populateddb.session
    rv = models(sesh, "ce")
    assert rv
