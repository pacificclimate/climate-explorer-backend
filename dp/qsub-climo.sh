#!/bin/bash
# Submit a job to the pbs queue that runs generate_climos on a single NetCDF file.
# Arguments:
# $1: destination directory for climo output files and log files
# $2: input NetCDF file path

# Create a heredoc containing the required script, and submit it via qsub.
# All qsub arguments are supplied via PBS directives inside the heredoc.
cat <<EOF | qsub
#PBS -l nodes=1:ppn=2
#PBS -l vmem=24000mb
#PBS -l walltime=01:00:00
#PBS -o $1
#PBS -e $1
#PBS -m abe
#PBS -N generate_climos
#PBS -d /storage/home/rglover/code/climate-explorer-backend

# Set up the execution environment
module load netcdf-bin
module load cdo-bin
source py3.4/bin/activate

# Copy NetCDF file to $TMPDIR/climo/input
indir=\$TMPDIR/climo/input
mkdir -p \$indir && cp $2 \$indir
infile=\$indir/$(basename $2)

# Output directory is automatically created by generate_climos
outdir=\$TMPDIR/climo/output

# Generate climo means
python dp/generate_climos.py --split-vars --split-intervals -o \$outdir \$infile

# Copy result file to final destination and remove temporary input file
rsync \$outdir $1
rm \$infile
EOF