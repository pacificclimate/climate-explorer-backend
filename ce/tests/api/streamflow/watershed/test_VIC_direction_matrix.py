import pytest
from ce.api.streamflow.watershed import VIC_direction_matrix


@pytest.mark.parametrize(
    "lat_step, lon_step, northeast",
    (
        (1.1, 1.5, (1, 1)),
        (2.2, -2.2, (1, -1)),
        (-3.3, 3.3, (-1, 1)),
        (-4.4, -4.4, (-1, -1)),
    ),
)
def test_VIC_direction_matrix(lat_step, lon_step, northeast):
    dm = VIC_direction_matrix(lat_step, lon_step)

    # Check generic expected types and values
    for i in range(10):
        for j in range(2):
            assert dm[i][j] in (-1, 0, 1)

    # Check fixed special cases
    assert dm[0] == (0, 0)
    assert dm[9] == (0, 0)

    # Check reference vector
    assert dm[2] == northeast

    # Check that diametrically opposite vectors point in opposite directions
    for i in range(1, 8):
        for j in range(2):
            assert dm[i][j] == -dm[((i + 3) % 8) + 1][j], "i = {}, j = {}".format(i, j)
