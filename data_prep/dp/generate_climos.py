import os, os.path
import logging
import sys
import re

from argparse import ArgumentParser
from datetime import datetime
import dateutil.parser
import numpy as np

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
logger.setLevel(logging.DEBUG)  # For testing, overridden by -l when run as a script


def create_climo_files(outdir, input_file, t_start, t_end, convert_longitudes=False, split_vars=False):
    """Generate climatological files from an input file and a selected time range.

    Parameters:
        outdir (str): path to base directory in which to store output climo file(s)
        input_file (nchelpers.CFDataset): the input data file
        convert_longitudes (bool): If True, convert longitudes from [0, 360) to [-180, 180).
        split_vars (bool): if True, produce one file per dependent variable in input file;
            otherwise produce a single output file containing all variables
        t_start (datetime.datetime): start date of climo period to process
        t_end (datetime.datetime): end date of climo period to process

    The input file is not modified.

    Output is either one file containing all variables, or one output file for each dependent variable in the
    input file. This behaviour is selected by the --split-vars flag.

    We use CDO to where it is convenient; in particular, to form the climatological means.
    Other operations are performed directly by this code, in-place on intermediate or final output files.

    To process an input file we must perform the following operations:

    - Select the temporal subset defined by t_start, t_end
    - Form climatological means over each dependent variable
    - Post-process climatological results:
        - if convert_longitudes, transform longitude range from [0, 360) to [-180, 180)
    - Apply any special per-variable post-processing:
        - pr: scale to mm/day
    - Update global attributes to reflect the fact this is a climatological means file
    - if split_vars:
        - Split multiple variables into separate files

    The above operations could validly be performed in several different orders, but the ordering given optimizes
    execution time and uses less intermediate storage space than most others.
    This ordering/optimization may need to change if different climatological outputs are later required.

    Warning: If the requested date range is not fully included in the input file, then output file will contain a
    smaller date range (defined by what's actually available in the input file) and the date range part of
    output file name will be misleading.

    """
    logger.info('Generating climo period %s to %s', d2s(t_start), d2s(t_end))

    if input_file.is_multi_year_mean:
        raise Exception('This file already contains climatological means!')

    supported_vars = {
        # Standard climate variables
        'tasmin', 'tasmax', 'pr',
        # Hydrological modelling variables
        'RUNOFF', 'BASEFLOW', 'EVAP', 'GLAC_MBAL_BAND', 'GLAC_AREA_BAND', 'SWE_BAND',
        # Climdex variables
        'cddETCCDI', 'csdiETCCDI', 'cwdETCCDI', 'dtrETCCDI', 'fdETCCDI',
        'gslETCCDI', 'idETCCDI', 'prcptotETCCDI', 'r10mmETCCDI', 'r1mmETCCDI',
        'r20mmETCCDI', 'r95pETCCDI', 'r99pETCCDI', 'rx1dayETCCDI',
        'rx5dayETCCDI', 'sdiiETCCDI', 'suETCCDI', 'thresholds', 'tn10pETCCDI',
        'tn90pETCCDI', 'tnnETCCDI', 'tnxETCCDI', 'trETCCDI', 'tx10pETCCDI',
        'tx90pETCCDI', 'txnETCCDI', 'txxETCCDI', 'wsdiETCCDI',
    }

    for variable in input_file.dependent_varnames:
        if variable not in supported_vars:
            raise Exception("Unsupported variable: cant't yet process {}".format(variable))

    cdo = Cdo()

    # Select the temporal subset defined by t_start, t_end
    logger.info('Selecting temporal subset')
    date_range = '{},{}'.format(d2s(t_start), d2s(t_end))
    temporal_subset = cdo.seldate(date_range, input=input_file.filepath())

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
            raise ValueError("Expected input file to have time resolution in {}, found '{}'"
                             .format(ops_by_resolution.keys(), time_resolution))

    logger.info('Forming climatological means')
    climo_means = cdo.copy(input=' '.join(climo_outputs(input_file.time_resolution)))

    # Post-process climatological means
    if convert_longitudes:
        # Transform longitude range from [0, 360) to [-180, 180)
        # CDO offers no simple way to do this computation, therefore we do it directly.
        # This code modifies the file with filepath climo_means in place.
        with CFDataset(climo_means, mode='r+') as cf:
            convert_these = [cf.lon_var]
            if hasattr(cf.lon_var, 'bounds'):
                lon_bnds_var = cf.variables[cf.lon_var.bounds]
                convert_these.append(lon_bnds_var)
            for lon_var in convert_these:
                for i, lon in np.ndenumerate(lon_var):
                    if lon >= 180:
                        lon_var[i] = lon - 360

    # Apply per-variable processing
    # - Scale pr variable if it is not in desired units
    #   - TODO: Use UDUNITS here for more robust processing of units? It has a fairly heavy API. But this is uuuugly.
    if 'pr' in input_file.dependent_varnames:
        units = input_file.variables['pr'].units
        if any(u in units for u in ['kg', 'mm']) and any(u in units for u in ['/s', '/ s', 's-1', 's^-1']):
            logger.info("Converting 'pr' variable to units mm/day")
            # Extract variable
            pr_only = cdo.select('name=pr', input=climo_means)
            # Multiply values by 86400 to convert from mm/s to mm/day
            pr_only = cdo.mulc('86400', input=pr_only)
            # Replace pr in all-variables file
            climo_means = cdo.replace(input=[climo_means, pr_only])
            # Update units attribute
            # TODO: Verify that "d-1" is desired way to express "per day" (alternaive is "day-1")
            pr_units_attr = re.sub('(/s|/ s|s-1|s\^-1)', ' d-1', units)

    # Update climo file with climo specific metadata attributes.
    # Do it in place via CFDataset to avoid CDO installation hassles: CDO < 1.8.0 does not have setattributes method
    # and there's no easy Ubuntu install for CDO >= 1.8.0 yet
    # Also avoids copying the file just to update its attributes.
    with CFDataset(climo_means, mode='r+') as cf:
        # For an explanation of frequency param, see PCIC metadata standard
        resolution_to_frequency = {
            'daily': 'msaClim',
            'monthly': 'saClim',
            'yearly': 'aClim'
        }
        try:
            cf.frequency = resolution_to_frequency[input_file.time_resolution]
        except KeyError:
            raise ValueError("Expected input file to have time resolution in {}, found '{}'"
                             .format(resolution_to_frequency.keys(), input_file.time_resolution))
        # In Python2.7, datetime.datime.isoformat does not take params telling it how much precision to
        # provide in its output; standard requires 'seconds' precision, which means the first 19 characters.
        cf.climo_start_time = t_start.isoformat()[:19] + 'Z'
        cf.climo_end_time = t_end.isoformat()[:19] + 'Z'
        if hasattr(input_file, 'tracking_id'):
            cf.climo_tracking_id=input_file.tracking_id
        try:
            cf.variables['pr'].units = pr_units_attr
        except NameError:
            pass

    # Update time metadata in climo file
    update_climo_time_meta(climo_means)

    # Create final output file(s): split climo means file by dependent variables if required
    output_file_paths = []

    def create_output_file(cdo_op, output_file_path):
        """Create the output file by applying function cdo_op, and update its time metadata.
        Catch any exception and log it; don't re-raise the exception.

        :param cdo_op: (function) applies the desired CDO operation. Invoked only with kw args; CDO operation-specific
            args should be curried by cdo_op. Input and output file args are supplied as kw args here
        :param output_file_path: (str) specifies file path for output file; it will be created by this function.
        """
        try:
            logger.info('Output file: {}'.format(output_file_path))
            if not os.path.exists(os.path.dirname(output_file_path)):
                os.makedirs(os.path.dirname(output_file_path))
            cdo_op(input=climo_means, output=output_file_path)
        except Exception as e:
            logger.warn('Failed to create climatology file. {}: {}'.format(e.__class__.__name__, e))
        else:
            output_file_paths.append(output_file_path)

    if split_vars and len(input_file.dependent_varnames) > 1:
        # Split climo means file into separate files, one per variable
        logger.info('Splitting into single-variable files')
        for variable in input_file.dependent_varnames:
            output_file_path = climo_output_filepath(outdir, input_file, t_start, t_end, variable=variable)
            create_output_file(lambda **io: cdo.select('name={}'.format(variable), **io), output_file_path)
    else:
        # Don't split; copy the temporary file to the final output filename
        output_file_path = climo_output_filepath(outdir, input_file, t_start, t_end)
        create_output_file(lambda **io: cdo.copy(**io), output_file_path)

    # TODO: fix <variable_name>:cell_methods attribute to represent climatological aggregation
    # TODO: Does the above TODO make any sense? Each variable has had up to 3 different aggregations applied
    # to it, and there is no standard cell_method string that expresses more than one.

    return output_file_paths


def generate_climo_time_var(t_start, t_end, types={'monthly', 'seasonal', 'annual'}):
    """Generate information needed to update the climatological time variable.

    :param t_start: (datetime.datetime) start date of period over which climatological means are formed
    :param t_end: (datetime.datetime) end date of period over which climatological means are formed
    :param types: (set) specifies what means have been generted, hence which time values to generate
    :returns: (tuple) times, climo_bounds
        times: (list) datetime for *center* of each climatological mean period; see CF standard
        climo_bounds: (list) bounds (start and end date) of each climatological mean period

    ASSUMPTION: Time values are in the following order within the time dimension variable.
        monthly: 12 months in their usual order
        seasonal: 4 seasons: DJF, MAM, JJA, SON
        annual: 1 value
    """

    # Year of all time values is middle year of period
    year = (t_start + (t_end - t_start)/2).year + 1

    times = []
    climo_bounds = []

    # Monthly time values
    if 'monthly' in types:
        for month in range(1,13):
            start = datetime(year, month, 1)
            end = start + relativedelta(months=1)
            mid =  start + (end - start)/2
            mid = mid.replace(hour = 0)
            times.append(mid)

            climo_bounds.append([datetime(t_start.year, month, 1), (datetime(t_end.year, month, 1) + relativedelta(months=1))])

    # Seasonal time values
    if 'seasonal' in types:
        for month in range(-1, 9, 3): # Index is start month of season
            start = datetime(year, 1, 1) + relativedelta(months=month)
            end = start + relativedelta(months=3)
            mid = (start + (end - start)/2).replace(hour=0)
            while mid in times: mid += relativedelta(days=1)
            times.append(mid)

            climo_start = datetime(t_start.year, 1, 1) + relativedelta(months=month)
            climo_end = datetime(t_end.year, 1, 1) + relativedelta(months=month) + relativedelta(months=3)
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
    """Updates an existing netCDF file to reflect the fact that it contains climatological means.
    Namely, update the time variable with climatological times computed according to CF Metadata Convetions,
    and create a climatology bounds variable with appropriate values.

    :param filepath: (str) filepath to a climatological means output file which needs to have its
        time variable

    IMPORTANT: THIS MAKES CHANGES TO FILES IN PLACE

    Section 7.4: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.6/build/cf-conventions.html
    """
    
    with CFDataset(filepath, mode='r+') as cf:
        # Generate new time/climo_bounds data
        frequency_to_time_types = {
            'msaClim': {'monthly', 'seasonal', 'annual'},
            'saClim': {'seasonal', 'annual'},
            'aClim': {'annual'},
        }
        try:
            time_types = frequency_to_time_types[cf.frequency]
        except KeyError:
            raise ValueError("Climatology file must have a frequency value in {}; found '{}'"
                             .format(frequency_to_time_types.keys(), cf.frequency))

        times, climo_bounds = generate_climo_time_var(
            dateutil.parser.parse(cf.climo_start_time[:19]),  # create tz naive dates by stripping off the tz indicator
            dateutil.parser.parse(cf.climo_end_time[:19]),
            time_types
        )

        # Update time var with CF standard climatological times
        cf.time_var[:] = date2num(times, cf.time_var.units, cf.time_var.calendar)

        # Create new climatology_bnds variable and required bnds dimension if necessary.
        # Note: CDO seems to do some automagic with bounds variable names, converting the string 'bounds' to 'bnds'.
        # For less confusion, we use that convention here, even though original code used the name 'climatology_bounds'.
        # TODO: Should this variable be added to cf.time_var.bounds?
        cf.time_var.climatology = 'climatology_bnds'
        if 'bnds' not in cf.dimensions:
            cf.createDimension('bnds', 2)
        climo_bnds_var = cf.createVariable('climatology_bnds', 'f4', ('time', 'bnds', ))
        climo_bnds_var.calendar = cf.time_var.calendar
        climo_bnds_var.units = cf.time_var.units
        climo_bnds_var[:] = date2num(climo_bounds, cf.time_var.units, cf.time_var.calendar)


def climo_output_filepath(output_dir, input_file, t_start, t_end, **kwargs):
    '''Join the output directory to the output filename for this file'''
    return os.path.realpath(os.path.join(output_dir, input_file.climo_output_filename(t_start, t_end, **kwargs)))


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
                logger.info('output_filepath: {}'.format(
                    climo_output_filepath(args.outdir, input_file, datetime.now(), datetime.now(), variable='var')
                ))
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
                create_climo_files(args.outdir, input_file, *t_range,
                                   convert_longitudes=args.convert_longitudes, split_vars=args.split_vars)

if __name__ == '__main__':
    parser = ArgumentParser(description='Create climatologies from CMIP5 data')
    parser.add_argument('filepaths', nargs='*', help='Files to process')
#    parser.add_argument('-c', '--climo', nargs= '+',  help='Climatological periods to generate. IN PROGRESS. Defaults to all available in the input file. Ex: -c 6190 7100 8100 2020 2050 2080')
    log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()
    parser.add_argument('-l', '--loglevel', help='Logging level',
                        choices=log_level_choices, default='INFO')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true')
    parser.add_argument('-g', '--convert-longitudes', dest='convert_longitudes', action='store_true')
    parser.add_argument('-s', '--split-vars', dest='split_vars', action='store_true')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    parser.set_defaults(dry_run=False, convert_longitudes=False, split_vars=False)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))
    main(args)
