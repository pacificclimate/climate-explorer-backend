import numpy
from itertools import product
import pytest
from sqlalchemy.orm.exc import NoResultFound
from ce.api.streamflow.watershed import \
    get_time_invariant_variable_dataset, \
    hypsometry, \
    VIC_direction_matrix, \
    build_watershed

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
    assert sum(cumulative_areas) == sum(areas)


@pytest.mark.parametrize('lat_step, lon_step, northeast', (
    (1.1, 1.5,   [1, 1]),
    (2.2, -2.2,  [1, -1]),
    (-3.3, 3.3,  [-1, 1]),
    (-4.4, -4.4, [-1, -1]),
))
def test_VIC_direction_matrix(lat_step, lon_step, northeast):
    dm = VIC_direction_matrix(lat_step, lon_step)

    # Check generic expected types and values
    for i in range(10):
        for j in range(2):
            assert dm[i][j] in (-1, 0, 1)

    # Check fixed special cases
    assert dm[0] == [0, 0]
    assert dm[9] == [0, 0]

    # Check reference vector
    assert dm[2] == northeast

    # Check that diametrically opposite vectors point in opposite directions
    for i in range(1, 8):
        for j in range(2):
            assert dm[i][j] == -dm[((i+3) % 8) + 1][j], \
                'i = {}, j = {}'.format(i,j)

# build_watershed test

direction_map = (
    ( 0,  0),   # filler - 0 is not used in the encoding
    ( 1,  0),   # 1 = north
    ( 1,  1),   # 2 = northeast
    ( 0,  1),   # 3 = east
    (-1,  1),   # 4 = southeast
    (-1,  0),   # 5 = south
    (-1, -1),   # 6 = southwest
    ( 0, -1),   # 7 = west
    ( 1, -1),   # 8 = northwest
    ( 0,  0),   # 9 = outlet    
)

N = 1
NE = 2
E = 3
SE = 4
S = 5
SW = 6
W = 7
NW = 8
O = 9


def routing(a, rev_rows=True):
    """Return a VIC routing array constructed from an array-like object `a`.

    Argument `rev` is convenient for layout of routing maps, where the
    longitude index (row) increases northward/upward, the reverse of
    array/tuple literal layout in text.
    """
    if rev_rows:
        a = tuple(reversed(a))
    return numpy.array(a)


# Fully connected routing arrays: All cells connect to the mouth

routing_fc_3x3 = routing((
    ( S,  S, SW),
    ( S, SW,  W),
    ( O,  W,  W),
))

# Linear ccw spiral; distal point at (1,2)
routing_fc_4x4 = routing((
    ( S, W, W, W),
    ( S, S, W, N),
    ( S, S, N, N),
    ( O, E, E, N),
))

# Partially connected routing arrays: Not all cells connect to the mouth

# Nortwesternmost cell does not connect to mouth
routing_pc_3x3 = routing((
    ( S,  S,  N),
    ( S, SW,  W),
    ( O,  W,  W),
))


# Routing arrays with loops

# Simplest and apparently most common loop
routing_loop_1x2 = routing((
    (E, W),
))

# Loop covering all cells in 2x2
routing_loop_2x2_quad = routing((
    (E, S),
    (N, W),
))

# Loop covering only 3 cells in 2x2
routing_loop_2x2_tri = routing((
    (E,  S),
    (S, NW),
))


def index_set(m, n):
    """Return the set of all indices of an m x n matrix"""
    def tuplify(x): return x if type(x) == tuple else (x,)
    return set(product(range(*tuplify(m)), range(*tuplify(n))))


@pytest.mark.parametrize(
    'mouth, routing, direction_map, max_depth, expected', (
        # Trivial case
        (None, None, None, 0, {None}),
        
        # Fully connected watersheds
        ((0, 0), routing_fc_3x3, direction_map, 10, index_set(3, 3)),
        ((1, 1), routing_fc_3x3, direction_map, 10, index_set((1,3), (1,3))),
        ((0, 0), routing_fc_4x4, direction_map, 20, index_set(4, 4)),
        ((1, 0), routing_fc_4x4, direction_map, 20, index_set(4, 4) - {(0, 0)}),

        # Partly connected watersheds
        ((0, 0), routing_pc_3x3, direction_map, 10,
         index_set(3, 3) - {(2, 2)}),
        ((1, 1), routing_pc_3x3, direction_map, 10,
         index_set((1,3), (1,3)) - {(2, 2)}),

        # Watersheds with loops
        ((0, 0), routing_loop_1x2, direction_map, 10, index_set(1, 2)),
        ((0, 1), routing_loop_1x2, direction_map, 10, index_set(1, 2)),
        ((0, 0), routing_loop_2x2_quad, direction_map, 10, index_set(2, 2)),
        ((1, 1), routing_loop_2x2_quad, direction_map, 10, index_set(2, 2)),
        ((0, 0), routing_loop_2x2_tri, direction_map, 10, {(0, 0)}),
        ((1, 1), routing_loop_2x2_tri, direction_map, 10,
         index_set(2, 2) - {(0, 0)}),

        # Recursion depth limit tests
        ((0, 0), routing_fc_4x4, direction_map, 14,
         index_set(4, 4) - {(1, 2)}),
        ((0, 0), routing_fc_4x4, direction_map, 13,
         index_set(4, 4) - {(1, 2), (2, 2)}),
    ))
def test_build_watershed(
        mouth, routing, direction_map, max_depth, expected
):
    watershed = build_watershed(mouth, routing, direction_map, max_depth)
    assert set(watershed) == expected
