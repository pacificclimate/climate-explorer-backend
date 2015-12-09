import os, os.path
import re

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
            print abspath
            if regexp.match(abspath):
                yield abspath

def main():
    files = iter_matching('/home/data/climate/CMIP5/CCCMA/CanESM2/', re.compile('.*rcp.*tasmax.*r1i1p1.*nc'))
    print [x for x in files]

if __name__ == '__main__':
    main()
