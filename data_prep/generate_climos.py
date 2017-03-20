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


def create_climo_files(outdir, input_file, t_start, t_end):
    """Generate climatological files from an input file and a selected time range.
    At present the climatological files contain multi-year means of the dependent variables in the input file.

    Parameters:
        outdir (str): path to base directory in which to store output climo files
        input_file (nchelpers.CFDataset): the input data file
        t_start (datetime.datetime): start date of climo period to process
        t_end (datetime.datetime): end date of climo period to process

    We use CDO to perform the key computations for the climatology outputs.

    One output file is generated per dependent variable in the input file. This simplifies the processing somewhat,
    since in order to apply variable-specific operations using CDO, the variable must at least temporarily be split
    out of the file. We can avoid copying all that back into a single file.

    To process an input file we must perform the following operations:
    - Select the temporal subset defined by t_start, t_end
    - Form climatological means over each dependent variable
    - Split multiple variables into separate files
    - Apply any special per-variable operations (e.g., scaling pr to mm/day)

    The above operations could validly be performed in several different orders, but the ordering given optimizes
    execution time and uses less intermediate storage space than some others.
    This ordering/optimization may need to change if different climatological outputs are later required.

    If the requested date range is not fully included in the input file, then output file will contain a smaller date
    range (defined by what's actually availabe in the input file) and the date range part of output file name will be
    misleading.

    """
    logger.info('Generating climo period %s to %s', d2s(t_start), d2s(t_end))

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

    # Select the temporal subset defined by t_start, t_end
    logger.info('Selecting temporal subset')
    date_range = '{},{}'.format(d2s(t_start), d2s(t_end))
    temporal_subset = cdo.seldate(date_range, input=input_file.filepath)

    # Form climatological means over dependent variables
    def climo_outputs(time_resolution):
        '''Return a list of cdo operators that generate the desired climo outputs.
        Result depends on the time resolution of input file data - different operators are applied depending.
        If operators depend also on variable, then modify this function to depend on variable as well.
        '''
        ops_by_resolution = {
            'daily': ['ymonmean', 'yseasmean', 'timmean'],
            'monthly': ['yseasmean', 'timmean'],
            'yearly': ['timmean']
        }
        try:
            return [getattr(cdo, op)(input=temporal_subset) for op in ops_by_resolution[time_resolution]]
        except:
            raise ValueError("Expected input file to have time resolution {}, found {}"
                             .format(' or '.join(ops_by_resolution.keys()), time_resolution))

    logger.info('Forming climatological means')
    climo_means = cdo.copy(' '.join(climo_outputs(input_file.time_resolution)))

    # Split climo means file into separate files, one per variable
    for variable in input_file.dependent_variables:
        logger.info('Splitting into single-variable files')
        try:
            output_file_path = climo_output_filepath(outdir, input_file, t_start, t_end, variable)
            logger.info('Output file: {}'.format(output_file_path))
            if not os.path.exists(os.path.dirname(output_file_path)):
                os.makedirs(os.path.dirname(output_file_path))

            by_var_name = 'name={}'.format(variable) # for cdo select cmd

            # Apply per-variable processing
            if variable == 'pr' and 's-1' in input_file.variables[variable].units: # units can be 'mm s-1', 'kg m-2 s-1'
                logger.info("Converting 'pr' variable to units mm/day")
                # Extract variable
                single_variable = cdo.select(by_var_name, input=climo_means)
                # Multiply values by 86400 to convert from mm/s to mm/day
                single_variable = cdo.mulc('86400', input=single_variable)
                # Update units attribute
                # TODO: Verify that "d-1" is desired way to express "per day" (alternaive is "day-1")
                # TODO: Reconsider whether we want to use CDO to set attributes - it copies the file to do so
                attribute_to_set = 'pr@units="{}"'.format(input_file.variables[variable].units.replace('s-1', 'd-1'))
                cdo.setattribute(attribute_to_set, input=single_variable, output=output_file_path)
            else:
                # Just extract variable
                cdo.select(by_var_name, input=climo_means, output=output_file_path)
            # TODO: fix <variable_name>:cell_methods attribute to represent climatological aggregation
            # TODO: Does the above TODO make any sense? Each variable has had up to 3 different aggregations applied
            # to it, and there is no standard cell_method string that expresses more than one.
        except Exception as e:
            logger.warn('Failed to create climatology file. {}: {}'.format(e.__class__.__name__, e))
        else:
            update_climo_time_meta(output_file_path)


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
    
    cf = CFDataset(filepath, mode='r+')
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
    if args.dry_run:
        logger.info('DRY RUN')
        for filepath in args.filepaths:
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

    for filepath in args.filepaths:
        logger.info('')
        logger.info('Processing: {}'.format(filepath))
        try:
            input_file = CFDataset(filepath)
        except Exception as e:
            logger.info('{}: {}'.format(e.__class__.__name__, e))
        else:
            for _, t_range in input_file.climo_periods.items():
                create_climo_files(args.outdir, input_file, *t_range)

if __name__ == '__main__':
    parser = ArgumentParser(description='Create climatologies from CMIP5 data')
    parser.add_argument('filepaths', nargs='*', help='Files to process')
#    parser.add_argument('-c', '--climo', nargs= '+',  help='Climatological periods to generate. IN PROGRESS. Defaults to all available in the input file. Ex: -c 6190 7100 8100 2020 2050 2080')
    log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()
    parser.add_argument('-l', '--loglevel', help='Logging level',
                        choices=log_level_choices, default='INFO')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    parser.set_defaults(dry_run=False, split_vars=False)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))
    main(args)
