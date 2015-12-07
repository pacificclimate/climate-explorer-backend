import os

from setuptools import setup, find_packages

def recursive_list(pkg_dir, basedir):
    def find():
        for dirname, dirnames, filenames in os.walk(basedir):
            for filename in filenames:
                yield os.path.join(dirname, filename).lstrip(pkg_dir)
    return [ x for x in find() ]

__version__ = '0.0.1'

setup(
    name="ce",
    description="PCIC's Climate Explorer (CE)",
    keywords="science climate meteorology downscaling modelling",
    packages=find_packages(),
    version=__version__,
    url="http://www.pacificclimate.org/",
    author="Basil Veerman",
    author_email="bveerman@uvic.ca",
    install_requires = [
        'flask',
        'Flask-SQLAlchemy',
        'Flask-Cors',
        'modelmeta',
        'shapely',
        'numpy',
        'netcdf4',
        'python-dateutil'
    ],
    scripts = ['scripts/devserver.py'],
    package_dir = {'ce': 'ce'},
    package_data = {'ce': ['tests/data/cgcm.nc', 'tests/data/cgcm-tmin.nc', 'templates/*.html'] + recursive_list('ce/', 'ce/static')},
    zip_safe=False
)
