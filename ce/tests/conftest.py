import sys
import os
import py.path
import tempfile
from datetime import datetime
from pkg_resources import resource_filename

from dateutil.relativedelta import relativedelta
import pytest

from modelmeta.v2 import (
    metadata,
    Ensemble,
    Emission,
    Model,
    Run,
    VariableAlias,
    Grid,
    Time,
    TimeSet,
    ClimatologicalTime,
    DataFile,
    DataFileVariableGridded,
)
from flask_sqlalchemy import SQLAlchemy
from netCDF4 import Dataset

from ce import get_app

# Add helpers directory to pythonpath: See https://stackoverflow.com/a/33515264
sys.path.append(os.path.join(os.path.dirname(__file__), "helpers",))


# From http://stackoverflow.com/q/25525202/
# FIXME: Why is this fixture scoped 'function', not 'session'?
@pytest.fixture(scope="function")
def sessiondir(request,):
    dir = py.path.local(tempfile.mkdtemp())
    request.addfinalizer(lambda: dir.remove(rec=1))
    return dir


@pytest.fixture(scope="function")
def dsn(sessiondir,):
    return "sqlite:///{}".format(sessiondir.join("test.sqlite").realpath())


@pytest.fixture
def app(dsn,):
    app = get_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = dsn
    app.config["SQLALCHEMY_ECHO"] = False
    return app


@pytest.fixture
def cleandb(app,):
    db = SQLAlchemy(app)
    metadata.create_all(bind=db.engine)
    db.create_all()
    return db


@pytest.fixture(scope="function")
def netcdf_file():
    fname = resource_filename(
        "ce",
        "tests/data/" "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc",
    )
    with Dataset(fname) as nc:
        yield nc, fname


# @pytest.fixture(scope='function')
# def big_nc_file(request):
#     return resource_filename('ce', 'tests/data/anuspline_na.nc')


@pytest.fixture(
    params=(
        resource_filename(
            "ce",
            "tests/data/" "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc",
        ),
        resource_filename("ce", "tests/data/anuspline_na.nc",),
    )
)
def ncfile(request,):
    return request.param


@pytest.fixture(scope="function")
def ncobject(ncfile,):
    with Dataset(ncfile) as nc:
        yield nc, ncfile


@pytest.fixture
def populateddb(cleandb,):

    now = datetime.utcnow()

    populateable_db = cleandb
    sesh = populateable_db.session

    # Ensembles

    ens_bccaqv2 = Ensemble(name="bccaqv2", version=1.0, changes="", description="",)
    ens_bc_prism = Ensemble(name="bc_prism", version=2.0, changes="", description="",)
    ens_ce = Ensemble(name="ce", version=2.0, changes="", description="",)
    ens_p2a_classic = Ensemble(
        name="p2a_classic", version=1.0, changes="", description="",
    )
    ensembles = [
        ens_bccaqv2,
        ens_bc_prism,
        ens_ce,
        ens_p2a_classic,
    ]

    # Emissions

    rcp45 = Emission(short_name="rcp45")
    rcp85 = Emission(short_name="rcp85")
    historical = Emission(short_name="historical")

    # Runs

    run1 = Run(name="run1", emission=rcp45,)
    run2 = Run(name="r1i1p1", emission=rcp85,)
    run3 = Run(name="r1i1p1", emission=historical,)

    # Models

    csiro = Model(short_name="csiro", type="GCM", runs=[run1], organization="CSIRO",)
    canems2 = Model(
        short_name="CanESM2",
        long_name="CCCma (Canadian Centre for Climate Modelling and Analysis, "
        "Victoria, BC, Canada)",
        type="GCM",
        runs=[run2],
        organization="CCCMA",
    )
    bnu_esm = Model(
        short_name="BNU-ESM",
        long_name="Beijing Normal University Earth System Model",
        type="GCM",
        runs=[run3],
        organization="BNU",
    )
    models = [
        csiro,
        canems2,
        bnu_esm,
    ]

    # Data files

    def make_data_file(
        unique_id, filename=None, run=None,
    ):
        if not filename:
            filename = "{}.nc".format(unique_id)
        if not filename.startswith("/"):
            filename = resource_filename("ce", "tests/data/{}".format(filename),)
        return DataFile(
            filename=filename,
            unique_id=unique_id,
            first_1mib_md5sum="xxxx",
            x_dim_name="lon",
            y_dim_name="lat",
            index_time=now,
            run=run,
        )

    # TODO: Create and use standards-compliant test files
    # (e.g., tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230)
    # that overlap with the test polygons. Currently these test files do
    # not, so the results of calls that mask by polygon are not much of a
    # test except in the no polygon case.

    file1 = make_data_file(
        unique_id="file1", filename="/path/to/some/other/netcdf_file.nc", run=run1,
    )
    file2 = make_data_file(
        unique_id="file2", filename="/path/to/some/other/netcdf_file.nc", run=run1,
    )
    file3 = make_data_file(
        unique_id="CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc",
        filename="CanESM2-rcp85-tasmax-r1i1p1-2010-2039.nc",
        run=run2,
    )

    df_5_monthly = make_data_file(
        unique_id="tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_5_seasonal = make_data_file(
        unique_id="tasmax_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_5_yearly = make_data_file(
        unique_id="tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_6_monthly = make_data_file(
        unique_id="tasmin_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_6_seasonal = make_data_file(
        unique_id="tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_6_yearly = make_data_file(
        unique_id="tasmin_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_7_yearly = make_data_file(
        unique_id="pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run3,
    )
    df_ti_flow_direction = make_data_file(unique_id="flow-direction_peace", run=run1,)

    data_files = [
        file1,
        file2,
        file3,
        df_5_monthly,
        df_5_seasonal,
        df_5_yearly,
        df_6_monthly,
        df_6_seasonal,
        df_6_yearly,
        df_7_yearly,
        df_ti_flow_direction,
    ]

    # VariableAlias
    # TODO: Really? Do we really use aliases?

    tasmin = VariableAlias(
        long_name="Daily Minimum Temperature",
        standard_name="air_temperature",
        units="degC",
    )
    tasmax = VariableAlias(
        long_name="Daily Maximum Temperature",
        standard_name="air_temperature",
        units="degC",
    )
    pr = VariableAlias(
        long_name="Precipitation",
        standard_name="precipitation_flux",
        units="kg d-1 m-2",
    )
    flow_direction = VariableAlias(
        long_name="Flow Direction", standard_name="flow_direction", units="1",
    )
    variable_aliases = [
        tasmin,
        tasmax,
        pr,
        flow_direction,
    ]

    # Grids

    grid_anuspline = Grid(
        name="Canada ANUSPLINE",
        xc_grid_step=0.0833333,
        yc_grid_step=0.0833333,
        xc_origin=-140.958,
        yc_origin=41.0417,
        xc_count=1068,
        yc_count=510,
        xc_units="degrees_east",
        yc_units="degrees_north",
        evenly_spaced_y=True,
    )
    grids = [grid_anuspline]

    # Add all the above

    sesh.add_all(ensembles)
    sesh.add_all(models)
    sesh.add_all(data_files)
    sesh.add_all(variable_aliases)
    sesh.add_all(grids)
    sesh.flush()

    # DataFileVariable

    def make_data_file_variable(
        file, var_name=None, grid=grid_anuspline,
    ):
        var_name_to_alias = {
            "tasmin": tasmin,
            "tasmax": tasmax,
            "pr": pr,
            "flow_direction": flow_direction,
        }[var_name]
        variable_cell_methods = {
            "tasmin": "time: minimum",
            "tasmax": "time: maximum time: standard_deviation over days",
            "pr": "time: mean time: mean over days",
            "flow_direction": "foo",
        }[var_name]
        return DataFileVariableGridded(
            file=file,
            netcdf_variable_name=var_name,
            range_min=0,
            range_max=50,
            variable_alias=var_name_to_alias,
            grid=grid,
            variable_cell_methods=variable_cell_methods,
        )

    tmin1 = make_data_file_variable(file1, var_name="tasmin",)
    tmax1 = make_data_file_variable(file2, var_name="tasmax",)
    tmax2 = make_data_file_variable(file3, var_name="tasmax",)
    tmax3 = make_data_file_variable(df_5_monthly, var_name="tasmax",)
    tmax4 = make_data_file_variable(df_5_seasonal, var_name="tasmax",)
    tmax5 = make_data_file_variable(df_5_yearly, var_name="tasmax",)
    tmax6 = make_data_file_variable(df_6_monthly, var_name="tasmin",)
    tmax7 = make_data_file_variable(df_6_seasonal, var_name="tasmin",)
    tmax8 = make_data_file_variable(df_6_yearly, var_name="tasmin",)
    pr1 = make_data_file_variable(df_7_yearly, var_name="pr",)
    fd = make_data_file_variable(df_ti_flow_direction, var_name="flow_direction",)

    data_file_variables = [
        tmin1,
        tmax1,
        tmax2,
        tmax3,
        tmax4,
        tmax5,
        tmax6,
        tmax7,
        tmax8,
        pr1,
        fd,
    ]

    sesh.add_all(data_file_variables)
    sesh.flush()

    # Associate to Ensembles

    for dfv in [
        tmax3,
        tmax6,
    ]:
        ens_bccaqv2.data_file_variables.append(dfv)

    for dfv in [tmax6]:
        ens_bc_prism.data_file_variables.append(dfv)

    for dfv in data_file_variables:
        ens_ce.data_file_variables.append(dfv)
        ens_p2a_classic.data_file_variables.append(dfv)

    sesh.add_all(sesh.dirty)

    # TimeSets

    ts_monthly = TimeSet(
        calendar="gregorian",
        start_date=datetime(1971, 1, 1,),
        end_date=datetime(2000, 12, 31,),
        multi_year_mean=True,
        num_times=12,
        time_resolution="monthly",
        times=[
            Time(time_idx=i, timestep=datetime(1985, 1 + i, 15,),) for i in range(12)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1971, 1 + i, 1,),
                time_end=datetime(2000, 1 + i, 1,)
                + relativedelta(months=1)
                - relativedelta(days=1),
            )
            for i in range(12)
        ],
    )
    ts_monthly.files = [
        file2,
        file3,
        df_5_monthly,
        df_6_monthly,
    ]

    ts_seasonal = TimeSet(
        calendar="gregorian",
        start_date=datetime(1971, 1, 1,),
        end_date=datetime(2000, 12, 31,),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(time_idx=i, timestep=datetime(1985, 3 * i + 1, 15,),) for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1971, 3 * i + 1, 1,) - relativedelta(months=1),
                time_end=datetime(2000, 3 * i + 1, 1,)
                + relativedelta(months=2)
                - relativedelta(days=1),
            )
            for i in range(4)
        ],
    )
    ts_seasonal.files = [
        df_5_seasonal,
        df_6_seasonal,
    ]

    ts_yearly = TimeSet(
        calendar="gregorian",
        start_date=datetime(1971, 1, 1,),
        end_date=datetime(2000, 12, 31,),
        multi_year_mean=True,
        num_times=1,
        time_resolution="yearly",
        times=[Time(time_idx=0, timestep=datetime(1985, 7, 2,),)],
        climatological_times=[
            ClimatologicalTime(
                time_idx=0,
                time_start=datetime(1971, 1, 1,),
                time_end=datetime(2000, 12, 31,),
            )
        ],
    )
    ts_yearly.files = [
        df_5_yearly,
        df_6_yearly,
        df_7_yearly,
    ]

    sesh.add_all(sesh.dirty)

    sesh.commit()
    return populateable_db


@pytest.fixture
def test_client(app,):
    with app.test_client() as client:
        yield client


def db(app,):
    return SQLAlchemy(app)


@pytest.fixture
def multitime_db(cleandb,):
    """A fixture which represents multiple runs where there exist
       multiple climatological time periods in each run
       This is realistic for a set of model output that we would be
       using, but unfortunately it's overly-complicated to set up as a
       test case :(

       Simulated 3 runs, each consisting of 3 files, so 9 files total.
       We'll have 3 timesets, each of which are only a single date for
       some particular multidecadal period (say, 1980s, 2010s, 2040s).
       Each of a run's 3 files, will point to a different timeset.
    """
    dbcopy = cleandb
    sesh = dbcopy.session
    now = datetime.utcnow()

    ce_ens = Ensemble(name="ce", version=2.0, changes="", description="",)
    # Create diff ensemble to test unit consistency ensemble filter
    p2a_ens = Ensemble(name="p2a", version=2.0, changes="", description="",)

    rcp45 = Emission(short_name="rcp45")

    # Create three runs
    runs = [Run(name="run{}".format(i), emission=rcp45,) for i in range(3)]

    bnu_esm = Model(
        short_name="BNU-ESM",
        long_name="Beijing Normal University Earth System Model",
        type="GCM",
        runs=runs,
        organization="BNU",
    )

    # Create three files for each run
    files = [
        DataFile(
            filename=resource_filename(
                "ce",
                "tests/data/"
                "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc",
            ),
            unique_id="file{}".format(j * 3 + i),
            first_1mib_md5sum="xxxx",
            x_dim_name="lon",
            y_dim_name="lat",
            index_time=now,
            run=run,
        )
        for i, run in enumerate(runs)
        for j in range(3)
    ]

    tasmax = VariableAlias(
        long_name="Daily Maximum Temperature",
        standard_name="air_temperature",
        units="degC",
    )
    # Create variable with different units
    tasmax_diff_units = VariableAlias(
        long_name="Tasmax with different units",
        standard_name="tmax_diff_units",
        units="degK",
    )

    anuspline_grid = Grid(
        name="Canada ANUSPLINE",
        xc_grid_step=0.0833333,
        yc_grid_step=0.0833333,
        xc_origin=-140.958,
        yc_origin=41.0417,
        xc_count=1068,
        yc_count=510,
        xc_units="degrees_east",
        yc_units="degrees_north",
        evenly_spaced_y=True,
    )

    dfvs = [
        DataFileVariableGridded(
            netcdf_variable_name="tasmax",
            range_min=0,
            range_max=50,
            file=file_,
            variable_alias=tasmax,
            grid=anuspline_grid,
        )
        for file_ in files
    ]
    # Create file with different units
    files.append(
        DataFile(
            filename=resource_filename(
                "ce",
                "tests/data/"
                "tasmax_mClim_BNU-ESM_historical_r1i1p1_19650101-19701230.nc",
            ),
            unique_id="file9",
            first_1mib_md5sum="xxxx",
            x_dim_name="lon",
            y_dim_name="lat",
            index_time=now,
            run=runs[0],
        )
    )
    # Create dfv with same var name and diff units
    dfv_diff_units = DataFileVariableGridded(
        netcdf_variable_name="tasmax",
        range_min=0,
        range_max=50,
        file=files[9],
        variable_alias=tasmax_diff_units,
        grid=anuspline_grid,
    )
    dfvs.append(dfv_diff_units)

    sesh.add_all(
        files
        + dfvs
        + runs
        + [anuspline_grid, tasmax, tasmax_diff_units, bnu_esm, rcp45, ce_ens, p2a_ens]
    )
    sesh.commit()

    ce_ens.data_file_variables += dfvs[:-1]
    # Add dfv with diff units to diff ensemble
    p2a_ens.data_file_variables.append(dfvs.pop())
    sesh.add_all(sesh.dirty)

    # Create the three timesets, with just one time step per timeset
    times = [
        Time(time_idx=0, timestep=datetime(1985 + y, 1, 15,),)
        for y in range(0, 90, 30,)
    ]

    timesets = [
        TimeSet(
            calendar="gregorian",
            start_date=datetime(1971, 1, 1,),
            end_date=datetime(2099, 12, 31,),
            multi_year_mean=True,
            num_times=10,
            time_resolution="other",
            times=[t],
        )
        for t in times
    ]

    # Wire up the timesets with the runs
    for run in runs:
        for (i, ts,) in enumerate(timesets):
            ts.files.append(run.files[i])
            sesh.add_all(sesh.dirty)

    sesh.commit()

    return dbcopy


polygons = {
    # Metro Van 10 vertex
    "metro_van_10": """POLYGON((-122.70904541015625 49.31438004800689,-122.92327880859375
            49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))""",
    # 18 point BC province
    "bc_18": """POLYGON((-134.09912109375 59.712097173322924,-132.86865234375
            58.401711667608,-130.49560546875 56.70450561416937,-128.95751953125
            54.49556752187406,-130.93505859375 54.059387886623576,-133.79150390625
            54.521081495443596,-134.01123046875 53.30462107510271,-132.91259765625
            52.3755991766591,-130.18798828125 50.84757295365389,-127.33154296875
            49.26780455063753,-125.13427734375 48.1367666796927,-122.89306640625
            48.16608541901253,-122.84912109375 49.03786794532644,-113.79638671875
            48.980216985374994,-115.68603515625 51.09662294502995,-118.98193359375
            53.14677033085084,-119.90478515625 53.904338156274704,-119.99267578125
            60.02095215374802,-134.09912109375 59.712097173322924))""",
    # Fraser Plateau 270 pts
    "fraser_plateau_270": """POLYGON ((-120.803494992649632
            51.028943367893262,-120.829195972290393
            51.03703427093464,-120.785172630137566
            51.152795518318662,-120.908343419489825
            51.223543446712412,-121.062759506554769
            51.184831434439474,-121.168905089489726
            51.128903790841363,-121.176570227934064
            51.108402266834752,-121.343480010073435
            51.03435864981067,-121.348375366884511
            51.002614663972658,-121.423397272269725
            50.981911607852183,-121.517554456830439
            50.976822963757954,-121.562017154024218
            51.011792190367721,-121.573725552038539
            51.050543540266389,-121.629997300110048
            51.094441768839424,-121.622260016896249
            51.129935447582,-121.756227455209199
            51.219569449709184,-121.820072503942697
            51.285765556795852,-121.900598171032414
            51.330422680201622,-121.988421028716374
            51.327105876385723,-121.981884949596747
            51.288066121853959,-122.026196431435153
            51.23698060839061,-122.154665835415059
            51.16605739022053,-122.228356479851598
            51.265996833086874,-122.356686247566685
            51.305120086022896,-122.352710739713103
            51.358543396900295,-122.38264253088056
            51.40189718707957,-122.503198539653383
            51.436798247384118,-122.561389406535966
            51.398264170507872,-122.55521619165404
            51.345813622246389,-122.612515931758253
            51.333945943529521,-122.662054369639364
            51.254740324387377,-122.697964600384196
            51.226750256710098,-122.803028735466199
            51.26780949322962,-122.903477406477919
            51.337103016607159,-123.021473252087233
            51.339686966618252,-123.048187088010877
            51.323028582379017,-123.127440242852273
            51.352250096697318,-123.207894318220255
            51.350024018531222,-123.334623853311541
            51.394733206847462,-123.550234449603138
            51.34873550222251,-123.617757098210575
            51.3681732104058,-123.698264959828578
            51.44363969312667,-123.770446011302283
            51.467328671603113,-123.789943194184559
            51.525348109845481,-123.836333385351125
            51.524933768972801,-123.848940336964304
            51.579699070722178,-123.908300672021539
            51.625964928814177,-123.973972351952298
            51.606829418684192,-124.006011999242574
            51.564173122664258,-124.065326905333606
            51.548530296890313,-124.104018022778618
            51.648632308745434,-124.166627668708429
            51.649195113332283,-124.1775610676886
            51.676336577917496,-124.331193601984722
            51.675904345893748,-124.468942328251543
            51.741003212809282,-124.505170041450924
            51.786112241814166,-124.580512438863039
            51.82321329171851,-124.650233811917758
            51.790690099797949,-124.744308267054933
            51.795851484563919,-124.740270383314652
            51.87239024199409,-124.964686109791344
            51.905262469281283,-125.072256070313102
            51.93292769077302,-125.100302884089345
            51.973940232691781,-125.107140488406955
            52.044118008326421,-125.090826178361752
            52.109242284457579,-125.185002082114295
            52.139791823927098,-125.253943471974537
            52.131331407717106,-125.33967284129281
            52.150377918342251,-125.373556506768722
            52.17309118618892,-125.429841281498412
            52.158259194832105,-125.482076272132332
            52.200246694497835,-125.389024248246201
            52.235326609399735,-125.287643698026955
            52.239868048255964,-125.28669734916258
            52.287053483903421,-125.354385195089193
            52.312156290715116,-125.372348623017217
            52.356657732562752,-125.455174333156961
            52.344188548296671,-125.51105591751822
            52.373706634029581,-125.619748116287639
            52.396340786450416,-125.669618141969892
            52.449379677042458,-125.604059244671916
            52.482770148537057,-125.527023121453993
            52.499791220937468,-125.497672101189664
            52.534272993664977,-125.584272340328482
            52.640616862825986,-125.5727227852814
            52.708930691629654,-125.587451795531322
            52.783618271706864,-125.630631621170906
            52.828307587148963,-125.737621028367258
            52.836986630455741,-125.868592820788123
            52.825641370476902,-125.917635542756614
            52.848205920886002,-125.94192711044623
            52.90590829194862,-125.984600187361835
            52.93371144297403,-126.057111969474178
            52.922582720213825,-126.043299305384323
            52.969803669807078,-126.073863913582329
            53.008432659041453,-126.055101375140936
            53.072927986150901,-126.064486841962292
            53.146215327571994,-126.007283209420237
            53.155754389610543,-125.952377918025093
            53.207122160344262,-125.977112595530954
            53.261421917458534,-125.869162314301704
            53.284945685713183,-125.923352835930714
            53.378086287800727,-125.866376299069515
            53.420460825800816,-125.842585089221913
            53.474585179664182,-125.787924576925818
            53.476190367007391,-125.756024540242322
            53.526753628796186,-125.827398619173977
            53.633518635091519,-125.897240442555344
            53.662162497589186,-125.986726186094458
            53.669374658162752,-126.065681978839407
            53.71483421427552,-126.171687674369082
            53.744245237690329,-126.273559625837137
            53.753995003564114,-126.334507965832259
            53.785643615298014,-126.47647259790692
            53.806234810515939,-126.514331057273466
            53.845774857180324,-126.474581626311334
            53.918065975982465,-126.55192447928772
            53.950482494212181,-126.687408259685157
            53.969499828288235,-126.783543480585948
            54.002964245902994,-126.75507839200769
            54.056459881933066,-126.801286714907931
            54.090211972504264,-126.86430106547455
            54.190581677144472,-126.992863232521259
            54.179634101448229,-126.889297750166577
            54.253059303042335,-126.90151560433624
            54.27774386863134,-126.870780671927093
            54.356125080107127,-126.822797111743768
            54.372415811440476,-126.895367495908729
            54.509131718537937,-126.882961003766923
            54.559888310095076,-126.977946433397577
            54.58484514820659,-127.029381244616616
            54.632887115911146,-127.113643858518529
            54.622582061475605,-127.234764223178942
            54.631669598710559,-127.186929231683735
            54.66488045192564,-127.181304060739507
            54.772565897959225,-127.237376791880394
            54.810095095614138,-127.352963433860893
            54.959053614141055,-127.250719603686264
            54.997804257756812,-127.187720281111481
            54.921806923155984,-127.068050139588777
            54.873388444170843,-127.005504792668347
            54.87100200461704,-126.925539490033572
            54.832094386103336,-126.884336397558059
            54.794207691156785,-126.786230788575025
            54.749740959630607,-126.769218823944911
            54.683886258937044,-126.679972227212104
            54.646560261328361,-126.540714159270749
            54.570428873163465,-126.415973505472351
            54.57741118460919,-126.301575844860281
            54.561342362159955,-126.149186096612226
            54.505795376519337,-126.059128503167912
            54.449318610817969,-125.889775920434317
            54.40818356902593,-125.853233467525271
            54.37051678825452,-125.742550813065591
            54.305826690269726,-125.729689377658488
            54.270409364562148,-125.681234010747033
            54.241957770519868,-125.604858372124482
            54.236931132333936,-125.418803767925326
            54.200443280520915,-125.370228163707239
            54.16144957349978,-125.324923620723283
            54.162549866003225,-125.209439666161273
            54.194180652649671,-125.169500218679303
            54.215995504239054,-125.133087240899783
            54.159396675123453,-124.969215812913433
            54.143922185076526,-124.888210865560239
            54.160227174163737,-124.789845659692233
            54.13778383256318,-124.681967955366815
            54.128367959543731,-124.612668835419584
            54.077068748691161,-124.634811576954192
            54.046517173386391,-124.615933032883362
            53.955370031070622,-124.572721197477392
            53.936183818238405,-124.582709685536287
            53.840803227995508,-124.612742903003763
            53.819647310278711,-124.568107873852625
            53.783607838748331,-124.65242775248899
            53.746158227658483,-124.619923395913219
            53.712064684337562,-124.556290077416307
            53.773383605132246,-124.505314771244315
            53.773882175446147,-124.365317788900214
            53.818777081571554,-124.111406383776028
            53.829376253193388,-124.034643779254907
            53.824321168365323,-123.971292783920418
            53.847028001491921,-123.885927799251007
            53.839455363533069,-123.839648053157262
            53.806728462249993,-123.836012711761228
            53.774952353613713,-123.758770314181945
            53.709049827191265,-123.707127150342529
            53.689833502764905,-123.64063013295214
            53.694351206256364,-123.589603979923311
            53.640406729730636,-123.467593260557507
            53.66799679749959,-123.449521013631212
            53.70136024136216,-123.384033234668166
            53.716090836893862,-123.280630919647521
            53.697308861811194,-123.225184722605491
            53.658927315892598,-123.090208173859125
            53.658431964356936,-122.927757497797415
            53.639118323740867,-122.821085864311755
            53.65777209510685,-122.71705551617427
            53.692735795968233,-122.601897275390982
            53.65437071484692,-122.47610597337335
            53.666798506557434,-122.584871766607037
            53.571730328941406,-122.496846377245035
            53.537516899847567,-122.458514856290321
            53.471144048745089,-122.464007433743163
            53.437654257680663,-122.431863946808789
            53.384500173162422,-122.363449757860778
            53.351342519556567,-122.219418862908825
            53.427712531706398,-122.186394036040795
            53.40214755322873,-122.190091809468754
            53.30177293910539,-122.16434179005428
            53.255821972092093,-122.161670456408629
            53.198051883424121,-122.129595317650285
            53.158363415099394,-122.145559627851711
            53.124495505880546,-122.076295875776012
            53.030053427352911,-122.019513274986693
            52.980026531565294,-122.032202052143617
            52.94788150607436,-121.902318565487178
            52.864884386800114,-121.799999907370264
            52.833779939380882,-121.800000440314932
            52.762927214372446,-121.735794071900273
            52.696825521701662,-121.790377757161593
            52.649863550110176,-121.6964381333799
            52.614355912596388,-121.724630010605296
            52.584456889476918,-121.778407226763491
            52.602400900128465,-121.776388757695145
            52.492542241110549,-121.721967147531743
            52.454972165233521,-121.620373177888212
            52.438298992663213,-121.548778678578643
            52.369532555755917,-121.475492165972398
            52.387554242872902,-121.49738233290708
            52.419573523042466,-121.432731203070134
            52.448880871754717,-121.388335667888967
            52.407634940788,-121.2527574854318
            52.366472823861251,-121.249509502237274
            52.332806966571397,-121.196594322024893
            52.319283594669919,-121.067197987970019
            52.315620606765449,-120.953209331431125
            52.243720833751013,-120.991353029407321
            52.220863272374729,-121.215883664574505
            52.254081642036056,-121.311060655957291
            52.229352412862568,-121.252712462249733
            52.098239790568712,-121.154232326351519
            52.053694110016302,-121.105471582869015
            52.047138200161761,-121.038683388502861
            52.003682478814866,-120.992009690470923
            51.991484927982434,-120.944191561151968
            51.946010117052104,-120.909860963042988
            51.882912649746771,-120.788875175852965
            51.876030202438173,-120.654069362876768
            51.911252032584791,-120.534003404336573
            51.853297457711449,-120.581070405464956
            51.823177275786655,-120.54044564845114
            51.790104277074548,-120.338292373674349
            51.744876426491821,-120.300926889640095
            51.694119087618368,-120.205223176385488
            51.636827440561845,-120.155167825351143
            51.624314675942578,-120.174940585109979
            51.576574183121821,-120.238175744057855
            51.578941791105564,-120.245441994578144
            51.512601137901974,-120.272532296603984
            51.453400530647102,-120.231987981207197
            51.396022653508567,-120.244946405495341
            51.305167274778015,-120.297010058836477
            51.340189871728114,-120.326705572424473
            51.302605784466309,-120.429067391663423
            51.282245823021256,-120.442598773002757
            51.252053384307246,-120.532052051146479
            51.254586184105975,-120.559632845872827
            51.229835708811365,-120.680156730065391
            51.233583933532906,-120.655107270903613
            51.101452014065629,-120.803494992649632
            51.028943367893262))""",
    # Haida Gwaii
    "haida_gwaii_6": """MULTIPOLYGON(((-133.4329023938909 54.383829480227,-131.07107067594964
            54.46520405265149,-130.32821767956855
            51.66447893217142,-131.63952512891498
            51.84675220747083,-133.49684680488463
            53.040426860630475,-133.4329023938909 54.383829480227)))""",
    "no_polygon_0": "",
}


@pytest.fixture(
    params=polygons.values(), ids=list(polygons.keys()),
)
def polygon(request,):
    return request.param
