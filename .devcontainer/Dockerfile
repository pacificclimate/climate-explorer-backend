# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.0/containers/python-3/.devcontainer/base.Dockerfile


# [Choice] Ubuntu version (use ubuntu-22.04 or ubuntu-18.04 on local arm64/Apple Silicon): ubuntu-22.04, ubuntu-20.04, ubuntu-18.04
ARG VARIANT=ubuntu-full-3.6.3
FROM ghcr.io/osgeo/gdal:${VARIANT}

# Postgres & our packages. Currently not customizable via VERSION param.
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    g++ \ 
    libpq-dev libhdf5-dev libnetcdf-dev libgdal-dev libffi-dev
#     libpq-dev \
#     python3 \
#     python3-dev \
#     python3-pip \
#     postgresql-client \
#     # Added for local build support with poetry.
#     python-is-python3 

# # Postgres is required in this container to run the test suite.
# # Postgres & our packages. Currently not customizable via VERSION param.
# RUN apt-get update \
#     && apt-get -y install --no-install-recommends curl ca-certificates gnupg
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN export DEBIAN_FRONTEND="noninteractive" \
    && apt-get update \
    && apt-get -y install --no-install-recommends postgresql-plpython3-14 postgresql-14-postgis-3 libpq-dev