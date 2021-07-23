export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal

# Used by GDAL check
GDAL_REQ=$(shell pipenv run pip freeze | grep -i gdal | cut -c 7-)
GDAL_VER=$(shell gdal-config --version)

ifeq ($(findstring $(GDAL_VER),$(GDAL_REQ)),$(GDAL_VER))
    FOUND=true
else
    FOUND=false
endif


all: apt gdal-check build-docs pre-commit-hook test

apt:
	sudo apt-get install -y \
		libpq-dev \
		python3-dev \
		python3-distutils \
		libhdf5-dev \
		libnetcdf-dev \
		libgdal-dev

build-docs:
	pipenv run python setup.py build_sphinx

gdal-check:
	if [ $(FOUND) = false ]; then \
	  echo "Python GDAL package version ($(GDAL_REQ)) must match GDAL installation ($(GDAL_VER))"; \
		false; \
	fi

pre-commit-hook:
	pipenv run pre-commit install

test:
	pipenv run pytest -vv
