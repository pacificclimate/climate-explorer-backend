import re
import os.path
from netCDF4 import Dataset, num2date, date2num
from util import s2d, d2ss


def standard_climo_periods(calendar='standard'):
    standard_climo_years = {
        '6190': ['1961', '1990'],
        '7100': ['1971', '2000'],
        '8110': ['1981', '2010'],
        '2020': ['2010', '2039'],
        '2050': ['2040', '2069'],
        '2080': ['2070', '2099']
    }
    day = {'360_day': '30'}.get(calendar, '31')
    return dict([(k, (s2d(year[0]+'-01-01'), s2d(year[1]+'-12-'+day))) for k, year in standard_climo_years.items()])


class ProductFile(object):
    '''Exposes the salient characteristics, for the purposes of this script, of a climate data file stored as netCDF.
    These characteristics are extracted from the metadata and exposed as the following properties:
        climo_periods: the subset of the standard climo periods which this file covers
        start_date: first date in time dimension in this file
        end_date: last date in time dimension in this file
        variable: dependent variable in this file (tasmax, tasmin, pr)
        frequency: frequency (time step) of data grids in this file
        model: name of model used to generate data in this file
        experiment: code for experiment conditions provided to model, formatted for use in filenames
        ensemble_member: ensemble member code

    Also, there are utility methods that construct filename and filepath for output file of the
    climatology script. For details see their docstrings.
    '''

    def __init__(self, input_filepath, output_dir='', raise_for_variable=True):
        '''Initializer

        Args:
            input_filepath (str): path to netCDF file to be processed
            raise_for_variable (bool): if true, raise an exception if an unexpected value is determined
                for `variable` property; otherwise the exception message is used for the property (for dry-run testing)
        '''
        self.input_filepath = input_filepath
        self.output_dir = output_dir

        nc = Dataset(input_filepath)

        time_var = nc.variables['time']
        s_time = time_var[0]
        e_time = time_var[-1]
        s_date = num2date(s_time, units=time_var.units, calendar=time_var.calendar)
        e_date = num2date(e_time, units=time_var.units, calendar=time_var.calendar)

        # Detect which climatological periods can be created:
        # those periods that are a subset of the date range in the file.
        self.climo_periods = dict([(k, v) for k, v in standard_climo_periods(time_var.calendar).items()
                                   if date2num(v[0], units=time_var.units, calendar=time_var.calendar) > s_time and
                                   date2num(v[1], units=time_var.units, calendar=time_var.calendar) < e_time])

        # Expose the start and end dates of this file, as strings
        self.start_date = d2ss(s_date)
        self.end_date = d2ss(e_date)

        # Find the dependent variables in this file. We expect only one, either taxmax, tasmin, or pr.
        # Expose that one as self.variable
        independent_variables = 'lon lon_bnds lat lat_bnds height height_bnds time time_bnds climatology_bounds'.split()
        dependent_variables = [name for name in nc.variables.keys() if name not in independent_variables]
        expected_dependent_variables = 'tasmax tasmin pr'.split()
        try:
            if len(dependent_variables) != 1:
                raise ValueError('Expected file to contain 1 dependent variable, found {}: {}'
                                 .format(len(dependent_variables), ', '.join(dependent_variables)))
            self.variable = dependent_variables[0]
            if self.variable not in expected_dependent_variables:
                raise ValueError('Expected dependent variable to be one of {} but found {}'.format(
                    ', '.join(expected_dependent_variables), self.variable
                ))
        except ValueError as e:
            if raise_for_variable:
                raise
            else:
                self.variable = 'ERROR: {}'.format(e)

        # Extract other metadata from the file header, mostly used for constructing output filename
        self.frequency = getattr(nc, 'frequency', 'unknown')
        self.model = getattr(nc, 'driving_model_id', 'unknown')
        self.experiment = '+'.join(re.split('\s*,\s*', getattr(nc, 'driving_experiment_name', 'unknown')))
        self.ensemble_member = getattr(nc, 'driving_model_ensemble_member', 'unknown')

        nc.close()

    def output_filename(self, t_start, t_end):
        '''Generate an appropriate CMOR filename for the climatology output file that will be generated 
        by this script.
        '''
        return '{variable}_{mip_table}_{model}_{experiment}_{ensemble_member}_{t_start}-{t_end}'.format(
            variable=self.variable,
            mip_table={'day': 'Amon', 'mon': 'aMon', 'yr': 'Ayr', 'unknown': 'unknown'}[self.frequency],
            model=self.model,
            experiment=self.experiment,
            ensemble_member=self.ensemble_member,
            t_start=d2ss(t_start),
            t_end=d2ss(t_end)
        )

    def output_filepath(self, t_start, t_end):
        '''Join the output directory to the output filename for this file'''
        return os.path.realpath(os.path.join(self.output_dir, self.output_filename(t_start, t_end)))


