"""module for requesting change from a baseline value, expressed as a
percentile value of the spread of the PCIC12 models. Because opening a file for
each of the 12 models is unworkably slow, this module instead extracts data
from CSV files holding precomputed results of /stats queries."""

from flask import abort
from csv import DictReader
import os
from datetime import datetime
import numpy as np


def percentileanomaly(
    sesh,
    region,
    climatology,
    variable,
    percentile="50",
    baseline_model="anusplin",
    baseline_climatology="6190",
):
    """Request percentiles summaries of the data range of the PCIC12 ensemble
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
              "anomaly": {
                "yearly": {
                  "2055-07-02 00:00:00": [ 2.3264379226208, 3.2458067672088 ]
                },
                "monthly": {
                  "2055-01-15 00:00:00": [ 2.1310248585852, 3.3104322776824],
                  "2055-02-15 00:00:00": [ 2.0116830378, 2.802655705519 ],
                  "2055-03-15 00:00:00": [ 2.176002151962, 2.8835552547429 ],
                  ...
                },
                "seasonal": {
                  "2055-01-16 00:00:00": [ 2.7983318484797, 3.3868735586218 ],
                  "2055-04-16 00:00:00": [ 2.3564425042040, 3.200660500285 ],
                  "2055-07-16 00:00:00": [ 2.0237840492108, 3.1990939413123 ],
                  ...
                }
              },
              "baseline": {
                "yearly": {
                  "1977-07-02 00:00:00": "0.8551423608977"
                },
                "monthly": {
                  "1977-01-15 00:00:00": "-11.71985179823",
                  "1977-02-15 00:00:00": "-8.14627567484",
                  "1977-03-15 00:00:00": "-4.646276537509",
                  ...
                },
                "seasonal": {
                  "1977-01-16 00:00:00": "-10.197912446193",
                  "1977-04-16 00:00:00": "0.6503344819899",
                  "1977-07-16 00:00:00": "11.495438686239",
                  ...
                }
              }
            }
    """

    # get data directory
    region_dir = os.getenv("REGION_DATA_DIRECTORY").rstrip("/")

    calculate_anomaly = False
    baseline_data = {}

    percentiles = [float(p) for p in percentile.split(",")]

    if baseline_model != "" and baseline_climatology != "":
        calculate_anomaly = True
    elif baseline_model != "" or baseline_climatology != "":
        abort(
            400,
            (
                "Must supply both historical model and climatology ",
                "for anomaly calculation",
            ),
        )

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

    # this function accepts a timestamp and returns a standardized value
    # for comparison between models with different calendars.
    # it is intended to smooth over differences of a day or two caused by
    # calendar divergences around month length, so it will raise an error
    # if a timestamp has an unexpected month value for its index.
    def canonical_timestamp(timestamp, timescale, timeidx):
        date_format = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        if timescale == "monthly":
            if dt.month == int(timeidx) + 1:
                return dt.replace(day=15, hour=0, minute=0, second=0).strftime(
                    date_format
                )
        elif timescale == "seasonal":
            if dt.month == (int(timeidx) * 3) + 1:
                return dt.replace(day=16, hour=0, minute=0, second=0).strftime(
                    date_format
                )
        elif timescale == "yearly":
            if dt.month == 7:
                return dt.replace(day=2, hour=0, minute=0, second=0).strftime(
                    date_format
                )
        abort(
            500, "Invalid timestamp for {} {}: {}".format(timescale, timeidx, timestamp)
        )

    try:
        # fetch stored queries from csv
        with open("{}/{}.csv".format(region_dir, region), "r") as stored_query_file:
            queries = DictReader(stored_query_file)

            projected_data = {}
            units = ""
            # go through stored queries, collecting all that match parameters
            for row in queries:
                ctimestamp = canonical_timestamp(
                    row["timestamp"], row["timescale"], row["timeidx"]
                )
                if row["variable"] == variable:
                    if row["units"] != units:  # make sure datasets share units
                        if units == "":
                            units = row["units"]
                        else:
                            abort(
                                500,
                                message=("Incompatible units: ", "{}, {}").format(
                                    units, row["units"]
                                ),
                            )

                    if row["climatology"] == climatology:
                        add_to_nested_dict(
                            projected_data,
                            row["mean"],
                            row["timescale"],
                            ctimestamp,
                            row["model"],
                        )
                    elif (
                        calculate_anomaly
                        and row["model"] == baseline_model
                        and row["climatology"] == baseline_climatology
                    ):
                        add_to_nested_dict(
                            baseline_data, row["mean"], row["timescale"], ctimestamp
                        )

        # calculate percentiles and anomalies
        for timescale in projected_data:
            for timestamp in projected_data[timescale]:
                # determine the baseline, if applicable
                if calculate_anomaly:
                    baseline = None
                    date_format = "%Y-%m-%d %H:%M:%S"
                    projected_date = datetime.strptime(timestamp, date_format)
                    if timescale not in baseline_data:
                        abort(
                            500,
                            "Missing baseline data: {} {} {}".format(
                                baseline_model, baseline_climatology, timescale
                            ),
                        )
                    for t in baseline_data[timescale]:
                        baseline_date = datetime.strptime(t, date_format)
                        if baseline_date.month == projected_date.month:
                            if not baseline:
                                baseline = float(baseline_data[timescale][t])
                            else:
                                abort(
                                    500,
                                    (
                                        "Multiple matching baseline datasets ",
                                        "for {} {} {} {}",
                                    ).format(
                                        baseline_model,
                                        baseline_climatology,
                                        timescale,
                                        timestamp,
                                    ),
                                )
                    if baseline is None:
                        abort(
                            500,
                            ("No baseline match available for ", "{} {} {} {}").format(
                                baseline_model,
                                baseline_climatology,
                                timescale,
                                timestamp,
                            ),
                        )
                else:
                    baseline = 0.0
                values = np.asarray(
                    [float(v) for v in projected_data[timescale][timestamp].values()]
                )
                if values.size < 12:
                    abort(
                        500, "Not all models available for {} {}. Models available: {}"
                    ).format(
                        timescale,
                        timestamp,
                        projected_data[timescale][timestamp].keys(),
                    )
                elif values.size > 12:
                    abort(
                        500, "Extraneous data for {} {}. Models available: {}"
                    ).format(
                        timescale,
                        timestamp,
                        projected_data[timescale][timestamp].keys(),
                    )
                anomalies = values - baseline
                projected_data[timescale][timestamp] = list(
                    np.percentile(anomalies, percentiles)
                )

        response = {
            "units": units,
            "percentiles": percentiles,
            "region": region,
            "climatology": climatology,
            "variable": variable,
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
