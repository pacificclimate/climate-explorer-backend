
# Used for GDAL installation
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
export PIP_INDEX_URL=https://pypi.pacificclimate.org/simple

# Setup venv var
ifeq ($(TMPDIR),)
VENV_PATH := /tmp/ceb-venv
else
VENV_PATH := $(TMPDIR)/ceb-venv
endif

# Makefile Vars
SHELL:=/bin/bash
PYTHON=${VENV_PATH}/bin/python3
PIP=${VENV_PATH}/bin/pip

.PHONY: all
all: apt gdal-check install build-docs pre-commit-hook test

.PHONY: apt
apt:
	sudo apt-get install -y \
		libpq-dev \
		python3-dev \
		python3-distutils \
		libhdf5-dev \
		libnetcdf-dev \
		libgdal-dev

.PHONY: build-docs
build-docs: venv
	${PYTHON} setup.py build_sphinx

.PHONY: clean
clean:
	rm -rf $(VENV_PATH)

.PHONY: gdal-check
gdal-check:
	$(eval GDAL_REQ=$(shell cat requirements.txt | grep -i gdal | cut -c 7-))
	$(eval GDAL_VER=$(shell gdal-config --version))

	if ! [ "$(GDAL_REQ)" == "$(GDAL_VER)" ]; then \
	  echo "Python GDAL package version ($(GDAL_REQ)) must match GDAL installation ($(GDAL_VER))"; \
		false; \
	fi

.PHONY: install
install: venv
	${PIP} install -U pip
	${PIP} install -r requirements.txt -r test_requirements.txt
	${PIP} install -e .

.PHONY: pre-commit-hook
pre-commit-hook: venv
	${PIP} install pre-commit
	pre-commit install

.PHONY: test
test: venv
	${PYTHON} -m pytest -vv

.PHONY: venv
venv:
	test -d $(VENV_PATH) || python3 -m venv $(VENV_PATH)
