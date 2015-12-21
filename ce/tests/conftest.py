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
    ens2 = Ensemble(name='ce', version=2.0, changes='', description='')

    rcp45 = Emission(short_name='rcp45')
    rcp85 = Emission(short_name='rcp85')

    run0 = Run(name='run0', emission=rcp45)
    run1 = Run(name='run1', emission=rcp45)
    run2 = Run(name='r1i1p1', emission=rcp85)

    cgcm = Model(short_name='cgcm3', long_name='Canadian Global Climate Model (version 3)',
                 type='GCM', runs=[run0], organization='CCCMA')
    csiro = Model(short_name='csiro', type='GCM', runs=[run1], organization='CSIRO')
    canems2 = Model(short_name='CanESM2',
                 long_name='CCCma (Canadian Centre for Climate Modelling and Analysis, Victoria, BC, Canada)',
                 type='GCM', runs=[run2], organization='CCCMA')

    file0 = DataFile(filename=resource_filename('ce', 'tests/data/cgcm.nc'),
                     unique_id='file0', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run0)
    file4 = DataFile(filename=resource_filename('ce', 'tests/data/cgcm-tmin.nc'),
                     unique_id='file4', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run0)
    file1 = DataFile(filename='/path/to/some/other/netcdf_file.nc',
                     unique_id='file1', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run1)
    file2 = DataFile(filename='/path/to/some/other/netcdf_file.nc',
                     unique_id='file2', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run1)
    file3 = DataFile(filename=resource_filename('ce', 'CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc'),
                     unique_id='CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc', first_1mib_md5sum='xxxx',
                     x_dim_name='lon', y_dim_name='lat', index_time=now,
                     run=run2)

    tasmin = VariableAlias(long_name='Daily Minimum Temperature',
                         standard_name='air_temperature', units='degC')
    tasmax = VariableAlias(long_name='Daily Maximum Temperature',
                         standard_name='air_temperature', units='degC')

    anuspline_grid = Grid(name='Canada ANUSPLINE', xc_grid_step=0.0833333,
                          yc_grid_step=0.0833333, xc_origin=-140.958,
                          yc_origin=41.0417, xc_count=1068, yc_count=510,
                          xc_units='degrees_east', yc_units='degrees_north',
                          evenly_spaced_y=True)

    sesh.add_all([ens0, ens1, ens2, cgcm, csiro, canems2, file0, file1, file2, file3, file4,
                  tasmin, tasmax, anuspline_grid])
    sesh.flush()

    tmin = DataFileVariable(netcdf_variable_name='tasmin', range_min=0,
                            range_max=50, file=file4,
                            variable_alias=tasmin, grid=anuspline_grid)
    tmax = DataFileVariable(netcdf_variable_name='tasmax', range_min=0,
                            range_max=50, file=file0,
                            variable_alias=tasmax, grid=anuspline_grid)

    tmin1 = DataFileVariable(netcdf_variable_name='tasmin', range_min=0,
                            range_max=50, file=file1,
                            variable_alias=tasmin, grid=anuspline_grid)
    tmax1 = DataFileVariable(netcdf_variable_name='tasmax', range_min=0,
                            range_max=50, file=file2,
                            variable_alias=tasmax, grid=anuspline_grid)
    tmax2 = DataFileVariable(netcdf_variable_name='tasmax', range_min=0,
                            range_max=50, file=file3,
                            variable_alias=tasmax, grid=anuspline_grid)

    sesh.add_all([tmin, tmax, tmin1, tmax1, tmax2])
    sesh.flush()

    ens0.data_file_variables.append(tmin)
    ens0.data_file_variables.append(tmax)
    ens1.data_file_variables.append(tmax)
    ens2.data_file_variables.append(tmin)
    ens2.data_file_variables.append(tmax)
    ens2.data_file_variables.append(tmin1)
    ens2.data_file_variables.append(tmax1)
    ens2.data_file_variables.append(tmax2)

    sesh.add_all(sesh.dirty)

    ts = TimeSet(calendar='gregorian', start_date=datetime(1971, 1, 1),
                 end_date=datetime(2000, 12, 31), multi_year_mean=True,
                 num_times=12, time_resolution='other',
                 times = [ Time(time_idx=i, timestep=datetime(1985, 1+i, 15)) for i in range(12) ])
    ts.files = [file0, file4]
    sesh.add_all(sesh.dirty)

    sesh.commit()
    return populateable_db


@pytest.fixture
def test_client(app):
    return app.test_client()


def db(app):
    return SQLAlchemy(app)

@pytest.fixture
def multitime_db(cleandb):
    '''A fixture which represents multiple runs where there exist
       multiple climatological time periods in each run
       This is realistic for a set of model output that we would be
       using, but unfortunately it's overly-complicated to set up as a
       test case :(

       Simulated 3 runs, each consisting of 3 files, so 9 files total.
       We'll have 3 timesets, each of which are only a single date for
       some particular multidecadal period (say, 1980s, 2010s, 2040s).
       Each of a run's 3 files, will point to a different timeset.
    '''
    dbcopy = cleandb
    sesh = dbcopy.session
    ens = Ensemble(name='ce', version=2.0, changes='', description='')

    now = datetime.now()

    rcp45 = Emission(short_name='rcp45')
    # Create three runs
    runs = [ Run(name='run{}'.format(i), emission=rcp45) for i in range(3) ]
    cgcm = Model(short_name='cgcm3', long_name='',
                 type='GCM', runs=runs, organization='CCCMA')

    files = [
        # Create three files for each run
        [ DataFile(filename=resource_filename('ce', 'tests/data/cgcm.nc'),
                       unique_id='file{}'.format(j*3+i), first_1mib_md5sum='xxxx',
                       x_dim_name='lon', y_dim_name='lat', index_time=now,
                       run=run) for i, run in enumerate(runs) ] for j in range(3)
    ]
    files = files[0] + files[1] + files[2]

    tasmax = VariableAlias(long_name='Daily Maximum Temperature',
                         standard_name='air_temperature', units='degC')

    anuspline_grid = Grid(name='Canada ANUSPLINE', xc_grid_step=0.0833333,
                          yc_grid_step=0.0833333, xc_origin=-140.958,
                          yc_origin=41.0417, xc_count=1068, yc_count=510,
                          xc_units='degrees_east', yc_units='degrees_north',
                          evenly_spaced_y=True)

    dfvs = [ DataFileVariable(netcdf_variable_name='tasmax', range_min=0,
                            range_max=50, file=file_,
                            variable_alias=tasmax, grid=anuspline_grid)
             for file_ in files]

    sesh.add_all(files + dfvs + runs + [anuspline_grid, tasmax, cgcm, rcp45, ens])
    sesh.commit()

    # Create the three timesets, with just one time step per timeset
    times = [
        Time(time_idx=0, timestep=datetime(1985+y, 1, 15))
        for y in range(0, 90, 30)
    ]

    timesets = [
        TimeSet(calendar='gregorian', start_date=datetime(1971, 1, 1),
                end_date=datetime(2099, 12, 31), multi_year_mean=True,
                num_times=10, time_resolution='other',
                times = [t]
        ) for t in times
    ]

    # Wire up the timesets with the runs
    for run in runs:
        for i, ts in enumerate(timesets):
            ts.files.append(run.files[i])
            sesh.add_all(sesh.dirty)

    sesh.commit()

    return dbcopy
