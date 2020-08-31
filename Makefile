.PHONY: all

# Used for GDAL installation
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
export PIP_INDEX_URL=https://pypi.pacificclimate.org/simple

# Makefile Vars
SHELL:=/bin/bash
VENV?=~/tmp/ceb-venv
PYTHON=${VENV}/bin/python3
PIP=${VENV}/bin/pip

all: apt gdal-check install build-docs pre-commit-hook test

apt:
	sudo apt-get install -y \
		libpq-dev \
		python3-dev \
		libhdf5-dev \
		libnetcdf-dev \
		libgdal-dev

build-docs: venv
	${PYTHON} setup.py build_sphinx

clean:
	rm -rf $(VENV)

gdal-check:
	$(eval GDAL_REQ=$(shell cat requirements.txt | grep -i gdal | cut -c 7-))
	$(eval GDAL_VER=$(shell gdal-config --version))

	if ! [ "$(GDAL_REQ)" == "$(GDAL_VER)" ]; then \
	  echo "Python GDAL package version ($(GDAL_REQ)) must match GDAL installation ($(GDAL_VER))"; \
		false; \
	fi

install: venv
	${PIP} install -U pip
	${PIP} install -r requirements.txt -r test_requirements.txt
	${PIP} install -e .

pre-commit-hook: venv
	${PIP} install pre-commit
	pre-commit install

test: venv
	${PYTHON} -m pytest -vv

venv:
	test -d $(VENV) || python3 -m venv $(VENV)
