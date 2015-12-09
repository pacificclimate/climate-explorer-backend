import os, os.path
import re

from cdo import Cdo

def iter_matching(dirpath, regexp):
    # http://stackoverflow.com/questions/4639506/os-walk-with-regex
    """Generator yielding all files under `dirpath` whose absolute path
       matches the regular expression `regexp`.
       Usage:

           >>> for filename in iter_matching('/', r'/home.*\.bak'):
           ....    # do something
    """
    for dir_, dirnames, filenames in os.walk(dirpath):
        for filename in filenames:
            abspath = os.path.join(dir_, filename)
            if regexp.match(abspath):
                yield abspath

def main():
    test_files = iter_matching('/home/data/climate/CMIP5/CCCMA/CanESM2/', re.compile('.*rcp.*tasmax.*r1i1p1.*nc'))

    cdo = Cdo()

    for fp in test_files:
        print fp
        temp = r'~/deleteme_temp.nc'
        ofile = r'~/deleteme_out.nc'
        cdo.seldate('2010-01-01,2039-12-31', input=fp, output=temp)
        cdo.copy(input='-ymonmean {} -yseasmean {} -timmean {}'.format(temp, temp, temp), output=ofile)


if __name__ == '__main__':
    main()
