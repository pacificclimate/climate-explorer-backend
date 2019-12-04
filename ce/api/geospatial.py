import math
import re
import shapely
from shapely.geometry import Point, Polygon, mapping
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


def outline_cell_rect(centres, height, width):
    """Returns a shapely geometry object, normally a Polygon, that is the
    outline, i.e., the concave hull, of the cells with given centres, height,
    and width. Uses a very simple algorithm based on cell rectangles, which
    also turns out to yield the simplest outline and do the least work."""
    dy = height / 2
    dx = width / 2
    return cascaded_union([
        shapely.geometry.box(x - dx, y - dy, x + dx, y + dy)
        for x, y in centres
    ])

def WKT_point_to_lonlat(text):
    pattern = re.compile(
        r'POINT\s*\(([+-]?[0-9]+\.?[0-9]*)\s+([+-]?[0-9]+\.?[0-9]*)\)'
    )
    match = re.match(pattern, text)
    if not match:
        raise ValueError('Cannot parse {} as a WKT point'.format(text))
    lon = float(match.group(1))
    lat = float(match.group(2))
    return lon, lat
