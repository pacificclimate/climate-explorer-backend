"""
Script to alter generate_climos params and PBS params of queue entries.
Altered entry must be in status NEW.
"""

from argparse import ArgumentParser
import logging
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.argparse_helpers import add_global_arguments, add_generate_climos_arguments, add_pbs_arguments
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


logger = default_logger()


def update_generate_climos_queue_entries_with_params(session, args):
    entries = session.query(GenerateClimosQueueEntry)\
        .filter(GenerateClimosQueueEntry.status == 'NEW')\
        .all()

    def args_to_entry(attr):
        """Oh for *#@%* sake. Oughta migrate the database but SQLite doesn't rename columns easily.
        Alembic can do it with extra effort but this is faster."""
        if attr == 'convert_longitudes':
            return 'convert_longitude'
        return attr

    updatable_attributes = 'output_directory convert_longitudes split_vars split_intervals ppn walltime'.split()
    for entry in entries:
        if args.input_filepath in entry.input_filepath:
            for attr in updatable_attributes:
                update_value = getattr(args, attr, None)
                if update_value is not None:
                    logger.debug('Updating {} to {}'.format(attr, update_value))
                    setattr(entry, args_to_entry(attr), update_value)

    session.commit()
    return 0


def main(args):
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    update_generate_climos_queue_entries_with_params(session, args)


if __name__ == '__main__':
    parser = ArgumentParser(description='''Update entries with generate_climos params and PBS params (but not status).
    Updated entry must be in status NEW.
    WARNING: ANY entry that partially matches the input filename is updated.''')
    add_global_arguments(parser)
    add_generate_climos_arguments(parser, o_required=False, flag_default=None)
    add_pbs_arguments(parser, ppn_default=None, walltime_default=None)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))

    for k in 'database loglevel ' \
             'input_filepath output_directory convert_longitudes split_vars split_intervals ' \
             'ppn walltime'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))

    exit_status = main(args)
    sys.exit(exit_status)
