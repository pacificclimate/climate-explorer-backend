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

### Building the Documentation

Building the docs requires the package to be installed first, as docstrings from installed modules are used to generate code documentation. 

```
pip install -e .
pyenv/bin/python setup.py build_sphinx
```

HTML documentation will then be available in the `doc/build/html` directory.

### Running the dev server

A development server can be run locally by using the Flask command line interface documented [here](http://flask.pocoo.org/docs/0.12/cli/). In general, you need to set one environment variable FLASK_APP=ce.wsgi:app and can optionally set FLASK_DEBUG=1 for live code reloading.

Database dsn can be configured with the MDDB_DSN environment variable. Defaults to 'postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta'

(venv)$ MDDB_DSN=postgresql://dbuser:dbpass@dbhost/dbname FLASK_APP=ce.wsgi:app flask run -p <port>

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

### Setup using Docker:
Build the image manually:
```bash
git clone https://github.com/pacificclimate/climate-explorer-backend
cd climate-explorer-backend
docker build -t climate-explorer-backend-image .
```

It's convenient to create a seperate read-only docker container to mount the data. This container can be shared by multiple instances of the server backend. More `-v` arguments can be supplied as needed to bring together data from multiple locations, as long as individual files end up mapped onto the locations given for them in the metadata database.

Jenkins image build:

Jenkins automatically handles the generation of docker images. Currently it is configured to trigger an image build for each push on individual branches. The image generated will have the name `climate-explorer-backend/[branch_name]`.

```bash
docker run --name ce_data -v /absolute/path/to/wherever/the/needed/data/is/:/storage/data/:ro ubuntu 16.04
```

Finally run the climate explorer backend image as a new container.

```bash
docker run -it -p whateverexternalport:8000
               -e "MDDB_DSN=postgresql://dbuser:dbpassword@host/databasename"
               --volumes-from ce_data
               --name climate-explorer-backend
               climate-explorer-backend-image
```

If you aren't using a read-only data container, replace `--volumes-from ce_data` with one or more `-v /absolute/path/to/wherever/the/needed/data/is/:/storage/data/` arguments.

If using the test data is sufficient, use `-e "MDDB_DSN=sqlite:////app/ce/tests/data/test.sqlite"` when running the container.

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
