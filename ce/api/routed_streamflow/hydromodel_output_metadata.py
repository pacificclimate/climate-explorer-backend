from modelmeta import DataFile

#The final version of this query will get all its information
#from a modelmeta database, but the database hasn't been updated yet.

#The shimmed version of this query will get its information from 
#inspecting netCDF files, but the files in question have gotten corrupted
#somehow. So for now, it's 100% canned data. :/

def hydromodel_output_metadata(sesh, id):
    
    #results.nc has gotten corrupted somehow (?) so return canned answers
    model_definition = {}
    model_definition["name"] = "VIC (Built from source: v0.0.2-142-g981d56a1bb)."
    model_definition["description"] = "Variable Infiltration Capacity Model GL with glacier dynamics"
    
    climate_input = {}
    climate_input["model"] = "ACCESS1-0"
    climate_input["scenario"] = "historical+rcp45"
    climate_input["run"] = "r1i1p1"
    
    grid = {}
    grid["longitude"] = (-124.96875,-109.71875)
    grid["lonstep"] = 0.0625
    grid["latitude"] = (41.03125, 53.15625)
    grid["latstep"] = 0.0625
    
    time = {}
    time["start"] = "1950-01-01T00:00:00"
    time["stop"] = "2100-01-01T00:00:00"
    time["increment"] = "1 day"
    
    
    
    
    output_metadata = {
        "hydromodel_output_metadata_id": 0,
        "model_definition": model_definition,
        "climate_input": climate_input,
        "grid": grid,
        "time": time
    }
        
    return output_metadata