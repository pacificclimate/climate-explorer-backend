import os, os.path
import logging
import sys
from itertools import chain

from argparse import ArgumentParser
from datetime import datetime

from cdo import Cdo
from netCDF4 import date2num
from dateutil.relativedelta import relativedelta

from nchelpers import CFDataset, standard_climo_periods
from nchelpers.date_utils import d2s


formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)


def create_climo_file(outdir, input_file, t_start, t_end):
    """Generate climatological files from an input file and a selected time range.

    Parameters:
        outdir (str): path to base directory in which to store output climo file
        input_file (nchelpers.CFDataset): the input data file
        t_start (datetime.datetime): start date of climo period to process
        t_end (datetime.datetime): end date of climo period to process

    Requested date range MUST exist in the input file.

    """
    # TODO: Are these all really legitimate variables for processing, i.e., for forming temporal means over?
    supported_vars = {
        'cddETCCDI', 'csdiETCCDI', 'cwdETCCDI', 'dtrETCCDI', 'fdETCCDI',
        'gslETCCDI', 'idETCCDI', 'prcptotETCCDI', 'r10mmETCCDI', 'r1mmETCCDI',
        'r20mmETCCDI', 'r95pETCCDI', 'r99pETCCDI', 'rx1dayETCCDI',
        'rx5dayETCCDI', 'sdiiETCCDI', 'suETCCDI', 'thresholds', 'tn10pETCCDI',
        'tn90pETCCDI', 'tnnETCCDI', 'tnxETCCDI', 'trETCCDI', 'tx10pETCCDI',
        'tx90pETCCDI', 'txnETCCDI', 'txxETCCDI', 'wsdiETCCDI', 'tasmin',
        'tasmax', 'pr'
    }

    for variable in input_file.dependent_variables:
        if variable not in supported_vars:
            raise Exception("Unsupported variable: cant't yet process {}".format(variable))

    cdo = Cdo()

    output_file_path = climo_output_filepath(outdir, input_file, t_start, t_end)
    if not os.path.exists(os.path.dirname(output_file_path)):
        os.makedirs(os.path.dirname(output_file_path))

    # Select input data within time range into temporary file
    date_range = '{},{}'.format(d2s(t_start), d2s(t_end))
    temporal_subset = cdo.seldate(date_range, input=input_file.filepath)
    if variable == 'pr':
        # Premultiply input values by 86400
        temporal_subset = cdo.mulc('86400', input=temporal_subset)

    # Process selected data into climatological means
    def climo_outputs(time_resolution):
        '''Return a list of cdo operators that generate the desired climo outputs.
        Result depends on the time resolution of input file data - different operators are applied depending.
        If operators depend also on variable, then modify this function to depend on variable as well.
        '''
        ops_by_resolution = {
            'daily': ['ymonmean', 'yseasmean', 'timmean'],
            'yearly': ['timmean']
        }
        try:
            return [getattr(cdo, op)(input=temporal_subset) for op in ops_by_resolution[time_resolution]]
        except:
            raise ValueError("Expected input file to have time resolution {}, found {}"
                             .format(' or '.join(ops_by_resolution.keys()), time_resolution))

    cdo.copy(' '.join(climo_outputs(input_file.time_resolution)), output=output_file_path)

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
    
    cf = CFDataset(filepath)
    time_var = cf.variables['time']

    # Generate new time/climo_bounds data
    if cf.time_resolution == 'yearly':
        time_types = ('annual')
    else:
        time_types = ('monthly', 'seasonal', 'annual')

    start_date, end_date = cf.time_range
    # Migration note: start_date, end_date may need to be converted to real datetime.datetime values
    times, climo_bounds = generate_climo_time_var(start_date, end_date, time_types)

    time_var[:] = date2num(times, time_var.units, time_var.calendar)

    # Create new climatology_bounds variable and required bnds dimension
    time_var.climatology = 'climatology_bounds'
    cf.createDimension('bnds', 2)
    climo_bnds_var = cf.createVariable('climatology_bounds', 'f4', ('time', 'bnds', ))
    climo_bnds_var.calendar = time_var.calendar
    climo_bnds_var.units = time_var.units
    climo_bnds_var[:] = date2num(climo_bounds, time_var.units, time_var.calendar)

    cf.close()


def climo_output_filepath(output_dir, input_file, t_start, t_end):
    '''Join the output directory to the output filename for this file'''
    return os.path.realpath(os.path.join(output_dir, input_file.climo_output_filename(t_start, t_end)))


def main(args):
    filepaths = args.filepaths
    if args.file_list:
        with open(args.file_list) as f:
            filepaths = chain(filepaths, [l for l in (l.strip() for l in f) if l[0] != '#'])

    filepaths = list(filepaths)  # Not very nice, but we reuse the list, at least for now

    logger.info('Will process the following files:')
    for filepath in filepaths:
        logger.info(filepath)

    if args.dry_run:
        logger.info('DRY RUN')
        for filepath in filepaths:
            logger.info('')
            logger.info('File: {}'.format(filepath))
            try:
                input_file = CFDataset(filepath)
            except Exception as e:
                logger.info('{}: {}'.format(e.__class__.__name__, e))
            else:
                logger.info('climo_periods: {}'.format(input_file.climo_periods.keys()))
                for attr in 'project institution model emissions run'.split():
                    try:
                        logger.info('{}: {}'.format(attr, getattr(input_file.metadata, attr)))
                    except Exception as e:
                        logger.info('{}: {}: {}'.format(attr, e.__class__.__name__, e))
                for attr in 'dependent_varnames time_resolution is_multi_year_mean'.split():
                    logger.info('{}: {}'.format(attr, getattr(input_file, attr)))
                logger.info('output_filepath: {}'.format(climo_output_filepath(args.outdir, input_file, *standard_climo_periods()['6190'])))
        sys.exit(0)

    for filepath in filepaths:
        logger.info('')
        logger.info('Processing: {}'.format(filepath))
        try:
            input_file = CFDataset(filepath)
        except Exception as e:
            # Likeliest exceptions:
            # - IOError: file not found
            logger.info('{}: {}'.format(e.__class__.__name__, e))
        else:
            for _, t_range in input_file.climo_periods.items():
                # Create climatological period and update metadata
                logger.info('Generating climo period %s to %s', d2s(t_range[0]), d2s(t_range[1]))
                output_filepath = climo_output_filepath(args.outdir, input_file, *t_range)
                logger.info('Output file: %s', format(output_filepath))
                try:
                    create_climo_file(args.outdir, input_file, *t_range)
                except:
                    logger.warn('Failed to create climatology file')
                else:
                    update_climo_time_meta(output_filepath)


if __name__ == '__main__':
    parser = ArgumentParser(description='Create climatologies from CMIP5 data')
    parser.add_argument('filepaths', nargs='*', help='Files to process')
#    parser.add_argument('-c', '--climo', nargs= '+',  help='Climatological periods to generate. IN PROGRESS. Defaults to all available in the input file. Ex: -c 6190 7100 8100 2020 2050 2080')
    parser.add_argument('-f', '--file-list', help='File containing list of filepaths (one per line) to process')
    parser.add_argument('-C', '--climdex', action='store_true')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true')
    log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()
    parser.add_argument('-l', '--loglevel', help='Logging level',
                        choices=log_level_choices, default='INFO')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    parser.set_defaults(
        climdex=False,
        dry_run=False
    )
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))
    main(args)
