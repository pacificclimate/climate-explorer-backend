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

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=4)

climo_periods = {
    '6190': [s2d('1961-01-01'),s2d('1990-12-31')],
    '7100': [s2d('1971-01-01'),s2d('2000-12-31')],
    '8110': [s2d('1981-01-01'),s2d('2010-12-31')],
    '2020': [s2d('2010-01-01'),s2d('2039-12-31')],
    '2050': [s2d('2040-01-01'),s2d('2069-12-31')],
    '2080': [s2d('2070-01-01'),s2d('2099-12-31')]
}

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

def find_var_name(keys):
    to_remove = [u'lat', u'lat_bnds', u'lon', u'lon_bnds', u'height', u'time', u'climatology_bounds']
    varnames = [x for x in keys if x not in to_remove]
    if len(varnames) == 1:
        return varnames[0]
    else:
        raise

def var_trans(variable):
    # Returns additional variable specific commands
    if variable == 'pr':
        return '-mulc,86400'
    return ''

def create_climo_file(fp_in, fp_out, t_start, t_end, variable):
    '''
    Generates climatological files from an input file and a selected time range

    Paramenters:
        f_in: input file path
        f_out: output file path
        t_start (datetime.datetime): start date of climo period
        t_end (datetime.datetime): end date of climo period
        variable (str): name of the variable which is being processed

    Requested date range MUST exist in the input file

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

    op = 'sum' if variable == 'pr' else 'mean'

    cdo = Cdo()
    date_range = '{},{}'.format(d2s(t_start), d2s(t_end))

    if not os.path.exists(os.path.dirname(fp_out)):
        os.makedirs(os.path.dirname(fp_out))

    with NamedTemporaryFile(suffix='.nc') as tempf:
        cdo.seldate(date_range, input=fp_in, output=tempf.name)

        # Add extra postprocessing for specific variables.
        vt = var_trans(variable)

        if 'yr' in fp_in:
            cdo_cmd = '{vt} -tim{op} {fname}'.format(fname=tempf.name, op=op, vt=vt)
        else:
            cdo_cmd = '{vt} -ymon{op} {fname} {vt} -yseas{op} {fname} {vt} -tim{op} {fname}'\
                .format(fname=tempf.name, op=op, vt=vt)

        cdo.copy(input=cdo_cmd, output=fp_out)

    # TODO: fix <variable_name>:cell_methods attribute to represent climatological aggregation

def determine_climo_periods(nc):
    '''
    Determine what climatological periods are available in a given netCDF file
    '''

    # Detect which climatological periods can be created
    time_var = nc.variables['time']
    s_date = num2date(time_var[0], units=time_var.units, calendar=time_var.calendar)
    e_date = num2date(time_var[-1], units=time_var.units, calendar=time_var.calendar)

    return dict([(k, v) for k, v in climo_periods.items() if v[0] > s_date and v[1] < e_date])

def generate_climo_time_var(t_start, t_end, units, types=('monthly', 'seasonal', 'annual')):
    '''
    '''

    year = (t_start + (t_end - t_start)/2).year + 1

    times = []
    climo_bounds = []

    # Calc month time values
    if 'monthly' in types:
        for i in range(1,13):
            start = datetime(year, i, 1)
            end = start + relativedelta(months=1)
            mid =  start + (end - start)/2
            mid = mid.replace(hour = 0)
            times.append(mid)

            climo_bounds.append([datetime(t_start.year, i, 1), (datetime(t_end.year, i, 1) + relativedelta(months=1))])

    # Seasonal time values
    if 'seasonal' in types:
        for i in range(3, 13, 3): # Index is start month of season
            start = datetime(year, i, 1)
            end = start + relativedelta(months=3)
            mid = (start + (end - start)/2).replace(hour=0)
            while mid in times: mid += relativedelta(days=1)
            times.append(mid)

            climo_start = datetime(t_start.year, i, 1)
            climo_end = datetime(t_end.year, i, 1) + relativedelta(months=3)
            # Account for DJF being a shorter season (crosses year boundary)
            if climo_end > t_end: climo_end -= relativedelta(years=1)
            climo_bounds.append([climo_start, climo_end])

    # Annual time value
    if 'annual' in types:
        days_to_mid = ((datetime(year, 1, 1) + relativedelta(years=1)) - datetime(year, 1, 1)).days/2
        mid = datetime(year, 1, 1) + relativedelta(days=days_to_mid)
        while mid in times: mid += relativedelta(days=1)
        times.append(mid)

        climo_bounds.append([t_start, t_end + relativedelta(days=1)])

    return times, climo_bounds

def update_climo_time_meta(fp, file_type=Cmip5File):
    '''
    Updates the time varaible in an existing netCDF file to reflect climatological values.

    IMPORTANT: THIS MAKES CHANGES TO FILES IN PLACE

    Section 7.4: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.6/build/cf-conventions.html

    Assumes:
      - 17 timesteps: 12 months, 4 seasons, 1 annual
      - PCIC CMIP5 style file path
    '''
    
    cf = file_type(fp)
    nc = Dataset(fp, 'r+')
    timevar = nc.variables['time']

    # Generate new time/climo_bounds data
    if cf.freq == 'yrClim':
        time_types = ('annual')
    else:
        time_types = ('monthly', 'seasonal', 'annual')

    times, climo_bounds = generate_climo_time_var(ss2d(cf.t_start), ss2d(cf.t_end), timevar.units, time_types)

    timevar[:] = date2num(times, timevar.units, timevar.calendar)

    # Create new climatology_bounds variable and required bnds dimension
    timevar.climatology = 'climatology_bounds'
    bnds_dim = nc.createDimension(u'bnds', 2)
    climo_bnds_var = nc.createVariable('climatology_bounds', 'f4', ('time', 'bnds', ))
    climo_bnds_var.calendar = timevar.calendar
    climo_bnds_var.units = timevar.units
    climo_bnds_var[:] = date2num(climo_bounds, timevar.units, timevar.calendar)

    nc.close()


def main(args):
    vars = '|'.join(args.variables)
    test_files = iter_matching(args.basedir, re.compile('.*({}).*(_rcp|_historical_).*r1i1p1.*nc'.format(vars)))

    FileType = ClimdexFile if args.climdex else Cmip5File

    for fp in test_files:
        log.info(fp)

        nc = Dataset(fp)
        available_climo_periods = determine_climo_periods(nc)
        nc.close()
        file_ = FileType(fp)
        variable = file_.variable

        for period, t_range in available_climo_periods.items():

            # Create climatological period and update metadata
            log.info('Generating climo period {} to {}'.format(d2s(t_range[0]), d2s(t_range[1])))
            out_fp = file_.generate_output_fp(t_range, args.outdir)
            log.info('Output file: {}'.format(out_fp))
            try:
                create_climo_file(fp, out_fp, t_range[0], t_range[1], variable)
            except:
                log.warn('Failed to create climatology file')
            else:
                update_climo_time_meta(out_fp, FileType)

if __name__ == '__main__':
    parser = ArgumentParser(description='Create climatologies from CMIP5 data')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
#    parser.add_argument('-c', '--climo', nargs= '+',  help='Climatological periods to generate. IN PROGRESS. Defaults to all available in the input file. Ex: -c 6190 7100 8100 2020 2050 2080')
    parser.add_argument('-b', '--basedir', help='Root directory from which to search for climate model output')
    parser.add_argument('-v', '--variables', nargs='+', help='Variables to include')
    parser.add_argument('-C', '--climdex', action='store_true')
    parser.set_defaults(
        variables=['tasmin', 'tasmax'],
        basedir='/home/data/climate/CMIP5/CCCMA/CanESM2/',
        climdex=False
    )
    args = parser.parse_args()
    main(args)
