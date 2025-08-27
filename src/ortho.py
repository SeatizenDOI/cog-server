import logging
import pyqtree
from pathlib import Path
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from morecantile.commons import BoundingBox

from .base import BaseManager, ParametersCOG


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrthoCogYear(BaseManager):

    def __init__(self, ortho_cogs_path: Path) -> None:
        self.ortho_cogs_path = ortho_cogs_path
        self.list_ortho_cogs = self.get_ortho_files()
        
        self._readers = self.load_readers(self.list_ortho_cogs)
        self._spindex = self.create_index(self.list_ortho_cogs)
  

    @property
    def spindex(self) -> pyqtree.Index:
        return self._spindex


    @property
    def readers(self) -> dict[Path, COGReader]:
        return self._readers


    def get_ortho_files(self) -> list[Path]:
        if not self.ortho_cogs_path.exists():
            raise FileNotFoundError("Cannot access to ortho data, folder not found")
        
        return [file for file in self.ortho_cogs_path.iterdir() if file.suffix.lower() == ".tif"]
    

    def get_tile(self, p: ParametersCOG) -> ImageData | None:
        """ Override get tile to sorted ASV before UAV. """


        list_cogs_intersect = self.spindex.intersect((
            p.bb.left, p.bb.bottom, p.bb.right, p.bb.top
        ))

        if len(list_cogs_intersect) == 0:
            return None
        
        if p.with_asv:
            list_cogs_intersect = sorted([a for a in list_cogs_intersect if "ASV" in a.name]) + sorted([a for a in list_cogs_intersect if "ASV" not in a.name])
        else:
            list_cogs_intersect = sorted([a for a in list_cogs_intersect if "ASV" not in a.name])

        tiles = [self.readers.get(file.name).tile(p.x, p.y, p.z, indexes=(1,2,3,4)) for file in list_cogs_intersect]
        
        tile = tiles[0] if len(tiles) == 1 else self.get_merge_tiles(tiles)

        return tile



class OrthoManager:
    def __init__(self, ortho_data_path: Path):
        self.ortho_data_path = ortho_data_path
        self.ortho_cog_by_year = self.load_ortho_cog()


    def load_ortho_cog(self) -> dict[str, OrthoCogYear]:

        if not self.ortho_data_path.exists():
            raise FileNotFoundError("Cannot access to ortho data, folder not found")

        ortho_cog_by_year = {byp.name:OrthoCogYear(byp) for byp in self.ortho_data_path.iterdir()}
        
        return ortho_cog_by_year
    

    def get_tile(self, year: str, bb: BoundingBox) -> ImageData | None:

        ortho_year_manager = self.ortho_cog_by_year.get(year, None)
        tile = None

        if ortho_year_manager == None:
            logger.error(f"Ortho for year {year} not found.")
        else:
            tile = ortho_year_manager.get_tile(bb)

        return tile
    


