import os, os.path
import re
import logging
import sys

from argparse import ArgumentParser
from datetime import datetime
from tempfile import NamedTemporaryFile

from cdo import Cdo
from netCDF4 import Dataset, num2date, date2num
from dateutil.relativedelta import relativedelta

from util import s2d, ss2d, d2ss, d2s
from ClimateFile import ClimateFile, standard_climo_periods


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
    for dir_, _, filenames in os.walk(dirpath):
        for filename in filenames:
            abspath = os.path.join(dir_, filename)
            if regexp.match(abspath):
                yield abspath


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

    def var_trans(variable):
        # Returns additional variable specific commands
        if variable == 'pr':
            return '-mulc,86400'
        return ''

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

    # Allow different ops by variable? # op = 'sum' if variable == 'pr' else 'mean'
    op = 'mean'

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


def generate_climo_time_var(t_start, t_end, types=('monthly', 'seasonal', 'annual')):
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
        for i in range(-1, 9, 3): # Index is start month of season
            start = datetime(year, 1, 1) + relativedelta(months=i)
            end = start + relativedelta(months=3)
            mid = (start + (end - start)/2).replace(hour=0)
            while mid in times: mid += relativedelta(days=1)
            times.append(mid)

            climo_start = datetime(t_start.year, 1, 1) + relativedelta(months=i)
            climo_end = datetime(t_end.year, 1, 1) + relativedelta(months=i) + relativedelta(months=3)
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


def update_climo_time_meta(filepath):
    '''
    Updates the time varaible in an existing netCDF file to reflect climatological values.

    IMPORTANT: THIS MAKES CHANGES TO FILES IN PLACE

    Section 7.4: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.6/build/cf-conventions.html

    Assumes:
      - 17 timesteps: 12 months, 4 seasons, 1 annual
      - PCIC CMIP5 style file path
    '''
    
    cf = ClimateFile(filepath)
    nc = Dataset(filepath, 'r+')
    time_var = nc.variables['time']

    # Generate new time/climo_bounds data
    if cf.frequency == 'yrClim':
        time_types = ('annual')
    else:
        time_types = ('monthly', 'seasonal', 'annual')

    times, climo_bounds = generate_climo_time_var(ss2d(cf.start_date), ss2d(cf.end_date), time_types)

    time_var[:] = date2num(times, time_var.units, time_var.calendar)

    # Create new climatology_bounds variable and required bnds dimension
    time_var.climatology = 'climatology_bounds'
    nc.createDimension('bnds', 2)
    climo_bnds_var = nc.createVariable('climatology_bounds', 'f4', ('time', 'bnds', ))
    climo_bnds_var.calendar = time_var.calendar
    climo_bnds_var.units = time_var.units
    climo_bnds_var[:] = date2num(climo_bounds, time_var.units, time_var.calendar)

    nc.close()


def main(args):
    variables = '|'.join(args.variables)
    filepaths = list(iter_matching(
        args.basedir,
        re.compile('.*({}).*_(historical)?((?<=l)\+(?=r))?(rcp26|rcp45|rcp85)?_.*r\di\dp\d.*nc'.format(variables))
    ))

    log.info('Will process the following files:')
    for filepath in filepaths:
        log.info(filepath)

    if args.dry_run:
        log.info('DRY RUN')
        for filepath in filepaths:
            log.info('')
            log.info('File: {}'.format(filepath))
            input_file = ClimateFile(filepath, raise_=False)
            log.info('   climo_periods: {}'.format(input_file.climo_periods.keys()))
            for attr in 'start_date end_date variable frequency model experiment ensemble_member'.split():
                log.info('   {}: {}'.format(attr, getattr(input_file, attr)))
            log.info('output_filename: {}'.format(input_file.output_filename(standard_climo_periods()['6190'])))
        sys.exit(0)

    for filepath in filepaths:
        log.info('')
        log.info('Processing: {}'.format(filepath))
        input_file = ClimateFile(filepath)

        for _, t_range in input_file.climo_periods.items():

            # Create climatological period and update metadata
            log.info('Generating climo period %s to %s', d2s(t_range[0]), d2s(t_range[1]))
            output_filepath = input_file.output_filepath(args.basedir, t_range)
            log.info('Output file: %s', format(output_filepath))
            try:
                create_climo_file(filepath, output_filepath, t_range[0], t_range[1], input_file.variable)
            except:
                log.warn('Failed to create climatology file')
            else:
                update_climo_time_meta(output_filepath)



if __name__ == '__main__':
    parser = ArgumentParser(description='Create climatologies from CMIP5 data')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
#    parser.add_argument('-c', '--climo', nargs= '+',  help='Climatological periods to generate. IN PROGRESS. Defaults to all available in the input file. Ex: -c 6190 7100 8100 2020 2050 2080')
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
