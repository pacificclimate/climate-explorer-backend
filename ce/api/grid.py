'''module for requesting the lat/lon grid for a given model run file
'''

from sqlalchemy.orm.exc import NoResultFound

from modelmeta import DataFile

from ce.api.util import get_grid_from_netcdf_file, open_nc

na_grid = {
    key: []
    for key in ('latitudes', 'longitudes')
}

def grid(sesh, id_):
    '''Request centroid latitudes and longitudes of all cells within a 
    given file.

    This is used for loading the front end with geographic extents
    information, from which enclosing polygons can be constructed in
    response to users clicking on a map.

    The grid call may only be called for a single data file per 
    invocation.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
        
        id_ (str): Unique id which is a key to the data file requested
     
    Returns:
        dict: Empty dictionary if id_ is not found in the database.

        Otherwise, returns a single dict with the key of the file's
        unique_id and the value consisting of a nested dictionary with
        the following attributes: 'latitudes', 'longitudes'.

        For example ::

            {'file0':
                {
                    'latitudes': [
                        -87.86380134, 
                        -85.09652949, 
                        -82.31291545, ...
                        ],
                    'longitudes': [
                        -180, 
                        -177.1875, 
                        -174.375, ... 
                        ],
                    'modtime': datetime.datetime(2011, 11, 11, 11, 11, 11)
                }
            }

        There are two semi-error cases which should be mentioned, when
        the filesystem is out of sync with the database.

        1. The file pointed to by `id_` does not exist in the filesystem
        2. The requested variable does not exist in the given file

        In these the first case, an empty dict is returned.  In the 
        second case, a dict with the id_ key and empty lists for 
        latitudes and longtitudes is returned.

    Raises:
        None?

    '''
    try:
        df = sesh.query(DataFile).filter(DataFile.unique_id == id_).one()
    except NoResultFound:
        return {}

    with open_nc(df.filename) as nc:
        try:
            grid = get_grid_from_netcdf_file(nc)
        except (RuntimeError, KeyError):
            return {id_: na_grid}

    grid.update({'modtime': df.index_time})

    return {id_: grid}
