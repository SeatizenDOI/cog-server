#!/bin/bash

source /home/bioeos/miniconda3/etc/profile.d/conda.sh
conda activate cog_server_env

ORTHO_COG_FOLDER=./data/unsorted_cogs
RASTER_FOLDER=/home/bioeos/Documents/project_hub/ign-upscaling/data/ign/IGN_2017_974

# rm -rf $ORTHO_COG_FOLDER
mkdir -p $ORTHO_COG_FOLDER

for filename in $RASTER_FOLDER/*.tif;
do
    echo $filename;
    BASENAME=$(basename "$filename" .tif)
    TMP_FILE="$ORTHO_COG_FOLDER/${BASENAME}_alpha.tif"

    # Check number of bands
    NBANDS=$(gdalinfo "$filename" | grep "Band " | wc -l)

    if [ "$NBANDS" -eq 3 ]; then
        echo "Adding alpha channel to $filename"
        gdalwarp -dstalpha "$filename" "$TMP_FILE"
        INPUT_FILE="$TMP_FILE"
    else
        INPUT_FILE="$filename"
    fi

    ORTHO_COG="${ORTHO_COG_FOLDER}/${BASENAME}_cog.tif"
    rio cogeo create \
        --cog-profile webp \
        --web-optimized \
        --overview-level 8 \
        "$INPUT_FILE" "$ORTHO_COG"
    
    rm $TMP_FILE

done
