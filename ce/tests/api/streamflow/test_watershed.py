import math
import pytest
from sqlalchemy.orm.exc import NoResultFound
from ce.api.streamflow.watershed import \
    get_time_invariant_variable_dataset, \
    hypsometry

@pytest.mark.parametrize('variable, exception', (
    ('bargle', NoResultFound),  # does not exist
    # TODO: Give tasmin-related test DataFiles a defined TimeSet and
    #  test this case.
    # ('tasmin', NoResultFound),  # exists, not time-invariant
    ('flow_direction', None),   # exists, time-invariant
))
def test_get_time_invariant_variable_dataset(populateddb, variable, exception):
    if exception:
        with pytest.raises(exception):
            file = get_time_invariant_variable_dataset(
                populateddb.session, 'ce', variable)
    else:
        file = get_time_invariant_variable_dataset(
            populateddb.session, 'ce', variable)


@pytest.mark.parametrize('elevations, areas, exception', (
    ([1, 2], [5, 10, 20], IndexError),
))
def test_hypsometry_exceptions(elevations, areas, exception):
    with pytest.raises(exception):
        hypsometry(elevations, areas)


@pytest.mark.parametrize('elevations, areas, num_bins, expected', (
    ([5, 10],     [1] * 2, 2, (7.5, [3.75, 11.25], [1, 1])),
    ([10, 5],     [1] * 2, 2, (7.5, [3.75, 11.25], [1, 1])),
    ([10, 20],    [1] * 2, 2, (10,  [10, 20], [1, 1])),
    ([5, 10],     [1, 2],  2, (7.5, [3.75, 11.25], [1, 2])),
    ([5, 10] * 2, [1] * 4, 2, (7.5, [3.75, 11.25], [2, 2])),
    ([5, 10] * 4, [1] * 8, 2, (7.5, [3.75, 11.25], [4, 4])),
    (list(range(40,0,-10)), [1] * 4, 2, (20,  [15, 35], [2, 2])),
))
def test_hypsometry(elevations, areas, num_bins, expected):
    bin_width, bin_centres, cumulative_areas = \
        hypsometry(elevations, areas, num_bins)
    e_bin_width, e_bin_centres, e_cum_areas, = expected
    assert bin_width == e_bin_width
    assert len(bin_centres) == num_bins
    assert bin_centres == e_bin_centres
    assert len(cumulative_areas) == num_bins
    assert cumulative_areas == e_cum_areas
