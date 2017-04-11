"""Update NetCDF metadata from a YAML file.
WARNING: THIS SCRIPT MODIFIES THE ORIGINAL FILE.

YAML file should contain a simple list of attribute name: value pairs.
Special cases:
    name:           # delete attribute name if it exists
    name: value     # set attribute name to value
    new: *@old      # rename attribute old to new (copy old to new, delete old)
"""

import logging

from argparse import ArgumentParser
from netCDF4 import Dataset
import yaml

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)  # For testing, overridden by -l when run as a script


def main(args):
    with open(args.updates) as ud:
        updates = yaml.safe_load(ud)

    logger.info('NetCDF file: {}'.format(args.ncfile))
    with Dataset(args.ncfile, mode='r+') as nc:
            for attr, value in updates:
                if value == None:
                    logger.info("Deleting attribute '{}'".format(attr))
                    if hasattr(nc, attr):
                        delattr(nc, value)
                else:
                    if value.startswith('*@'):  # Or some other unlikely sequence of chars
                        old_name = value[2:]
                        logger.info("Renaming attribute '{}' to '{}'".format(old_name, attr))
                        try:
                            setattr(nc, attr, getattr(nc, old_name))
                            delattr(nc, old_name)
                        except AttributeError:
                            pass
                    else:
                        logger.info("Setting attribute '{}'".format(attr))
                        setattr(nc, attr, value)


if __name__ == '__main__':
    parser = ArgumentParser(description='Update NetCDF file attributes from a file')
    parser.add_argument('-u', '--updates', required=True, help='File containing updates')
    parser.add_argument('ncfile', help='NetCDF file to update')
    args = parser.parse_args()
    main(args)
