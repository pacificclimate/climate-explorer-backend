#!python
"""
Script to update the status of entries in generate climos queue using `qstat`.

`qstat` is called for each submitted job in the queue, and the result is used to
update the queue entry for that job.
"""

from argparse import ArgumentParser
import logging
import re
import sys
from subprocess import Popen, PIPE

from dateutil import parser as dateparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def qstat_to_yaml(string):
    """Convert the output of `qstat -f -1` to a YAML-compliant string so it
    can easily be parsed. """
    job_id_re = re.compile(r'^Job Id: (.*)$', re.MULTILINE)
    string = job_id_re.sub(r'-\n    pbs_job_id: \1', string)
    key_val_re = re.compile(r' = ', re.MULTILINE)
    string = key_val_re.sub(r': ', string)
    return string


def update_from_qstat_item(session, entry, qstat_item):
    """
    Update the status of entries in generate climos queue from output of a
    'qstat` command for a single PBS job.

    :param session: database session
    :param entry: queue entry to be updated
    :param qstat_item: dict encoding the output of a 'qstat` command for a
        single PBS job
    :return: None
    """
    logger.info('Updating {}'.format(entry.pbs_job_id))
    start_time = qstat_item.get('start_time', None)
    if start_time and entry.status == 'SUBMITTED':
        logger.info('Sub -> Run')
        entry.status = 'RUNNING'
        entry.started_time = dateparser.parse(start_time)

    comp_time = qstat_item.get('comp_time', None)
    if comp_time and entry.status == 'RUNNING':
        logger.info('Run -> Succ')
        entry.status = 'SUCCESS'
        entry.completed_time = dateparser.parse(comp_time)
        entry.completion_message = \
            yaml.dump(qstat_item, default_flow_style=False)

    session.commit()


def update(session):
    """
    Update the status of entries in generate climos queue using `qstat`.

    :param session: database session
    :return: None
    """
    entries = (
        session.query(GenerateClimosQueueEntry)
        .filter(GenerateClimosQueueEntry.status.in_(['SUBMITTED', 'RUNNING']))
        .all()
    )
    for entry in entries:
        qstat = Popen(['qstat', '-f', '-1', entry.pbs_job_id], stdout=PIPE)
        stdout, stderr = qstat.communicate()
        qstat_item = yaml.load(qstat_to_yaml(stdout.decode('utf-8')))[0]
        update_from_qstat_item(session, entry, qstat_item)


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    update(session)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Update generate_climos queue using PBS status email')
    add_global_arguments(parser)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    exit_status = main(args)
    sys.exit(exit_status)
