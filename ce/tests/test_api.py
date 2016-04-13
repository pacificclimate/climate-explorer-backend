import math
from time import time

import pytest

from flask import url_for
from dateutil.parser import parse

from ce.api import *

@pytest.mark.parametrize(('endpoint', 'query_params'), [
    ('stats', {'id_': '', 'time': '', 'area': '', 'variable': ''}),
    ('data', {'model': '', 'emission': '', 'time': '0', 'area': '', 'variable': ''}),
    ('timeseries', {'id_': '', 'area': '', 'variable': ''}),
    ('models', {}),
    ('metadata', {'model_id': 'file0'}),
    ('multimeta', {'model': ''}),
    ('lister', {'model': ''}),
    ('grid', {'id_': ''})
])
def test_api_endpoints_are_callable(test_client, cleandb, endpoint, query_params):
    url = '/api/' + endpoint
    response = test_client.get(url, query_string=query_params)
    assert response.status_code == 200

def test_models(populateddb):
    sesh = populateddb.session
    rv = models(sesh, 'ce')
    assert rv

@pytest.mark.parametrize(('args', 'expected'), [
    ({'ensemble_name': 'bccaqv2'}, ['file0', 'file4']),
    ({'model': 'csiro'}, ['file1', 'file2'])
])
def test_lister(populateddb, args, expected):
    sesh = populateddb.session
    rv = lister(sesh, **args)
    assert set(rv) == set(expected)

@pytest.mark.parametrize(('unique_id'), ('file0', 'file4'))
def test_metadata(populateddb, unique_id):
    sesh = populateddb.session
    rv = metadata(sesh, unique_id)
    assert unique_id in rv
    for key in ['institution', 'model_id', 'model_name', 'experiment',
                'variables', 'ensemble_member', 'times', 'timescale']:
        assert key in rv[unique_id]

    times = rv[unique_id]['times']
    assert len(times) > 0

    # Are the values converible into times?
    for val in times.values():
        assert parse(val)

def test_metadata_no_times(populateddb):
    sesh = populateddb.session
    rv = metadata(sesh, 'file1')
    assert rv['file1']['times'] == {}

def test_metadata_empty(populateddb):
    sesh = populateddb.session
    assert metadata(sesh, None) == {}

@pytest.mark.parametrize(('model'), ('cgcm3', ''))
def test_multimeta(populateddb, model):
    sesh = populateddb.session
    rv = multimeta(sesh, model=model) # Multimeta is wrapped for caching. Call the wrapped function
    assert 'file0' in rv
    assert rv['file0']['model_id'] == 'cgcm3'
    # times are not included in the multimeta API call
    assert 'timescale' in rv['file0']
    assert 'times' not in rv['file0']

def test_stats(populateddb, polygon):
    sesh = populateddb.session
    rv = stats(sesh, 'file0', None, polygon, 'tasmax')
    for attr in ('min', 'max', 'mean', 'median', 'stdev'):
        assert rv['file0'][attr] > 0
        assert type(rv['file0'][attr]) == float

    for attr in ('units', 'time'):
        assert rv['file0'][attr]
        print(rv['file0'][attr])

    assert type(rv['file0']['ncells']) == int
    assert parse(rv['file0']['time'])

@pytest.mark.parametrize(('filters', 'keys'), (
    ({'variable': 'tasmax'}, ('CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc', 'file0', 'file2')),
    ({'variable': 'tasmax', 'model': 'cgcm3'}, ['file0'])
))
def test_multistats(populateddb, filters, keys):
    sesh = populateddb.session
    rv = multistats(sesh, 'ce', **filters)
    for key in keys:
        assert key in rv

# stats() should return NaNs for the values
@pytest.mark.parametrize(('id_', 'var'), (
    ('file0', 'no_variable'), # Variable does not exist in file
    ('file1', 'tasmax') # File does not exist on the filesystem
))
def test_stats_bad_params(populateddb, id_, var):
    sesh = populateddb.session

    rv = stats(sesh, id_, None, None, var)
    assert math.isnan(rv[id_]['max'])
    assert 'time' not in rv[id_]
    assert 'units' not in rv[id_]


def test_stats_bad_id(populateddb):
    rv = stats(populateddb.session, 'id-does-not-exist', None, None, None)
    assert rv == {}


@pytest.mark.parametrize(('time_idx'), (0, 1, 11))
def test_data(populateddb, time_idx):
    rv = data(populateddb.session, 'cgcm3', 'rcp45', time_idx, None, 'tasmax',
              timescale="other", ensemble_name="ce")
    assert 'run0' in rv
    assert 'data' in rv['run0']
    for val in rv['run0']['data'].values():
        assert val > 0
    for key in rv['run0']['data'].keys():
        assert parse(key)
    assert 'units' in rv['run0']
    assert rv['run0']['units'] == 'degC'


@pytest.mark.parametrize(('model', 'scenario'), (
    ('', ''),
    (None, None),
    ('cgcm19', 'rcp45')
    ))
def test_data_bad_model_scenario(populateddb, model, scenario):
    rv = data(populateddb.session, model, scenario, 1, None, 'tasmax')
    assert rv == {}

def test_data_bad_time(populateddb):
    with pytest.raises(Exception) as exc:
        data(populateddb.session, '', '', 'time-not-an-int', '', '')
    assert 'time parameter "time-not-an-int" not convertable to an integer.' == \
        str(exc.value)

@pytest.mark.parametrize(('variable'), ('tasmax', 'tasmin'))
def test_data_single_variable_file(populateddb, variable):
    rv = data(populateddb.session, 'cgcm3', 'rcp45', 1, None, variable)
    assert len(rv) == 1


def test_data_multiple_times(multitime_db):
    rv = data(multitime_db.session, 'cgcm3', 'rcp45', 0, None, 'tasmax')
    assert len(rv) > 1
    for run in rv.values():
        assert len(run['data']) > 1

@pytest.mark.parametrize(('id_', 'var'), (
    ('file0', 'tasmax'),
))
def test_timeseries(populateddb, polygon, id_, var):
    sesh = populateddb.session
    rv = timeseries(sesh, id_, polygon, var)
    for key in ('id', 'data', 'units'):
        assert key in rv
    assert rv['id'] == id_
    assert set(rv['data'].keys()) == {'1985-01-15T00:00:00Z',
            '1985-08-15T00:00:00Z', '1985-04-15T00:00:00Z',
            '1985-09-15T00:00:00Z', '1985-06-15T00:00:00Z',
            '1985-12-15T00:00:00Z', '1985-05-15T00:00:00Z',
            '1985-02-15T00:00:00Z', '1985-03-15T00:00:00Z',
            '1985-07-15T00:00:00Z', '1985-10-15T00:00:00Z',
            '1985-11-15T00:00:00Z'}
    for val in rv['data'].values():
        assert type(val) == float
    assert rv['units'] == 'K'

@pytest.mark.parametrize(('id_'), (None, '', 'does-not-exist'))
def test_timeseries_bad_id(populateddb, id_):
    rv = timeseries(populateddb.session, id_, None, None)
    assert rv == {}

@pytest.mark.parametrize(('id_', 'var'), (
    ('file0', 'tasmax'),
    ('file4', 'tasmin'),
))
def test_timeseries_speed(populateddb, polygon, id_, var):
    sesh = populateddb.session
    t0 = time()
    rv = timeseries(sesh, id_, polygon, var)
    t = time() - t0
    print(t)
    assert t < 3

@pytest.mark.parametrize(('id_'), ('file0',))
def test_grid(populateddb, id_):
    rv = grid(populateddb.session, id_)
    for key in rv.keys():
      assert 'latitudes' in rv[key]
      assert len(rv[key]['latitudes']) > 0
      assert type(rv[key]['latitudes'][0]) == float
      assert 'longitudes' in rv[key]
      assert len(rv[key]['longitudes']) > 0
      assert type(rv[key]['longitudes'][0]) == float
