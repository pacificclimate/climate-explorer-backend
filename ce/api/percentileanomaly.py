'''module for requesting change from a baseline value, expressed as a
percentile value of the spread of the PCIC12 models. Because opening a file for
each of the 12 models is unworkably slow, this module instead extracts data
from CSV files holding precomputed results of /stats queries.'''

from flask import abort
from csv import DictReader
import json
import os
from datetime import datetime
import numpy as np


def percentileanomaly(sesh, region, climatology, variable, percentile='50',
                      baseline_model="anusplin", baseline_climatology="6190"):
    '''Request percentiles summaries of the data range of the PCIC12 ensemble
    for a specific region.

    This call uses CSV files, one for each of the 52 defined plan2adapt
    regions, where each row stores all the parameters and results of a call to
    the /stats API. It is implemented this way to speed up what would otherwise
    be a process of calling the /stats API seperately for each model in the
    ensemble.

    It assumes the CSV files contain all required models and no extra - it
    checks that twelve different models are present, but not that they are the
    PCIC12 models and runs.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database Session object
            (not actually used, but automatically provided by the API router)

        region (string) name of one of the 52 p2a regions

        climatology (int): standard projected climo period (2020, 2050, 2080)

        variable (string): short name of variable to be returned

        percentile (number or list of numbers): percentile value, eg 50 or
            10,50,90 Defaults to 50th percentile

        baseline_model (string): a model to use as the baseline for anomaly
            calculations. Defaults to the ANUSPLIN dataset

        baseline_climatology (number): a standard climatological period to use
            for anomaly calculations. Defaults to 6190.

    Returns:
        dict: A dictionary with attributes restating the input parameters, as
            well as a units value. If both baseline_model and
            baseline_climatology are not None, the dictionary will have the
            data attributes "anomaly" and "baseline"; otherwise there will be a
            single data attribute called "data" that returns nominal values of
            the variable during the projected climatological period.

            A data attribute's value is a dictionary of time resolutions:
            monthly, seasonal, annual, whichever are available for the variable
            in question. Each time resolution attribute will have the
            appropriate number of timestamps (12, 4, or 1) for a climatology,
            corresponding to a list containing the requested percentiles for
            that timestamp.

        For example::

            {
              "units": "degC",
              "percentiles": [ 10, 50 ],
              "region": "bc",
              "climatology": "2050",
              "variable": "tasmean",
              "baseline_model": "anusplin",
              "baseline_climatology": "6190",
              "anomaly":[
                {   
                "timescale": 'monthly',
                "date": '1977-01-15 00:00:00',
                "values": [ 2.1310248585852, 3.3104322776824]
                },
                {   
                "timescale": 'monthly',
                "date": '1977-02-15 00:00:00',
                "values": [ 2.0116830378, 2.802655705519 ]
                },
                {   
                "timescale": 'monthly',
                "date": '1977-03-15 00:00:00',
                "values": [ 2.176002151962, 2.8835552547429 ]
                },

                ...
                
                {
                "timescale": 'seasonal',
                "date": '1977-01-16 00:00:00',
                "values": [ 2.7983318484797, 3.3868735586218 ]
                },
                {
                "timescale": 'seasonal',
                "date": '1977-04-16 00:00:00',
                "values": [ 2.3564425042040, 3.200660500285 ]
                },
                {
                "timescale": 'seasonal',
                "date": '1977-07-16 00:00:00',
                "values": [ 2.0237840492108, 3.1990939413123 ]
                },

                ...

                {
                "timescale": 'yearly',
                "date": '1977-07-02 00:00:00',
                "values": [ 2.3264379226208, 3.2458067672088 ]
                }   
              ],         
              
              "baseline": [
                {   
                "timescale": 'monthly',
                "date": '1977-01-15 00:00:00',
                "values": "-11.71985179823"
                },
                {   
                "timescale": 'monthly',
                "date": '1977-02-15 00:00:00',
                "values": "-8.14627567484"
                },
                {   
                "timescale": 'monthly',
                "date": '1977-03-15 00:00:00',
                "values": "-4.646276537509"
                },

                ...
                
                {
                "timescale": 'seasonal',
                "date": '1977-01-16 00:00:00',
                "values": "-10.197912446193"
                },
                {
                "timescale": 'seasonal',
                "date": '1977-04-16 00:00:00',
                "values": "0.6503344819899"
                },
                {
                "timescale": 'seasonal',
                "date": '1977-07-16 00:00:00',
                "values": "11.495438686239"
                },

                ...

                {
                "timescale": 'yearly',
                "date": '1977-07-02 00:00:00',
                "values": "0.8551423608977"
                }   
              ]

            }
    '''

    # get data directory
    region_dir = os.getenv('REGION_DATA_DIRECTORY').rstrip("/")

    calculate_anomaly = False
    baseline_data = [{} for i in range(17)]

    percentiles = [float(p) for p in percentile.split(',')]

    if baseline_model != '' and baseline_climatology != '':
        calculate_anomaly = True
    elif baseline_model != '' or baseline_climatology != '':
        abort(400,
              ('Must supply both historical model and climatology ',
               'for anomaly calculation'))

    def generate_list_idx(timescale, timeidx):
        '''
        This function accepts a timescale and timeidx to generate
        an index that is useful for list data structure. 
        Index 0~11 is assigned to "monthly" timescale Jan~Dec.
        Index 12~15 is assigned to "seasonal" timescale Winter~Fall.
        Index 16 is assigned to "yearly" timescale.
        '''
        if timescale == "monthly":
            idx = int(timeidx)
        elif timescale == "seasonal": 
            idx = int(timeidx) + 12
        else:
            idx = 16

        return idx

    def add_to_nested_li(li, attributes, date):
        '''
        This function accepts a list of data objects(can be empty), 
        attributes data and ctimestamp. The output is an updated list 
        with an added data object/value. Unlike li.append(), this 
        function checks if there is a data object that has the same 
        index already in the list. If there is a duplicate, it only 
        updates the data object by appending the new value to the 
        object's "values" attribute. Otherwise, create a new data
        object and add to the list.
        '''

        idx = generate_list_idx(attributes["timescale"], attributes["timeidx"])
        
        k = "values"
        if k in li[idx].keys():
            li[idx][k].append(attributes["mean"])
        else:
            obj = create_data_object(attributes["mean"], attributes["timescale"],
                                            date, attributes["model"])
            li[idx] = obj

        return li

    def create_data_object(value, timescale, date, model=None):
        '''    
        this function accepts data arguments and assembles them into a dictionary.
        it is intended to create a data object from given data to store in lists effectively.
        '''

        if model:
            return {"timescale": timescale,
                    "date": date,
                    "values": [value],
                    "models": [model]}
        else:
            return {"timescale": timescale,
                    "date": date,
                    "values": [value]}            



    def canonical_timestamp(timestamp, timescale, timeidx):
        '''    
        this function accepts a timestamp and returns a standardized value
        for comparison between models with different calendars.
        it is intended to smooth over differences of a day or two caused by
        calendar divergences around month length, so it will raise an error
        if a timestamp has an unexpected month value for its index.
        '''

        date_format = '%Y-%m-%d %H:%M:%S'
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        if timescale == "monthly":
            if dt.month == int(timeidx) + 1:
                return dt.replace(day=15, hour=0,
                                  minute=0, second=0).strftime(date_format)
        elif timescale == "seasonal":
            if dt.month == (int(timeidx) * 3) + 1:
                return dt.replace(day=16, hour=0,
                                  minute=0, second=0).strftime(date_format)
        elif timescale == "yearly":
            if dt.month == 7:
                return dt.replace(day=2, hour=0,
                                  minute=0, second=0).strftime(date_format)
        abort(500,
              "Invalid timestamp for {} {}: {}".format(timescale,
                                                       timeidx,
                                                       timestamp))

    try:
        # fetch stored queries from csv
        with open("{}/{}.csv".format(region_dir, region),
                  "r") as stored_query_file:
            queries = DictReader(stored_query_file)

            projected_data = [{} for i in range(17)]
            units = ''
            # go through stored queries, collecting all that match parameters
            for row in queries:
                ctimestamp = canonical_timestamp(row["timestamp"],
                                                 row["timescale"],
                                                 row["timeidx"])
                if row['variable'] == variable:
                    if row["units"] != units:  # make sure datasets share units
                        if units == '':
                            units = row['units']
                        else:
                            abort(500,
                                  message=("Incompatible units: ",
                                           "{}, {}").format(units,
                                                            row['units']))

                    if row['climatology'] == climatology:

                        projected_data = add_to_nested_li(projected_data, row, ctimestamp)

                    elif (calculate_anomaly and
                            row['model'] == baseline_model and
                            row['climatology'] == baseline_climatology):
                        obj = create_data_object(row["mean"], row["timescale"], ctimestamp)
                        idx = generate_list_idx(row["timescale"], row["timeidx"])
                        baseline_data[idx] = obj


        projected_data = [data_object for data_object in projected_data if data_object != {}]
        baseline_data = [data_object for data_object in baseline_data if data_object != {}]

        # calculate percentiles and anomalies
        for p in projected_data:
            # determine the baseline, if applicable
            if calculate_anomaly:
                baseline = None
                date_format = '%Y-%m-%d %H:%M:%S'
                projected_date = datetime.strptime(p["date"], date_format)

                for b in baseline_data:
                    baseline_date = datetime.strptime(b["date"], date_format)
                    if p["timescale"] == b["timescale"] and baseline_date.month == projected_date.month:
                        if not baseline:
                            b["values"] =b["values"][0]
                            baseline = float(b["values"])
                        else:
                            abort(500,
                                    ("Multiple matching baseline datasets ",
                                    "for {} {} {} {}").format(
                                        baseline_model,
                                        baseline_climatology,
                                        p["timescale"], p["date"]))       

                if(not baseline):
                    abort(500, "Missing baseline data: {} {} {}".format(
                                                baseline_model, baseline_climatology, p["timescale"]))    

            else:
                baseline = 0.0
            values = np.asarray([float(v) for v in p["values"]])

            if values.size < 12:
                abort(500,
                        "Not all models available for {} {}. Models available: {}").format(
                            p["timescale"], p["date"], p["models"])
            elif values.size > 12:
                abort(500,
                        "Extraneous data for {} {}. Models available: {}").format(
                            p["timescale"], p["date"], p["models"])

            anomalies = values - baseline

            p["values"] = list(np.percentile(anomalies, percentiles))
            del(p["models"])




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
            response["data"] = projected_data

        return response

    except EnvironmentError:
        abort(404, description="Data for region {} not found".format(region))