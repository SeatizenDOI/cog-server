#!/bin/bash

source /home/bioeos/miniconda3/etc/profile.d/conda.sh
conda activate cog_server_env

COLORED_FOLDER=./data/colored_rasters
COG_FOLDER=./data/cog_rasters

rm -rf $COG_FOLDER

for YEAR_FOLDER in $COLORED_FOLDER/*;
do
    echo $YEAR_FOLDER;
    YEAR=$(basename "$YEAR_FOLDER" .tif)

    COG_FOLDER_YEAR=$COG_FOLDER/$YEAR
    mkdir -p $COG_FOLDER_YEAR

    for FILE in $YEAR_FOLDER/*.tif;
    do
        echo $FILE;
        BASENAME=$(basename "$FILE" .tif)

        COLOR_COG="${COG_FOLDER_YEAR}/${BASENAME}_cog.tif"
        rio cogeo create \
            --cog-profile webp \
            --web-optimized \
            --overview-level 8 \
            $FILE $COLOR_COG
        
    done
done