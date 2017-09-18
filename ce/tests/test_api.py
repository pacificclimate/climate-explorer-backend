import math
from time import time
import re

import pytest

from flask import url_for
from dateutil.parser import parse

from ce.api import *


def extract_ids(s):
    pattern = re.compile("_(.Clim)_BNU")
    m = pattern.search(s)
    if m:
        return m.group(1)
    else:
        return s

@pytest.mark.parametrize(('endpoint', 'query_params'), [
    ('stats', {'id_': '', 'time': '', 'area': '', 'variable': ''}),
    ('data', {'model': '', 'emission': '', 'time': '0', 'area': '', 'variable': ''}),
    ('timeseries', {'id_': '', 'area': '', 'variable': ''}),
    ('models', {}),
    ('metadata', {'model_id': 'tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230'}),
    ('multimeta', {'model': ''}),
    ('lister', {'model': ''}),
    ('grid', {'id_': ''})
], ids=extract_ids)
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
    ({'ensemble_name': 'bccaqv2'},
     ['tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230',
      'tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230']),
    ({'model': 'csiro'}, ['file1', 'file2'])
], ids=extract_ids)
def test_lister(populateddb, args, expected):
    sesh = populateddb.session
    rv = lister(sesh, **args)
    assert set(rv) == set(expected)


@pytest.mark.parametrize(('unique_id'), (
        'tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230',
        'tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230'
), ids=extract_ids)
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


@pytest.mark.parametrize(('model'), ('BNU-ESM', ''))
def test_multimeta(populateddb, model):
    unique_id = 'tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230'
    sesh = populateddb.session
    rv = multimeta(sesh, model=model) # Multimeta is wrapped for caching. Call the wrapped function
    assert unique_id in rv
    assert rv[unique_id]['model_id'] == 'BNU-ESM'
    # times are not included in the multimeta API call
    assert 'timescale' in rv[unique_id]
    assert 'times' not in rv[unique_id]
    # make sure start_date and end_date are present
    assert 'start_date' in rv[unique_id]
    assert 'end_date' in rv[unique_id]


@pytest.mark.parametrize('unique_id, var_name', [
    ('tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
    ('tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
    ('tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
    ('tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmin'),
    ('tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmin'),
    ('tasmin_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmin'),
    ],
    ids=extract_ids
)
def test_stats(populateddb, polygon, unique_id, var_name):
    sesh = populateddb.session
    rv = stats(sesh, unique_id, None, polygon, var_name)
    statistics = rv[unique_id]
    for attr in ('min', 'max', 'mean', 'median', 'stdev'):
        value = statistics[attr]
        assert type(value) == float, attr
        assert value >= 0, attr

    for attr in ('units', 'time'):
        assert statistics[attr]

    assert type(statistics['ncells']) == int
    assert parse(statistics['time'])


@pytest.mark.parametrize(('filters', 'keys'), (
    ({'variable': 'tasmax'},
     ('CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc', 'file2')),
    ({'variable': 'tasmax', 'model': 'BNU-ESM'},
     ['tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230']),
    ({'variable': 'tasmax', 'timescale': 'seasonal'},
     ['tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230'])
), ids=extract_ids)
def test_multistats(populateddb, filters, keys):
    sesh = populateddb.session
    rv = multistats(sesh, 'ce', **filters)
    for key in keys:
        assert key in rv


# stats() should return NaNs for the values
@pytest.mark.parametrize(('unique_id', 'var'), (
    # Variable does not exist in file
    ('tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'no_variable'),
    # File does not exist on the filesystem
    ('file1', 'tasmax')
), ids=extract_ids)
def test_stats_bad_params(populateddb, unique_id, var):
    sesh = populateddb.session

    rv = stats(sesh, unique_id, None, None, var)
    assert math.isnan(rv[unique_id]['max'])
    assert 'time' not in rv[unique_id]
    assert 'units' not in rv[unique_id]


def test_stats_bad_id(populateddb):
    rv = stats(populateddb.session, 'id-does-not-exist', None, None, None)
    assert rv == {}


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


@pytest.mark.parametrize('variable', (
        'tasmax',
        'tasmin',
))
@pytest.mark.parametrize('timescale, time_idx, expected_ymd', (
        ('monthly', 8, (1985, 9, 15)),
        ('seasonal', 2, (1985, 7, 15)),
        ('yearly', 0, (1985, 7, 2)),
))
def test_data_single_file(populateddb, variable,
                          timescale, time_idx, expected_ymd):
    rv = data(
        populateddb.session,
        model='BNU-ESM',
        emission='historical',
        area=None,
        variable=variable,
        timescale=timescale,
        time=time_idx,
    )

    assert len(rv) == 1
    expected_run = 'r1i1p1'
    assert expected_run in rv
    assert 'data' in rv[expected_run]

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
        model='BNU-ESM',
        emission='rcp45',
        time=0,
        area=None,
        variable='tasmax',
        timescale='other'
    )
    assert len(rv) > 1
    for run in rv.values():
        assert len(run['data']) > 1


@pytest.mark.parametrize(('unique_id', 'var'), (
    ('tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
), ids=extract_ids)
def test_timeseries(populateddb, polygon, unique_id, var):
    sesh = populateddb.session
    rv = timeseries(sesh, unique_id, polygon, var)
    for key in ('id', 'data', 'units'):
        assert key in rv
    assert rv['id'] == unique_id
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

#verifies that different months or seasons of an annual timeseries
#have different values
@pytest.mark.parametrize('unique_id,var', [
    ('tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
    ('tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmin'),
    ('tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
    ('tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmin')],
    ids=extract_ids)
def test_timeseries_annual_variation(populateddb, unique_id, var):
    sesh = populateddb.session
    poly = """POLYGON((-265 65,-265 74,-276 74,-276 65,-265 65))"""
    rv = timeseries(sesh, unique_id, poly, var)
    values = set([])
    for val in rv['data'].values():
        assert val not in values
        values.add(val)

@pytest.mark.parametrize(('unique_id'), (None, '', 'does-not-exist'))
def test_timeseries_bad_id(populateddb, unique_id):
    rv = timeseries(populateddb.session, unique_id, None, None)
    assert rv == {}


@pytest.mark.parametrize(('unique_id', 'var'), (
    ('tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmax'),
    ('tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230', 'tasmin'),
), ids=extract_ids)
def test_timeseries_speed(populateddb, polygon, unique_id, var):
    sesh = populateddb.session
    t0 = time()
    rv = timeseries(sesh, unique_id, polygon, var)
    t = time() - t0
    print(t)
    assert t < 3

@pytest.mark.parametrize(('unique_id'), ('test_timeseries_speed',))
def test_grid(populateddb, unique_id):
    rv = grid(populateddb.session, unique_id)
    for key in rv.keys():
      assert 'latitudes' in rv[key]
      assert len(rv[key]['latitudes']) > 0
      assert type(rv[key]['latitudes'][0]) == float
      assert 'longitudes' in rv[key]
      assert len(rv[key]['longitudes']) > 0
      assert type(rv[key]['longitudes'][0]) == float
