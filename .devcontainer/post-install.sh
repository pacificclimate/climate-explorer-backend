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

# Ensure the prebuilt virtualenv is owned by the (possibly UID-remapped) dev
# user. VS Code's updateRemoteUserUID can remap the container user to the host
# UID after the image is built, which would otherwise leave /opt/venv (chowned
# to a fixed UID at build time) unwritable. This only touches container-internal
# paths, never bind mounts.
sudo chown -R "$(id -u):$(id -g)" /opt/venv

# Install into the geospatial-python base image's prebuilt virtualenv
# (/opt/venv), which already provides GDAL/numpy/netCDF4/... matched to the
# system libraries. This mirrors the production image and avoids rebuilding the
# geospatial stack from source.
poetry config cache-dir ${WORKSPACE_DIR}/.cache
poetry config virtualenvs.create false

# Now install all dependencies (dev + docs extras) into /opt/venv.
poetry install --all-extras

echo "Done!"
