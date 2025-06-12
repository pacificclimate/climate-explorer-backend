# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
import sys
import os

# import some values from pyproject.toml
from sphinx_pyproject import SphinxConfig

sys.path.insert(0, os.path.abspath("../../ce"))

# -- Project information -----------------------------------------------------
# These values are loaded from pyproject.toml

config = SphinxConfig("../../pyproject.toml", globalns=globals())
project = config.name
copyright = "2019, James Hiebert"
author = config.author
release = config.version
documentation_summary = config.description

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "m2r2"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

# We're using it to supress warnings on *.md files inlined with the include
# command, which for some reason, sphinx doesn't count as source files.
exclude_patterns = [
    "api/*-usage.md",
    "api/api-overview.md",
    "api/sesh-not-needed.md",
    "api/rest-item.md",
    "api/p2a-regions.md",
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"
