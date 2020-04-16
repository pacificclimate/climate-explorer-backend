from ce.api import health
from ce.api import multimeta
from csv import DictWriter
from datetime import datetime
import os


def test_stored_data(populateddb):
    sesh = populateddb.session
    mm = multimeta(sesh, "p2a_classic")
    # checking whether a file has been updated in the database is a little complicated, because
    # the database is rebuilt each time pytest is run. So we need to build the "stored data"
    # CSV during testing as well.
    removed_id="removed"
    current_id="pr_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    outdated_id= "tasmax_aClim_BNU-ESM_historical_r1i1p1_19650101-19701230"
    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip("/")
    with open("{}/test_health.csv".format(region_dir), "w") as outfile:
        outcsv = DictWriter(outfile, fieldnames=["unique_id", "modtime"])
        outcsv.writeheader()
    
        #list a file that has been "removed" from the database.
        outcsv.writerow({"unique_id": "removed", "modtime": "2020-03-16T17:47:47Z"})
    
        #list an outdated file.
        outcsv.writerow({"unique_id": outdated_id, "modtime": "2020-03-16T17:47:47Z"})
    
        #list an up-to-date file - ie, same date as test database
        mtime = datetime.strftime(mm[current_id]["modtime"], '%Y-%m-%dT%H:%M:%SZ')
        outcsv.writerow({"unique_id": current_id, "modtime": mtime})
    
    # test summary
    h = health(sesh)["stored_regional_queries"]["test_health.csv"]
    assert h["current"] == 1
    assert h["outdated"] == 1
    assert h["removed"] == 1
    
    # test full list
    h = health(sesh, list_files="true")["stored_regional_queries"]["test_health.csv"]
    assert current_id in h["current"] and len(h["current"]) == 1
    assert outdated_id in h["outdated"] and len(h["outdated"]) == 1
    assert removed_id in h["removed"] and len(h["removed"]) == 1
        
    os.remove("{}/test_health.csv".format(region_dir))