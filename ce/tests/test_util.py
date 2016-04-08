from pkg_resources import resource_filename
from datetime import timezone
from datetime import datetime
from time import time

import pytest
import numpy as np
from numpy.ma import MaskedArray
from dateutil.parser import parse

from ce.api.util import get_array, mean_datetime

@pytest.mark.parametrize(('fname', 'var'), (
    ('cgcm.nc', 'tasmax'),
    ('cgcm-tmin.nc', 'tasmin'),
    ('prism_pr_small.nc', 'pr'), # a file with masked values
    ('bccaq_tnx.nc', 'tnxETCCDI'),
))
def test_get_array(fname, var, polygon):
    fname = resource_filename('ce', 'tests/data/' + fname)
    t0 = time()
    x = get_array(fname, 0, polygon, var)
    t = time() - t0
    print(t)
    assert t < .030
    assert type(x) == MaskedArray
    assert hasattr(x, 'mask')
    assert np.mean(x) > 0 or np.all(x.mask)

utc = timezone.utc

@pytest.mark.parametrize(('input_', 'output'), (
    (['2001-01-01T00:00:00Z'], '2001-01-01T00:00:00Z'),
    (['2001-01-01T00:00:00Z', '2001-01-04T00:00:00Z'], '2001-01-02T12:00:00Z'),
    (['2001-01-01T00:00:00Z', '2001-01-04T00:00:00Z', '2001-01-07T00:00:00Z'], '2001-01-04T00:00:00Z'),
))
def test_mean_datetime(input_, output):
    x = [ parse(t).replace(tzinfo=utc) for t in input_ ]
    assert mean_datetime(x) == parse(output).replace(tzinfo=utc)
