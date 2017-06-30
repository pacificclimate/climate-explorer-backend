"""
Script to update the status of a queue entry.
"""

from argparse import ArgumentParser
import logging
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments, add_reset_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry
from dp.jobqueueing.argparse_helpers import status_choices


logger = default_logger()


def reset_generate_climos_queue_entry(session, args):
    entry = session.query(GenerateClimosQueueEntry)\
        .filter(GenerateClimosQueueEntry.input_filepath == args.input_filepath)\
        .first()

    if not entry:
        logger.error('Could not find generate_climos queue entry matching input file {}. Skipping.'
                     .format(args.input_filepath))
        return 1

    def single_step_to(status, entry):
        """Single-step reset to `status` from next later status."""
        logger.debug('Stepping from status {} to {}'.format(entry.status, status))
        if status == 'NEW':
            assert entry.status == 'SUBMITTED'
            entry.status = 'NEW'
            entry.submitted_time = None
            entry.pbs_job_id = None

        elif status == 'SUBMITTED':
            assert entry.status == 'RUNNING'
            entry.status = 'SUBMITTED'
            entry.started_time = None

        elif status == 'RUNNING':
            assert entry.status in {'SUCCESS', 'ERROR'}
            entry.status = 'RUNNING'
            entry.completed_time = None
            entry.completion_message = None

        else:
            raise ValueError

    rev_statuses = list(reversed(status_choices))
    from_i = rev_statuses.index(entry.status)
    to_i = rev_statuses.index(args.status)
    if to_i <= from_i:
        logger.error('Cannot reset status from {} to {}'.format(entry.status, args.status))
        return 1
    # Iterate through statuses in reverse order from predecessor of `entry.status` to `arg.status`.
    # Example: for an entry in SUCCESS status, iterate from RUNNING to NEW.
    for i, status in enumerate(rev_statuses):
        if from_i < i <= to_i:
            try:
                single_step_to(status, entry)
            except ValueError:
                logger.error('Cannot reset status from {} to {}'.format(entry.status, args.status))
                return 1
            except AssertionError:
                logger.error('Cannot step from status {} to {}'.format(entry.status, status))
                return 1

    session.commit()
    return 0


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    reset_generate_climos_queue_entry(session, args)


if __name__ == '__main__':
    parser = ArgumentParser(description='Update generate_climos queue using PBS status email')
    add_global_arguments(parser)
    add_reset_arguments(parser)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    exit_status = main(args)
    sys.exit(exit_status)
