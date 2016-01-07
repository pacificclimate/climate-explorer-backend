import os
from datetime import datetime

def d2ss(d):
    return datetime.strftime(d, '%Y%m%d')

class Cmip5File(object):

    def __init__(self, fp=None, **kwargs):
        '''
        Documentation in section 3.4: http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf

        Parses or builds a PCIC CMIP5 file path with specific metadata.
        Pattern is "<base_dir>/<institue>/<model>/<experiment>/<frequency>/<modeling realm>/<MIP table>/<ensemble member>/<version>/<variable name>/<CMOR filename>.nc"
                        -11       -10       -9        -8           -7            -6             -5           -4              -3           -2              -1
        CMOR filename is of pattern <variable_name>_<MIP table>_<model>_<experiment>_<ensemble member>_<temporal subset>.nc
                                           1             2         3         4               5                  6
        ex: root_dir/CCCMA/CanCM4/historical/day/atmos/day/r1i1p1/v20120612/tasmax/tasmax_day_CanCM4_historical_r1i1p1_19610101-20051231.nc
        Metadata requirements are found: http://cmip-pcmdi.llnl.gov/cmip5/docs/CMIP5_output_metadata_requirements.pdf
        Data Reference Syntax: http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
        Standard Output (CMOR Tables): http://cmip-pcmdi.llnl.gov/cmip5/docs/standard_output.pdf
        '''

        if fp:
            dirname, basename = os.path.split(os.path.abspath(fp))
            splitdirs = dirname.split('/')
            self.institute, self.model, self.experiment, self.freq, self.realm, self.mip_table, self.run, self.version, self.variable = splitdirs[-9:]
            self.root = os.path.sep + os.path.join(*splitdirs[:-9])
            self.trange = os.path.splitext(basename)[0].split('_')[-1]

        else:
            required_meta = ['institute', 'model', 'experiment', 'freq', 'realm', 'mip_table', 'run', 'version', 'variable', 'trange']
            for att in required_meta:
                try:
                    v = kwargs.pop(att)
                    setattr(self, att, v)
                except KeyError:
                    raise KeyError('Required attribute "{}" not provided'.format(att))
            if len(kwargs) != 0:
                for k, v in kwargs.items():
                    setattr(self, k, v)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.fullpath

    def __repr__(self):
        s = "Cmip5File("
        args = ", ".join(["{} = '{}'".format(k, v) for k, v in self.__dict__.items()])
        # if self.root:
        #     args += ", root = '{}'".format(self.root)
        s += args + ")"
        return s

    @property
    def basename(self):
        return '_'.join([self.variable, self.mip_table, self.model, self.experiment, self.run, self.trange]) + '.nc'

    @property
    def dirname(self, root=None):
        if not root: root = self.root
        return os.path.join(root, self.institute, self.model, self.experiment, self.freq, self.realm, self.mip_table, self.run, self.version, self.variable)

    @property
    def fullpath(self):
        return os.path.join(self.dirname, self.basename)

    @property
    def t_start(self):
        return self.trange.split('-')[0]

    @t_start.setter
    def t_start(self, value):
        self.trange = '-'.join([value, self.trange.split('-')[1]])

    @property
    def t_end(self):
        return self.trange.split('-')[1]

    @t_end.setter
    def t_end(self, value):
        self.trange = '-'.join([self.trange.split('-')[0], value])

    def generate_output_fp(self, t_range, outdir):
        '''The input file path and the output file path are not the same
           since the CDO commands change some properties (MIP table,
           date range) of which the file path consists.
        '''
        new_mip_table = {'day': 'monClim', 'mon': 'monClim', 'yr': 'yrClim'}[self.freq]
        dirname = os.path.join(outdir, self.institute, self.model, self.experiment, self.freq, self.realm, new_mip_table, self.run, self.version, self.variable)
        basename = '{}_{}_{}_{}_{}_{}-{}.nc'.format(self.variable, new_mip_table, self.model, self.experiment, self.run, d2ss(t_range[0]), d2ss(t_range[1]))
        return os.path.realpath(os.path.join(dirname, basename))

class ClimdexFile(Cmip5File):
    ''' See DB's ClimDEX directory in /home/data/climate/CLIMDEX/CMIP5
    '''
    def __init__(self, fp=None, **kwargs):
        if fp:
            dirname, basename = os.path.split(os.path.abspath(fp))
            splitdirs = dirname.split('/')
            variable, freq, model, experiment, run, trange = basename.strip('.nc').split('_')
            kwargs.update({
                    'experiment': experiment,
                    'model': model,
                    'run': run,
                    'freq': freq,
                    'realm': 'atmos',
                    'mip_table': freq,
                    'version': 'vUnknown', # FIXME: get this from file modtime
                    'institute': 'unknown', # FIXME: get this from NetCDF metadata
                    'variable': variable,
                    'trange': trange
                    })
            self.root = os.path.sep + os.path.join(*splitdirs[:-3])
        else:
            raise Exception()
        super(ClimdexFile, self).__init__(**kwargs)

    @property
    def dirname(self, root=None):
        '''This is where to *find* the files
        '''
        if not root:
            root = self.root
        return os.path.join(root, self.experiment, self.model, self.run)
