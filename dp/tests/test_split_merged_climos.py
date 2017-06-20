from datetime import datetime
import os
from pytest import mark

from netCDF4 import date2num

from nchelpers import CFDataset
from dp.split_merged_climos import split_merged_climos


# Helper functions

def basename_components(filepath):
    """Returns the CMOR(ish) components of the basename (filename) of the given filepath."""
    # Slightly tricky because variable names can contain underscores, which separate components.
    # We find the location f of the frequency component in the split and use it to assemble the components properly.
    pieces = os.path.basename(filepath).split('_')
    f = next(i for i, piece in enumerate(pieces) if 'Clim' in piece)
    return ['_'.join(pieces[:f])] + pieces[f:]


datasets = 'gcm_climos gcm_360_climos downscaled_tasmax_climos hydromodel_gcm_climos'.split()

# Tests

@mark.parametrize('tiny_dataset', datasets, indirect=['tiny_dataset'])
def test_existence(outdir, tiny_dataset):
    split_filepaths = split_merged_climos(tiny_dataset, outdir)
    expected_num_splits = len(tiny_dataset.frequency[:-4])  # number of letters before 'Clim' is number of interval sets
    assert len(split_filepaths) == expected_num_splits
    assert len(os.listdir(outdir)) == expected_num_splits
    assert set(split_filepaths) == set(os.path.join(outdir, f) for f in os.listdir(outdir))


@mark.parametrize('tiny_dataset', datasets, indirect=['tiny_dataset'])
def test_filenames(outdir, tiny_dataset):
    split_filepaths = split_merged_climos(tiny_dataset, outdir)
    assert {basename_components(fp)[0] for fp in split_filepaths} == {'+'.join(sorted(tiny_dataset.dependent_varnames))}
    assert {basename_components(fp)[1] for fp in split_filepaths} == {'mClim', 'sClim', 'aClim'}


@mark.parametrize('tiny_dataset', datasets, indirect=['tiny_dataset'])
def test_metadata_and_time(outdir, tiny_dataset):
    split_filepaths = split_merged_climos(tiny_dataset, outdir)
    for fp in split_filepaths:
        with CFDataset(fp) as cf:
            assert cf.is_multi_year_mean
            assert cf.frequency in {'mClim', 'sClim', 'aClim'}

            assert cf.time_var.size == {
                'mClim': 12,
                'sClim': 4,
                'aClim': 1,
            }[cf.frequency]

            def d2n(date):
                return date2num(date, cf.time_var.units, cf.time_var.calendar)

            year = tiny_dataset.time_steps['datetime'][0].year
            assert cf.time_var[0] == {
                'mClim': d2n(datetime(year, 1, 15)),
                'sClim': d2n(datetime(year, 1, 16)),
                'aClim': d2n(datetime(year, 7, 2)),
            }[cf.frequency]


@mark.parametrize('tiny_dataset', datasets, indirect=['tiny_dataset'])
def test_dependent_variables(outdir, tiny_dataset):
    split_filepaths = split_merged_climos(tiny_dataset, outdir)
    for fp in split_filepaths:
        with CFDataset(fp) as cf:
            assert tiny_dataset.dependent_varnames == cf.dependent_varnames