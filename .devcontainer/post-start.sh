#!/bin/bash
set -ex

# Convenience workspace directory for later use
WORKSPACE_DIR=$(pwd)

# Set current workspace as safe for git
git config --global --add safe.directory ${WORKSPACE_DIR}