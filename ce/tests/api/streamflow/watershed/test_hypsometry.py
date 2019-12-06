import pytest
from ce.api.streamflow.watershed import hypsometry


@pytest.mark.parametrize('elevations, areas, exception', (
        ([1, 2], [5, 10, 20], IndexError),
))
def test_validation(elevations, areas, exception):
    with pytest.raises(exception):
        hypsometry(elevations, areas)


@pytest.mark.parametrize(
    'elevations, areas, bin_start, bin_width, num_bins, e_cum_areas',
    (
        # No bin clipping
        ([4.9, 10.1],     [1] * 2, 0, 10, 2, [1, 1]),
        ([4.9, 10.1],     [1] * 2, 0, 5, 4, [1, 0, 1, 0]),
        ([10.1, 4.9],     [1] * 2, 0, 10, 2, [1, 1]),
        ([10.1, 20.1],    [1] * 2, 0, 20, 2, [1, 1]),
        ([4.9, 10.1],     [1, 2],  0, 10, 2, [1, 2]),
        ([4.9, 10.1] * 2, [1] * 4, 0, 10, 2, [2, 2]),
        ([4.9, 10.1] * 4, [1] * 8, 0, 10, 2, [4, 4]),
        ([39.9, 29.9, 19.9, 9.9], [1] * 4, 0, 20, 2, [2, 2]),

        # Bin clipping
        ([4.9, 10, 20, 25.1], [2, 1, 1, 3], 5, 10, 2, [3, 4]),
    ))
def test_computation(
        elevations, areas, bin_start, bin_width, num_bins, e_cum_areas
):
    cumulative_areas = hypsometry(
        elevations, areas, bin_start, bin_width, num_bins)
    assert len(cumulative_areas) == num_bins
    assert cumulative_areas == e_cum_areas
    assert sum(cumulative_areas) == sum(areas)

