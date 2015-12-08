from pkg_resources import resource_filename

import pytest
import numpy as np
from numpy.ma import MaskedArray

from ce.api.util import get_array

@pytest.mark.parametrize(('fname', 'var'), (
    ('cgcm.nc', 'tasmax'),
    ('cgcm-tmin.nc', 'tasmin'),
    ('prism_pr_small.nc', 'pr') # a file with masked values
))
def test_get_array(fname, var):
    fname = resource_filename('ce', 'tests/data/' + fname)
    x = get_array(fname, 0, "", var)
    assert type(x) == MaskedArray
    assert hasattr(x, 'mask')
    assert np.mean(x) > 0
