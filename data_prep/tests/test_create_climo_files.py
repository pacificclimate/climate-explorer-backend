"""Unit tests for the core function create_climo_files.

These tests are all parametrized over several test input files, which requires a little trickiness with fixtures.
pytest doesn't directly support parametrizing over fixtures (which here deliver the test input files
and the output of create_climo_files). To get around that, we use indirect fixtures, which are passed a parameter
that they use to determine their behaviour, i.e. what input file to return or process.

The key indirected fixtures are:

input_file
    param: (str) selects the input file to be processed by create_climo_files
    returns: (nchelpers.CFDataset) input file to be processed by create_climo_files

climo_files
    request.param: (tuple)
        [0]: code for selecting input file; selected input file is passed as first param to create_climo_files
        [1:]: remaining parameters of create_climo_files
    returns: result of invoking create_climo_files: list of output filepaths

input_and_climo_files
    request.param: as for climo_files
    returns: (input_file, climo_files) as above
"""
# TODO: Add more test input files:
# - downscaled with pr variable
# - hydromodel from observed data

import os
import datetime
from pytest import mark
from nchelpers import CFDataset


def t_start(year):
    """Returns the start date of a climatological processing period beginning at start of year"""
    return datetime.datetime(year, 1, 1)


def t_end(year):
    """Returns the end date of a climatological processing period ending at end of year"""
    return datetime.datetime(year, 12, 30)


def basename_components(filepath):
    """Returns the CMOR(ish) components of the basename (filename) of the given filepath."""
    # Slightly tricky because variable names can contain underscores, which separate components.
    # We find the location f of the frequency component in the split and use it to assemble the components properly.
    pieces = os.path.basename(filepath).split('_')
    f = next(i for i, piece in enumerate(pieces) if piece in 'msaClim saClim aClim'.split())
    return ['_'.join(pieces[:f])] + pieces[f:]


@mark.parametrize('climo_files, num_files', [
    (('gcm', False, t_start(1965), t_end(1970)), 1),
    (('gcm', True, t_start(1965), t_end(1970)), 1),
    (('downscaled_tasmax', False, t_start(1961), t_end(1990)), 1),
    (('hydromodel_gcm', False, t_start(1984), t_end(1995)), 1),
    (('hydromodel_gcm', True, t_start(1984), t_end(1995)), 6),
], indirect=['climo_files'])
def test_existence(outdir, climo_files, num_files):
    """Test that the expected number of files was created and that the filenames returned by
    create_climo_files are those actually created.
    """
    assert len(climo_files) == num_files
    assert len(os.listdir(outdir)) == num_files
    assert set(climo_files) == set(os.path.join(outdir, f) for f in os.listdir(outdir))


@mark.parametrize('input_and_climo_files', [
    ('gcm', False, t_start(1965), t_end(1970)),
    ('gcm', True, t_start(1965), t_end(1970)),
    ('downscaled_tasmax', False, t_start(1961), t_end(1990)),
    ('hydromodel_gcm', False, t_start(1984), t_end(1995)),
    ('hydromodel_gcm', True, t_start(1984), t_end(1995)),
], indirect=['input_and_climo_files'])
def test_filenames(input_and_climo_files):
    """Test that the filenames are as expected. Tests only the following easy-to-test filename components:
    - variable name
    - frequency
    Testing all the components of the filenames would be a lot of work and would duplicate unit tests for
    the filename generator in nchelpers.
    """
    input_file, climo_files = input_and_climo_files
    if len(climo_files) == 1:
        varnames = {'+'.join(sorted(input_file.dependent_varnames))}
    else:
        varnames = set(input_file.dependent_varnames)
    assert varnames == set(basename_components(fp)[0] for fp in climo_files)
    for fp in climo_files:
        with CFDataset(fp) as cf:
            assert all(cf.frequency in basename_components(fp) for fp in climo_files)


@mark.parametrize('input_and_climo_files, t_start, t_end', [
    (('gcm', False, t_start(1965), t_end(1970)), t_start(1965), t_end(1970)),
    (('downscaled_tasmax', False, t_start(1961), t_end(1990)), t_start(1961), t_end(1990)),
    (('hydromodel_gcm', True, t_start(1984), t_end(1995)), t_start(1984), t_end(1995)),
], indirect=['input_and_climo_files'])
def test_climo_metadata(input_and_climo_files, t_start, t_end):
    """Test that the correct climo-specific metadata has been added/updated."""
    input_file, climo_files = input_and_climo_files
    for fp in climo_files:
        with CFDataset(fp) as cf:
            assert cf.frequency == {
                'daily': 'msaClim',
                'monthly': 'saClim',
                'yearly': 'aClim'
            }[input_file.time_resolution]
            assert cf.climo_start_time == t_start.isoformat()[:19] + 'Z'
            assert cf.climo_end_time == t_end.isoformat()[:19] + 'Z'
            assert getattr(cf, 'climo_tracking_id', None) == getattr(input_file, 'tracking_id', None)
            if 'pr' in cf.dependent_varnames:
                assert cf.variables['pr'].units.endswith('d-1')


@mark.parametrize('input_and_climo_files', [
    ('gcm', False, t_start(1965), t_end(1970)),
    ('downscaled_tasmax', False, t_start(1961), t_end(1990)),
    ('hydromodel_gcm', False, t_start(1984), t_end(1995)),
    ('hydromodel_gcm', True, t_start(1984), t_end(1995)),
], indirect=['input_and_climo_files'])
def test_dependent_variables(input_and_climo_files):
    """Test that the output files contain the expected dependent variables"""
    input_file, climo_files = input_and_climo_files
    dependent_varnames_in_cfs = set()
    for fp in climo_files:
        with CFDataset(fp) as cf:
            dependent_varnames_in_cfs.update(cf.dependent_varnames)
            if len(climo_files) > 1:
                # There should be one dependent variable from the input file
                # plus the added climatology_bnds dependent variable (TODO: is that right? see below)
                assert 'climatology_bnds' in cf.dependent_varnames
                assert len(cf.dependent_varnames) == 2
    # All the input dependent variables should be covered by all the output files
    # TODO: Find out if climatology_bnds should really be a dependent variable. If not, fix it
    # either by modifying how it is created create_climo_files() or by modifying how nchelpers#dependent_variables
    # works, as appropriate to how it really should be created
    assert dependent_varnames_in_cfs == set(input_file.dependent_varnames) | {'climatology_bnds'}


@mark.parametrize('input_and_climo_files, climo_year', [
    (('gcm', False, t_start(1965), t_end(1970)), 1968),
    (('downscaled_tasmax', False, t_start(1961), t_end(1990)), 1976),
    (('hydromodel_gcm', False, t_start(1984), t_end(1995)), 1990),
    (('hydromodel_gcm', True, t_start(1984), t_end(1995)), 1990),
], indirect=['input_and_climo_files'])
def test_time_var(input_and_climo_files, climo_year):
    """Test that the climo output files contain the expected time values.
    Precise testing of time values is hard. Defer to tests of generate_climo_time_var?
    """
    input_file, climo_files = input_and_climo_files
    expected_num_time_values = {
        'daily': 17,
        'monthly': 5,
        'yearly': 1,
    }[input_file.time_resolution]
    for fp in climo_files:
        with CFDataset(fp) as cf:
            assert cf.time_var
            assert cf.time_var.climatology == 'climatology_bnds'
            assert len(cf.time_var) == expected_num_time_values
            time_steps = (t for t in cf.time_steps['datetime'])
            # Test monthly mean timesteps
            if expected_num_time_values == 17:
                for month in range(1,13):
                    t = next(time_steps)
                    assert t.year == climo_year
                    assert t.month == month
                    assert t.day in [15, 16]
            # Test seasonal mean timesteps
            if expected_num_time_values >= 5:
                for month in [1, 4, 7, 10]:  # center months of seasons
                    t = next(time_steps)
                    assert t.year == climo_year
                    assert t.month == month
                    assert t.day in [15, 16, 17]  # TODO: Is day 17 really right?? Need unit tests for generate_climo_time_var
            # Test annual mean timestep
            t = next(time_steps)
            assert t.year == climo_year
