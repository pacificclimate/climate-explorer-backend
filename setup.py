import os
from setuptools import setup, find_packages


def recursive_list(pkg_dir, basedir):
    def find():
        for dirname, dirnames, filenames in os.walk(basedir):
            for filename in filenames:
                yield os.path.join(dirname, filename).lstrip(pkg_dir)
    return [x for x in find()]

__version__ = '0.1.1'

setup(
    name="ce",
    description="PCIC's Climate Explorer (CE)",
    version=__version__,
    author="James Hiebert",
    author_email="hiebert@uvic.ca",
    url="https://github.com/pacificclimate/climate-explorer-backend",
    keywords="science climate meteorology downscaling modelling",
    packages=find_packages(),
    install_requires=[
        'flask',
        'Flask-SQLAlchemy',
        'Flask-Cors',
        'Flask-Cache',
        'modelmeta',
        'shapely',
        'numpy',
        'netcdf4',
        'python-dateutil',
        'nchelpers',
        'GDAL',
        'rasterio',
        'cdo',
        'pytest',
    ],
    scripts=['scripts/devserver.py'],
    package_dir={  # necessary?
        'ce': 'ce',
        'dp': 'dp',
    },
    package_data={
        'ce': ['tests/data/*.nc', 'templates/*.html'] + recursive_list('ce/', 'ce/static'),
        'dp': ['data/*.nc']  # TODO: move this into tests/
    },
    zip_safe=False
)
