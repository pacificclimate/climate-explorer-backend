import os
import os.path
import logging
import shutil
import sys

from argparse import ArgumentParser
from datetime import datetime
import dateutil.parser
import numpy as np

from cdo import Cdo
from netCDF4 import date2num
from dateutil.relativedelta import relativedelta

from nchelpers import CFDataset
from nchelpers.date_utils import d2s

from dp.units_helpers import Unit


# Set up logging
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)  # For testing, overridden by -l when run as a script

# Instantiate CDO interface
cdo = Cdo()


def create_climo_files(outdir, input_file, t_start, t_end,
                       convert_longitudes=False, split_vars=False, split_intervals=False):
    """Generate climatological files from an input file and a selected time range.

    Parameters:
        outdir (str): path to base directory in which to store output climo file(s)
        input_file (nchelpers.CFDataset): the input data file
        convert_longitudes (bool): If True, convert longitudes from [0, 360) to [-180, 180).
        split_vars (bool): If True, produce one file per dependent variable in input file;
            otherwise produce a single output file containing all variables.
            Note: Can split both variables and intervals.
        split_intervals (bool): If True, produce one file per averaging interval (month, season, year);
            otherwise produce a single output file with all averating intervals concatenated.
            Note: Can split both variables and intervals.
        t_start (datetime.datetime): start date of climo period to process
        t_end (datetime.datetime): end date of climo period to process

    The input file is not modified.

    Output is either one of the following:
    - one output file containing all variables and all intervals
    - one output file for each dependent variable in the input file, and all intervals
    - one output file for each interval, containing all variables
    - one output file for each dependent variable and each interval
    This behaviour is selected by the --split-vars and --split-intervals flags.

    We use CDO to where it is convenient; in particular, to form the climatological means.
    Other operations are performed directly by this code, in-place on intermediate or final output files.

    To process an input file we must perform the following operations:

    - Select the temporal subset defined by t_start, t_end
    - Form climatological means over each dependent variable over all available averaging intervals
    - if not split_intervals:
        - concat files (averaging intervals)
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

    # Select the temporal subset defined by t_start, t_end
    logger.info('Selecting temporal subset')
    date_range = '{},{}'.format(d2s(t_start), d2s(t_end))
    temporal_subset = cdo.seldate(date_range, input=input_file.filepath())

    # Form climatological means over dependent variables
    def climo_outputs(time_resolution):
        """Return a list of cdo operators that generate the desired climo outputs.
        Result depends on the time resolution of input file data - different operators are applied depending.
        If operators depend also on variable, then modify this function to depend on variable as well.
        """
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
    climo_means_files = climo_outputs(input_file.time_resolution)

    # Optionally concatenate means for each interval (month, season, year) into one file
    if not split_intervals:
        logger.info('Concatenating mean interval files')
        climo_means_files = [cdo.copy(input=' '.join(climo_means_files))]

    # Optionally convert longitudes in each file
    if convert_longitudes:
        logger.info('Converting longitudes')
        for climo_means_file in climo_means_files:
            convert_longitude_range(climo_means_file)

    # Convert units on any pr variable in each file
    climo_means_files = [convert_pr_var_units(input_file, climo_mean_file) for climo_mean_file in climo_means_files]

    # Update metadata in climo files
    logger.debug('Updating climo metadata')
    for climo_means_file in climo_means_files:
        update_climo_metadata(input_file, t_start, t_end, climo_means_file)

    # Split climo files by dependent variables if required
    if split_vars:
        climo_means_files = [
            fp
            for climo_means_file in climo_means_files
            for fp in split_on_variables(climo_means_file, input_file.dependent_varnames)
        ]

    # Move/copy the temporary files to their final output filepaths
    output_file_paths = []
    for climo_means_file in climo_means_files:
        with CFDataset(climo_means_file) as cf:
            output_file_path = os.path.join(outdir, cf.cmor_filename)
        try:
            logger.info('Output file: {}'.format(output_file_path))
            if not os.path.exists(os.path.dirname(output_file_path)):
                os.makedirs(os.path.dirname(output_file_path))
            shutil.move(climo_means_file, output_file_path)
        except Exception as e:
            logger.warning('Failed to create climatology file. {}: {}'.format(e.__class__.__name__, e))
        else:
            output_file_paths.append(output_file_path)

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

    # We follow the examples in sec 7.4 Climatological Statistics of the CF Metadata Standard
    # (http://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#climatological-statistics),
    # in which for climatological times they use the 15th day of each month for multi-year monthly averages
    # and the 16th day of the mid-season months (Jan, Apr, July, Oct) for multi-year seasonal averages.
    # In that spirit, we use July 2 as the middle day of the year (https://en.wikipedia.org/wiki/July_2).
    times = []
    climo_bounds = []

    # Monthly time values
    if 'monthly' in types:
        for month in range(1, 13):
            times.append(datetime(year, month, 15))
            climo_bounds.append([datetime(t_start.year, month, 1),
                                 datetime(t_end.year, month, 1) + relativedelta(months=1)])

    # Seasonal time values
    if 'seasonal' in types:
        for month in [1, 4, 7, 10]:  # Center months of season
            times.append(datetime(year, month, 16))
            climo_bounds.append([datetime(t_start.year, month, 1) + relativedelta(months=-1),
                                 datetime(t_end.year, month, 1) + relativedelta(months=2)])

    # Annual time value
    # Standard climatological periods, provided by nchelpers and implicit here, begin Jan 1 and end Dec 31
    # This is a mismatch to hydrological years, which begin/end Oct 1 / Sep 30. Discussions with Markus Schnorbus
    # confirm that for 30-year means, the difference in annual and
    # season averages is negligible and therefore we do not have to allow for alternate begin and end dates.
    # """
    if 'annual' in types:
        times.append(datetime(year, 7, 2))
        climo_bounds.append([datetime(t_start.year, 1, 1),
                             datetime(t_end.year+1, 1, 1)])

    return times, climo_bounds


def convert_longitude_range(climo_means):
    """Transform longitude range from [0, 360) to [-180, 180).

    CDO offers no simple way to do this computation, therefore we do it directly.

    WARNING: This code modifies the file with filepath climo_means IN PLACE.
    """
    with CFDataset(climo_means, mode='r+') as cf:
        convert_these = [cf.lon_var]
        if hasattr(cf.lon_var, 'bounds'):
            lon_bnds_var = cf.variables[cf.lon_var.bounds]
            convert_these.append(lon_bnds_var)
        for lon_var in convert_these:
            for i, lon in np.ndenumerate(lon_var):
                if lon >= 180:
                    lon_var[i] = lon - 360


def convert_pr_var_units(input_file, climo_means):
    """If the file contains a 'pr' variable, and if its units are per second, convert its units to per day.

    """
    pr_attributes = {}  # will contain updates, if any, to pr variable attributes

    if 'pr' in input_file.dependent_varnames:
        pr_variable = input_file.variables['pr']
        pr_units = Unit.from_udunits_str(pr_variable.units)
        if pr_units in [Unit('kg / m**2 / s'), Unit('mm / s')]:
            logger.info("Converting 'pr' variable to units mm/day")
            # Update units attribute
            pr_attributes['units'] = (pr_units * Unit('s / day')).to_udunits_str()
            # Multiply values by 86400 to convert from mm/s to mm/day
            seconds_per_day = 86400
            if hasattr(pr_variable, 'scale_factor') or hasattr(pr_variable, 'add_offset'):
                # This is a packed file; need only modify packing parameters
                try:
                    pr_attributes['scale_factor'] = seconds_per_day * pr_variable.scale_factor
                except AttributeError:
                    pr_attributes['scale_factor'] = seconds_per_day * 1.0  # default value 1.0 for missing scale factor
                try:
                    pr_attributes['add_offset'] = seconds_per_day * pr_variable.add_offset
                except AttributeError:
                    pr_attributes['add_offset'] = 0.0  # default value 0.0 for missing offset
            else:
                # This is not a packed file; modify the values proper
                # Extract variable
                pr_only = cdo.select('name=pr', input=climo_means)
                # Multiply values by 86400 to convert from mm/s to mm/day
                pr_only = cdo.mulc(str(seconds_per_day), input=pr_only)
                # Replace pr in all-variables file
                climo_means = cdo.replace(input=[climo_means, pr_only])

    # Update pr variable metadata as necessary to reflect changes madde
    with CFDataset(climo_means, mode='r+') as cf:
        for attr in pr_attributes:
            setattr(cf.variables['pr'], attr, pr_attributes[attr])

    return climo_means


def split_on_variables(climo_means_file, var_names):
    if len(var_names) > 1:
        return [cdo.select('name={}'.format(var_name), input=climo_means_file)
                for var_name in var_names]
    else:
        return [climo_means_file]


def update_climo_metadata(input_file, t_start, t_end, climo_filepath):
    """Updates an existing netCDF file to reflect the fact that it contains climatological means.

    Specifically:
    - add start and end time attributes
    - update tracking_id attribute
    - update the frequency attribute
    - update the time variable with climatological times computed according to CF Metadata Convetions,
    and create a climatology bounds variable with appropriate values.

    :param input_file: (CFDataset) input file from which the climatological output file was produced
    :param t_start: (datetime.datetime) start date of climatological output file
    :param t_end: (datetime.datetime) end date of climatological output file
    :param climo_filepath: (str) filepath to a climatological means output file which needs to have its
        metadata update

    WARNING: THIS CHANGES FILE `climo_filepath` IN PLACE

    For information on climatological statistics, and specifically on datetimes to apply to such statistics,
    see Section 7.4 of http://cfconventions.org/Data/cf-conventions/cf-conventions-1.6/build/cf-conventions.html
    """
    with CFDataset(climo_filepath, mode='r+') as cf:
        # Add start and end time attributes
        # In Python2.7, datetime.datime.isoformat does not take params telling it how much precision to
        # provide in its output; standard requires 'seconds' precision, which means the first 19 characters.
        cf.climo_start_time = t_start.isoformat()[:19] + 'Z'
        cf.climo_end_time = t_end.isoformat()[:19] + 'Z'

        # Update tracking_id attribute
        if hasattr(input_file, 'tracking_id'):
            cf.climo_tracking_id = input_file.tracking_id

        # Deduce the set of averaging intervals from the number of times in the file.
        # WARNING: This is fragile, and depends on the assumption that a climo output file contains only the following
        # possible contents: multi-decadal averages of monthly, seasonal, and annual averages, possibly concatenated
        # in that order (starting with monthly, seasonal, or annual as the original file contents allow).
        # This computation only works because each case results in a unique number of time values!
        try:
            num_times_to_interval_set = {
                12: {'monthly'},
                4: {'seasonal'},
                1: {'annual'},
                5: {'seasonal', 'annual'},
                17: {'monthly', 'seasonal', 'annual'},
            }
            interval_set = num_times_to_interval_set[cf.time_var.size]
        except KeyError:
            raise ValueError('Expected climo file to contain # time values in {}, but found {}'
                             .format(num_times_to_interval_set.keys(), cf.time_var.size))

        # Update frequency attribute to reflect that this is a climo file.
        prefix = ''.join(abbr for interval, abbr in (('monthly', 'm'), ('seasonal', 's'), ('annual', 'a'), )
                         if interval in interval_set)
        cf.frequency = prefix + 'Clim'

        # Generate info for updating time variable and creating climo bounds variable
        times, climo_bounds = generate_climo_time_var(
            dateutil.parser.parse(cf.climo_start_time[:19]),  # create tz naive dates by stripping off the tz indicator
            dateutil.parser.parse(cf.climo_end_time[:19]),
            interval_set
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
    # parser.add_argument('-c', '--climo', nargs= '+',  help='Climatological periods to generate.
    # IN PROGRESS. Defaults to all available in the input file. Ex: -c 6190 7100 8100 2020 2050 2080')
    log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()
    parser.add_argument('-l', '--loglevel', help='Logging level',
                        choices=log_level_choices, default='INFO')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true')
    parser.add_argument('-g', '--convert-longitudes', dest='convert_longitudes', action='store_true',
                        help='Transform longitude range from [0, 360) to [-180, 180)')
    parser.add_argument('-v', '--split-vars', dest='split_vars', action='store_true',
                        help='Generate a separate file for each dependent variable in the file')
    parser.add_argument('-i', '--split-intervals', dest='split_intervals', action='store_true',
                        help='Generate a separate file for each climatological period')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    parser.set_defaults(dry_run=False, convert_longitudes=False, split_vars=False, split_intervals=True)
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))
    main(args)
