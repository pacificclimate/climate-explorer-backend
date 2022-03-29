import shapely.wkt
from shapely.geometry import Point, mapping, LineString
from shapely.ops import cascaded_union


class GeospatialError(Exception):
    """Base class for exceptions in this module."""

    pass


class GeospatialTypeError(GeospatialError):
    """Exception for an invalid geospatial datatype used in some context.
    So far that context is just "expecting a point" (as opposed, say, to a
    polygon.
    """

    def __init__(self, obj):
        self.obj = obj
        self.message = "Expected a Point but got a {}".format(type(obj).__name__)


def geojson_feature(thing, **kwargs):
    """Returns a dict defining a GeoJSON Feature containing the shapely
    geometric object `thing`.
    Any additional keyword args are added at the top level of the dict.
    Normally this would be a component such as 'properties'.
    """
    return {
        "type": "Feature",
        "geometry": mapping(thing),
        **kwargs,
    }


def outline_cell_rect(centres, height, width):
    """Returns a shapely geometry object, normally a Polygon, that is the
    outline, i.e., the concave hull, of the cells with given centres, height,
    and width. Uses a very simple algorithm based on cell rectangles, which
    also turns out to yield the simplest outline and do the least work."""
    dy = height / 2
    dx = width / 2
    return cascaded_union(
        [shapely.geometry.box(x - dx, y - dy, x + dx, y + dy) for x, y in centres]
    )


def path_line(points):
    """Returns a shapely LineString, that is the downstream path"""
    return LineString(points)


def WKT_point_to_lonlat(text):
    p = shapely.wkt.loads(text)
    if type(p) != Point:
        raise GeospatialTypeError(p)
    return p.x, p.y
