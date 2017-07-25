import math
from time import time
import re

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

@pytest.mark.parametrize(('endpoint', 'missing_params'), [
    ('/api/metadata', ['model_id']),
    ('/api/data', ('model', 'emission', 'time', 'area', 'variable'))
])
def test_missing_query_param(test_client, cleandb, endpoint, missing_params):
    response = test_client.get(endpoint)
    assert response.status_code == 400
    content = response.data.decode(response.charset)
    assert re.search("Missing query params?:", content)
    for param in missing_params:
        assert param in content


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
    file_metadata = rv[unique_id]

    for key in ['institution', 'model_id', 'model_name', 'experiment',
                'variables', 'ensemble_member', 'times', 'timescale',
                'multi_year_mean', 'start_date', 'end_date']:
        assert key in file_metadata

    times = file_metadata['times']
    assert len(times) > 0

    # Are the values converible into times?
    for val in times.values():
        assert parse(val)

    if file_metadata['multi_year_mean'] is True:
        assert parse(file_metadata['start_date'])
        assert parse(file_metadata['end_date'])
    else:
        assert file_metadata['start_date'] is None
        assert file_metadata['end_date'] is None

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
              timescale="monthly", ensemble_name="ce")
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
    rv = data(
        populateddb.session,
        model='cgcm3',
        emission='rcp45',
        time=1,
        area=None,
        variable=variable,
        timescale='monthly'
    )

    assert len(rv) == 1
    print('\n', rv)


@pytest.mark.parametrize('variable', (
        'tasmax',
        'tasmin',
))
@pytest.mark.parametrize('timescale, time_idx, expected_ymd', (
        ('monthly', 8, (1985, 9, 15)),
        ('seasonal', 2, (1985, 7, 15)),
        ('yearly', 0, (1985, 7, 2)),
))
def test_data_new(populateddb, variable, timescale, time_idx, expected_ymd):
    rv = data(
        populateddb.session,
        model='BNU-ESM',
        emission='historical',
        area=None,
        variable=variable,
        timescale=timescale,
        time=time_idx,
    )
    print('\n', rv)
    assert len(rv) == 1
    for run_id, run_value in rv.items():
        assert len(run_value['data']) >= 1
        for time_str, value in run_value['data'].items():
            time = parse(time_str)
            assert (time.year, time.month, time.day) == expected_ymd
            assert 173 <= value <= 373 # -100 to +100 C, in K
        # FIXME: Or, fix something: units are wrong! Its K, not C.
        assert run_value['units'] == 'degC'


def test_data_multiple_times(multitime_db):
    rv = data(
        multitime_db.session,
        # 'cgcm3', 'rcp45', 0, None, 'tasmax'
        model='cgcm3',
        emission='rcp45',
        time=0,
        area=None,
        variable='tasmax',
        timescale='other'
    )
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
