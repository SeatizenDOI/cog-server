import logging
import pyqtree
from pathlib import Path
from rio_tiler.models import ImageData
from morecantile.commons import BoundingBox

import rasterio
from rasterio.warp import transform

from .base import BaseManager

LABEL_TEXT_MATCHING = {
    "1": "Acropora Branching", 
    "2": "Acropora Tabular",
    "3": "Non-acropora Massive",
    "4": "Other Corals",
    "5": "Sand",
}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredDroneCogYear(BaseManager):

    def __init__(self, pred_cogs_path: Path) -> None:
        super().__init__()
        self.pred_cogs_path = pred_cogs_path
        self.list_pred_cogs, self.pred_file_by_color = self.match_color_pred_file()

        self._spindex = self.create_index(self.list_pred_cogs)
  

    @property
    def spindex(self) -> pyqtree.Index:
        return self._spindex


    def match_color_pred_file(self) -> tuple[list, dict[Path, Path]]:
        if not self.pred_cogs_path.exists():
            raise FileNotFoundError("Cannot access to predictions data, folder not found")
        
        list_color_cogs, pred_file_by_color = [], {}
        for file in self.pred_cogs_path.iterdir():
            if file.suffix.lower() != ".tif": continue
            if "color" not in file.name: continue

            file_pred = Path(file.parent, file.name.replace("color", "preddata"))

            if not file_pred.exists():
                raise FileNotFoundError(f"File {file_pred} not found for {file}")
            
            list_color_cogs.append(file)
            pred_file_by_color[file] = file_pred
        
        return list_color_cogs, pred_file_by_color
        

    def get_prediction(self, lon: float, lat: float) -> str | None:

        list_cogs = self.spindex.intersect((lon, lat, lon, lat))
        if len(list_cogs) == 0:
            return None
        
        pred_path = self.pred_file_by_color.get(list_cogs[0], None)
        if pred_path == None or not pred_path.exists():
            return None
        
        with rasterio.open(pred_path) as src:
            raster_crs = src.crs

            # Transform lon/lat (EPSG:4326) into raster CRS
            xs, ys = transform("EPSG:4326", raster_crs, [lon], [lat])
            xs, ys = xs[0], ys[0]

            val = list(src.sample([(xs, ys)]))[0][0]

        return LABEL_TEXT_MATCHING.get(str(val), None)



class PredDroneManager:

    def __init__(self, pred_data_path: Path):
        self.pred_data_path = pred_data_path
        self.pred_cog_by_year = self.load_pred_cog()


    def get_legend(self) -> list:
        """ Return the current legend. """
        color_dict = {}
        with open("tools/pred_drone/color.txt", "r") as file:
            for row in file:
                prof, r, g, b, a = [b for b in row.replace("\n", "").split(" ") if b != ""]
                if prof in ['-9999', 'nan', '0']: continue
                color_dict[LABEL_TEXT_MATCHING.get(prof, prof)] = f"rgba({int(r)}, {int(g)}, {int(b)}, {int(a)})"
        return {"title": "Habitat Prediction by drone", "legend": color_dict, "description": "Click on map to get local habitat prediction."}


    def load_pred_cog(self) -> dict[str, PredDroneCogYear]:

        if not self.pred_data_path.exists():
            raise FileNotFoundError("Cannot access to pred data, folder not found")

        pred_cog_by_year = {pyp.name:PredDroneCogYear(pyp) for pyp in self.pred_data_path.iterdir()}
        
        return pred_cog_by_year
    

    def get_tile(self, year: str, bb: BoundingBox) -> ImageData | None:

        pred_year_manager = self.pred_cog_by_year.get(year, None)
        tile = None

        if pred_year_manager == None:
            logger.error(f"Pred for year {year} not found.")
        else:
            tile = pred_year_manager.get_tile(bb)

        return tile
    
    
    def get_prediction(self, lon: float, lat:float, year: str) -> str | None:

        pred_year_manager = self.pred_cog_by_year.get(year, None)

        pred = None
        if pred_year_manager == None:
            logger.error(f"Pred for year {year} not found.")
        else:
            pred = pred_year_manager.get_prediction(lon, lat)

        return pred



