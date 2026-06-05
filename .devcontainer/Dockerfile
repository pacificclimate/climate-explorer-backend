# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.0/containers/python-3/.devcontainer/base.Dockerfile


# [Choice] Ubuntu version (use ubuntu-22.04 or ubuntu-18.04 on local arm64/Apple Silicon): ubuntu-22.04, ubuntu-20.04, ubuntu-18.04
ARG VARIANT=ubuntu-24.04
FROM mcr.microsoft.com/vscode/devcontainers/base:${VARIANT}

# Postgres & our packages. Currently not customizable via VERSION param.
# RUN apt-get update \
#     && apt-get -y install --no-install-recommends curl ca-certificates gnupg
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN apt-get update \
    && apt-get -y install --no-install-recommends postgresql-plpython3-17 postgresql-17-postgis-3 libpq-dev

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -yq --no-install-recommends \
    libhdf5-dev \
    libnetcdf-dev \
    libyaml-dev \
    libgdal-dev \
    python3 \
    python3-dev \
    python3-pip \
    cython3 && \
    rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN pip install numpy --break-system-packages

RUN pip install gdal==3.8.4 h5py netCDF4 psycopg2 PyYAML pillow --break-system-packages