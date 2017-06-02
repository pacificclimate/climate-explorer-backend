from pytest import fixture, mark
from pkg_resources import resource_filename
from nchelpers import CFDataset
from dp.generate_climos import create_climo_files

# It saves a little bit of execution time to define these session scoped input file fixtures
# and use those fixtures in get_input_file rather than to create them directly in get_input_file.

@fixture(scope='session')
def tiny_gcm():
    return CFDataset(resource_filename('dp', 'tests/data/tiny_gcm.nc'))


@fixture(scope='session')
def tiny_gcm_360_day_cal():
    return CFDataset(resource_filename('dp', 'tests/data/tiny_gcm_360_day_cal.nc'))


@fixture(scope='session')
def tiny_downscaled_tasmax():
    return CFDataset(resource_filename('dp', 'tests/data/tiny_downscaled_tasmax.nc'))


@fixture(scope='session')
def tiny_downscaled_pr():
    return CFDataset(resource_filename('dp', 'tests/data/tiny_downscaled_pr.nc'))


@fixture(scope='session')
def tiny_downscaled_pr_packed():
    return CFDataset(resource_filename('dp', 'tests/data/tiny_downscaled_pr_packed.nc'))


@fixture(scope='session')
def tiny_hydromodel_gcm():
    return CFDataset(resource_filename('dp', 'tests/data/tiny_hydromodel_gcm.nc'))


@fixture(scope='session')
def get_input_file(tiny_gcm, tiny_gcm_360_day_cal, tiny_downscaled_tasmax, tiny_downscaled_pr, tiny_downscaled_pr_packed, tiny_hydromodel_gcm):
    """Helper fixture: Returns a function that returns a test input file selected by its param.
    This fixture is used by other resources to DRY up their parametrization over input file resources.
    """
    def get(code):
        """Helper function: returns a test input file based on parameter.
        :param code: (str) code for desired input file
        """
        return {
            'gcm': tiny_gcm,
            'gcm_360': tiny_gcm_360_day_cal,
            'downscaled_tasmax': tiny_downscaled_tasmax,
            'downscaled_pr': tiny_downscaled_pr,
            'downscaled_pr_packed': tiny_downscaled_pr_packed,
            'hydromodel_gcm': tiny_hydromodel_gcm,
        }[code]
    return get


@fixture(scope='session')
def input_file(request, get_input_file):
    """Returns one of the input files, based on the request param.

    request.param: (str) selects the input file to be processed by create_climo_files
    returns: (nchelpers.CFDataset) input file to be processed by create_climo_files
    This fixture should be invoked with indirection.
    """
    return get_input_file(request.param)


@fixture(scope='function')
def outdir(tmpdir_factory):
    return str(tmpdir_factory.mktemp('outdir'))


@fixture(scope='function')
def climo_files(request, outdir, get_input_file):
    """Returns the result of create_climo_files applied to values specified by request param tuple.

    request.param: (tuple): (code, t_start, t_end, options)
        code: (str) code for selecting input file, which is passed as first param to create_climo_files
        t_start: (datetime.datetime) start date of climo period
        t_end: (datetime.datetime) end date of climo period
        options: (dict) keyword args for create_climo_files
    returns: (list) result of invoking create_climo_files: list of output filepaths

    Output files are placed in a temporary directory created by the fixture outdir.
    This fixture should be invoked with indirection.
    """
    # print('\nclimo_files: SETUP')
    code, t_start, t_end, options = request.param
    yield create_climo_files(outdir, get_input_file(code), t_start, t_end, **options)
    # print('\nclimo_files: TEARDOWN')


@fixture(scope='function') # scope?
def input_and_climo_files(request, outdir, get_input_file):
    """Returns the input file and the result of create_climo_files applied to values specified by reequest param tuple.
    This fixture simplifies the parameterization of many tests.
    See fixtures input_file and climo_files for details each component returned.
    This fixture should be invoked with indirection.
    """
    # print('\input_and_climo_files: SETUP')
    code, t_start, t_end, options = request.param
    yield get_input_file(code),\
          create_climo_files(outdir, get_input_file(code), t_start, t_end, **options)
    # print('\input_and_climo_files: TEARDOWN')
