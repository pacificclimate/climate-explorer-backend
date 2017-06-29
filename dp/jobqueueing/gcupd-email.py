"""
Script to update the status of a queue entry based on the content of a standard status email sent by PBS.

The email is read from stdin and scanned for information that identifies the job and its status,
and the queue entry is found and updated accordingly.

WARNING: Currently this script does not enforce any ordering of begin and terminate status changes.
"""

from argparse import ArgumentParser
import datetime
import logging
import re
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def update_generate_climos_queue_from_status_email(session, status_email):
    # Extract important info from email
    pbs_job_id = action = exit_status = None
    match = re.search(r'^PBS Job Id: *(.*)$', status_email, flags=re.MULTILINE)
    if match:
        pbs_job_id = match.group(1)
    match = re.search(r'(Begun) execution|Execution (terminated)', status_email, flags=re.MULTILINE)
    if match:
        action = match.group(1) or match.group(2)
    match = re.search(r'Exit_status=(\d+)', status_email, flags=re.MULTILINE)
    if match:
        exit_status = match.group(1)

    if not pbs_job_id:
        logger.error('Could not find PBS job id in status email. Skipping.')
        return 1

    entry = session.query(GenerateClimosQueueEntry)\
        .filter(GenerateClimosQueueEntry.pbs_job_id == pbs_job_id)\
        .first()

    if not entry:
        logger.error('Could not find generate_climos queue entry corresponding to PBS job id {}. Skipping.'
                     .format(pbs_job_id))
        return 1

    if action == 'Begun':
        entry.status = 'RUNNING'
        entry.started_time = datetime.datetime.now()

    elif action == 'terminated':
        if not exit_status:
            logger.error('Could not determine PBS job exit status from status email. Skipping.')
            return 1

        if exit_status == '0':
            entry.status = 'SUCCESS'
        else:
            entry.status = 'ERROR'
        entry.completed_time = datetime.datetime.now()
        entry.completion_message = status_email

    else:
        logger.error('Could not determine action (begin, terminate) from status email. Skipping.')
        return 1

    session.commit()
    return 0


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    update_generate_climos_queue_from_status_email(session, '\n'.join(sys.stdin))


if __name__ == '__main__':
    parser = ArgumentParser(description='Update generate_climos queue using PBS status email')
    add_global_arguments(parser)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    exit_status = main(args)
    sys.exit(exit_status)
