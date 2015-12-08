from pkg_resources import resource_filename

import pytest
from numpy.ma import MaskedArray

from ce.api.util import get_array

@pytest.mark.parametrize(('fname', 'var'), (
    ('cgcm.nc', 'tasmax'),
    ('cgcm-tmin.nc', 'tasmin'),
    ('CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc', 'tasmax')
    # FIXME: Need to test a file with masked values
))
def test_get_array(fname, var):
    fname = resource_filename('ce', 'tests/data/' + fname)
    x = get_array(fname, 0, "", var)
    assert type(x) == MaskedArray
    assert hasattr(x, 'mask')
