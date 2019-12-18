import os
from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc


def recursive_list(pkg_dir, basedir):
    def find():
        for dirname, dirnames, filenames in os.walk(basedir):
            for filename in filenames:
                yield os.path.join(dirname, filename).lstrip(pkg_dir)
    return [x for x in find()]

__version__ = '1.1.1'

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
        'modelmeta==0.2.0',
        'shapely>=1.6',
        'numpy',
        'netcdf4<1.4',
        'python-dateutil',
        'GDAL',
        'rasterio',
        'pytest',
    ],
    package_dir={
        'ce': 'ce',
    },
    package_data={
        'ce': ['tests/data/*.nc', 'templates/*.html'] + recursive_list('ce/', 'ce/static'),
    },
    cmdclass = {
        'build_sphinx': BuildDoc
        },
    command_options={
        'build_sphinx': {
            'project': ('setup.py', "ce"),
            'version': ('setup.py', __version__),
            'source_dir': ('setup.py', 'doc/source')
            }
        },
    zip_safe=False
)
