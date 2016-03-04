import os, os.path
import re
import logging
import sys

from argparse import ArgumentParser
from datetime import datetime
from tempfile import NamedTemporaryFile

import numpy as np

from cdo import Cdo
from netCDF4 import Dataset, num2date, date2num
from dateutil.relativedelta import relativedelta

from Cmip5File import Cmip5File, ClimdexFile

def s2d(s):
    return datetime.strptime(s, '%Y-%m-%d')

def ss2d(s):
    return datetime.strptime(s, '%Y%m%d')

def d2s(d):
    return datetime.strftime(d, '%Y-%m-%d')

def d2ss(d):
    return datetime.strftime(d, '%Y%m%d')

# def ncd2s(d):
#     '''
#     Same as d2s function, but converts netcdftime._datetime.datetime to string
#     due to python datetime's inability to handle dates before year 1900
#     '''
    

# def ncs2d(s):
#        '''
#     Same as ss2d function, except avoids use of datetime due to its
#     inability to handle dates before year 1900
#     '''
#     return datetime.strptime(str(d.year)+'-'+str(d.month)+'-'+str(d.day), '%Y-%m-%d')

def iter_matching(dirpath, regexp):
    # http://stackoverflow.com/questions/4639506/os-walk-with-regex
    """Generator yielding all files under `dirpath` whose absolute path
       matches the regular expression `regexp`.
       Usage:

           >>> for filename in iter_matching('/', r'/home.*\.bak'):
           ....    # do something
    """
    for dir_, dirnames, filenames in os.walk(dirpath):
        for filename in filenames:
            abspath = os.path.join(dir_, filename)
            if regexp.match(abspath):
                yield abspath

def create_annual_average_file(fp_in, fp_out, variable):
    '''
    Generates file with annual averages for the given variable across all time within an input file

    Paramenters:
        f_in: input file path
        f_out: output file path
        variable (str): name of the variable which is being processed

    '''
    supported_vars = {
        'cddETCCDI', 'csdiETCCDI', 'cwdETCCDI', 'dtrETCCDI', 'fdETCCDI',
        'gslETCCDI', 'idETCCDI', 'prcptotETCCDI', 'r10mmETCCDI', 'r1mmETCCDI',
        'r20mmETCCDI', 'r95pETCCDI', 'r99pETCCDI', 'rx1dayETCCDI',
        'rx5dayETCCDI', 'sdiiETCCDI', 'suETCCDI', 'thresholds', 'tn10pETCCDI',
        'tn90pETCCDI', 'tnnETCCDI', 'tnxETCCDI', 'trETCCDI', 'tx10pETCCDI',
        'tx90pETCCDI', 'txnETCCDI', 'txxETCCDI', 'wsdiETCCDI', 'tasmin',
        'tasmax', 'pr'
    }

    if variable not in supported_vars:
        raise Exception("Unsupported variable: cant't yet process {}".format(variable))

    if not os.path.exists(os.path.dirname(fp_out)):
        os.makedirs(os.path.dirname(fp_out))

    cdo = Cdo()
    cdo.yearmean(input=fp_in, output=fp_out)


def main(args):
    vars = '|'.join(args.variables)
    test_files = iter_matching(args.basedir, re.compile('.*({}).*(_rcp26|_rcp45|_rcp85|_historical_).*r1i1p1.*nc'.format(vars)))

    if args.dry_run:
        for f in test_files:
            print(f)
        sys.exit(0)

    FileType = ClimdexFile if args.climdex else Cmip5File

    for fp in test_files:
        # log.info(fp)
        
        file_ = FileType(fp)
        file_.freq ='yr'
        file_.root = args.outdir
        variable = file_.variable

        # calculate annual averages for all years in the file and store in a new NetCDF 
        out_fp = file_.fullpath
        # log.info('Output file: {}'.format(out_fp))
        print('Output file: {}'.format(out_fp))

        create_annual_average_file(fp, out_fp, variable)

        # TODO: open up generated yearmean NC file and modify metadata (long_name, frequency...any others?)
        # nc = Dataset(out_fp)
        # modify metadata here
        # nc.close()

if __name__ == '__main__':
    parser = ArgumentParser(description='Create annual averages from CMIP5 data')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    parser.add_argument('-b', '--basedir', help='Root directory from which to search for climate model output')
    parser.add_argument('-v', '--variables', nargs='+', help='Variables to include')
    parser.add_argument('-C', '--climdex', action='store_true')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true')
    parser.set_defaults(
        variables=['tasmin', 'tasmax'],
        basedir='/home/data/climate/CMIP5/CCCMA/CanESM2/',
        climdex=False,
        dry_run=False
    )
    args = parser.parse_args()
    main(args)
