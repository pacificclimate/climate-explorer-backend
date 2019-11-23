from datetime import datetime
import pytest

from ce.api import multimeta


@pytest.mark.parametrize(('model'), ('BNU-ESM', ''))
def test_multimeta(populateddb, model):
    unique_id = 'tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230'
    sesh = populateddb.session
    rv = multimeta(sesh, ensemble_name='ce', model=model) # Multimeta is wrapped for caching. Call the wrapped function
    assert unique_id in rv
    assert rv[unique_id]['model_id'] == 'BNU-ESM'
    # times are not included in the multimeta API call
    assert 'timescale' in rv[unique_id]
    assert 'times' not in rv[unique_id]
    # make sure start_date and end_date are present
    assert 'start_date' in rv[unique_id]
    assert 'end_date' in rv[unique_id]
    assert 'modtime' in rv[unique_id]
    assert isinstance(rv[unique_id]['modtime'], datetime)
