#!/bin/bash
set -ex

##
## Create some aliases
##
echo 'alias ll="ls -alF"' >> $HOME/.bashrc
echo 'alias la="ls -A"' >> $HOME/.bashrc
echo 'alias l="ls -CF"' >> $HOME/.bashrc

# Convenience workspace directory for later use
WORKSPACE_DIR=$(pwd)

# Install into the geospatial-python base image's prebuilt virtualenv
# (/opt/venv), which already provides GDAL/numpy/netCDF4/... matched to the
# system libraries. This mirrors the production image and avoids rebuilding the
# geospatial stack from source.
poetry config cache-dir ${WORKSPACE_DIR}/.cache
poetry config virtualenvs.create false

# Now install all dependencies (dev + docs extras) into /opt/venv.
poetry install --all-extras

echo "Done!"
