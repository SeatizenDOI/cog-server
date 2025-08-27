import io
import functools
import numpy as np
from PIL import Image
from pathlib import Path
import  numpy.ma as ma
from rio_tiler.models import ImageData
from rio_tiler.io import COGReader

import logging
import rasterio
import pyqtree
from rasterio.warp import transform_bounds
from morecantile.commons import BoundingBox

from dataclasses import dataclass
from abc import ABC, abstractmethod


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ParametersCOG:
    x: int
    y: int
    z: int
    bb: BoundingBox
    with_asv: bool

class BaseManager(ABC):

    @property
    @abstractmethod
    def spindex(self):
        """Subclasses must define this attribute or property."""
        pass
        
    @property
    @abstractmethod
    def readers(self):
        """Subclasses must define this attribute or property."""
        pass


    def create_index(self, list_rasters: list[Path]) -> pyqtree.Index:
        """This function create a quadtree index with all the cog raster."""

        bounds_list = []

        for path in list_rasters:
            with rasterio.open(path) as src:
                bounds = src.bounds  # (minx, miny, maxx, maxy)
                bounds_list.append({
                    "name": path,
                    "bounds": bounds
                })

        for b in bounds_list:
            with rasterio.open(b["name"]) as src:
                b["bounds"] = transform_bounds(src.crs, "EPSG:4326", *b["bounds"])


        # Calculate global extent (min/max of all bounds)
        all_minx = min(b["bounds"][0] for b in bounds_list)
        all_miny = min(b["bounds"][1] for b in bounds_list)
        all_maxx = max(b["bounds"][2] for b in bounds_list)
        all_maxy = max(b["bounds"][3] for b in bounds_list)

        spindex = pyqtree.Index(bbox=(all_minx, all_miny, all_maxx, all_maxy))

        # Insert each raster into the quadtree
        for b in bounds_list:
            spindex.insert(item=b["name"], bbox=b["bounds"])

        return spindex

    def get_merge_tiles(self, tiles: list[ImageData]):
        reference_tile = tiles[0]
        merged_array = reference_tile.array.copy() 
        merged_mask = reference_tile.mask.copy()

        for sub_tile in tiles[1:]:

            tile_array = sub_tile.array.copy()
            tile_mask = sub_tile.mask.copy()

            for i in range(3):
                merged_array[i, ...] = np.where(merged_mask != 0, merged_array[i, ...], tile_array[i, ...])
                                                    
            merged_mask = np.where(merged_mask != 0, merged_mask, tile_mask)

        im = ImageData(
            array=ma.masked_array(merged_array, mask=~np.repeat(merged_mask.reshape(1, 256, 256), 3, axis=0)),
            crs=reference_tile.crs,
            bounds=reference_tile.bounds,
        )
        return im


    def load_readers(self, list_cogs_path: list[Path]) -> dict[Path, COGReader]:
        readers = {}
        for file in list_cogs_path:
            try:
                reader = COGReader(file)
                readers[file.name] = reader
            except Exception as e:
                logger.warning(f"Failed to initialize COG reader for {file}: {e}")
        return readers


    def get_tile(self, p: ParametersCOG) -> ImageData | None:
        
        list_cogs_intersect = self.spindex.intersect((
            p.bb.left, p.bb.bottom, p.bb.right, p.bb.top
        ))

        if len(list_cogs_intersect) == 0:
            return None

        tiles = [self.readers.get(file.name).tile(p.x, p.y, p.z) for file in list_cogs_intersect]
        
        tile = tiles[0] if len(tiles) == 1 else self.get_merge_tiles(tiles)

        return tile