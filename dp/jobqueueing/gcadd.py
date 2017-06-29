from argparse import ArgumentParser
import logging
import datetime
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import \
    add_global_arguments, add_generate_climos_arguments, add_pbs_arguments, add_ext_submit_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def add_to_generate_climos_queue(session, args):
    entry_args = dict(
        input_filepath=args.input_filepath,
        output_directory=args.output_directory,
        convert_longitude=args.convert_longitudes,
        split_vars=args.split_vars,
        split_intervals=args.split_intervals,
        ppn=args.ppn,
        walltime=args.walltime,
        added_time=datetime.datetime.now(),
    )
    if args.submitted:
        entry_args.update(
            status='SUBMITTED',
            submitted_time=args.submitted,
            pbs_job_id=args.pbs_job_id,
        )
    else:
        entry_args.update(status='NEW')

    session.add(GenerateClimosQueueEntry(**entry_args))
    session.commit()


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    add_to_generate_climos_queue(session, args)


if __name__ == '__main__':
    parser = ArgumentParser(description='Queue a file for processing with generate_climos')
    add_global_arguments(parser)
    add_generate_climos_arguments(parser)
    add_pbs_arguments(parser)
    add_ext_submit_arguments(parser)

    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel input_filepath output_directory convert_longitudes split_vars split_intervals ppn walltime submitted'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    main(args)
    sys.exit()