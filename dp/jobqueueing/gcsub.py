#!python
"""
Script to dequeue one or more generate_climos queue entries with NEW status,
and submit a PBS job for each, updating the queue entries accordingly.

Entries are dequeued in order of addition to the database (column added_time);
i.e., it is a FIFO queue.
"""

from argparse import ArgumentParser
import datetime
import logging
import os.path
import sys
from subprocess import Popen, PIPE

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import asc

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments, add_submit_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def make_qsub_test_script(queue_entry):
    return '''
#PBS -l nodes=1:ppn={qe.ppn}
#PBS -l vmem={vmem}mb
#PBS -l walltime={qe.walltime}
#PBS -o {qe.output_directory}/logs
#PBS -e {qe.output_directory}/logs
#PBS -m abe
#PBS -N generate_climos:{input_filename}

pbs_job_num=$(expr match "$PBS_JOBID" '\([0-9]*\)')

# Set up the execution environment
module load netcdf-bin
module load cdo-bin
module list
source {qe.py_venv}/bin/activate
which python

# Copy NetCDF file to $TMPDIR/climo/input
indir=$TMPDIR/climo/input
echo mkdir -p $indir && cp {qe.input_filepath} $indir
infile=$indir/{input_filename}
echo infile = $infile

# Output directory is automatically created by generate_climos
baseoutdir=$TMPDIR/climo/output
echo baseoutdir = $baseoutdir
outdir=$baseoutdir/$pbs_job_num
echo outdir = $outdir

# Generate climo means
echo generate_climos.py -g {qe.convert_longitudes} -v {qe.split_vars} -i {qe.split_intervals} -o $outdir $infile

# Copy result file to final destination and remove temporary input file
# Since output files are small, we're not removing them here.
echo rsync -r $baseoutdir {qe.output_directory}
echo rm $infile
            '''.format(qe=queue_entry,
                       input_filename=os.path.basename(
                           queue_entry.input_filepath),
                       vmem=queue_entry.ppn * 12000)


def make_qsub_script(queue_entry):
    return '''
#PBS -l nodes=1:ppn={qe.ppn}
#PBS -l vmem={vmem}mb
#PBS -l walltime={qe.walltime}
#PBS -o {qe.output_directory}/logs
#PBS -e {qe.output_directory}/logs
#PBS -m abe
#PBS -N generate_climos:{input_filename}
set -o verbose

pbs_job_num=$(expr match "$PBS_JOBID" '\([0-9]*\)')
echo pbs_job_num = $pbs_job_num

# Set up the execution environment
module load netcdf-bin
module load cdo-bin
module list
source {qe.py_venv}/bin/activate
which python

# Copy NetCDF file to $TMPDIR/climo/input
indir=$TMPDIR/climo/input
echo indir = $indir
mkdir -p $indir && cp {qe.input_filepath} $indir
ls $indir
infile=$indir/{input_filename}
echo infile = $infile

# Output directory is automatically created by generate_climos
baseoutdir=$TMPDIR/climo/output
echo baseoutdir = $baseoutdir
outdir=$baseoutdir/$pbs_job_num
echo outdir = $outdir

# Generate climo means
generate_climos.py -g {qe.convert_longitudes} -v {qe.split_vars} -i {qe.split_intervals} -o $outdir $infile
ls $outdir

# Copy result file to final destination and remove temporary input file
# Since output files are small, we're not removing them here.
rsync -r $baseoutdir {qe.output_directory}
ls $baseoutdir
rm $infile
            '''.format(qe=queue_entry,
                       input_filename=os.path.basename(
                           queue_entry.input_filepath),
                       vmem=queue_entry.ppn * 12000)


def submit_generate_climos_pbs_jobs(session, number, test_job):
    """
    Take `number` queue entries with status NEW from the front of the
    queue and submit them as PBS jobs, updating the queue entries
    accordingly.

    :param session: database session
    :param number (int): number of entries to dequeue and submit
    :param test_job (bool): If True, submit a no-work test job that
        simply echoes commands that would be executed in a real job.
        Otherwise, submit a real job.
    :return: None
    """
    entries = (
        session.query(GenerateClimosQueueEntry)
        .filter(GenerateClimosQueueEntry.status == 'NEW')
        .order_by(asc(GenerateClimosQueueEntry.added_time))
        .limit(number)
        .all()
    )

    for entry in entries:
        qsub = Popen(['qsub'], stdin=PIPE, stdout=PIPE)
        if test_job:
            input = make_qsub_test_script(entry).encode('utf-8')
        else:
            input = make_qsub_script(entry).encode('utf-8')
        pbs_job_id, error = qsub.communicate(input=input)
        if error:
            entry.status = 'ERROR'
            logger.error('qsub failed: {}'.format(error))
        else:
            entry.status = 'SUBMITTED'
            entry.submitted_time = datetime.datetime.now()
            entry.pbs_job_id = pbs_job_id.decode('utf-8').strip()
            logger.info('Submitted job: {}'.format(entry.pbs_job_id))

    session.commit()


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    submit_generate_climos_pbs_jobs(session, args.number, args.test_job)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Submit file(s) from generate_climos queue '
                    'to PBS jobs queue')
    group = add_global_arguments(parser)
    group.add_argument('--test-job', dest='test_job', action='store_true',
                       help='Submit a test job that performs no work')
    add_submit_arguments(parser)

    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel number'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    main(args)
    sys.exit()
