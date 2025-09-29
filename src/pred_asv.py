import json
import logging
import pyqtree
from pathlib import Path
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from morecantile.commons import BoundingBox


from .base import BaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredASVCogSpecie(BaseManager):

    def __init__(self, pred_cogs_path: Path, specie: str) -> None:
        super().__init__()
        self.pred_cogs_path = pred_cogs_path
        self.list_pred_cogs = [raster for raster in self.pred_cogs_path.iterdir() if specie in raster.name]
        
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


class PredASVCogYear():

    def __init__(self, pred_data_path: Path):
        self.pred_data_year_path = pred_data_path
        self.pred_cog_by_specie = self.load_pred_cog()


    def load_pred_cog(self) -> dict[str, PredASVCogSpecie]:

        if not self.pred_data_year_path.exists():
            raise FileNotFoundError("Cannot access to pred data, folder not found")
        
        species = set()
        for raster in self.pred_data_year_path.iterdir():
            extracted_part = raster.name.split("_")
            specie = "_".join(extracted_part[2:len(extracted_part)-3])
            species.add(specie)


        pred_cog_by_specie = {specie:PredASVCogSpecie(self.pred_data_year_path, specie) for specie in list(species)}
        
        return pred_cog_by_specie
    

    def get_tile(self, specie: str, bb: BoundingBox) -> ImageData | None:

        pred_specie_manager = self.pred_cog_by_specie.get(specie, None)
        tile = None

        if pred_specie_manager == None:
            logger.error(f"Pred for specie {specie} not found.")
        else:
            tile = pred_specie_manager.get_tile(bb)

        return tile
        

class PredASVManager:

    def __init__(self, pred_data_path: Path):
        self.pred_data_path = pred_data_path
        self.pred_cog_by_year = self.load_pred_cog()
        self.species = self.get_species()
        self.color_asv_pred_by_specie = self.get_color_pred_asv_by_specie()


    def load_pred_cog(self) -> dict[str, PredASVCogYear]:

        if not self.pred_data_path.exists():
            raise FileNotFoundError("Cannot access to pred data, folder not found")

        pred_cog_by_year = {byp.name:PredASVCogYear(byp) for byp in self.pred_data_path.iterdir() if byp.is_dir()}
        
        return pred_cog_by_year
    

    def get_tile(self, year: str, specie: str, bb: BoundingBox) -> ImageData | None:

        pred_year_manager = self.pred_cog_by_year.get(year, None)
        tile = None

        if pred_year_manager == None:
            logger.error(f"Pred for year {year} not found.")
        else:
            tile = pred_year_manager.get_tile(specie, bb)

        return tile
    

    def get_species(self) -> list[str]:
        """ Extract all species. """
        species = set()
        for byp in self.pred_data_path.iterdir():
            if not byp.is_dir(): continue

            for raster in byp.iterdir():
                extracted_part = raster.name.split("_")
                specie = "_".join(extracted_part[2:len(extracted_part)-3])
                species.add(specie)
            break

        return sorted(list(species))
    

    def get_color_pred_asv_by_specie(self) -> dict:
        color_path = Path(self.pred_data_path, "color_asv_pred_by_specie.json")
        if not color_path.exists(): raise FileNotFoundError("Cannot access to pred data color, file not found")
        
        with open(color_path, "r") as f:
            data = json.load(f)

        return data
