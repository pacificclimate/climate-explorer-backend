from argparse import ArgumentParser, ArgumentTypeError
import logging
import re
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dp.script_helpers import default_logger
from dp.jobqueueing.jobqueueing_db import GenerateClimosQueueEntry


# Set up logging
logger = default_logger()
log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()


def add_to_generate_climos_queue(session, args):
    session.add(GenerateClimosQueueEntry(
        input_filepath=args.input_filepath,
        output_directory=args.output_directory,
        convert_longitude=args.convert_longitudes,
        split_vars=args.split_vars,
        split_intervals=args.split_intervals,
        ppn=args.ppn,
        walltime=args.walltime,
        added_time=datetime.datetime.now(),
        status='NEW',
    ))
    session.commit()


def main(args):
    for k in 'database loglevel input_filepath output_directory convert_longitudes split_vars split_intervals ppn walltime'.split():
        logger.debug('{}: {}'.format(k, getattr(args, k)))
    dsn = 'sqlite+pysqlite:///{}'.format(args.database)
    engine = create_engine(dsn)
    session = sessionmaker(bind=engine)()

    add_to_generate_climos_queue(session, args)


if __name__ == '__main__':
    def strtobool(string):
        return string.lower() in {'true', 't', 'yes', '1'}

    def walltime(string):
        if not re.match(r'(\d{1,2}:)?(\d{2}:)*\d{2}', string):
            raise ArgumentTypeError("'{}' is not a valid walltime value")
        return string

    parser = ArgumentParser(description='Queue a file for processing with generate_climos')

    # Global arguments
    group = parser.add_argument_group('Global arguments')
    group.add_argument('-d', '--database', help='Filepath to queue management database',
                       # FIXME: Set up a prod database on /storage
                       default='/home/rglover/code/climate-explorer-backend/dp/jobqueueing/jobqueueing.sqlite')
    group.add_argument('-L', '--loglevel', help='Logging level',
                        choices=log_level_choices, default='INFO')

    # generate_climos arguments
    group = parser.add_argument_group('generate_climos arguments')
    group.add_argument('input_filepath', help='File to queue')
    group.add_argument('-o', '--output-directory', required=True, dest='output_directory',
                       help='Path to directory where output files will be placed')
    group.add_argument('-g', '--convert-longitudes', type=strtobool, dest='convert_longitudes', default=True,
                       help='Transform longitude range from [0, 360) to [-180, 180)')
    group.add_argument('-v', '--split-vars', type=strtobool, dest='split_vars', default=True,
                       help='Generate a separate file for each dependent variable in the file')
    group.add_argument('-i', '--split-intervals', type=strtobool, dest='split_intervals', default=True,
                       help='Generate a separate file for each climatological period')

    # PBS arguments
    group = parser.add_argument_group('PBS arguments')

    group.add_argument('-p', '--ppn', type=int, dest='ppn', default=1,
                        help='Processes per node')
    group.add_argument('-w', '--walltime', type=str, dest='walltime', default='10:00:00',
                        help='Maximum wall time')

    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))
    main(args)
