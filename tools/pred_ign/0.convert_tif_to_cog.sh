#!/bin/bash

COLOR_FOLDER=./data/rasters_color
rm -rf $COLOR_FOLDER
mkdir -p $COLOR_FOLDER

RASTER_FOLDER=/home/bioeos/Documents/project_hub/ign-upscaling/output_inference2/final_predictions_raster

for filename in $RASTER_FOLDER/*.tif;
do
    echo $filename;
    BASENAME=$(basename "$filename" .tif)

    if [ ! -f $filename ]; then
        echo "File not found: ${filename}"
        continue
    fi
    COLOR_OUTPUT_FILE="${COLOR_FOLDER}/${BASENAME}_color.tif"

    gdaldem color-relief $filename color.txt $COLOR_OUTPUT_FILE -alpha -co COMPRESS=LZW

    COLOR_COG="${COLOR_FOLDER}/${BASENAME}_color_cog.tif"
    rio cogeo create \
        --cog-profile webp \
        --web-optimized \
        --overview-level 8 \
        $COLOR_OUTPUT_FILE $COLOR_COG
    
    PRED_COG="${COLOR_FOLDER}/${BASENAME}_preddata_cog.tif"
    rio cogeo create \
        --cog-profile deflate \
        --web-optimized \
        --overview-resampling average \
        $filename $PRED_COG

    rm $COLOR_OUTPUT_FILE

done