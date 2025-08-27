import logging
from pathlib import Path
from rio_tiler.io import COGReader
from morecantile.commons import BoundingBox
from rio_tiler.models import ImageData
import pyqtree
import numpy as np
import numpy.ma as ma

from .base import BaseManager, ParametersCOG


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredCogYear(BaseManager):

    def __init__(self, pred_cogs_path: Path) -> None:
        self.pred_cogs_path = pred_cogs_path
        self.list_pred_cogs = self.get_pred_files()
        
        self._readers = self.load_readers(self.list_pred_cogs)
        self._spindex = self.create_index(self.list_pred_cogs)
  

    @property
    def spindex(self) -> pyqtree.Index:
        return self._spindex


    @property
    def readers(self) -> dict[Path, COGReader]:
        return self._readers


    def get_pred_files(self) -> list:
        if not self.pred_cogs_path.exists():
            raise FileNotFoundError("Cannot access to predictions data, folder not found")
        
        return [file for file in self.pred_cogs_path.iterdir() if file.suffix.lower() == ".tif"]



class PredManager:
    def __init__(self, pred_data_path: Path):
        
        self.pred_data_path = pred_data_path

        self.pred_cog_by_year = self.load_pred_cog()

    def load_pred_cog(self) -> dict[str, PredCogYear]:

        if not self.pred_data_path.exists():
            raise FileNotFoundError("Cannot access to pred data, folder not found")

        pred_cog_by_year = {byp.name:PredCogYear(byp) for byp in self.pred_data_path.iterdir()}
        
        return pred_cog_by_year
    

    def get_tile(self, year: str, bb: BoundingBox) -> ImageData | None:

        pred_year_manager = self.pred_cog_by_year.get(year, None)
        tile = None

        if pred_year_manager == None:
            logger.error(f"Pred for year {year} not found.")
        else:
            tile = pred_year_manager.get_tile(bb)

        return tile
    


