from pkg_resources import resource_filename
from datetime import timezone
from datetime import datetime

import pytest
import numpy as np
from numpy.ma import MaskedArray
from dateutil.parser import parse

from ce.api.util import get_array, mean_datetime

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

utc = timezone.utc

@pytest.mark.parametrize(('input_', 'output'), (
    (['2001-01-01T00:00:00Z'], '2001-01-01T00:00:00Z'),
    (['2001-01-01T00:00:00Z', '2001-01-04T00:00:00Z'], '2001-01-02T12:00:00Z'),
    (['2001-01-01T00:00:00Z', '2001-01-04T00:00:00Z', '2001-01-07T00:00:00Z'], '2001-01-04T00:00:00Z'),
))
def test_mean_datetime(input_, output):
    x = [ parse(t).replace(tzinfo=utc) for t in input_ ]
    assert mean_datetime(x) == parse(output).replace(tzinfo=utc)
