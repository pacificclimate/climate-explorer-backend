This API endpoint provides contextual information about the watershed that drains to the point specified by the parameters. It is intended to clarify and provide context for data about streamflow in watershed.

Every grid cell is defined as flowing into a single other grid cell, so this data is most reliable for larger watersheds representing at least ten grid cells, and completely inappropriate for creeks or culverts smaller than a single grid cell. At small scales, streamflow variations within grid cells, not capturable by a gridded dataset, play too large a role.

## Hypsometric curve
The `hypsometric_curve` object defines a histogram of area by elevation. 

* Elevation bins are of equal width, `w = elevation_bin_width`.
* Elevation bin `k` is bounded by elevations `ek` and `ek+1`, where `ek = e0 + (k * w)` for `0 <= k < n`
* where `e0 = elevation_bin_start` and `n = elevation_num_bins`
* The sum of areas of all cells with elevation falling into elevation bin `k` is given by `ak = cumulative_areas[k]`.
* Units of elevation and area are specified by the properties `elevation_units` and `area_units`.

### Gaps in the hypsometric curve, or "empty" bins
For large areas of the earth and reasonably large elevation bins, we expect to see non-zero cumulative areas for each elevation bin between the minimum and maximum elevation over that area. In other words, there should be at least some area at each elevation in the histogram.

However, for small areas with steep topography, it is common to see some of the elevation bins between min and max elevation with zero area. This is not an error in either the computation or the data that feeds it. It is instead a product of the fact that `n` surface grid cells can represent at most `n` elevations.

Consider the most extreme case of `n = 2` cells that happen to be positioned at the edge of a steep sided valley. One cell is in the valley bottom with an average elevation of 100 m. The other cell, just adjacent to it, mostly covers the highland above with an average elevation of 500 m. In a histogram with 100 m bin width, we'd see non-zero areas for the 100 m bin and the 500 m bin, but zero areas for the 200 m, 300 m, and 400 m elevation bins, and in the graph these would look like gaps.

We can see a similar effect for other small values of `n > 2` in steep terrain too. Once `n` becomes large enough, then the likelihood of an elevation bin not having some cells is quite low and these gaps do not appear.

## Melton Ratio

The Melton Ratio (ratio of watershed relief to the square of the area) is used to characterize a location as being dominated by either flooding (Melton ratios < 0.3) or debris flows (Melton ratios > 0.6) (Wilford et al., 2004).

The watershed API delineates a watershed boundary, or drainage polygon, based on a selected point of interest, from which all upstream cells are determined with VIC-GL’s flow network. The drainage polygon is used to select the minimum and maximum elevations, compute the watershed relief and area.

Watershed relief is defined as maximum elevation minus minimum elevation. Minimum and maximum elevations are extracted from the GMTED2010 7.5 arc-second DEM (Danielson and Gesch, 2011).