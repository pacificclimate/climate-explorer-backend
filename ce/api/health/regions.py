'''module for requesting a summary of stored region data status.'''
import os
from csv import DictReader
from ce.api.multimeta import multimeta
from datetime import datetime


def region_status(region, metadata):
    '''Opens a stored data file for a region, checks the modtime of the
      stored data against the current versions of each file (as listed
      in the metadata) and returns a list of the each file from which
      stored data was calculated and its status.''' 
    
    date_format = '%Y-%m-%dT%H:%M:%SZ'

    # open each stored query file and make sure all data is up to date
    files_checked = {}
    sq_files = []
    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip("/")

    try:
        with open("{}/{}.csv".format(region_dir, region),
                  "r") as region_query_file:
            region_queries = DictReader(region_query_file)
            for row in region_queries:
                uid = row['unique_id']
                modtime = row['modtime']

                if uid not in files_checked or files_checked[uid] != modtime:
                    file_status = {
                        "unique_id": uid,
                        "date": modtime
                        }
                    if uid in files_checked and files_checked[uid] != modtime:
                        # there is stored data from
                        # conflicting versions of this file.
                        file_status["status"] = "conflicted"
                    elif uid not in metadata:
                        # this stored query is from a
                        # dataset that has since been deleted!
                        file_status["status"] = "removed"
                    elif datetime.strftime(metadata[uid]["modtime"],
                                           date_format) != modtime:
                        # this stored query is from a
                        # dataset that has since been updated
                        file_status["status"] = "outdated"
                    else:
                        # this stored data is still accurate
                        file_status["status"] = "current"
                    files_checked[uid] = modtime
                    sq_files.append(file_status)
    except EnvironmentError:
        abort(404, description="Data for region {} not found".format(region))
    return sq_files

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


def regions(sesh, item=None, ensemble_name='p2a_classic'):
    '''Request summary data on whether data source files have been updated
    since the stored region queries were calculated.
    Possible status of the source data files are:
    
        current: (the source file is up to date)
        outdated: (the source file has been updated)
        removed: (the source file is no longer in the database)
        conflicted: (data was calculated from multiple versions of the source)

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
            pointing to a modelmeta database with up-to-date information
    
        item name of a specific region. If supplied, returns detailed
            information about stored data for that region. Otherwise,
            returns a summary of all regions.

        ensemble_name a dataset ensemble to check the stored data against

    Returns:
        With no region specified::

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
        
        With a region specified::

            {
                "region": "bc",
                "files":
                    [
                        {
                            "unique_id": "tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
                            "date": "2020-03-16T17:47:47Z",
                            "status": "current"
                        },
                        {
                            "unique_id": "pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
                            "date": "2019-08-30T17:49:03Z",
                            "status": "outdated"
                        },
                        ...
                    ]
            }
        
    '''
    
    print("item = {}".format(item))

    # first get metadata on current datasets from the database:
    current_metadata = multimeta(sesh, ensemble_name=ensemble_name)
    date_format = '%Y-%m-%dT%H:%M:%SZ'
    
    if item:
        # return full data for a single region
        return {
            "region": item,
            "files": region_status(item, current_metadata)
            }
    else:
        # return summary data for all regions
        region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip('/')
        region_names = [file.split('.')[0] for file in os.listdir(region_dir)]

        return [summarize_region(rn, region_status(rn, current_metadata))
                    for rn in region_names]
