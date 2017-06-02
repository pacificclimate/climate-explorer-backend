import pytest

from dp.units_helpers import Unit


def test_d_for_day():
    assert Unit('d') == Unit('day')
    assert Unit('day').to_udunits_str() == 'd'


udunits_to_pint = [
    # powers on a single unit
    ('s', 's'),
    ('s2', 's**2'),
    ('s^2', 's**2'),
    ('s**2', 's**2'),
    ('s-2', 's**-2'),
    ('s^-2', 's**-2'),
    ('s**-1', 's**-1'),
    ('s**-2', 's**-2'),
    # multiplication operators
    ('kg s', 'kg * s'),
    ('kg  s', 'kg * s'),
    ('kg-s', 'kg * s'),
    ('kg- s', 'kg * s'),
    ('kg -s', 'kg * s'),
    ('kg - s', 'kg * s'),
    ('kg.s', 'kg * s'),
    ('kg. s', 'kg * s'),
    ('kg .s', 'kg * s'),
    ('kg . s', 'kg * s'),
    ('kg m s', 'kg * m * s'),
    ('kg.m-s', 'kg * m * s'),
    # division operator - note spacing is not normalized as with mult
    ('kg/s', 'kg/s'),
    ('kg /s', 'kg /s'),
    ('kg/ s', 'kg/ s'),
    ('kg / s', 'kg / s'),
    # combined
    ('kg m3 / s2', 'kg * m**3 / s**2'),
    ('kg m**3 / s^2', 'kg * m**3 / s**2'),
    ('kg m^3 / s**2', 'kg * m**3 / s**2'),
    ('kg.m^3 / s**2', 'kg * m**3 / s**2'),
    ('kg m-3 s-2', 'kg * m**-3 * s**-2'),
    ('kg m^-3 s^-2', 'kg * m**-3 * s**-2'),
    ('kg m**-3 s**-2', 'kg * m**-3 * s**-2'),
]


@pytest.mark.parametrize('input, expected', udunits_to_pint)
def test_udunits_str_to_pint_parsable_str(input, expected):
    assert Unit.udunits_str_to_pint_parsable_str(input) == expected


@pytest.mark.parametrize('input, expected',
                         [(udunits_str, Unit(pint_str)) for (udunits_str, pint_str) in udunits_to_pint])
def test_from_udunits(input, expected):
    assert Unit.from_udunits_str(input) == expected


pint_to_udunits = [
    # powers on a single unit
    ('s', 's'),
    ('s ** 2', 's2'),
    ('s ** -2', 's-2'),
    # multiplication operator
    ('kg * s', 'kg s'),
    ('kg * m * s', 'kg m s'),
    # division operator
    ('1 / s', 's-1'),
    ('1 / s ** 2', 's-2'),
    ('m / s', 'm s-1'),
    ('m / s ** 2', 'm s-2'),
    # combined
    ('kg * m ** 3 / s ** 2', 'kg m3 s-2'),
]


@pytest.mark.parametrize('input, expected', pint_to_udunits)
def test_pint_str_to_udunits_str(input, expected):
    assert Unit.pint_str_to_udunits_str(input) == expected


@pytest.mark.parametrize('input, expected',
                         [(Unit(pint_str), udunits_str) for (pint_str, udunits_str) in pint_to_udunits])
def test_to_udunits_str(input, expected):
    assert input.to_udunits_str() == expected
