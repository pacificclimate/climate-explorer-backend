from argparse import ArgumentParser

from netCDF4 import Dataset

from generate_annual_averages import update_annual_avg_file_global_metadata, \
update_annual_avg_file_variable_metadata, update_annual_avg_file_time_metadata

supported_vars = ['pr', 'tasmin', 'tasmax']

def main(args):

    start_year = args.start_year
    nc = Dataset(args.input_file, 'r+')

    if start_year is None:
        try:
            # infer the start year from the time units metadata
            start_year = int(nc.variables['time'].units.split('since ')[1][0:4])
        except:
            nc.close()
            print("ERROR: Input file time variable units not given or not \
                formatted correctly. Expected format: 'days since yyyy-mm-dd \
                00:00:00'. Input file unchanged.")
            exit(0)
    update_annual_avg_file_time_metadata(nc, start_year)

    # Note: this will miss modifying metadata for any variables that may be in
    # the file but not listed in supported_vars
    for variable in supported_vars:
        try:
            update_annual_avg_file_variable_metadata(nc, variable)
        except:
            continue

    update_annual_avg_file_global_metadata(nc)
    nc.close()

if __name__ == '__main__':
    parser = ArgumentParser(description='Write time and time_bnds data, and \
        modify global title, frequency, and variable long_name metadata to \
        reflect the annual nature of the data. This modifies the NetCDF \
        input_file in place.')
    parser.add_argument('input_file')
    parser.add_argument('-y', '--year-start', dest='start_year', type=int, \
        help='Year that the first time step in the file should be. If \
        unspecified, it will be inferred from the "days since..." year in the \
        units attribute of the time dimension.  Currently supports the \
        following variables: {}'.format(supported_vars))
    parser.set_defaults(
        start_year=None
    )
    args = parser.parse_args()
    main(args)
