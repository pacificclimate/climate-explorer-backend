"""
Script to list entries in the `generate_climos` queue.
"""

from argparse import ArgumentParser
import logging
import datetime
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def list_entries(session, args):
    entries = session.query(GenerateClimosQueueEntry)\
        .order_by(GenerateClimosQueueEntry.added_time)\
        .all()
    for entry in entries:
        print('{}:'.format(entry.input_filepath))
        for attr in '''
                output_directory
                convert_longitude
                split_vars
                split_intervals
                ppn
                walltime
                status
                added_time
                submitted_time
                pbs_job_id
                started_time
                completed_time
                completion_message
                '''.split():
            print('    {} = {}'.format(attr, getattr(entry, attr)))


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    list_entries(session, args)


if __name__ == '__main__':
    parser = ArgumentParser(description='Queue a file for processing with generate_climos')
    add_global_arguments(parser)

    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    main(args)
    sys.exit()
