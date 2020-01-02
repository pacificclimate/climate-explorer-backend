This endpoint accepts parameters describing a collection of datasets and a time of year and extracts data for the requested time of year from all datasets that match the parameters and contain it as one or more timeseries.

It shows how a variable changes over the long term. For example, with six datasets representing different climatologies it would return mean daily  August precipitation from 1961-1990, 1971-2000, 1981-2010, 2010-2039, 2040-2069, and 2070-2099 as a single timeseries.

This slices the data along a different axis than the `timeseries` endpoint, which shows values of a variable within a given dataset, and would return a timeseries consisting of mean daily precipitation for January 1961-1990, February 1961-1990, etc. instead.