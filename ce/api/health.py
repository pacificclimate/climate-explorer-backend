'''module for requesting information on how the backend is running.'''
import os
from csv import DictReader
from ce.api.multimeta import multimeta
from datetime import datetime


def health(sesh):
    '''Request an overview of the health of the API. Reports on whether any
    of the stored query data is out of data with the source files, and gives
    unique_ids and timestamps for any that are.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
            pointing to a modelmeta database with up-to-date information

    Returns:
        dict: a dictionary with attributes corresponding to various aspects
            of current API function. At present, the only attribute is 
            `stored_regional_queries`, which, for each of the regional
            datafiles reports how many datasets are up to date, and how
            many and which are have been updated or removed from the database.

        For example::

            {
                "stored_regional_queries": {
                    "bc.csv": {
                        'current': 1,
                        'outdated': {
                            'tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230': '2020-03-16T17:47:47Z'
                        },
                        'removed': {
                            'pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230': '2020-03-16T17:47:47Z'
                        }
                    }
                    "vancouver_island.csv": {
                        ...
                    }
                    ...
                }
            }
    '''

    # check to see if any of the stored queries are out of date.
    # first get metadata on current datasets from the database:
    current_metadata = multimeta(sesh, ensemble_name='all_files')
    date_format = '%Y-%m-%dT%H:%M:%SZ'

    # open each stored query file and make sure all data is up to date
    regional_checks = {}
    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip("/")
    for region in os.listdir(region_dir):
        with open("{}/{}".format(region_dir,
                                 region), "r") as region_query_file:
            region_queries = DictReader(region_query_file)
            region_status = {
                "current": 0,
                "outdated": {},
                "removed": {}
                }
            for row in region_queries:
                uid = row['unique_id']
                modtime = row['modtime']
                if uid not in current_metadata:
                    # this stored query is from a
                    # dataset that has since been deleted!
                    region_status["removed"][uid] = modtime
                elif datetime.strftime(current_metadata[uid]["modtime"],
                                       date_format) != modtime:
                    # this stored query is from a
                    # dataset that has since been updated
                    region_status["outdated"][uid] = modtime
                else:
                    # this stored data is still accurate
                    region_status["current"] = region_status["current"] + 1

        regional_checks[region] = region_status

    return {
        "stored_regional_queries": regional_checks
        }
