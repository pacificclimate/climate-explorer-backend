import os, os.path
import re
import logging
import sys

from argparse import ArgumentParser
from datetime import datetime

from cdo import Cdo
from netCDF4 import Dataset, num2date, date2num
import numpy as np
from dateutil.relativedelta import relativedelta

from Cmip5File import Cmip5File

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=4)

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

def create_annual_avg_file(in_fp, out_fp, variable):
    '''
    Generates file with annual averages for the given variable across
    all time within an input file

    Parameters:
        in_fp: input file path
        out_fp: output file path
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
        raise Exception("Unsupported variable: can't yet process {}".format(variable))

    if not os.path.exists(os.path.dirname(out_fp)):
        os.makedirs(os.path.dirname(out_fp))

    cdo = Cdo()
    cdo.yearmean(input=in_fp, output=out_fp)

def update_annual_avg_file_global_metadata(nc):
    '''
    Modifies global metadata of generated yearmean NetCDF file
    '''
    title = nc.getncattr('title')
    new_title = 'Annual Average of Daily ' + title
    new_frequency = 'yr'
    nc.setncatts({'title': new_title, 'frequency': new_frequency})

def update_annual_avg_file_variable_metadata(nc, variable):
    '''
    Modifies metadata of one variable of generated yearmean NetCDF file
    '''
    long_name = nc.variables[variable].getncattr('long_name')
    new_long_name = 'Annual Average ' + long_name
    nc.variables[variable].setncattr('long_name', new_long_name)

def has_valid_time_bounds(bounds_var):
    '''
    Verifies if the input NetCDF has a valid, and populated, time_bnds variable
    '''
    # bounds_var might be a np.masked_array, and if any elements are masked, it's bad
    if (hasattr(bounds_var, 'mask') and (np.ma.is_masked(bounds_var[:]))):
        return False
    # or, bounds_var might be full of zeros, also bad
    elif (not np.any(bounds_var)):
        return False
    else:
        return True

def update_annual_avg_file_time_metadata(nc, start_year=None):
    '''
    Converts time values of a newly produced annual average NetCDF file
    to annual midpoints. Checks validity of the time bounds variable
    (initially set by CDO), overwriting it if necessary, and assigns
    correct units and calendar attributes.

    time values are the calculated midpoint between <year n>-01-01 and
    <year n+1>-01-01
    time bounds are <year n>-01-01 00:00:00 and <year n+1>-01-01 00:00:00

    Optional parameter: 
        start_year - set to override the time variable's start year
    '''
    time_var = nc.variables['time']
    units = time_var.units
    calendar = time_var.calendar
    new_times = []
    bounds_var = nc.variables['time_bnds']
    new_bounds = []
    write_new_bounds = False

    if start_year is None:
        start_year = num2date(time_var[0], units, calendar).year
    # we are (possibly) setting a new start_year, so units and bounds will change
    else:
        units = "days since {}-01-01 00:00:00".format(start_year)
        time_var.units = units
        write_new_bounds = True
    end_year = start_year + time_var.shape[0]

    bounds_var.units = units
    bounds_var.calendar = calendar

    if not has_valid_time_bounds(bounds_var):
        write_new_bounds = True

    for year in range(start_year, end_year):
        days_to_mid = ((datetime(year, 1, 1) + relativedelta(years=1)) \
            - datetime(year, 1, 1)).days/2
        mid = datetime(year, 1, 1) + relativedelta(days=days_to_mid)
        new_times.append(mid)
        if write_new_bounds:
            lower_bound = datetime(year, 1, 1)
            upper_bound = datetime(year, 1, 1) + relativedelta(years=1)
            new_bounds.append([lower_bound, upper_bound])

    time_var[:] = date2num(new_times, units, calendar)
    if write_new_bounds:
        bounds_var[:] = date2num(new_bounds, units, calendar)

def main(args):
    vars = '|'.join(args.variables)
    test_files = iter_matching(args.basedir, \
        re.compile('.*({}).*(_rcp26|_rcp45|_rcp85|_historical_).*r1i1p1.*nc'\
        .format(vars)))

    if args.dry_run:
        for f in test_files:
            print(f)
        sys.exit(0)

    for fp in test_files:
        log.info('Processing input file: {}'.format(fp))
        file_ = Cmip5File(fp, freq='yr', mip_table='yr')
        file_.root = args.outdir
        # trim time range that will appear in filename to just the years, as
        # that is the limit of resolution
        file_.t_start = file_.t_start[0:4]
        file_.t_end = file_.t_end[0:4]
        variable = file_.variable
        # calculate annual averages for all years in the file and store in a new NetCDF 
        out_fp = file_.fullpath
        log.info('Generating annual average output file: {}'.format(out_fp))
        create_annual_avg_file(fp, out_fp, variable)
        # update the metadata in the file generated by cdo.yearmean
        nc = Dataset(out_fp, 'r+')
        update_annual_avg_file_global_metadata(nc)
        update_annual_avg_file_variable_metadata(nc, variable)
        update_annual_avg_file_time_metadata(nc)
        nc.close()

if __name__ == '__main__':
    parser = ArgumentParser(description='Creates annual averages from CMIP5 \
        data and writes to new CMIP5 path+file.')
    parser.add_argument('-o', '--outdir', required=True, help='Output directory')
    parser.add_argument('-b', '--basedir', help='Base directory from which to \
        search for climate model output files to process.')
    parser.add_argument('-v', '--variables', nargs='+', help='Variables to include')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true', \
        help='Just list the climate model output files found, and exit.')
    parser.set_defaults(
        variables=['tasmin', 'tasmax'],
        basedir='/home/data/climate/CMIP5/CCCMA/CanESM2/',
        dry_run=False
    )
    args = parser.parse_args()
    main(args)
