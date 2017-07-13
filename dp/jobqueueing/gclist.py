#!python
"""
Script to list entries in the `generate_climos` queue.
"""

from argparse import ArgumentParser
import logging
import sys
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments, add_listing_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def list_entries(
        session,
        input_filepath=None, pbs_job_id=None, status=None, full=None
):
    """
    List entries in generate_climos queue.

    :param session: database session
    :param input_filepath (str): list only entries with input_filepath that
        partially matches this value
    :param pbs_job_id (str): list only entries with PBS job id that
        partially matches this value
    :param status (str): list only entries with status that
        exactly matches this value
    :param full (bool): If True, generate full listing with all parameters
        for each entry. Otherwise generate compact listing.
    :return:
    """
    q = session.query(GenerateClimosQueueEntry)\
        .order_by(GenerateClimosQueueEntry.added_time)
    if input_filepath:
        q = q.filter(GenerateClimosQueueEntry.input_filepath
                     .like('%{}%'.format(input_filepath)))
    if pbs_job_id:
        q = q.filter(GenerateClimosQueueEntry.pbs_job_id
                     .like('%{}%'.format(pbs_job_id)))
    if status:
        q = q.filter(GenerateClimosQueueEntry.status == status)
    entries = q.all()

    if full:
        for entry in entries:
            print('{}:'.format(entry.input_filepath))
            for attr in '''
                    py_venv
                    output_directory
                    convert_longitudes
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
    else:
        title_fmt = ('  {:<16.16}'
                     ' | {:<9.9}'
                     ' | {:<16.16}'
                     ' | {:<4.4}'
                     ' | {:<16.16}'
                     ' | {:<16.16}')
        print(title_fmt.format(
            'Added time', 'Status', 'Submitted time', 'JID',
            'Started time', 'Completed time'
        ))
        print(title_fmt.format(*(('-'*100,) * 20)))
        for entry in entries:
            print('{}:'.format(os.path.basename(entry.input_filepath)))
            e = {name: getattr(entry, name)
                 for name in ('added_time',
                              'status',
                              'submitted_time',
                              'pbs_job_id',
                              'started_time',
                              'completed_time'
                             )}
            print("  {e[added_time]!s:.16}"
                  " | {e[status]:<9}"
                  " | {e[submitted_time]!s:<16.16}"
                  " | {e[pbs_job_id]!s:4.4}"
                  " | {e[started_time]!s:<16.16}"
                  " | {e[completed_time]!s:<16.16}"
                  .format(e={key: value if value else '--'
                           for key, value in e.items()}))



def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    list_entries(session,
                 **{key: getattr(args, key, None)
                    for key in 'input_filepath pbs_job_id status full'.split()})


if __name__ == '__main__':
    parser = ArgumentParser(description='List entries in generate_climos queue')
    add_global_arguments(parser)
    add_listing_arguments(parser)

    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    main(args)
    sys.exit()
