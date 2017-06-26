#!/bin/bash
# Submit a job to the PBS queue that runs generate_climos on a single NetCDF file.
#
# We want to process one NetCDF file at a time for several reasons:
# - improve scheduling of jobs by making them as short as possible
# - avoid filling up $TMPDIR with copies of large files for processing; each is deleted per job
#
# Arguments:
# $1: destination base directory for climo output files and log files;
#     log files are placed in the base directory
#     climo output files are placed in a subdirectory of the base directory named by the PBS job id
# $2: NetCDF file path
# $3: maximum execution time (walltime); if omitted, defaults to 01:00:00 (1 hour)

# Create a heredoc containing the required script, and submit it via qsub.
# All qsub arguments are supplied via PBS directives inside the heredoc.
filename=$(basename $2)

cat <<EOF | qsub
#PBS -l nodes=1:ppn=2
#PBS -l vmem=24000mb
#PBS -l walltime=${3:-01:00:00}
#PBS -o $1
#PBS -e $1
#PBS -m abe
#PBS -N generate_climos:$filename
#PBS -d /storage/home/rglover/code/climate-explorer-backend

pbs_job_num=\$(expr match "\$PBS_JOBID" '\([0-9]*\)')

# Set up the execution environment
module load netcdf-bin
module load cdo-bin
source py3.4/bin/activate

# Copy NetCDF file to $TMPDIR/climo/input
indir=\$TMPDIR/climo/input
mkdir -p \$indir && cp $2 \$indir
infile=\$indir/$filename

# Output directory is automatically created by generate_climos
baseoutdir=\$TMPDIR/climo/output
outdir=\$baseoutdir/\$pbs_job_num

# Generate climo means
python dp/generate_climos.py -o \$outdir \$infile

# Copy result file to final destination and remove temporary input file
# Since output files are small, we're not removing them here.
rsync -r \$baseoutdir $1
rm \$infile
EOF
