from ce.api.health.regions import regions
from ce.api import multimeta
from csv import DictWriter
from datetime import datetime
import os
import flask

import pytest

@pytest.mark.external_data
def test_stored_data(populateddb):
    app = flask.Flask(__name__)
    sesh = populateddb.session
    mm = multimeta(sesh, "p2a_classic")
    # checking whether a file has been updated in the database is a little complicated,
    # because the database is rebuilt each time pytest is run. So we need to build the
    # "stored data" CSV during testing as well.
    removed_id = "removed"
    current_id = "pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    outdated_id = "tasmin_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    region_dir = os.getenv("REGION_DATA_DIRECTORY").rstrip("/")
    with open("{}/test_region.csv".format(region_dir), "w") as outfile:
        outcsv = DictWriter(outfile, fieldnames=["unique_id", "modtime"])
        outcsv.writeheader()

        # list a file that has been "removed" from the database.
        outcsv.writerow({"unique_id": "removed", "modtime": "2020-03-16T17:47:47Z"})

        # list an outdated file.
        outcsv.writerow({"unique_id": outdated_id, "modtime": "2020-03-16T17:47:47Z"})

        # list an up-to-date file - ie, same date as test database
        mtime = datetime.strftime(mm[current_id]["modtime"], "%Y-%m-%dT%H:%M:%SZ")
        outcsv.writerow({"unique_id": current_id, "modtime": mtime})

    # fake up the request url for RESTy URL munging
    with app.test_request_context("http://example.com/api/health/regions"):

        # test regions endpoint for status summary
        r = list(filter(lambda x: x["region"] == "test_region", regions(sesh)))

        assert len(r) == 1

        assert r[0]["current"] == 1
        assert r[0]["outdated"] == 1
        assert r[0]["removed"] == 1
        assert r[0]["conflicted"] == 0

        # test region endpoint for individual file details
        r = regions(sesh, item="test_region")["files"]
        assert len(r) == 3

        current = list(filter(lambda f: f["status"] == "current", r))
        assert len(current) == 1
        assert current[0]["unique_id"] == current_id

        outdated = list(filter(lambda f: f["status"] == "outdated", r))
        assert len(outdated) == 1
        assert outdated[0]["unique_id"] == outdated_id

        removed = list(filter(lambda f: f["status"] == "removed", r))
        assert len(removed) == 1
        assert removed[0]["unique_id"] == removed_id

    os.remove("{}/test_region.csv".format(region_dir))
