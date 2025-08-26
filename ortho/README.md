# How to produce the ortho cogs file.


## Transform the raw raster in web optimized cog.

Gather all your uav ortho in one folder.

Apply the script `0.convert_tif_to_cog.sh` and change the `RASTER_FOLDER` path:
```bash
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
```

If the script doesn't launch, you can use a docker image like : 

`docker run --rm --user 1000:1000 -v /media/bioeos/E1/drone/drone_ortho_tif/:/app -v ./:/code -it ghcr.io/osgeo/gdal`

But you need to set `RASTER_FOLDER` like `RASTER_FOLDER=/app`



## Sort the cogs file by year.

Use the notebook `1.move_cog_file.ipynb` 