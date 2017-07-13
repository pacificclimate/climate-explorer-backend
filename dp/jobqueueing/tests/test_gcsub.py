import datetime

import pytest

from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry
from dp.jobqueueing.gcsub import make_qsub_script, make_qsub_test_script


@pytest.mark.parametrize('make_script', [make_qsub_script, make_qsub_test_script])
def test_make_qsub_script(make_script):
    entry = GenerateClimosQueueEntry(
        input_filepath='/input/directory/file.nc',
        py_venv='/path/to/venv',
        output_directory='/output/directory',
        convert_longitudes=False,
        split_vars=True,
        split_intervals=True,
        ppn=1,
        walltime='01:23:45',
        added_time=datetime.datetime(2000, 1, 2, 3, 4, 5),
        status='NEW',
    )
    script = make_script(entry)
    assert '#PBS -l nodes=1:ppn=1' in script
    assert '#PBS -l vmem=12000mb' in script
    assert '#PBS -l walltime=01:23:45'
    assert '#PBS -o /output/directory/logs' in script
    assert '#PBS -e /output/directory/logs' in script
    assert '#PBS -N generate_climos:file.nc' in script
    assert 'source /path/to/venv/bin/activate' in script
    assert 'cp /input/directory/file.nc' in script
    assert 'infile=$indir/file.nc' in script
    assert 'generate_climos.py -g False -v True -i True -o $outdir $infile' in script
    assert 'rsync -r $baseoutdir /output/directory' in script