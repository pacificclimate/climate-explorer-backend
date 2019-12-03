import numpy
import pytest
from ce.api.streamflow.watershed import build_watershed
from ce.api.util import index_set
from test_utils import np_array, direction_map, \
    N, NE, E, SE, S, SW, W, NW, O


routing_0x0 = np_array((()))
routing_1x1 = np_array(((N,),))

# Fully connected routing arrays: All cells connect to the mouth

routing_fc_3x3 = np_array((
    ( S,  S, SW),
    ( S, SW,  W),
    ( O,  W,  W),
))

# Linear ccw spiral; distal point at (1,2)
routing_fc_4x4 = np_array((
    ( S, W, W, W),
    ( S, S, W, N),
    ( S, S, N, N),
    ( O, E, E, N),
))

# Partially connected routing arrays: Not all cells connect to the mouth

# Nortwesternmost cell does not connect to mouth
routing_pc_3x3 = np_array((
    ( S,  S,  N),
    ( S, SW,  W),
    ( O,  W,  W),
))


# Routing arrays with loops

# Simplest and apparently most common loop
routing_loop_1x2 = np_array((
    (E, W),
))

# Loop covering all cells in 2x2
routing_loop_2x2_quad = np_array((
    (E, S),
    (N, W),
))

# Loop covering only 3 cells in 2x2
routing_loop_2x2_tri = np_array((
    (E,  S),
    (S, NW),
))


@pytest.mark.parametrize(
    'mouth, routing, direction_map, expected', (
            # Trivial cases
            ((0, 0), routing_0x0, None, {(0, 0)}),
            ((0, 0), routing_1x1, None, {(0, 0)}),

            # Fully connected watersheds
            ((0, 0), routing_fc_3x3, direction_map, index_set(3, 3)),
            ((1, 1), routing_fc_3x3, direction_map, index_set((1,3), (1,3))),
            ((0, 0), routing_fc_4x4, direction_map, index_set(4, 4)),
            ((1, 0), routing_fc_4x4, direction_map, index_set(4, 4) - {(0, 0)}),

            # Partly connected watersheds
            ((0, 0), routing_pc_3x3, direction_map,
             index_set(3, 3) - {(2, 2)}),
            ((1, 1), routing_pc_3x3, direction_map,
             index_set((1,3), (1,3)) - {(2, 2)}),

            # Watersheds with loops
            ((0, 0), routing_loop_1x2, direction_map, index_set(1, 2)),
            ((0, 1), routing_loop_1x2, direction_map, index_set(1, 2)),
            ((0, 0), routing_loop_2x2_quad, direction_map, index_set(2, 2)),
            ((1, 1), routing_loop_2x2_quad, direction_map, index_set(2, 2)),
            ((0, 0), routing_loop_2x2_tri, direction_map, {(0, 0)}),
            ((1, 1), routing_loop_2x2_tri, direction_map,
             index_set(2, 2) - {(0, 0)}),
    )
)
def test_build_watershed(mouth, routing, direction_map, expected):
    watershed = build_watershed(mouth, routing, direction_map)
    assert watershed == expected
