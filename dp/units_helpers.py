"""Helper functions for parsing, manipulating, and formatting units expressed as strings in `udunits` syntax.

`udunits` syntax and formatting is documented at http://www.unidata.ucar.edu/software/netcdf/netcdf/Units.html.
See section on `utPrint()` for recommendations about using default formatting.
This formatting appears to be used consistently in GCM output files.

We'd like to use the `cfunits` library for this, but it is not compatible with Python >= 3.0.
So instead we use the `pint` library, and do a little string munging to convert between `pint`' string formats
and `udunits` string formats.

`pint` formatting is documented at https://pint.readthedocs.io/en/0.7.2/tutorial.html#string-formatting
"""
import re

from pint import UnitRegistry

ureg = UnitRegistry()
ureg.define('day = 24 * hour = d')  # add 'd' as a synonym for 'day'; udunits uses 'd'


class Unit(ureg.Unit):

    @staticmethod
    def udunits_str_to_pint_parsable_str(udunits_str):
        """Convert any valid udunits string to a string that pint can parse."""
        # Convert powers
        s = re.sub(r'(\^|\*\*)?(-?\d+)', r'**\2', udunits_str)
        # Convert multiplication operators
        s = re.sub(r'(?<=[a-zA-Z0-9])\s*( |\.|-)\s*(?=[a-zA-Z])', r' * ', s)
        return s


    @staticmethod
    def pint_str_to_udunits_str(pint_str):
        """Convert a pint str to a default formatted udunits string."""
        # Split `pint` string into parts separated by multiplication or division (* or /). Keep the separators.
        pint_parts = re.split(r' ([\/\*]) ', pint_str)

        # Normalize the split so that it always begins with a * or /.
        if pint_parts[0] == '1':
            pint_parts = pint_parts[1:]
        else:
            pint_parts = ['*'] + pint_parts

        # Convert `pint` parts to `udunits` parts by extracting base units and powers and formatting them
        # in `udunits` default style.
        udunits_parts = []
        for i in range(0, len(pint_parts), 2):
            sign = {'*': '', '/': '-'}[pint_parts[i]]
            unit_power = re.split(r'\s*\*\*\s*', pint_parts[i+1])
            if len(unit_power) == 1 and sign == '-':
                unit_power.append('1')
            udunits_parts.append(sign.join(unit_power))

        return ' '.join(udunits_parts)


    @classmethod
    def from_udunits_str(cls, udunits_str):
        """Create a Unit object from a udunits formatted string."""
        return cls(cls.udunits_str_to_pint_parsable_str(udunits_str))


    def to_udunits_str(self):
        """Format self as a default `udunits` format string."""
        # Format self as a pint string with abbreviated units and convert it to a udunits string
        return Unit.pint_str_to_udunits_str('{:~}'.format(self))