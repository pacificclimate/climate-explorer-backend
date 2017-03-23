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
    name="dp",
    description="PCIC's Climate Explorer (CE) Data Preparation",
    keywords="science climate meteorology downscaling modelling",
    packages=find_packages(),
    version=__version__,
    url="http://www.pacificclimate.org/",
    author="Rod Glover",
    author_email="rglover@uvic.ca",
    install_requires=[
        'python-dateutil',
        'cdo',
        'shapely',
        'numpy',
        'netcdf4',
        'nchelpers',
        'pytest'
    ],
    # scripts=['scripts/devserver.py'],
    package_dir={'dp': 'dp'},
    package_data={
        'dp': ['data/*.nc']
    },
    zip_safe=False
)
