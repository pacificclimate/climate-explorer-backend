from pytest import fixture, mark
from pkg_resources import resource_filename
from nchelpers import CFDataset
from dp.generate_climos import create_climo_files


@fixture
def tiny_dataset(request):
    return CFDataset(resource_filename('dp', 'tests/data/tiny_{}.nc').format(request.param))


@fixture(scope='function')
def outdir(tmpdir_factory):
    return str(tmpdir_factory.mktemp('outdir'))
