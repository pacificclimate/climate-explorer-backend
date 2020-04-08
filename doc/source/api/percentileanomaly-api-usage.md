This API serves percentile calculations taken across the PCIC12 ensemble for each of plan2adapt's 52 defined regions. It relies on stored values previously calculated by calling the `stats` API, so only the specific set of variables, regions, and time periods for which the results have been stored are available. While all these values could, of course, be calculated in real time by calling the `stats` endpoint, calling the `stats` endpoint separately for each of the 12 datasets in order to calculate precentiles is prohibitively slow, necessitating this use of stored data.

This endpoint can return either percentiles calculated over the set of projected absolute values for some climatology, or percentiles calculated over the set of anomaly values calculated by subtracting the value of a historical baseline from the value of each projected value for the climatology. Be default, percentiles of anomalies from the ANUSPLIN 1961-1990 baseline are returned.

This endpoint was created to speed up percentile calculations needed by plan2adapt, it supports only the climatologies, variables, and regions required by plan2adapt; it is not a general interface allowiing access to all PCIC data. All values are for the rcp 8.5 emissions scenario.

## Supported regions:
1. alberni_clayoquot
1. bc
1. boreal_plains
1. bulkley_nechako
1. capital
1. cariboo
1. central_coast
1. central_interior
1. central_kootenay
1. central_okanagan
1. coast_and_mountains
1. columbia_shuswap
1. comox_valley
1. cowichan_valley
1. east_kootenay
1. fraser_fort_george
1. fraser_valley
1. georgia_depression
1. greater_vancouver
1. interior
1. kitimat_stikine
1. kootenay_boundary
1. mt_waddington
1. nanaimo
1. northeast
1. northern_boreal_mountains
1. northern
1. northern_rockies
1. north_okanagan
1. okanagan_similkameen
1. omineca
1. peace_river
1. powell_river
1. skeena
1. skeena_queen_charlotte
1. south_coast
1. southern_interior
1. southern_interior_mountains
1. squamish_lillooet
1. stikine
1. strathcona
1. sub_boreal_mountains
1. sunshine_coast
1. taiga_plains
1. thompson_nicola
1. thompson_okanagan
1. vancouver_coast
1. vancouver_fraser
1. vancouver_island
1. west_coast

## Supported variables:
1. ffd (Frost Free Days)
1. gdd (Growing Degree Days)
1. hdd (Heating Degree Days)
1. pr (Precipitation)
1. prsn (Precipitation as Snow)

## Supported climatologies:
1. 2020 (2010-2039)
2. 2050 (2040-2069)
3. 2080 (2070-2099)

## Supported baseline:
The only available baseline is the ANUSPLIN dataset, 1961-1990 climatology.