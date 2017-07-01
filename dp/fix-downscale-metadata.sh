#!/bin/bash
for file in $(find /storage/data/climate/downscale/BCCAQ2/bccaqv2_with_metadata/ -name "*.nc"); do
    python ./update_metadata.py -u fix-downscale-metadata.yaml $file
done