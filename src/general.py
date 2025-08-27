import io
import functools
import numpy as np
from PIL import Image
from pathlib import Path
from rio_tiler.models import ImageData
import rasterio
import pyqtree
from rasterio.warp import transform_bounds

from morecantile.commons import BoundingBox

from .base import ParametersCOG
from .bathy import BathyManager
from .ortho import OrthoManager
from .pred import PredManager

from enum import Enum

class ManagerType(Enum):
    BATHY = "bathy"
    PRED = "pred"
    ORTHO = "ortho"


class GeneralManager:

    def __init__(self, data_path: Path):
        
        self.bathy_manager = BathyManager(Path(data_path, ManagerType.BATHY.value))
        self.ortho_manager = OrthoManager(Path(data_path, ManagerType.ORTHO.value))
        self.pred_manager = PredManager(Path(data_path, ManagerType.PRED.value))



    def get_tile(self, collection_type: str, year: str, params: ParametersCOG) -> ImageData | None:
        
        tile = None
        if collection_type == ManagerType.BATHY.value:
            tile = self.bathy_manager.get_tile(year, params)
        elif collection_type == ManagerType.ORTHO.value:
            tile = self.ortho_manager.get_tile(year, params)
        elif collection_type == ManagerType.PRED.value:
            tile = self.pred_manager.get_tile(year, params)

        return tile
    
    def get_depth(self, lon: float, lat: float, year: str) -> float | None:
        return self.bathy_manager.get_depth(lon, lat, year)
         