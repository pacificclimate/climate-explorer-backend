'''module for requesting change from a baseline value, expressed as a percentile
value of the spread of the PCIC12 models. Because opening a file for each of the
12 models is unworkably slow, this module instead extracts data from CSV files
holding precomputed values.'''

from flask import abort
from csv import DictReader
import json
import os
from datetime import datetime
import numpy as np

def percentileanomaly(sesh, region, climatology, variable, percentile='50', 
                      baseline_model="anusplin", baseline_climatology="6190"):
    
    # get data directory
    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip("/")
    
    
    calculate_anomaly = False
    baseline_data = {}
    
    percentiles = [float(p) for p in percentile.split(',')]
    
    if baseline_model != '' and baseline_climatology != '':
        calculate_anomaly = True
    elif baseline_model != '' or baseline_climatology != '':
        abort(400, message='Must supply both historical model and climatology for anomaly calculation')
        
    
    # adds data to a nested dictionary, creating new key levels as needed
    def add_to_nested_dict(dict, value, *keys):
        key = keys[0]
        rest = list(keys[1:])
        if len(rest) == 0:
            dict[key] = value
        elif key in dict:
            dict[key] = add_to_nested_dict(dict[key], value, *rest)
        else:
            dict[key] = add_to_nested_dict({}, value, *rest)
        return dict
    
    
    try:
        # fetch stored queries from csv
        with open("{}/{}.csv".format(region_dir, region), "r") as stored_query_file:
            queries = DictReader(stored_query_file)
            
            projected_data = {}
            units = ''
            # go through stored queries, collecting all that match parameters
            for row in queries:
                if row['variable'] == variable:
                    if row["units"] != units: # make sure datasets share units
                        if units == '':
                            units = row['units']
                        else:
                            abort(500, message="Incompatible units: {}, {}".format(units, row['units']))
                    
                    if row['climatology'] == climatology:
                        add_to_nested_dict(projected_data, 
                                           row["mean"],
                                           row["timescale"],
                                           row["timestamp"],
                                           row["model"])
                    elif calculate_anomaly and row['model'] == baseline_model and row['climatology'] == baseline_climatology:
                        add_to_nested_dict(baseline_data, row['mean'], row['timescale'], row["timestamp"])
        
        #calculate percentiles and anomalies
        for timescale in projected_data:
            for timestamp in projected_data[timescale]:
                # determine the baseline, if applicable
                if calculate_anomaly:
                    baseline = None
                    date_format = '%Y-%m-%d %H:%M:%S'
                    projected_date = datetime.strptime(timestamp, date_format)
                    if not timescale in baseline_data:
                        abort(500, "Missing baseline data: {} {} {}".format(baseline_model, baseline_climatology, timescale))
                    for t in baseline_data[timescale]:
                        baseline_date = datetime.strptime(t, date_format)
                        if baseline_date.month == projected_date.month:
                            if not baseline:
                                baseline = float(baseline_data[timescale][t])
                            else:
                                abort(500, "multiple matching baseline datasets for {} {} {} {}".format(
                                    baseline_model, baseline_climatology, timescale, timestamp))
                    if not baseline:
                        abort(500, "No baseline match available for {} {} {} {}".format(
                                    baseline_model, baseline_climatology, timescale, timestamp))
                else:
                    baseline = 0.0
                values = np.asarray([float(v) for v in projected_data[timescale][timestamp].values()])
                if values.size < 12:
                    abort(500, "Not all models available for {} {}. Models available: {}".format(
                        timescale, timestamp, projected_data[timescale][timestamp].keys()))
                elif values.size > 12:
                    abort(500, "Extraneous data for {} {}. Models available: {}".format(
                        timescale, timestamp, projected_data[timescale][timestamp].keys()))
                anomalies = values - baseline
                #percentiles = np.percentile(anomalies, percentiles)                
                projected_data[timescale][timestamp] = list(np.percentile(anomalies, percentiles))
                
        response = {
                'units': units,
                'percentiles': percentiles,
                'region': region,
                'climatology': climatology,
                'variable': variable
            }
        if calculate_anomaly:
            response["baseline_model"] = baseline_model
            response["baseline_climatology"] = baseline_climatology
            response["anomaly"] = projected_data
            response["baseline"] = baseline_data
        else:
            response["data"]: projected_data

        return response
            
    except EnvironmentError:
        abort(404, description="Data for region {} not found".format(region))
