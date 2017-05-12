# PCIC Climate Explorer Backend

[![Build Status](https://travis-ci.org/pacificclimate/climate-explorer-backend.svg?branch=master)](https://travis-ci.org/pacificclimate/climate-explorer-backend)
[![Code Climate](https://codeclimate.com/github/pacificclimate/climate-explorer-backend/badges/gpa.svg)](https://codeclimate.com/github/pacificclimate/climate-explorer-backend)

## Dependencies

```bash
$ sudo apt-get install libpq-dev python-dev libhdf5-dev libnetcdf-dev libgdal-dev
```

GDAL doesn't properly source its own lib paths when installing the python package, so we have to define
these environment variables:

```bash
$ export CPLUS_INCLUDE_PATH=/usr/include/gdal
$ export C_INCLUDE_PATH=/usr/include/gdal
```

## Development

### Installation

Setup using virtual environment. 
Use Python 3 module `venv`, not `virtualenv`, which installs Python 2. 
Unit tests use `datetime.timezone`, which is available only in Python 3.

```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv)$ pip install -U pip
(venv)$ pip install -i https://pypi.pacificclimate.org/simple/ -r requirements.txt
(venv)$ pip install -e .
```

### Running the dev server

Database dsn can be configured with the MDDB_DSN environment variable. Defaults to 'postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta'

(venv)$ MDDB_DSN=postgresql://dbuser:dbpass@dbhost/dbname python scripts/devserver.py -p <port>

### Testing

#### Within the virtual environment:

```bash
pip install pytest
py.test -v
```

#### Using Docker container to test current directory:

```bash
sudo docker run --rm -it -v ${PWD}:/app --name backend-test pcic/climate-explorer-backend bash -c "pip install pytest; py.test -v ce/tests"
```

#### Using Docker container to test remote code changes:

```bash
sudo docker run --rm -it --name backend-test pcic/climate-explorer-backend bash -c "apt-get update; apt-get install -yq git; git fetch; git checkout <commit-ish>; pip install pytest; py.test -v ce/tests"
```

### Setup using Docker *IN PROGRESS*:

While this will run a functional container, you must also link in all appropriate data to the correct location defined in the metadata database. Use multiple `-v /data/location:/data/location` options to mount them in the container. If using the test data is sufficient, use `-e "MDDB_DSN=sqlite:////app/ce/tests/data/test.sqlite" when running the container

```bash
docker build -t climate-explorer-backend .
docker run --rm -it -p 8000:8000 -e "MDDB_DSN=postgresql://dbuser:dbpass@dbhost/dbname" -v $(pwd):/app --name backend climate-explorer-backend
```

## Releasing

Creating a versioned release involves:

1. Incrementing `__version__` in `setup.py`
2. Summarize the changes from the last release in `NEWS.md`
3. Commit these changes, then tag the release:

  ```bash
git add setup.py NEWS.md
git commit -m"Bump to version x.x.x"
git tag -a -m"x.x.x" x.x.x
git push --follow-tags
  ```
## Data file preparation

Input data files can be created from CMIP5 compliant input using the script `dp/generate_climos.py`.

This script:

1. Opens an existing NetCDF file

2. Determines what climatological periods to generate

3. For each climatological period:

    a. Aggregates the daily data for the period into a new climatological output file.
    
    b. Revises the time variable of the output file to meet CF1.6/CMIP5 specification.
    
    c. Adds a climatology_bounds variable to the output file match climatological period.
    
    d. Optionally splits the climatology file into one file per dependent variable in the input file.
    
    e. Uses PCIC standards-compliant filename(s) for the output file(s).

All input file metadata is obtained from standard metadata attributes in the netCDF file. 
No metadata is deduced from the filename or path.

All output files contain PCIC standard metadata attributes appropriate to climatology files.

For information on PCIC metadata standards, see
see https://pcic.uvic.ca/confluence/display/CSG/PCIC+metadata+standard+for+downscaled+data+and+hydrology+modelling+data 

### Installation

Clone the repo onto the target machine.

If installing on a PCIC compute node, you must load the environment modules that data prep depends on
_before_ installing the Python modules.

```bash
$ module load netcdf-bin
$ module load cdo-bin
```

Python installation should be done in a virtual environment. We recommend a Python3 virtual env, created and activated
as follows:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $
```

The data prep component does _not_ depend the CE backend (`ce`).
Given the effort and time required to install the CE backend, when only the data prep component is required
it is worth installing only its dependencies. There's a custom `requirements.txt` in `dp` for just this purpose.

```bash
(venv) $ pip install -U pip setuptools wheel
(venv) $ pip install -i https://pypi.pacificclimate.org/simple/ -r dp/requirements.txt
```

See bash script `process-climo-means.sh` for an example of using this script.

### `generate_climos` script
#### Usage

```bash
# Dry run
python generate_climos.py --dry-run -o outdir files...

# Use defaults:
python generate_climos.py -o outdir files...

# Split output into separate files per dependent variable
python generate_climos.py -s -o outdir files...
```

Usage is further detailed in the script help information `python generate_climos.py -h`

#### Indexing

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

### `update_metadata` script

#### Specifying updates to make

`update_metadata` can update the global attributes and/or the attributes of variables in a NetCDF file. 
Three update operations are available (detailed below): delete attribute, set attribute value, rename attribute.

Updates to be made are specified in a separate updates file.
It uses a simple, human-readable data format called [YAML](https://en.wikipedia.org/wiki/YAML).
You only need to know a couple of things about YAML and how we employ it to use this script:

* Updates are specified with `key: value` syntax. A space must separate the colon from the value.
* Indentation matters (see next item). Indentation must be consistent within a block.
* There are two levels of indentation. 
  * The first (unindented) level specifies what group of attributes is to be updated. 
    * The key `global` specifies global attributes. 
    * Any other key is assumed to be the name of a variable whose attributes are to be updated.
    * The *value* for a first-level key is the indented block below it.
  * The second (indented) level specifies the attribute and the change to be made to it.
    See below for details.

##### Delete attribute:

```yaml
global-or-variable-name:
    name:
```

##### Set attribute value (create if does not exist):

```yaml
global-or-variable-name:
    name: value
```

Note: This script is clever (courtesy of YAML cleverness) about the data type of the value specified. 

* If you provide a value that looks like an integer, it is interpreted as an integer.
* If you provide a value that looks like a float, it is interpreted as a float.
* Otherwise it is treated as a string.
  If you need to force a numeric-looking value to be a string, enclose it in single or double quotes (e.g., `'123'`).

More details on the [Wikipedia YAML page](https://en.wikipedia.org/wiki/YAML#Advanced_components).

##### Rename attribute:

```yaml
global-or-variable-name:
    newname: <-oldname
```

Note: The special sequence `<-` after the colon indicates renaming. 
This means that you can't set an attribute with a value that begins with `<-`. Sorry.

##### Example updates file:

```yaml
global:
    foo: 
    bar: 42
    baz: <-qux

temperature:
    units: degrees_C
```

This file causes a NetCDF file to be updated in the following way:

Global attributes: 
* delete global attribute `foo`
* set global attribute `bar` to (integer) `42`
* rename global attribute `qux` to `baz`

Attributes of variable named `temperature`:
* set attribute `units` to (string) `degrees_C`

#### Usage

```bash
# update metadata in ncfile according to instructions in updates
python update_metadata.py -u updates ncfile
```