class GeoDataGrid2DError(Exception):
    """Base class for exceptions in this module."""

    pass


class GeoDataGrid2DIndexError(GeoDataGrid2DError):
    """Exception for attempt to incorrectly index a data grid. This is more
    stringent than a simple IndexError.

    Attributes:
        index: offending index
        shape: offended grid shape
        message: explanation of the error, generated from params
    """

    def __init__(self, index, shape):
        self.index = index
        self.shape = shape
        self.message = "Index {} is not valid for a grid of shape {}".format(
            index, shape
        )


class GeoDataGrid2D:
    """Represents the contents of a geospatial gridded dataset. Such a dataset
    is characterized by the following contents:

    - Two coordinate variables named 'lat' and 'lon'
    - One or more additional variables dimensioned by the lat and lon
      dimensions.
    """

    def __init__(self, longitudes, latitudes, values, units=None):
        self.longitudes = longitudes
        self.latitudes = latitudes
        self.values = values
        self.units = units

    @classmethod
    def from_nc_dataset(cls, dataset, variable_name):
        """Factory method. Extracts relevant data from a netcdf file (`Dataset`)
        with standard contents and returns it as a `DataGrid`."""
        return cls(
            dataset.variables["lon"],
            dataset.variables["lat"],
            dataset.variables[variable_name][:],
            dataset.variables[variable_name].units,
        )

    def is_valid_index(self, index):
        """True if index is in valid range for the grid"""
        return all(0 <= i < n for i, n in zip(index, self.values.shape))

    def check_valid_index(self, index):
        if not self.is_valid_index(index):
            raise GeoDataGrid2DIndexError(index, self.values.shape)
