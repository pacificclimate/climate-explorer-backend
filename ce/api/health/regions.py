'''module for requesting a summary of current and outdated stored region queries.'''
import os
from csv import DictReader
from ce.api.multimeta import multimeta
from ce.api.health.region import region
from datetime import datetime


def regions(sesh, ensemble_name='p2a_classic'):
    '''Request summary data on whether data source files have been updated 
    since the stored region queries were calculated.
    Provides counts for:
        current (the source file is up to date)
        outdated (the source file has been updated)
        removed (the source file is no longer in the database)

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
            pointing to a modelmeta database with up-to-date information
        
        ensemble_name: a dataset ensemble to check the stored data against
        
        list_files: true/false, whether to return lists of files that have 
            and haven't been updated, or just counts

    Returns:
        list: a list with an dictionary for each region, reporting how
            many datasets are up to date, and how many have been
            updated or removed from the database.

        For example::

            [
                {
                    "region": "bc",
                    "current": 100,
                    "outdated": 3,
                    "removed": 6,
                    "conflicted": 0
                },
                {
                    "region": "vancouver_island",
                    ...
                },
                ...
            ]
        
    '''

    # first get metadata on current datasets from the database:
    current_metadata = multimeta(sesh, ensemble_name=ensemble_name)
    date_format = '%Y-%m-%dT%H:%M:%SZ'
    
    def summarize_region(region_name, region_files):
        'accepts a list of files, returns counts of how many have each status'
        count = {
            "region": region_name,
            "current": 0,
            "outdated": 0,
            "removed": 0,
            "conflicted": 0
            }
        for file in region_files:
            count[file["status"]] = count[file["status"]] + 1
        return count
        
        

    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip('/')
    region_names = [file.split('.')[0] for file in os.listdir(region_dir)]
    
    return [summarize_region(rn, region(sesh, rn, ensemble_name, current_metadata))
            for rn in region_names]