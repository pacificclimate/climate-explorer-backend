## Datafile Preparation

Input data files can be created from CMIP5 compliant input using the `generate_climos.py` script.

This script:

1. Opens an existing NetCDF file
2. Determines what climatological periods to generate
3. Aggregates the daily data to each respective climatological period
4. Revises the time variable to meet CF1.6/CMIP5 specification
5. Adds a climatology_bounds variable to match climatological period
6. Revises output file name with climatological period

The general process is to:

1. Revise time variable to meet CF1.6 spec for climatological series
2. Add a climatology_bounds variable as per CF1.6 spec
3. Process file names to correct the time range available

### Installation

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
# Use defaults:
python generate_climos.py -o <outdir>

# Specify variables and input data:
python generate_climos.py -v tasmax tasmin pr -b <indir> -o <outdir>
```

Usage is further detailed in the provided help information `python generate_climos.py -h`

### Post Processing

As created, the files may need some post processing. This includes:

* Converting longitudes from 0 -> 360 to -180 -> 180
* Scaling variables to more user interpretable values

#### tasmin/tasmax

```
for VAR in tasmin tasmax;
do
  for i in $(find -type f -name "*$VAR*");
  do
    echo $i;
    ncks -O -v $VAR,lon_bnds,lat_bnds,climatology_bounds --msa -d lon,180.,360. -d lon,0.,179.999999 $i $i;
    ncap2 -O -s 'where(lon>=180) lon=lon-360' $i $i;
  done
done
```

#### precip

Precip also requires you to convert to kg m-2 s-1 to mm since we have summed over each time of year

```bash
for i in $(find -type f -name "*pr*");
do
  echo $i;
  ncks -O -v pr,lon_bnds,lat_bnds,climatology_bounds --msa -d lon,180.,360. -d lon,0.,179.999999 $i $i
  ncap2 -O -s 'where(lon>=180) lon=lon-360' $i $i
  cdo -O mulc,86400 $i $i.1
  mv $i.1 $i
  ncatted -a units,pr,m,c,"mm" $i
done
```

### Indexing

Indexing is done using R scripts in the [modelmeta](https://github.com/pacificclimate/modelmeta) package.

To create a fresh modelmeta database, you can use the `mkblankdb.py` script in the modelmeta package.

```bash
python modelmeta/scripts/mkblankdb.py -d sqlite:////tmp/mddb.sqlite3
```

```R
source("db/index_netcdf.r")
f.list <- list.files("<input_directory>", full.name=TRUE, pattern = "\\.nc$", recursive=TRUE)
index.netcdf.files(f.list, host="dbhost", db="dbname", user="dbuser", password="optional")
# Or using sqlite
index.netcdf.files.sqlite(f.list, "/tmp/mddb.sqlite3")
```

Finally, you'll have to add all of the indexed files to an "ensemble", i.e. a group of files to be served in a given application. There currently exists another script in the modelmeta package that searches a database for all of the existing data_file_variables and adds them to a newly created ensemble. This works for the simple case, but you may want to do something more customized.
