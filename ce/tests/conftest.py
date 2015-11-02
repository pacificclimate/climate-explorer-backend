import py.path
import tempfile
from datetime import datetime
from pkg_resources import resource_filename

import pytest
import modelmeta
from modelmeta import *
from flask.ext.sqlalchemy import SQLAlchemy

from ce import get_app


# From http://stackoverflow.com/questions/25525202/py-test-temporary-folder-for-the-session-scope
@pytest.fixture(scope='function')
def sessiondir(request):
    dir = py.path.local(tempfile.mkdtemp())
    request.addfinalizer(lambda: dir.remove(rec=1))
    return dir


@pytest.fixture(scope='function')
def dsn(sessiondir):
    return 'sqlite:///{}'.format(sessiondir.join('test.sqlite').realpath())


@pytest.fixture
def app(dsn):
    app = get_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = dsn
    app.config['SQLALCHEMY_ECHO'] = False
    return app


@pytest.fixture
def cleandb(app):
    db = SQLAlchemy(app)
    modelmeta.v2.metadata.create_all(bind=db.engine)
    db.create_all()
    return db


@pytest.fixture
def populateddb(cleandb):

    now = datetime.now()

    populateable_db = cleandb
    sesh = populateable_db.session
    ens0 = Ensemble(name='bccaqv2', version=1.0, changes='', description='')
    ens1 = Ensemble(name='bc_prism', version=2.0, changes='', description='')

    rcp45 = Emission(short_name='rcp45')
    rcp85 = Emission(short_name='rcp85')

    run0 = Run(name='run0', emission=rcp45)
    run1 = Run(name='run1', emission=rcp45)

    cgcm = Model(short_name='cgcm3', long_name='Canadian Global Climate Model (version 3)',
                 type='GCM', runs=[run0], organization='CCCMA')
    csiro = Model(short_name='csiro', type='GCM', runs=[run1], organization='CSIRO')

    file0 = DataFile(filename=resource_filename('ce', 'tests/data/cgcm.nc'),
                     unique_id='file0', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run0)
    file1 = DataFile(filename='/path/to/some/other/netcdf_file.nc',
                     unique_id='file1', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run1)

    tmin = VariableAlias(long_name='Daily Minimum Temperature',
                         standard_name='air_temperature', units='degC')
    tmax = VariableAlias(long_name='Daily Maximum Temperature',
                         standard_name='air_temperature', units='degC')

    anuspline_grid = Grid(name='Canada ANUSPLINE', xc_grid_step=0.0833333,
                          yc_grid_step=0.0833333, xc_origin=-140.958,
                          yc_origin=41.0417, xc_count=1068, yc_count=510,
                          xc_units='degrees_east', yc_units='degrees_north',
                          evenly_spaced_y=True)

    sesh.add_all([ens0, ens1, cgcm, csiro, file0, file1, tmin, tmax,
                  anuspline_grid])
    sesh.flush()

    tmin = DataFileVariable(netcdf_variable_name='tasmin', range_min=0,
                            range_max=50, file=file0,
                            variable_alias=tmin, grid=anuspline_grid)
    tmax = DataFileVariable(netcdf_variable_name='tasmax', range_min=0,
                            range_max=50, file=file0,
                            variable_alias=tmax, grid=anuspline_grid)

    sesh.add_all([tmin, tmax])

    sesh.flush()

    ens0.data_file_variables.append(tmin)
    ens1.data_file_variables.append(tmax)

    sesh.add_all(sesh.dirty)

    ts = TimeSet(calendar='gregorian', start_date=datetime(1971, 1, 1),
                 end_date=datetime(2000, 12, 31), multi_year_mean=True,
                 num_times=12, time_resolution='other',
                 times = [ Time(time_idx=i, timestep=datetime(1985, 1+i, 15)) for i in range(12) ])
    ts.files = [file0]
    sesh.add_all(sesh.dirty)

    sesh.commit()
    return populateable_db


@pytest.fixture
def test_client(app):
    return app.test_client()


def db(app):
    return SQLAlchemy(app)
