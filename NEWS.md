# News / Release Notes

## 3.0.1
*13-July-2020*

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
