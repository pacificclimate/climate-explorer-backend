# Development container, rebased on the same geospatial-python image used in
# production so the dev environment matches prod exactly:
#   Ubuntu 26.04, Python 3.14, GDAL 3.12.2, numpy 2.x.
# The base ships a prebuilt virtualenv at /opt/venv with the geospatial stack;
# we add dev tooling and a non-root user, then install the project into that
# venv (see post-install.sh).
ARG GEOSPATIAL_PYTHON_TAG=3.12.2
FROM pcic/geospatial-python:${GEOSPATIAL_PYTHON_TAG}

ARG DEBIAN_FRONTEND=noninteractive

# Non-root user expected by the devcontainer (matches "remoteUser": "vscode").
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# System packages:
#  - build tooling + dev headers so Poetry can compile any source-only deps
#    (e.g. psycopg2) and, if ever needed, rebuild GDAL against the system lib;
#  - PostgreSQL 18 + PostGIS + PL/Python (distro packages on 26.04 — no pgdg
#    repo needed) for local database work;
#  - sudo/git/curl/locales for a comfortable dev shell.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        python3-venv \
        git \
        curl \
        ca-certificates \
        sudo \
        locales \
        libpq-dev \
        libffi-dev \
        libgdal-dev \
        libhdf5-dev \
        libnetcdf-dev \
        libyaml-dev \
        postgresql \
        postgresql-plpython3-18 \
        postgresql-18-postgis-3 \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i '/C.UTF-8/!{$a\C.UTF-8 UTF-8\n}' /etc/locale.gen 2>/dev/null || true

# Create the non-root user with passwordless sudo. Ubuntu 26.04 base images
# ship a default "ubuntu" user at UID/GID 1000, so remove it first to free the
# id for our user.
RUN userdel -r ubuntu 2>/dev/null || true \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m --shell /bin/bash $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    # Give the dev user ownership of the prebuilt venv so Poetry can install
    # the project (and its dev extras) into it without sudo.
    && chown -R $USER_UID:$USER_GID /opt/venv

# Reuse the base image's virtualenv for the project; Poetry installs into it
# (see post-install.sh, which sets virtualenvs.create=false).
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# Install Poetry into its OWN isolated virtualenv (/opt/poetry), NOT into
# /opt/venv. The project is installed into /opt/venv with virtualenvs.create=false,
# so if Poetry lived there too, `poetry install` would resolve the project lock
# and downgrade Poetry's own runtime deps (packaging<24.2, virtualenv, platformdirs),
# breaking Poetry itself (e.g. "No module named 'packaging.licenses'"). Keeping
# Poetry isolated avoids that; it still targets /opt/venv for installs because
# $VIRTUAL_ENV points there.
RUN python -m pip install --upgrade pip && \
    python -m venv /opt/poetry && \
    /opt/poetry/bin/pip install --upgrade pip && \
    /opt/poetry/bin/pip install poetry==2.4 && \
    ln -sf /opt/poetry/bin/poetry /usr/local/bin/poetry

USER $USERNAME
