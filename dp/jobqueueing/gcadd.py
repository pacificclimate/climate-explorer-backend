#!python
"""
Script to add an entry to a `generate_climos` queue, which is to say to add a
record to a `GenerateClimosQueueEntry` in a database.

Such a record denotes a file queued for processing with `generate_climos`
via PBS `qsub`. The record includes `generate_climos` arguments and arguments
for `qsub`.

Normally, a queue entry is designated 'NEW' (not yet submitted), and will be
changed to 'SUBMITTED' by use of the gcsub.py script, which performs an actual
PBS `qsub` based on the queue entry (modifying it accordingly).

However, a queue entry after a PBS job has been submitted via some external
(to this database) process. In that case, the submission date and the PBS job
id can be supplied manually through command-line args.
See script help for details.

To ease adding files from a changing directory, a new entry is created only
if there is no entry with the same input filepath. This can be overridden
with the `-f --force` option.
"""

from argparse import ArgumentParser
import logging
import datetime
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import \
    add_global_arguments, add_gcadd_arguments, \
    add_execution_environment_arguments, \
    add_generate_climos_arguments, add_pbs_arguments, add_ext_submit_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def add_to_generate_climos_queue(
        session,
        input_filepath=None,
        py_venv=None,
        output_directory=None,
        convert_longitudes=None,
        split_vars=None,
        split_intervals=None,
        ppn=None,
        walltime=None,
        submitted=None,
        pbs_job_id=None,
        force=None
):
    """
    Add an entry to a `generate_climos` queue.

    :param session: database session
    :param input_filepath (str): filepath of file to be queued
    :param py_venv (str): path to root of Python virtual environment in which
        generate_climos and its dependencies are installed
    :param output_directory (str): directory for output from generate_climos
        (-o/--output param)
    :param convert_longitudes (bool): generate_climos parameter
    :param split_vars (bool): generate_climos parameter
    :param split_intervals (bool): generate_climos parameter
    :param ppn (str): PBS job parameter (processors per node)
    :param walltime (str): PBS job parmeter (maximum elapsed run time)
    :param submitted (str, parseable as a date/time):
        For normal queueing of files to be later submitted using this toolset,
        value is None.
        For jobs submitted to PBS outside this toolset,
        value is the date/time that the job was submitted.
        If not None, `pbs_job_id` must also be non-None
    :param pbs_job_id (str):
        For normal queueing of files to be later submitted using this toolset,
        value is None.
        For jobs submitted to PBS outside this toolset,
        value is PBS job id of submitted job.
        If not None, `submitted` must also be non-None
    :param force (bool):
    :return: None
    """
    entry = (
        session.query(GenerateClimosQueueEntry)
        .filter(GenerateClimosQueueEntry.input_filepath == input_filepath)
        .first()
    )
    if entry and not force:
        logger.info('Skipping file {}: already in queue'
                    .format(input_filepath))
        return

    entry_args = dict(
        input_filepath=input_filepath,
        py_venv=py_venv,
        output_directory=output_directory,
        convert_longitudes=convert_longitudes,
        split_vars=split_vars,
        split_intervals=split_intervals,
        ppn=ppn,
        walltime=walltime,
        added_time=datetime.datetime.now(),
        status='NEW',
    )
    if submitted and pbs_job_id:
        entry_args.update(
            status='SUBMITTED',
            submitted_time=submitted,
            pbs_job_id=pbs_job_id,
        )

    session.add(GenerateClimosQueueEntry(**entry_args))
    session.commit()


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    add_to_generate_climos_queue(
        session,
        **{key: getattr(args, key)
           for key in '''
            input_filepath
            py_venv
            output_directory
            convert_longitudes
            split_vars
            split_intervals
            ppn
            walltime
            submitted
            pbs_job_id
            force
            '''.split()}
    )


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Queue a file for processing with generate_climos')
    add_global_arguments(parser)
    add_gcadd_arguments(parser)
    add_execution_environment_arguments(parser)
    add_generate_climos_arguments(parser)
    add_pbs_arguments(parser)
    add_ext_submit_arguments(parser)

    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in '''
            database
            loglevel
            input_filepath
            py_venv
            output_directory
            convert_longitudes
            split_vars
            split_intervals
            ppn
            walltime
            submitted
            '''.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    main(args)
    sys.exit()
