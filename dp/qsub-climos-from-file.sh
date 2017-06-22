#!/bin/bash
# Submit generate_climos jobs to PBS queue, reading files to process from a 'todofile',
# and writing submitted files to a 'donefile' (with PBS job id identifier).
# Do not reprocess files found in donefile.
#
# Arguments
# $1: todofile: File containing filepaths (one per line) to process. Not modified.
# $2: donefile: File containing filepaths that have been submitted. Modified (appended).
# $3: destination base directory for climo output files and log files
# $4: maximum execution time (walltime); if omitted, defaults to 01:00:00 (1 hour)
# $5: maximum number of jobs to submit; if omitted, defaults to 1
#
# todofile is NOT modified
# filepaths submitted are appended to donefile
# filepaths submitted are also echoed to stdout

todofile="$1"
donefile="$2"
destdir="$3"
walltime="$4"
maxjobs=${3:-1}

# Create donefile if it does not exist
if [ ! -e $donefile ]; then touch $donefile; fi

# Submit jobs for files not in donefile; limit maxjobs submissions
jobs=0
for filepath in $(cat $todofile); do
    if [ $jobs -ge $maxjobs ]; then exit; fi
    if ! grep -Fq "$filepath" $donefile
    then
        echo "$filepath"
        jobid=$(./qsub-climo.sh $destdir $filepath $walltime)
        echo "$filepath" ":" $jobid >>$donefile
        jobs=$((jobs + 1))
    fi
done
