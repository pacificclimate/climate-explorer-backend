This API endpoint provides contextual information about the watershed that drains to the point specified by the parameters. 

Every grid cell is defined as flowing into a single other grid cell, so this data is most reliable for larger watersheds representing at least ten grid cells, and completely inappropriate for creeks or culverts smaller than a single grid cell. At small scales, streamflow variations within grid cells, not captured by this dataset, play too large a role.

## Hypometric curve
The `hypsometric_curve` object defines a histogram of area by elevation. 

* Elevation bins are of equal width, `w = elevation_bin_width`.
* Elevation bin `k` is bounded by elevations `ek` and `ek+1`, where `ek = e0 + (k * w)` for `0 <= k < n`
* where `e0 = elevation_bin_start` and `n = elevation_num_bins`
* The sum of areas of all cells with elevation falling into elevation bin `k` is given by `ak = cumulative_areas[k]`.
* Units of elevation and area are specified by the properties `elevation_units` and `area_units`.

Because elevation data is given as the mean of each grid square it is possible to have nonzero values for two elevation bins `ek` and `ek+2` but a zero value for `ek+1` in steep landscapes.