## Datafile Preparation

Input data files can be created from CMIP5 compliant input with the following method:

```
.... detail functions here
```


```
for i in $(find -type f -name "*tasmin*");
do
  echo $i;
  ncks -O -v tasmin,lon_bnds,lat_bnds,climatology_bounds --msa -d lon,180.,360. -d lon,0.,179.999999 $i $i
  ncap2 -O -s 'where(lon>180) lon=lon-360' $i $i
done


for i in $(find -type f -name "*tasmax*");
do
  echo $i;
  ncks -O -v tasmax,lon_bnds,lat_bnds,climatology_bounds --msa -d lon,180.,360. -d lon,0.,179.999999 $i $i
  ncap2 -O -s 'where(lon>180) lon=lon-360' $i $i
done
```

### Terrible Bash Method

Creating basic climatological files can be accomplished with the following bash method, but it suffers from some shortcomings. In addition to the bash methods, we need to:

1. Revise time variable to meet CF1.6 spec for climatological series
2. Add a climatology_bounds variable as per CF1.6 spec
3. Process file names to correct the time range available

```bash
IFILE=/home/data/climate/CMIP5/CCCMA/CanESM2/rcp45/day/atmos/day/r1i1p1/v20120410/tasmax/tasmax_day_CanESM2_rcp45_r1i1p1_20060101-23001231.nc
TEMP=~/deleteme_temp.nc
OUTPUT_CLIM=~/deleteme_chained.nc

cdo seldate,2010-01-01,2039-12-31 $IFILE $TEMP
cdo copy -ymonmean $TEMP -yseasmean $TEMP -timmean $TEMP $OUTPUT_CLIM
```

If the longitude in the original file is 0 -> 360 rather than -180 -> 180 this will also need to be transformed

```bash
ncks -O -v <variabl> --msa -d lon,180.,360. -d lon,0.,179.999999 $OUTPUT_CLIM $OUTPUT_CLIM
ncap2 -O -s 'where(lon>180) lon=lon-360' $i $i
```
