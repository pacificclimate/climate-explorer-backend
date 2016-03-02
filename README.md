# PCIC Climate Explorer Backend

[![Build Status](https://travis-ci.org/pacificclimate/climate-explorer-backend.svg?branch=master)](https://travis-ci.org/pacificclimate/climate-explorer-backend)
[![Code Climate](https://codeclimate.com/github/pacificclimate/climate-explorer-backend/badges/gpa.svg)](https://codeclimate.com/github/pacificclimate/climate-explorer-backend)

## Requirements

libpq-dev python-dev

## Development

### Config

Database dsn can be configured with the MDDB_DSN environment variable. Defaults to 'postgresql://httpd_meta@monsoon.pcic.uvic.ca/pcic_meta'

Setup using virtualenv:

```bash
$ virtualenv venv
$ source venv/bin/activate
(venv)$ pip install -U pip
(venv)$ pip install --trusted-host tools.pacificclimate.org -i http://tools.pacificclimate.org/pypiserver/ -e .
(venv)$ MDDB_DSN=postgresql://dbuser:dbpass@dbhost/dbname python scripts/devserver.py -p <port>
```

### Testing

Within the virtual environment:

```bash
pip install pytest
py.test -v
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
```
