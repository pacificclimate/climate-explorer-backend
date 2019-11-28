import shapely
from shapely.geometry import Polygon, mapping
from shapely.ops import cascaded_union


def geojson_feature(thing, **kwargs):
    """Returns a dict defining a GeoJSON Feature containing the shapely
    geometric object `thing`.
    Any additional keyword args are added at the top level of the dict.
    Normally this would be a component such as 'properties'.
    """
    return {
        'type': 'Feature',
        'geometry': mapping(thing),
        **kwargs,
    }


def outline(centres, height, width):
    """Returns a shapely geometry object, normally a Polygon, that is the
    outline, i.e., the concave hull, of the cells with given centres, height,
    and width."""
    dy = height / 2
    dx = width / 2
    return cascaded_union([
        shapely.geometry.box(x - dx, y - dy, x + dx, y + dy)
        for x, y in centres
    ])
