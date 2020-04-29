'''module for requesting stored query status for a specific p2a region'''
import os
from csv import DictReader
from ce.api.multimeta import multimeta
from datetime import datetime
from flask import abort


def region(sesh, item, ensemble_name='p2a_classic', metadata=None):
    '''Request a list of all files from which stored data is available for
    this region and the timestamp corresponding to the last modification
    made to that file at the time the stored data was calculated.
    Each file will be checked against a modelmeta database to determine
    whether the file has been updated or deleted since then.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
            pointing to a modelmeta database with up-to-date information

        item (string): the canonical name of one of the plan2adapt
            regions.

        ensemble_name: a dataset ensemble to check the stored data against

        metadata: a dictionary as returned by the multimeta function. This
            argument is to save time and allow multiple calls to this API
            to share multimeta results. Cannot be passed as a URL parameter.

    Returns:
        list: a list with one entry for each file, with the unique_id,
            modtime, region, and status of the file.

        For example::

            [
                {
                    "region": "bc",
                    "unique_id": "tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
                    "date": "2020-03-16T17:47:47Z",
                    "status": "current"
                },
                {
                    "region": "bc",
                    "unique_id": "pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230",
                    "date": "2019-08-30T17:49:03Z",
                    "status": "outdated"
                },
                ...
            ]
    '''

    # obtain metadata, if it was not received as an argument
    if not metadata:
        metadata = multimeta(sesh, ensemble_name=ensemble_name)

    date_format = '%Y-%m-%dT%H:%M:%SZ'

    # open each stored query file and make sure all data is up to date
    files_checked = {}
    sq_files = []
    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip("/")

    try:
        with open("{}/{}.csv".format(region_dir, item),
                  "r") as region_query_file:
            region_queries = DictReader(region_query_file)
            for row in region_queries:
                uid = row['unique_id']
                modtime = row['modtime']

                if uid not in files_checked or files_checked[uid] != modtime:
                    file_status = {
                        "region": item,
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
        abort(404, description="Data for region {} not found".format(item))

    return sq_files
