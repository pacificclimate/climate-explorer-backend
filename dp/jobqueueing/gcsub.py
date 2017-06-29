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
from dp.jobqueueing.argparse_helpers import add_global_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def make_qsub_script(queue_entry):
    return '''
#PBS -l nodes=1:ppn={queue_entry.ppn}
#PBS -l vmem={vmem}mb
#PBS -l walltime={queue_entry.walltime}
#PBS -o {queue_entry.output_directory}
#PBS -e {queue_entry.output_directory}
#PBS -m abe
#PBS -N generate_climos:{input_filename}
#PBS -d /storage/home/rglover/code/climate-explorer-backend

pbs_job_num=$(expr match "$PBS_JOBID" '([0-9]*)')

# Set up the execution environment
module load netcdf-bin
module load cdo-bin
source py3.4/bin/activate

# Copy NetCDF file to $TMPDIR/climo/input
indir=$TMPDIR/climo/input
mkdir -p $indir && cp {queue_entry.input_filepath} $indir
infile=$indir/{input_filename}

# Output directory is automatically created by generate_climos
baseoutdir=$TMPDIR/climo/output
outdir=$baseoutdir/$pbs_job_num

# Generate climo means
python dp/generate_climos.py -o $outdir $infile

# Copy result file to final destination and remove temporary input file
# Since output files are small, we're not removing them here.
rsync -r $baseoutdir {queue_entry.output_directory}
rm $infile
            '''.format(queue_entry=queue_entry,
                       input_filename=os.path.basename(queue_entry.input_filepath),
                       vmem=queue_entry.ppn * 12000)


def submit_generate_climos_pbs_jobs(session, args):
    entries = session.query(GenerateClimosQueueEntry)\
        .filter(GenerateClimosQueueEntry.status == 'NEW')\
        .order_by(asc(GenerateClimosQueueEntry.added_time))\
        .limit(args.number)\
        .all()

    for entry in entries:
        qsub = Popen(['qsub'], stdin=PIPE, stdout=PIPE)
        pbs_job_id, error = qsub.communicate(input=make_qsub_script(entry).encode('utf-8'))
        if error:
            entry.status = 'ERROR'
            logger.error('qsub failed: {}'.format(error))
        else:
            entry.status = 'SUBMITTED'
            entry.submitted_time = datetime.datetime.now()
            entry.pbs_job_id = pbs_job_id.decode('utf-8')

    session.commit()


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    submit_generate_climos_pbs_jobs(session, args)


if __name__ == '__main__':
    parser = ArgumentParser(description='Submit file(s) from generate_climos queue to PBS jobs queue')
    add_global_arguments(parser)

    group = parser.add_argument_group('Submission arguments')
    group.add_argument('-n', '--number', type=int, dest='number', default=1,
                       help='Number of files to submit')


    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel number'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    main(args)
    sys.exit()