#!/bin/bash

source /home/bioeos/miniconda3/etc/profile.d/conda.sh
conda activate titiler_env

ORTHO_COG_FOLDER=./data/unsorted_cogs
RASTER_FOLDER=/media/bioeos/E/drone/drone_ortho_tif

rm -rf $ORTHO_COG_FOLDER
mkdir -p $ORTHO_COG_FOLDER

for filename in $RASTER_FOLDER/*.tif;
do
    echo $filename;
    BASENAME=$(basename "$filename" .tif)

    ORTHO_COG="${ORTHO_COG_FOLDER}/${BASENAME}_cog.tif"
    rio cogeo create \
        --cog-profile webp \
        --web-optimized \
        --overview-level 8 \
        $filename $ORTHO_COG

done
