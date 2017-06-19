"""Unit tests for the core function create_climo_files.

These tests are all parametrized over several test input files, which requires a little trickiness with fixtures.
pytest doesn't directly support parametrizing over fixtures (which here deliver the test input files
and the output of create_climo_files). To get around that, we use indirect fixtures, which are passed a parameter
that they use to determine their behaviour, i.e. what input file to return or process.

The key indirected fixtures are:

    tiny_dataset
        param: (str) selects the input file to be processed by create_climo_files
        returns: (nchelpers.CFDataset) input file to be processed by create_climo_files
    
    climo_files
        request.param: (tuple): (code, t_start, t_end, options)
            code: (str) code for selecting input file; selected input file is passed as first param to create_climo_files
            t_start: (datetime.datetime) start date of climo period
            t_end: (datetime.datetime) end date of climo period
            options: (dict) keyword parameters (options) of create_climo_files
        returns: result of invoking create_climo_files: list of output filepaths
    
    input_and_climo_files
        request.param: as for climo_files
        returns: (tiny_dataset, climo_files) as above
    
Values for climo period options are only specified when they are different from the default.
"""
# TODO: Add more test input files:
# - hydromodel from observed data

import os
from datetime import datetime

from netCDF4 import date2num
from dateutil.relativedelta import relativedelta
from pytest import mark
import numpy as np

from nchelpers import CFDataset

from dp.units_helpers import Unit
from dp.generate_climos import create_climo_files


def t_start(year):
    """Returns the start date of a climatological processing period beginning at start of year"""
    return datetime(year, 1, 1)


def t_end(year):
    """Returns the end date of a climatological processing period ending at end of year"""
    return datetime(year, 12, 30)


def basename_components(filepath):
    """Returns the CMOR(ish) components of the basename (filename) of the given filepath."""
    # Slightly tricky because variable names can contain underscores, which separate components.
    # We find the location f of the frequency component in the split and use it to assemble the components properly.
    pieces = os.path.basename(filepath).split('_')
    f = next(i for i, piece in enumerate(pieces) if piece in 'msaClim saClim aClim'.split())
    return ['_'.join(pieces[:f])] + pieces[f:]


@mark.parametrize('tiny_dataset, t_start, t_end, options, num_files', [
    ('gcm', t_start(1965), t_end(1970), {}, 1),
    ('gcm', t_start(1965), t_end(1970), {'split_vars': True}, 1),
    ('gcm_360_day_cal', t_start(1965), t_end(1970), {}, 1),  # test date processing
    ('downscaled_tasmax', t_start(1961), t_end(1990), {}, 1),
    ('downscaled_pr', t_start(1961), t_end(1990), {}, 1),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {}, 1),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'split_vars': True}, 6),
], indirect=['tiny_dataset'])
def test_existence(outdir, tiny_dataset, t_start, t_end, options, num_files):
    """Test that the expected number of files was created and that the filenames returned by
    create_climo_files are those actually created.
    """
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)
    assert len(climo_files) == num_files
    assert len(os.listdir(outdir)) == num_files
    assert set(climo_files) == set(os.path.join(outdir, f) for f in os.listdir(outdir))


@mark.parametrize('tiny_dataset, t_start, t_end, options', [
    ('gcm', t_start(1965), t_end(1970), {}),
    ('gcm', t_start(1965), t_end(1970), {'split_vars': True}),
    ('downscaled_tasmax', t_start(1961), t_end(1990), {}),
    ('downscaled_pr', t_start(1961), t_end(1990), {}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'split_vars': True}),
], indirect=['tiny_dataset'])
def test_filenames(outdir, tiny_dataset, t_start, t_end, options):
    """Test that the filenames are as expected. Tests only the following easy-to-test filename components:
    - variable name
    - frequency
    Testing all the components of the filenames would be a lot of work and would duplicate unit tests for
    the filename generator in nchelpers.
    """
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)
    if len(climo_files) == 1:
        varnames = {'+'.join(sorted(tiny_dataset.dependent_varnames))}
    else:
        varnames = set(tiny_dataset.dependent_varnames)
    assert varnames == set(basename_components(fp)[0] for fp in climo_files)
    for fp in climo_files:
        with CFDataset(fp) as cf:
            assert all(cf.frequency in basename_components(fp) for fp in climo_files)


@mark.parametrize('tiny_dataset, t_start, t_end, options', [
    ('gcm', t_start(1965), t_end(1970), {}),
    ('downscaled_tasmax', t_start(1961), t_end(1990), {}),
    ('downscaled_pr', t_start(1961), t_end(1990), {}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'split_vars': True}),
], indirect=['tiny_dataset'])
def test_climo_metadata(outdir, tiny_dataset, t_start, t_end, options):
    """Test that the correct climo-specific metadata has been added/updated."""
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)
    for fp in climo_files:
        with CFDataset(fp) as cf:
            assert cf.is_multi_year_mean
            assert cf.frequency == {
                'daily': 'msaClim',
                'monthly': 'saClim',
                'yearly': 'aClim'
            }[tiny_dataset.time_resolution]
            # In Python2.7, datetime.datime.isoformat does not take params telling it how much precision to
            # provide in its output; standard requires 'seconds' precision, which means the first 19 characters.
            assert cf.climo_start_time == t_start.isoformat()[:19] + 'Z'
            assert cf.climo_end_time == t_end.isoformat()[:19] + 'Z'
            assert getattr(cf, 'climo_tracking_id', None) == getattr(tiny_dataset, 'tracking_id', None)


@mark.parametrize('tiny_dataset, t_start, t_end, options', [
    ('downscaled_pr', t_start(1965), t_end(1970), {}),
    ('downscaled_pr_packed', t_start(1965), t_end(1970), {}),
], indirect=['tiny_dataset'])
def test_pr_units_conversion(outdir, tiny_dataset, t_start, t_end, options):
    """Test that units conversion for 'pr' variable is performed properly, for both packed and unpacked files.
    Test for unpacked file is pretty elementary: check pr units.
    Test for packed checks that packing params are modified correctly.
    """
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)
    assert 'pr' in tiny_dataset.dependent_varnames
    input_pr_var = tiny_dataset.variables['pr']
    assert input_pr_var.units.endswith('s-1')
    seconds_per_day = 86400
    for fp in climo_files:
        with CFDataset(fp) as cf:
            if 'pr' in cf.dependent_varnames:
                output_pr_var = cf.variables['pr']
                assert Unit.from_udunits_str(output_pr_var.units) in [Unit('kg/m**2/day'), Unit('mm/day')]
                if hasattr(input_pr_var, 'scale_factor') or hasattr(input_pr_var, 'add_offset'):
                    try:
                        assert output_pr_var.scale_factor == seconds_per_day * input_pr_var.scale_factor
                    except AttributeError:
                        assert output_pr_var.scale_factor == seconds_per_day * 1.0
                    try:
                        assert output_pr_var.add_offset == seconds_per_day * input_pr_var.add_offset
                    except AttributeError:
                        assert output_pr_var.add_offset == 0.0


@mark.parametrize('tiny_dataset, t_start, t_end, options', [
    ('gcm', t_start(1965), t_end(1970), {}),
    ('downscaled_tasmax', t_start(1961), t_end(1990), {}),
    ('downscaled_pr', t_start(1961), t_end(1990), {}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'split_vars': True}),
], indirect=['tiny_dataset'])
def test_dependent_variables(outdir, tiny_dataset, t_start, t_end, options):
    """Test that the output files contain the expected dependent variables"""
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)
    dependent_varnames_in_cfs = set()
    for fp in climo_files:
        with CFDataset(fp) as cf:
            dependent_varnames_in_cfs.update(cf.dependent_varnames)
            if len(climo_files) > 1:
                # There should be one dependent variable from the input file
                assert len(cf.dependent_varnames) == 1
    # All the input dependent variables should be covered by all the output files
    assert dependent_varnames_in_cfs == set(tiny_dataset.dependent_varnames)


@mark.parametrize('tiny_dataset, t_start, t_end, options', [
    ('gcm', t_start(1965), t_end(1970), {}),
    ('downscaled_tasmax', t_start(1961), t_end(1990), {}),
    # No need to repleat with downscaled_pr
    ('hydromodel_gcm', t_start(1984), t_end(1995), {}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'split_vars': True}),
], indirect=['tiny_dataset'])
def test_time_and_climo_bounds_vars(outdir, tiny_dataset, t_start, t_end, options):
    """Test that the climo output files contain the expected time values and climo bounds. """
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)

    expected_num_time_values = {
        'daily': 17,
        'monthly': 5,
        'yearly': 1,
    }[tiny_dataset.time_resolution]

    for fp in climo_files:
        with CFDataset(fp) as cf:
            assert cf.time_var
            assert cf.time_var.climatology == 'climatology_bnds'
            climo_bnds_var = cf.variables[cf.time_var.climatology]
            assert climo_bnds_var

            assert len(cf.time_var) == expected_num_time_values
            assert len(climo_bnds_var) == expected_num_time_values

            climo_year = (t_start.year + t_end.year + 1) / 2
            time_steps = (t for t in cf.time_steps['datetime'])
            climo_bnds = (cb for cb in climo_bnds_var)

            def d2n(date):
                return date2num(date, cf.time_var.units, cf.time_var.calendar)

            # Test monthly mean timesteps and climo bounds
            if expected_num_time_values == 17:
                for month in range(1, 13):
                    t = next(time_steps)
                    assert (t.year, t.month, t.day) == (climo_year, month, 15)
                    cb = next(climo_bnds)
                    assert len(cb) == 2
                    assert cb[0] == d2n(datetime(t_start.year, month, 1))
                    assert cb[1] == d2n(datetime(t_end.year, month, 1) + relativedelta(months=1))

            # Test seasonal mean timesteps and climo bounds
            if expected_num_time_values >= 5:
                for month in [1, 4, 7, 10]:  # center months of seasons
                    t = next(time_steps)
                    assert (t.year, t.month, t.day) == (climo_year, month, 16)
                    cb = next(climo_bnds)
                    assert cb[0] == d2n(datetime(t_start.year, month, 1) + relativedelta(months=-1))
                    assert cb[1] == d2n(datetime(t_end.year, month, 1) + relativedelta(months=2))

            # Test annual mean timestep and climo bounds
            t = next(time_steps)
            assert (t.year, t.month, t.day) == (climo_year, 7, 2)
            cb = next(climo_bnds)
            assert cb[0] == d2n(t_start)
            assert cb[1] == d2n(datetime(t_end.year+1, 1, 1))


@mark.parametrize('tiny_dataset, t_start, t_end, options', [
    # input_and_climo_files parameters: (code, t_start, t_end, options)
    ('gcm', t_start(1965), t_end(1970), {'convert_longitudes': False}),
    ('gcm', t_start(1965), t_end(1970), {'convert_longitudes': True}),
    ('downscaled_tasmax', t_start(1961), t_end(1990), {'convert_longitudes': False}),
    ('downscaled_tasmax', t_start(1961), t_end(1990), {'convert_longitudes': True}),
    # No need to repleat with downscaled_pr
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'convert_longitudes': False}),
    ('hydromodel_gcm', t_start(1984), t_end(1995), {'convert_longitudes': True}),
], indirect=['tiny_dataset'])
def test_convert_longitudes(outdir, tiny_dataset, t_start, t_end, options):
    """Test that longitude conversion is performed correctly."""
    climo_files = create_climo_files(outdir, tiny_dataset, t_start, t_end, **options)
    input_lon_var = tiny_dataset.lon_var
    for fp in climo_files:
        with CFDataset(fp) as output_file:
            output_lon_var = output_file.lon_var
            check_these = [(input_lon_var, output_lon_var)]
            if hasattr(input_lon_var, 'bounds'):
                check_these.append((tiny_dataset.variables[input_lon_var.bounds],
                                    output_file.variables[output_lon_var.bounds]))
            for input_lon_var, output_lon_var in check_these:
                if options.get('convert_longitudes', False):
                    assert all(-180 <= lon < 180 for _, lon in np.ndenumerate(output_lon_var))
                    assert all(output_lon_var[i] == input_lon if input_lon < 180 else input_lon - 360
                               for i, input_lon in np.ndenumerate(input_lon_var))
                else:
                    assert all(-180 <= lon < 360 for _, lon in np.ndenumerate(output_lon_var))
                    assert all(output_lon_var[i] == input_lon for i, input_lon in np.ndenumerate(input_lon_var))

    