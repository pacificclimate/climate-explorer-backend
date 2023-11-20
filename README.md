# PCIC Climate Explorer Backend

![Python CI](https://github.com/pacificclimate/climate-explorer-backend/workflows/Python%20CI/badge.svg)
![Docker Publishing](https://github.com/pacificclimate/climate-explorer-backend/workflows/Docker%20Publishing/badge.svg)
[![Code Climate](https://codeclimate.com/github/pacificclimate/climate-explorer-backend/badges/gpa.svg)](https://codeclimate.com/github/pacificclimate/climate-explorer-backend)

## Setup

### System Dependencies

A few system dependencies are necessary to subsequently build the
various python packages. In Ubuntu these are:

```bash
$ sudo apt-get install libpq-dev python-dev libhdf5-dev libnetcdf-dev libgdal-dev libffi-dev
```

Under other systems, you may need to adjust the install command as
well as the specific names of the packages.

### GDAL

Installing the GDAL Python package requires two pieces: the system
libraries and the Python bindings. While the latter is easily done
with `pip`/`poetry` and is included in the poetry.lock file, the former
can be complicated depending on your system. If you're lucky, there is
a pre-built package available from apt, apk, or yum. If you're not,
see below.

Keep in mind that the minor version number of the GDAL system
libraries *must agree* with the minor version of the GDAL `pip`
package. If the `pip` package fails to install or load, it is highly
likely that you're trying to install a mismatched version.

Also know that while we so pin the GDAL version and keep it up to
date, an updated version isn't strictly a requirement. If you are
developing on a system where the most recent GDAL system libraries are
not available (e.g. Ubuntu bionic), feel free to install a lesser
version of GDAL for development purposes. You may be able to install a
different version and resolve the dependencies by executing something
like `poetry add GDAL==3.3`, but your mileage may vary.

If you prefer to build GDAL from source (not recommended), there is a
`build_gdal.sh` script in the repo that does reasonably well. The
specifics in the script may need a bit of tweaking.


#### Troubleshooting

GDAL doesn't properly source its own lib paths when installing the python package, so we have to define
these environment variables:

```bash
$ export CPLUS_INCLUDE_PATH=/usr/include/gdal
$ export C_INCLUDE_PATH=/usr/include/gdal
```

### `THREDDS` Data
If you plan to use a `THREDDS` server to provide the data you must set the root
of the url in an environment variable.
```
export THREDDS_URL_ROOT=https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds/dodsC/datasets
```

## Development

### Installation

Setup using `poetry` which sets up the virtual environment automatically.

```bash
$ poetry install # --with=dev to include development packages
$ poetry shell
```

Development packages are listed under
`[tool.poetry.group.dev.dependencies]` in the `pyproject.toml` file.

#### Pre-commit hook
The `pre-commit hook` will run checks against your code whenever you make a commit. This prevents styling from breaking the CI/CD actions pipeline. This will be automatically installed by the command above, but to do so manually run the following:
```bash
$ poetry add --group=dev pre-commit
```

### Building the Documentation

FIXME: Sphinx no longer supports Python < 3.9, so docs will be broken
until we upgrade (hopefully that will be the next step!). This section
will be updated with the python3.9 update.

Building the docs requires the package to be installed first, as docstrings from installed modules are used to generate code documentation.

```
pipenv install -e .
pipenv run python setup.py build_sphinx
```

HTML documentation will be in the `doc/build/html` directory.

Sphinx can also generate a PDF by invoking the TeXlive toolchain, if it is installed on your machine. On Ubuntu, you will to install the following packages before sphinx can successfully create a PDF:
* latexmk
* texlive-latex-recommended
* texlive-fonts-recommended
* texlive-latex-extra

You can then create a PDF from the `doc` directory with this command:
```
make latexpdf
```

### Running the dev server

A development server can be run locally by using the Flask command line interface documented [here](http://flask.pocoo.org/docs/0.12/cli/). In general, you need to set one environment variable FLASK_APP=ce.wsgi:app and can optionally set FLASK_DEBUG=1 for live code reloading.

Database dsn can be configured with the MDDB_DSN environment variable. Defaults to 'postgresql://httpd_meta@db.pcic.uvic.ca/pcic_meta'

The location of the precalculated regional datafiles is specified with the `REGION_DATA_DIRECTORY` environment variable.

(venv)$ MDDB_DSN=postgresql://dbuser:dbpass@dbhost/dbname REGION_DATA_DIRECTORY=/storage/data/projects/comp_support/climate_explorer_data_prep/precalculated_regions/ FLASK_APP=ce.wsgi:app flask run -p <port>

### Testing

#### Within the virtual environment:

```bash
poetry run py.test -v
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
docker build -t climate-explorer-backend-image -f docker/Dockerfile.dev .
```

It's convenient to create a separate read-only docker container to mount the data. This container can be shared by multiple instances of the server backend. More `-v` arguments can be supplied as needed to bring together data from multiple locations, as long as individual files end up mapped onto the locations given for them in the metadata database.

Automated image build:

Github actions will automatically build and publish and image to our [docker hub](https://hub.docker.com/r/pcic/climate-explorer-backend) on each push and tag creation. The tagging strategy is defined by the [docker workflow](https://github.com/marketplace/actions/build-and-push-docker-images#tag_with_ref).

```bash
docker run --name ce_data -v /absolute/path/to/wherever/the/needed/data/is/:/storage/data/:ro ubuntu 22.04
```

Finally run the climate explorer backend image as a new container.

```bash
docker run -it -p whateverexternalport:8000
               -e "MDDB_DSN=postgresql://dbuser:dbpassword@host/databasename"
               -e "REGION_DATA_DIRECTORY=/path/to/region/data"
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
