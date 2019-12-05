import math
from ce.geo_data_grid_2d import GeoDataGrid2D


class VicDataGrid(GeoDataGrid2D):
    """Represents the contents of a geospatial gridded dataset used in VIC
    processing. More specifically, it is used to represent the flow_direction,
    elevation, and area datasets. This class depends on such datasets having
    the following features:

    - Uniform step size in latitude and longitude

    The existence of this class has two motivations:

    - Factor out common operations on datasets (e.g., convert between lonlat
        and xy coordinates).
    - Make it much simpler to construct test data for the `worker` function.
    """

    def __init__(self, longitudes, latitudes, values, units=None):
        super().__init__(longitudes, latitudes, values, units)
        # Note assumption of uniform step sizes
        self.lon_step = longitudes[1] - longitudes[0]
        self.lat_step = latitudes[1] - latitudes[0]

    def is_compatible(self, other):
        """Return a boolean indicating whether this `VicDataGrid` and
        another are compatible. Compatible means that their lon and lat grids
        have the same step size."""
        # Note assumption of uniform step sizes
        return math.isclose(self.lon_step, other.lon_step) and \
               math.isclose(self.lat_step, other.lat_step)

    def lonlat_to_xy(self, lonlat):
        """Returns the (x, y) data index for a given lon-lat coordinate,
        switching the order of the coordinates. Checks that the index is
        valid for the grid; we must at minimum exclude negative index values,
        which are valid but wrong in this application."""
        # Note assumption of uniform step sizes
        x = int(round((lonlat[1] - self.latitudes[0]) / self.lat_step))
        y = int(round((lonlat[0] - self.longitudes[0]) / self.lon_step))
        self.check_valid_index((x, y))
        return x, y

    def xy_to_lonlat(self, xy):
        """Returns the lon-lat coordinate for a given xy data index,
        switching the order of the coordinates."""
        self.check_valid_index(xy)
        return self.longitudes[xy[1]], self.latitudes[xy[0]]

    def get_values_at_lonlats(self, lonlats):
        """Map an iterable of lonlats to a list of values at those lonlats"""
        return [
            float(self.values[self.lonlat_to_xy(lonlat)]) for lonlat in lonlats
        ]
