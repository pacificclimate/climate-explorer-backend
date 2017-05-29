"""Update NetCDF metadata from a YAML file.

WARNING: THIS SCRIPT MODIFIES THE ORIGINAL FILE.

See README for details of update specification file (YAML format).
"""

import logging

from argparse import ArgumentParser
from netCDF4 import Dataset
import yaml
import six

rename_prefix = '<-'  # Or some other unlikely sequence of chars

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
        for target_name in updates:
            if target_name == 'global':
                target = nc
                logger.info("Global attributes:")
            else:
                target = nc.variables[target_name]
                logger.info("Attributes of variable '{}':".format(target_name))

            for attr, value in updates[target_name].items():
                if value == None:
                    logger.info("\tDeleting attribute '{}'".format(attr))
                    if hasattr(target, attr):
                        delattr(target, value)
                else:
                    if isinstance(value, six.string_types) and value.startswith(rename_prefix):
                        old_name = value[len(rename_prefix):]
                        logger.info("\tRenaming attribute '{}' to '{}'".format(old_name, attr))
                        try:
                            setattr(target, attr, getattr(target, old_name))
                            delattr(target, old_name)
                        except AttributeError:
                            pass
                    else:
                        logger.info("\tSetting attribute '{}'".format(attr))
                        setattr(target, attr, value)


if __name__ == '__main__':
    parser = ArgumentParser(description='Update NetCDF file attributes from a file')
    parser.add_argument('-u', '--updates', required=True, help='File containing updates')
    parser.add_argument('ncfile', help='NetCDF file to update')
    args = parser.parse_args()
    main(args)
