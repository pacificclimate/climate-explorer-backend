Regional Precalculated Data
===========================

This directory contains stored results from the `stats` API for each of the 52 plan2adapt regions. 
These support the `percentileanomaly` query, as opening thirteen files for each percentile datum proved
prohibitively slow. 

Each row in a CSV file stores the parameters and results of a `stats` call on a single dataset and timestamp
that meets either the *projection* criteria or the *baseline* criteria. All datasets and timestamps fitting the
criteria are included, even though plan2adapt does not use all of them.

Projection criteria
-------------------
* the model is one of the PCIC12
* the variable is one of: `tasmax`, `tasmin`, `pr`, `gdd`, `fdETCCDI`, `prsn`, `hdd` OR the composite variables `ffd` and `tasmean`
* the climatology is a projected climatology, either the 2010-2039 (2020s), 2040-2069 (2050s), or 2070-2099 (2080s)

Baseline criteria
-----------------
* the model is `anusplin`, plan2adapt's designated baseline
* the variable is one of: `tasmax`, `tasmin`, `pr`, `gdd`, `fdETCCDI`, `prsn`, `hdd` OR the composite variables `ffd` and `tasmean`
* the climatology is the historical 1961-1990 climatology

Composite variables
-------------------
Composite variables are caculated from one or more real variables, but do not correspond to a real
dataset listed in the metadata database or available on disk. They have `unique_ids` of `null` but
otherwise are presented identically to actual datasets.

`tasmean` is the average of `tasmin` and `tasmax` for a given scenario, model, climatology, time resolution,
and timestamp.

`ffd` is 365 days minus the value of `fdETCCDI` for a given scenario, model, climatology, time resolution,
and timestamp.

How to use the precomputed stats calls
--------------------------------------
Try not to! It's always best to use live data if possible.

To substitute precalculated data for a call to the `stats` API, you can check the 
`unique_id`, `timeidx`, and `variable` columns to match the parameters of your desired `stats`
query, then read the `min`, `max`, `mean`, `median`, `stdev`, `ncells`, and `units` column.

To substitute precalculated data for a call to the `multistats` API, you will additionally
need to check the `model`, `scenario`, and `timescale` columns to find the set of `unique_ids`
that match your parameters. 

To substitute for a `timeseries` API call, you would need to check the `unique_id` and `variable`
columns, and return data from the `mean` and `timestamp` columns.

Note that the composite variables, `ffd` and `tasmean` do not have `unique_id` values, as they do not
correspond to a real dataset in the modelmeta database or in storage. They'll require special 
handling if you want to mock an API endpoint that normally uses `unique_id`

There are additional metadata columns for debugging and quality control purposes.