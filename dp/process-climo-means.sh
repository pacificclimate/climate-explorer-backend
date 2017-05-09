#!/bin/bash

# process a model output file into climatological means
# - copy input file to local temp
# - process it with generate_climos.py
# - copy results from local temp to permanent location
# - delete copy of input file
#
# arguments:
# $1: unique id for logfile so that this script can be run in several independent processes. Easy: Pass in $$.
# $2: path to file to be processed
#
# typical usage:
# $ find /input/file/root/ -name "*.nc" -size +1 -print0 | xargs -0 -L 1 ./process-climo-means.sh $$

cp $2 $TMPDIR/
infile=$TMPDIR/$(basename $2)
logfile=/storage/data/projects/comp_support/climate_exporer_data_prep/climatological_means/log_$1.txt
python generate_climos.py --split-vars -o $TMPDIR/output/ $infile >>$logfile 2>&1
rsync $TMPDIR/output/*.nc /storage/data/projects/comp_support/climate_exporer_data_prep/climatological_means/
rm $infile

