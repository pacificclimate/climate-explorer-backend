import re
import numpy


direction_map = (
    (0, 0),  # filler - 0 is not used in the encoding
    (1, 0),  # 1 = north
    (1, 1),  # 2 = northeast
    (0, 1),  # 3 = east
    (-1, 1),  # 4 = southeast
    (-1, 0),  # 5 = south
    (-1, -1),  # 6 = southwest
    (0, -1),  # 7 = west
    (1, -1),  # 8 = northwest
    (0, 0),  # 9 = outlet
)

# VIC direction codes
N, NE, E, SE, S, SW, W, NW, OUTLET = range(1, 10)


def np_array(a, rev_rows=True):
    """Return a numpy array constructed from an array-like object `a`.

    Argument `rev` is convenient for layout of routing maps, where the
    longitude index (row) increases northward/upward, the reverse of
    array/tuple literal layout in text.
    """
    if rev_rows:
        a = tuple(reversed(a))
    return numpy.array(a)


def check_dict_subset(dict1, dict2, path=[]):
    """Check (by assertion) that dict1 is a "subset" of dict2.
    "Subset" here means that every key in dict1 is in dict2, recursively
     for values that are themselves dicts. For values that are not dicts,
     then the values must be equal.
    """

    def compare(key_, value1, value2):
        path_ = path + [key]
        if type(value1) == dict:
            check_dict_subset(value1, value2, path=path_)
        elif type(value1) == type(re.compile('')) and type(value2) == str:
            # TODO: Replace `type(re.compile(''))` with `re.Pattern` for Py>=3.7
            # Special case for comparing strings: if a supplied value is a
            # regex and the comparison value is a string, then comparison is
            # regex match.
            assert value1.search(value2) is not None, \
                f"Regex '{value1}' does not match string '{value2}'"
        else:
            assert value1 == value2, "{}: {} != {}".format(
                "".join("['{}']".format(p) for p in path_), value1, value2
            )

    for key in dict1.keys():
        assert key in dict2, f"key '{key}' in dict1 but not in dict2"
        compare(key, dict1[key], dict2[key])


def is_dict_subset(dict1, dict2):
    """Return a boolean indicating whether dict1 is a "subset" of dict2.
    "Subset" here means that every key in dict1 is in dict2, recursively
     for values that are themselves dicts. For values that are not dicts,
     then the values must be equal.
     """

    def compare(value1, value2):
        if type(value1) == dict:
            return is_dict_subset(value1, value2)
        return value1 == value2

    return all(compare(dict1[key], dict2[key]) for key in dict1.keys())
