import pytest

from ce.api import lister


@pytest.mark.parametrize(('args', 'expected'), [
    ({'ensemble_name': 'bccaqv2'},
     {'tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230',
      'tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230'}),
    ({'ensemble_name': 'ce', 'model': 'csiro'},
     {'file1', 'file2', 'flow-direction_peace'})
])
def test_lister(populateddb, args, expected):
    sesh = populateddb.session
    rv = lister(sesh, **args)
    assert set(rv) == expected
