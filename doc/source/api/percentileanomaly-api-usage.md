This API serves percentile calculations taken across the PCIC12 ensemble for each of plan2adapt's defined regions. It relies on stored values previously calculated by calling the `stats` API, so only the specific set of variables, regions, and time periods for which the results have been stored are available. While all these values could, of course, be calculated in real time by calling the `stats` endpoint, calling the `stats` endpoint separately for each of the 12 datasets in order to calculate precentiles is prohibitively slow, necessitating this use of stored data.

This endpoint can return either percentiles calculated over the set of projected absolute values for some climatology, or percentiles calculated over the set of anomaly values calculated by subtracting the value of a historical baseline from the value of each projected value for the climatology. Be default, percentiles of anomalies from the ANUSPLIN 1961-1990 baseline are returned.

This endpoint was created to speed up percentile calculations needed by plan2adapt, it supports only the climatologies, variables, and regions required by plan2adapt; it is not a general interface allowiing access to all PCIC data. All values are for the rcp 8.5 emissions scenario.

## Supported variables:
1. ffd (Frost Free Days)
1. gdd (Growing Degree Days)
1. hdd (Heating Degree Days)
1. pr (Precipitation)
1. prsn (Precipitation as Snow)
1. tasmean (Daily Mean Air temperature)

## Supported climatologies:
1. 2020 (2010-2039)
2. 2050 (2040-2069)
3. 2080 (2070-2099)

## Supported baseline:
The only available baseline is the ANUSPLIN dataset, 1961-1990 climatology.