# How to produce the ortho cogs file.


## Transform the raw raster in web optimized cog.

Gather all your uav ortho in one folder.

Apply the script `0.convert_tif_to_cog.sh` and change the `RASTER_FOLDER` path:
```bash
#!/bin/bash

COLOR_FOLDER=./data/rasters_color
rm -rf $COLOR_FOLDER
mkdir -p $COLOR_FOLDER

RASTER_FOLDER=/media/bioeos/E/drone/serge_ortho_pred/final_predictions_raster

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
```

If the script doesn't launch, you can use a docker image like : 

`docker run --rm --user 1000:1000 -v /media/bioeos/E1/drone/drone_ortho_tif/:/app -v ./:/code -it ghcr.io/osgeo/gdal`

But you need to set `RASTER_FOLDER` like `RASTER_FOLDER=/app`



## Sort the cogs file by year.

Use the notebook `1.move_cog_file.ipynb` 