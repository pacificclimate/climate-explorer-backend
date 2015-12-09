## Datafile Preparation

Creating basic climatological files can be accomplished with the following bash method, but it suffers from some shortcomings. In addition to the bash methods, we need to:

1. Revise time variable to meet CF1.6 spec for climatological series
2. Add a climatology_bounds variable as per CF1.6 spec
3. Process file names to correct the time range available

### Bash Methods

```bash
$ find /home/data/climate/CMIP5/ -regex ".*CanESM2/\(rcp\|historical/\).*tasmax.*r1i1p1.*nc"

/home/data/climate/CMIP5/CCCMA/CanESM2/rcp45/day/atmos/day/r1i1p1/v20120410/tasmax/tasmax_day_CanESM2_rcp45_r1i1p1_20060101-23001231.nc
/home/data/climate/CMIP5/CCCMA/CanESM2/rcp26/day/atmos/day/r1i1p1/v20120410/tasmax/tasmax_day_CanESM2_rcp26_r1i1p1_20060101-23001231.nc
/home/data/climate/CMIP5/CCCMA/CanESM2/historical/day/atmos/day/r1i1p1/v20120410/tasmax/tasmax_day_CanESM2_historical_r1i1p1_18500101-20051231.nc
/home/data/climate/CMIP5/CCCMA/CanESM2/rcp85/day/atmos/day/r1i1p1/v20120407/tasmax/tasmax_day_CanESM2_rcp85_r1i1p1_20060101-21001231.nc
```

#### Method 1

```bash
IFILE=/home/data/climate/CMIP5/CCCMA/CanESM2/rcp45/day/atmos/day/r1i1p1/v20120410/tasmax/tasmax_day_CanESM2_rcp45_r1i1p1_20060101-23001231.nc
TEMP_MON=~/deleteme_mon.nc
TEMP_ANN=~/deleteme_ann.nc
TEMP_SEAS=~/deleteme_seas.nc
OUTPUT_CLIM=~/deleteme.nc

cdo ymonmean -seldate,2010-01-01,2039-12-31 $IFILE $TEMP_MON
cdo yearmean $TEMP_MON $TEMP_ANN
cdo yseasmean -seldate,2010-01-01,2039-12-31 $IFILE $TEMP_SEAS
cdo copy $TEMP_MON $TEMP_SEAS $TEMP_ANN $OUTPUT_CLIM
```

#### Method 2 (Chaining)

```bash
IFILE=/home/data/climate/CMIP5/CCCMA/CanESM2/rcp45/day/atmos/day/r1i1p1/v20120410/tasmax/tasmax_day_CanESM2_rcp45_r1i1p1_20060101-23001231.nc
TEMP=~/deleteme_temp.nc
OUTPUT_CLIM=~/deleteme_chained.nc

cdo seldate,2010-01-01,2039-12-31 $IFILE $TEMP
cdo copy -ymonmean $TEMP -yseasmean $TEMP -timmean $TEMP $OUTPUT_CLIM
```
