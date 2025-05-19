from datetime import datetime
import pytest

from ce.api import grid


@pytest.mark.parametrize(("unique_id"), ("test_timeseries_speed",))
def test_grid(populateddb_session, unique_id):
    rv = grid(populateddb_session, unique_id)
    for key in rv.keys():
        assert "latitudes" in rv[key]
        assert len(rv[key]["latitudes"]) > 0
        assert type(rv[key]["latitudes"][0]) == float
        assert "longitudes" in rv[key]
        assert len(rv[key]["longitudes"]) > 0
        assert type(rv[key]["longitudes"][0]) == float
        assert "modtime" in rv[key]
        assert isinstance(rv[key]["modtime"], datetime)
