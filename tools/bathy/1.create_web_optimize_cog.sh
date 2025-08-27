#!/bin/bash

source /home/bioeos/miniconda3/etc/profile.d/conda.sh
conda activate titiler_env

BATHY_FOLDER=./data/bathy_cogs
MERGED_RASTER_FOLDER=./data/merged_rasters

rm -rf $BATHY_FOLDER

for YEAR_FOLDER in $MERGED_RASTER_FOLDER/*;
do
    echo $YEAR_FOLDER;
    YEAR=$(basename "$YEAR_FOLDER" .tif)

    BATHY_FOLDER_YEAR=$BATHY_FOLDER/$YEAR
    mkdir -p $BATHY_FOLDER_YEAR

    for FILE in $YEAR_FOLDER/*.tif;
    do
        echo $FILE;
        BASENAME=$(basename "$FILE" .tif)

        # 1. COLOR COG (RGBA)
        COLOR_TIF="${BATHY_FOLDER}/${BASENAME}_color.tif"
        gdaldem color-relief $FILE color.txt $COLOR_TIF -alpha

        COLOR_COG="${BATHY_FOLDER_YEAR}/${BASENAME}_color_cog.tif"
        rio cogeo create \
            --cog-profile webp \
            --web-optimized \
            --overview-level 8 \
            $COLOR_TIF $COLOR_COG
        
        # 2. BATHY COG (Float32)
        BATHY_COG="${BATHY_FOLDER_YEAR}/${BASENAME}_depth_cog.tif"
        rio cogeo create \
            --cog-profile deflate \
            --web-optimized \
            --overview-resampling average \
            $FILE $BATHY_COG
            
        rm $COLOR_TIF
    done
done