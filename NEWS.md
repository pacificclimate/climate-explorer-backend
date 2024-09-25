# News / Release Notes

## 3.6.4
**2024-Sep-24**

- Updated to python 3.10 [#247](https://github.com/pacificclimate/climate-explorer-backend/pull/247)

## 3.6.3
**2024-Aug-07**

- Fixes a transient build error (no PR). 

## 3.6.2
**2024-Feb-13**

- Updates the structure of sqlalchemy joins. [#226](https://github.com/pacificclimate/climate-explorer-backend/pull/226)

- Accept POST requests to handle very long area strings [#229](https://github.com/pacificclimate/climate-explorer-backend/pull/229) 

## 3.6.1
**2023-Feb-03**

- Add pre-ping param to engine creation (seems to solve problem of database 
  connections being closed and causing 500s).
  [#223](https://github.com/pacificclimate/climate-explorer-backend/pull/223)


## 3.6.0
**2023-Feb-03**

ERRONEOUS - DO NOT USE

## 3.5.1
**2022-October-31**

- Update documentation for watershed-related APIs. [#218](https://github.com/pacificclimate/climate-explorer-backend/pull/218)

- Speed up the process of building a drainage area in watershed APIs by preloading data instead of repeatedly accessing the file. [#214](https://github.com/pacificclimate/climate-explorer-backend/pull/214)


## 3.5.0
**2022-April-26**

- Switch install method to pipenv [#194](https://github.com/pacificclimate/climate-explorer-backend/pull/194)

- Replace anchore scanner with snyk [#196](https://github.com/pacificclimate/climate-explorer-backend/pull/196)

- Add a downstream API that returns the path from a selected stream to the sea or the edge of the file. [#199](https://github.com/pacificclimate/climate-explorer-backend/pull/199)

- Add a watershed_streams API that returns the network of streamflow connectivity with a watershed defined by all grid cells upstream of a selected point [#200](https://github.com/pacificclimate/climate-explorer-backend/pull/200), [#207](https://github.com/pacificclimate/climate-explorer-backend/pull/207)


## 3.4.0
**2021-March-29**

- Change the way Melton ratio is calculated for better accuracy [#190](https://github.com/pacificclimate/climate-explorer-backend/pull/190)

- Allow filtering by Nth percentile in data and multimeta[#188](https://github.com/pacificclimate/climate-explorer-backend/pull/188)

- Rename "cell_methods" parameter "climatological_statistic" and add filtering on it to multimeta API [#187](https://github.com/pacificclimate/climate-explorer-backend/pull/187)

## 3.3.2
**2021-March-10**

- Add filtering on cell_methods parameter to `multimeta` API. [#182](https://github.com/pacificclimate/climate-explorer-backend/pull/182)

## 3.3.1
**2021-February-16**

- Speed up the `data` API by streamlining units comparison done in `get_units_from_run_object()` [#180](https://github.com/pacificclimate/climate-explorer-backend/pull/180)

## 3.3.0
**2021-January-29**

- Add calculation of the Melton Ratio (elevation delta over a stream divided by square root of area drained) to the `watershed` API [#174](https://github.com/pacificclimate/climate-explorer-backend/pull/174)
- Extend filtering on cell methods, previously only available in the `multistats` API, to the `data` API and support new parameter value, `percentile` in anticipation of new data types [#176](https://github.com/pacificclimate/climate-explorer-backend/pull/176)

## 3.2.0
**2020-November-9**

- Replace `m2r` with `m2r2` [#164](https://github.com/pacificclimate/climate-explorer-backend/pull/164)
- Provides units in `metadata` and `multidata` responses [#165](https://github.com/pacificclimate/climate-explorer-backend/pull/165)
- Add ensemble name filter to `get_units_from_file_object` [#169](https://github.com/pacificclimate/climate-explorer-backend/pull/169)
- Optionally target data from thredds server [#171](https://github.com/pacificclimate/climate-explorer-backend/pull/171)

## 3.1.0
*2020-Aug-7*

- Add optional `filepath` property to metadata responses
  [#150](https://github.com/pacificclimate/climate-explorer-backend/pull/150)

## 3.0.1
*2020-Aug-6*

* Fix errors in database queries for API endpoints [#154](https://github.com/pacificclimate/climate-explorer-backend/pull/154)
* Use Black as Python code style checker [#155](https://github.com/pacificclimate/climate-explorer-backend/pull/155)

## 3.0.0
*13-July-2020*

* Upgrades modelmeta and netCDF4 requirements [#147](https://github.com/pacificclimate/climate-explorer-backend/pull/147)
  and [#144](https://github.com/pacificclimate/climate-explorer-backend/pull/144)
* Migrate Continuous Integration to Github Actions [#145](https://github.com/pacificclimate/climate-explorer-backend/pull/145)

## 2.0.0
*21-May-2020*

* Update GDAL to version 3.0 [#140](https://github.com/pacificclimate/climate-explorer-backend/pull/140)
* Format `percentileanomaly` API output as a list [#133](https://github.com/pacificclimate/climate-explorer-backend/pull/137)
* Set up PEP8 testing and bring existing code up to standard [#141](https://github.com/pacificclimate/climate-explorer-backend/pull/141)


## 1.3.0
*21-May-2020*

* Use the PCIC jenkins library [#124](https://github.com/pacificclimate/climate-explorer-backend/pull/124)
* Document suggested use of watershed API [#132](https://github.com/pacificclimate/climate-explorer-backend/pull/132)
* Add `percentileanomaly` and `regions` API endpoints to support plan2adapt [#128](https://github.com/pacificclimate/climate-explorer-backend/pull/128)

## 1.2.0
*28-January-2020*

* Add support for Jenkins PRs [#104](https://github.com/pacificclimate/climate-explorer-backend/pull/104), [#107](https://github.com/pacificclimate/climate-explorer-backend/pull/107), and [#117](https://github.com/pacificclimate/climate-explorer-backend/pull/117)
* Drop support for Python 3.5 [PR #116](https://github.com/pacificclimate/climate-explorer-backend/pull/116)
* Add sphinx documentation of API functionality [PR #114](https://github.com/pacificclimate/climate-explorer-backend/pull/114)
* Add watershed API endpoint to serve information about the physical hydrology of the watershed draining to a specific point [PR #108](https://github.com/pacificclimate/climate-explorer-backend/pull/108)
* Improve efficiency of data cache [PR #102](https://github.com/pacificclimate/climate-explorer-backend/pull/102)
* Pin netcdf4 to <1.4, avoiding a change to default array behaviour in 1.4 where all variables, even those with no masked items, as returned as MaskedArrays [PR #100](https://github.com/pacificclimate/climate-explorer-backend/pull/100)

## 1.1.1
*15-April-2019*

* Fix for `cell_method` filter issue [PR #99](https://github.com/pacificclimate/climate-explorer-backend/pull/99)

## 1.1.0

*08-February-2019*

* Update rasterio to new release candidate [PR #80](https://github.com/pacificclimate/climate-explorer-backend/pull/80)
* Update /data query to only use appropriate files [PR #82](https://github.com/pacificclimate/climate-explorer-backend/pull/82)
* Several updates to tests [PR #84](https://github.com/pacificclimate/climate-explorer-backend/pull/84) [PR #90](https://github.com/pacificclimate/climate-explorer-backend/pull/90)
* Add streamflow API spec [PR #88](https://github.com/pacificclimate/climate-explorer-backend/pull/88)
* Fix outdated documentation [PR #95](https://github.com/pacificclimate/climate-explorer-backend/pull/95)
* Add `cell_method` filtering option [PR #96](https://github.com/pacificclimate/climate-explorer-backend/pull/96)

## 1.0.0

*08-February-2018*

* Improvements to data processing pipline PRs [#32](https://github.com/pacificclimate/climate-explorer-backend/pull/32), [#33](https://github.com/pacificclimate/climate-explorer-backend/pull/33), [#38](https://github.com/pacificclimate/climate-explorer-backend/pull/38).
* Improves the 400 error message with a list of missing query params [PR #28](https://github.com/pacificclimate/climate-explorer-backend/pull/28).
* Replaces home-cooked code for "burning" a polygon into a raster with [rasterio](https://github.com/mapbox/rasterio)'s mask() function [PR #55](https://github.com/pacificclimate/climate-explorer-backend/pull/55).
* Add climatological info to GET /api/metadata request [PR #56](https://github.com/pacificclimate/climate-explorer-backend/pull/56).
* Add climatology bounds info to /api/multimeta request [PR #62](https://github.com/pacificclimate/climate-explorer-backend/pull/62).
* Fixes bug in timeseries call where values would not vary across the year [PR #66](https://github.com/pacificclimate/climate-explorer-backend/pull/66).
* Fixes GDAL crash bug [PR #70](https://github.com/pacificclimate/climate-explorer-backend/pull/70).
* Sets HTTP headers to enable client-side caching [PR #75](https://github.com/pacificclimate/climate-explorer-backend/pull/75).
* Replaces Dockerfile with a build that uses gunicorn for production deployment.

## 0.2.0

*11-April-2017*

* Adds 'timescale' addtribute to the multimeta API call
* Overhauls the data preparation script (i.e. the generation of climatological means) to rely solely on metadata *within* the file (no file paths or file names)

## 0.1.1

*11-April-2016*

* Remove Flask-Cache due to insufficient key creation. [PR #19](https://github.com/pacificclimate/climate-explorer-backend/pull/19).
* Harden mask cacheing key creation. [PR #22](https://github.com/pacificclimate/climate-explorer-backend/pull/22).
* Delegate grid masking to [rasterio](https://github.com/mapbox/rasterio). [PR #24](https://github.com/pacificclimate/climate-explorer-backend/pull/24)

## 0.1.0

*2-March-2016*

* Initial versioned release
