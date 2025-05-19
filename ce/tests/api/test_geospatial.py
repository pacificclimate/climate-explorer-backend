import pytest
from shapely.errors import ShapelyError
from shapely.geometry import Polygon
from ce.api.geospatial import (
    geojson_feature,
    outline_cell_rect,
    WKT_point_to_lonlat,
    GeospatialTypeError,
)


coordinates = ((0, 0), (0, 1), (1, 1), (0, 0))


@pytest.mark.parametrize(
    "thing, kwargs, expected",
    (
        (
            Polygon(coordinates),
            dict(properties=dict(name="fred", age=42)),
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": (coordinates,)},
                "properties": {"name": "fred", "age": 42},
            },
        ),
    ),
)
def test_geojson_feature(thing, kwargs, expected):
    assert geojson_feature(thing, **kwargs) == expected


@pytest.mark.parametrize(
    "centres, height, width, expected",
    (
        # Test cases are on a unit grid. For simplicity, cell centres are at
        # coordinates integer + 0.5, therefore boundaries at integer coordinates.
        # Simplest case: one cell
        (((0.5, 0.5),), 1, 1, ((0, 0), (1, 0), (1, 1), (0, 1))),
        # Various 2x2 grid cases
        (
            ((0.5, 0.5), (1.5, 1.5)),
            1,
            1,
            ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (1, 2), (1, 1), (0, 1)),
        ),
        (
            ((1.5, 0.5), (0.5, 1.5)),
            1,
            1,
            ((1, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2), (0, 1), (1, 1)),
        ),
        (
            ((0.5, 0.5), (0.5, 1.5), (1.5, 1.5)),
            1,
            1,
            ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1)),
        ),
        (
            ((0.5, 0.5), (0.5, 1.5), (1.5, 0.5), (1.5, 1.5)),
            1,
            1,
            ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1)),
        ),
        # Case on a 3x4 grid
        #
        # XXX
        #  XX
        #  X
        # X
        (
            (
                (0.5, 0.5),
                (1.5, 1.5),
                (1.5, 2.5),
                (2.5, 2.5),
                (0.5, 3.5),
                (1.5, 3.5),
                (2.5, 3.5),
            ),
            1,
            1,
            (
                (0, 0),
                (1, 0),
                (1, 1),
                (2, 1),
                (2, 2),
                (3, 2),
                (3, 3),
                (3, 4),
                (2, 4),
                (1, 4),
                (0, 4),
                (0, 3),
                (1, 3),
                (1, 2),
                (1, 1),
                (0, 1),
            ),
        ),
    ),
)
def test_outline(centres, height, width, expected):
    ol = outline_cell_rect(centres, height, width)
    assert ol.equals(Polygon(expected))


@pytest.mark.parametrize(
    "text, result",
    (
        ("blerg", ShapelyError),
        ("POINT", ShapelyError),
        ("POINT(,)", ShapelyError),
        ("POINT(99,)", ShapelyError),
        ("POINT(,99)", ShapelyError),
        ("POLYGON ((0 2, 0 0, 1 1, 0 2))", GeospatialTypeError),
        ("POINT(1 -2)", (1, -2)),
    ),
)
def test_WKT_point_to_lonlat(text, result):
    if type(result) == tuple:
        assert WKT_point_to_lonlat(text) == result
    else:
        with pytest.raises(result):
            try:
                WKT_point_to_lonlat(text)
            except Exception as e:
                print("####", e)
                raise e
