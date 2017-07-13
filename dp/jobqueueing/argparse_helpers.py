"""
Helpers for setting up argument parsing for jobqueueing
"""
import os
from argparse import ArgumentTypeError
import re

from dateutil import parser as dateparser

from dp.jobqueueing.jobqueueing_db import gcq_statuses
from dp.argparse_helpers import log_level_choices, strtobool


def walltime(string):
    if not re.match(r'(\d{1,2}:)?(\d{2}:)*\d{2}', string):
        raise ArgumentTypeError("'{}' is not a valid walltime value")
    return string


def add_global_arguments(parser):
    group = parser.add_argument_group('Global arguments')
    GCQ_DATABASE = os.environ.get('GCQ_DATABASE', None)
    group.add_argument(
        '-d', '--database',
        required=not bool(GCQ_DATABASE),
        default=GCQ_DATABASE,
        help='Filepath to queue management database.'
             'Defaults to value of environment variable GCQ_DATABASE. '
             'You must either define the env var or set the value of this '
             'option in the command line.',
    )
    group.add_argument(
        '-L', '--loglevel', help='Logging level',
                       choices=log_level_choices, default='INFO')
    return group


def add_gcadd_arguments(parser):
    group = parser.add_argument_group('Add arguments')
    group.add_argument(
        '-f', '--force', action='store_true',
        help='Force addition of a new queue entry even if one for this '
             'input filename already exists')
    return group


def add_execution_environment_arguments(parser, required=True):
    group = parser.add_argument_group('Execution environment arguments')
    GCQ_PY_VENV = os.environ.get('GCQ_PY_VENV', None)
    group.add_argument(
        '-P', '--py-venv', dest='py_venv',
        required=required and not bool(GCQ_PY_VENV),
        default=GCQ_PY_VENV,
        help='Path to Python virtual env containing scripts. ' +
             ('Defaults to value of environment variable GCQ_PY_VENV. '
             'You must either define the env var or set the value of this '
             'option in the command line.' if required else '')
    )
    return group


def add_generate_climos_arguments(parser, o_required=True, flag_default=True):
    group = parser.add_argument_group('generate_climos arguments')
    group.add_argument(
        'input_filepath', help='File to queue')
    group.add_argument(
        '-o', '--output-directory',
        required=o_required, dest='output_directory',
        help='Path to directory where output files will be placed')
    group.add_argument(
        '-g', '--convert-longitudes', type=strtobool,
        dest='convert_longitudes', default=flag_default,
        help='Transform longitude range from [0, 360) to [-180, 180)')
    group.add_argument(
        '-v', '--split-vars', type=strtobool,
        dest='split_vars', default=flag_default,
        help='Generate a separate file for each dependent variable in the file')
    group.add_argument(
        '-i', '--split-intervals', type=strtobool,
        dest='split_intervals', default=flag_default,
        help='Generate a separate file for each climatological period')
    return group


def add_pbs_arguments(parser, ppn_default=1, walltime_default='10:00:00'):
    group = parser.add_argument_group('PBS arguments')
    group.add_argument(
        '-p', '--ppn', type=int,
        dest='ppn', default=ppn_default,
        help='Processes per node')
    group.add_argument(
        '-w', '--walltime', type=str,
        dest='walltime', default=walltime_default,
        help='Maximum wall time')
    return group


def add_submit_arguments(parser):
    group = parser.add_argument_group('Submit arguments')
    group.add_argument(
        '-n', '--number', type=int, dest='number', default=1,
        help='Number of files to submit')
    return group


def add_ext_submit_arguments(parser):
    group = parser.add_argument_group('External submission arguments')
    group.add_argument(
        '-s', '--submitted', type=dateparser.parse,
        help='Date/time that job was submitted to PBS without use of gcsub')
    group.add_argument(
        '-j', '--job-id', dest='pbs_job_id', type=str,
        help='PBS job id of submission')
    return group


def add_listing_arguments(parser):
    group = parser.add_argument_group('Listing control arguments')
    group.add_argument(
        '-f', '--full', action='store_true',
        help='Display full listing')
    group.add_argument(
        '-i', '--input-filepath', dest='input_filepath',
        help='Input filepath (partial match)')
    group.add_argument(
        '-j', '--job-id', dest='pbs_job_id', type=str,
        help='PBS job id of submission')
    group.add_argument(
        '-s', '--status', help='Status of queue entry',
        choices=gcq_statuses)
    return group


def add_reset_arguments(parser):
    group = parser.add_argument_group('Reset arguments')
    group.add_argument(
        'input_filepath', help='Input filepath (full match)')
    group.add_argument(
        '-s', '--status', help='Status of queue entry',
        choices=gcq_statuses, default='NEW')
    return group
