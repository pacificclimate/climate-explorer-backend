import os
from setuptools import setup, find_packages


def recursive_list(pkg_dir, basedir):
    def find():
        for dirname, dirnames, filenames in os.walk(basedir):
            for filename in filenames:
                yield os.path.join(dirname, filename).lstrip(pkg_dir)
    return [x for x in find()]

__version__ = '0.2.0'

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
        'GDAL',
        'rasterio',
        'pint',
        'pytest',
    ],
    extras_require={
        'data_prep': [
            'cdo',
            'nchelpers',
            'PyYAML',
        ]
    },
    scripts='''
        scripts/devserver.py
        dp/generate_climos.py
        dp/update_metadata.py
        dp/split_merged_climos.py
        dp/jobqueueing/gcadd.py
        dp/jobqueueing/gcalter-params.py
        dp/jobqueueing/gclist.py
        dp/jobqueueing/gcreset.py
        dp/jobqueueing/gcsub.py
        dp/jobqueueing/gcupd-email.py
        dp/jobqueueing/gcupd-qstat.py
    '''.split(),
    package_dir={
        'ce': 'ce',
        'dp': 'dp',
    },
    package_data={
        'ce': ['tests/data/*.nc', 'templates/*.html'] + recursive_list('ce/', 'ce/static'),
        'dp': ['tests/data/*.nc']
    },
    zip_safe=False
)
