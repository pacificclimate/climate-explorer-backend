import pytest

from flask import url_for

from ce.api import *

@pytest.mark.parametrize(('endpoint', 'query_params'), [
    ('stats', {'id_': '', 'time': '', 'area': '', 'variable': ''}),
    ('data', {'id_': '', 'time': '', 'area': '', 'variable': ''}),
    ('models', {}),
    ('metadata', {'model_id': 'file0'})
])
def test_api_endpoints_are_callable(test_client, cleandb, endpoint, query_params):
    url = '/api/' + endpoint
    response = test_client.get(url, query_string=query_params)
    assert response.status_code == 200

def test_models(populateddb):
    sesh = populateddb.session
    rv = models(sesh, 'bc_prism')
    assert rv

@pytest.mark.parametrize(('unique_id'), ('file0', 'file1'))
def test_metadata(populateddb, unique_id):
    sesh = populateddb.session
    rv = metadata(sesh, unique_id)
    assert unique_id in rv
    for key in ['institute_id', 'institution', 'model_id', 'model_name',
                'experiment', 'variables', 'ensemble_member']:
        assert key in rv[unique_id]
