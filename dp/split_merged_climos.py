from argparse import ArgumentParser
import logging
import os.path
import shutil

from cdo import Cdo

from nchelpers import CFDataset


# Set up logging
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)  # For testing, overridden by -l when run as a script

# Instantiate CDO interface
cdo = Cdo()


def split_merged_climos(input_file, outdir):

    # Check that we can split this file
    if not input_file.is_multi_year_mean:
        raise ValueError('File is not a multi-year mean')

    output_filepaths = []
    start_timestep = 1
    for input_freqs, num_timesteps, output_freq in [
        ({'msaClim'}, 12, 'mClim'),
        ({'saClim', 'msaClim'}, 4, 'sClim'),
        ({'saClim', 'msaClim'}, 1, 'aClim'),
    ]:
        if input_file.frequency in input_freqs:
            # The given climo interval set is in the file.
            logger.info("Splitting averaging interval '{}'".format(output_freq))

            # Determine what timesteps should be selected from the file
            timesteps = list(range(start_timestep, start_timestep+num_timesteps))
            start_timestep += num_timesteps

            # Split out those timesteps
            temp_filepath = cdo.seltimestep(','.join(str(t) for t in timesteps), input=input_file.filepath())

            with CFDataset(temp_filepath, mode='r+') as cf:
                # Update metadata in the split file
                cf.frequency = output_freq
                # Extract the final filename for this file
                output_filepath = os.path.join(outdir, cf.cmor_filename)

            # Move/copy split file to final location
            try:
                logger.info('Output file: {}'.format(output_filepath))
                if not os.path.exists(os.path.dirname(output_filepath)):
                    os.makedirs(os.path.dirname(output_filepath))
                shutil.move(temp_filepath, output_filepath)
            except Exception as e:
                logger.warning('Failed to create output file. {}: {}'.format(e.__class__.__name__, e))
            else:
                output_filepaths.append(output_filepath)

    return output_filepaths


def main(args):
    for filepath in args.filepaths:
        logger.info('')
        logger.info('Processing: {}'.format(filepath))
        try:
            input_file = CFDataset(filepath)
        except Exception as e:
            logger.info('{}: {}'.format(e.__class__.__name__, e))
        else:
            split_merged_climos(input_file, args.outdir)


if __name__ == '__main__':
    parser = ArgumentParser(description='Create climatologies from CMIP5 data')
    parser.add_argument('filepaths', nargs='*', help='Files to process')
    log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()
    parser.add_argument('-l', '--loglevel', help='Logging level',
                        choices=log_level_choices, default='INFO')
    parser.add_argument('-o', '--outdir', required=True, help='Output folder')
    args = parser.parse_args()
    logger.setLevel(getattr(logging, args.loglevel))
    main(args)
