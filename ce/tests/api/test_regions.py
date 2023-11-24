from ce.api.health.regions import regions
from ce.api import multimeta
from csv import DictWriter
from datetime import datetime
import os
from tempfile import NamedTemporaryFile
from pathlib import Path

import flask

def test_stored_data(populateddb, app):

    sesh = populateddb.session
    mm = multimeta(sesh, "p2a_classic")
    # checking whether a file has been updated in the database is a little complicated,
    # because the database is rebuilt each time pytest is run. So we need to build the
    # "stored data" CSV during testing as well.
    removed_id = "removed"
    current_id = "pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    outdated_id = "tasmin_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    region_dir = os.getenv("REGION_DATA_DIRECTORY").rstrip("/")

    with NamedTemporaryFile("w", suffix=".csv", dir=region_dir) as outfile:
        region_name = Path(outfile.name).stem
        outcsv = DictWriter(outfile, fieldnames=["unique_id", "modtime"])
        outcsv.writeheader()

        # list a file that has been "removed" from the database.
        outcsv.writerow({"unique_id": "removed", "modtime": "2020-03-16T17:47:47Z"})

        # list an outdated file.
        outcsv.writerow({"unique_id": outdated_id, "modtime": "2020-03-16T17:47:47Z"})

        # list an up-to-date file - ie, same date as test database
        mtime = datetime.strftime(mm[current_id]["modtime"], "%Y-%m-%dT%H:%M:%SZ")
        outcsv.writerow({"unique_id": current_id, "modtime": mtime})
        outfile.flush()

        # fake up the request url for RESTy URL munging
        with app.test_request_context("http://example.com/api/health/regions"):
                
            # test regions endpoint for status summary
            status = list(filter(lambda x: x["region"] == region_name, regions(sesh)))

            # test region endpoint for individual file details
            details = regions(sesh, item=region_name)["files"]

    assert len(status) == 1
    status = status[0]

    assert status["current"] == 1
    assert status["outdated"] == 1
    assert status["removed"] == 1
    assert status["conflicted"] == 0

    assert len(details) == 3

    current = list(filter(lambda f: f["status"] == "current", details))
    assert len(current) == 1
    assert current[0]["unique_id"] == current_id

    outdated = list(filter(lambda f: f["status"] == "outdated", details))
    assert len(outdated) == 1
    assert outdated[0]["unique_id"] == outdated_id

    removed = list(filter(lambda f: f["status"] == "removed", details))
    assert len(removed) == 1
    assert removed[0]["unique_id"] == removed_id
