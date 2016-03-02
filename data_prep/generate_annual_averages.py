import os, os.path
import re
import logging
import sys


def determine_climo_periods(nc):
    '''
    Determine what climatological periods are available in a given netCDF file
    '''

    # Detect which climatological periods can be created
    time_var = nc.variables['time']
    s_date = num2date(time_var[0], units=time_var.units, calendar=time_var.calendar)
    e_date = num2date(time_var[-1], units=time_var.units, calendar=time_var.calendar)

    return dict([(k, v) for k, v in climo_periods.items() if v[0] > s_date and v[1] < e_date])



def main(args):
    vars = '|'.join(args.variables)
    test_files = iter_matching(args.basedir, re.compile('.*({}).*(_rcp26|_rcp45|_rcp85|_historical_).*r1i1p1.*nc'.format(vars)))

    if args.dry_run:
        for f in test_files:
            print f
        sys.exit(0)

    FileType = ClimdexFile if args.climdex else Cmip5File

    for fp in test_files:
        log.info(fp)

  


if __name__ == '__main__':
    parser = ArgumentParser(description='Create annual averages from CMIP5 data')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    parser.add_argument('-b', '--basedir', help='Root directory from which to search for climate model output')
    parser.add_argument('-v', '--variables', nargs='+', help='Variables to include')
    parser.add_argument('-C', '--climdex', action='store_true')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true')
    parser.set_defaults(
        variables=['tasmin', 'tasmax'],
        basedir='/home/data/climate/CMIP5/CCCMA/CanESM2/',
        climdex=False,
        dry_run=False
    )
    args = parser.parse_args()
    main(args)
