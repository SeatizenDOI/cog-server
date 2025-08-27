import logging
from pathlib import Path
from rio_tiler.io import COGReader
from morecantile.commons import BoundingBox
from rio_tiler.models import ImageData
import pyqtree
import rasterio
from rasterio.warp import transform


from .base import BaseManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BathyCogYear(BaseManager):

    def __init__(self, bathy_cogs_path: Path) -> None:
        self.bathy_cogs_path = bathy_cogs_path
        self.list_color_cogs, self.bathy_file_by_color = self.match_color_depth_file()
        
        self._readers = self.load_readers(self.list_color_cogs)
        self._spindex = self.create_index(self.list_color_cogs)
  

    @property
    def spindex(self) -> pyqtree.Index:
        return self._spindex


    @property
    def readers(self) -> dict[Path, COGReader]:
        return self._readers


    def match_color_depth_file(self) -> tuple[list, dict[Path, Path]]:
        if not self.bathy_cogs_path.exists():
            raise FileNotFoundError("Cannot access to bathy data, folder not found")

        list_color_cogs, bathy_file_by_color = [], {}
        for file in self.bathy_cogs_path.iterdir():
            if "color" not in file.name: continue

            file_bathy = Path(file.parent, file.name.replace("color", "depth"))

            if not file_bathy.exists():
                raise FileNotFoundError(f"File {file_bathy} not found for {file}")
            
            list_color_cogs.append(file)
            bathy_file_by_color[file] = file_bathy
        
        return list_color_cogs, bathy_file_by_color

    def get_depth(self, lon: float, lat: float) -> float | None:
        
        list_cogs = self.spindex.intersect((lon, lat, lon, lat))
        if len(list_cogs) == 0:
            return None
        
        bathy_path = self.bathy_file_by_color.get(list_cogs[0], None)
        if bathy_path == None or not bathy_path.exists():
            return None
        
        with rasterio.open(bathy_path) as src:
            raster_crs = src.crs

            # Transform lon/lat (EPSG:4326) into raster CRS
            xs, ys = transform("EPSG:4326", raster_crs, [lon], [lat])
            xs, ys = xs[0], ys[0]

            depth = list(src.sample([(xs, ys)]))[0][0]

        return depth



class BathyManager:
    def __init__(self, bathy_data_path: Path):
        
        self.bathy_data_path = bathy_data_path

        self.bathy_cog_by_year = self.load_bathy_cog()


    def load_bathy_cog(self) -> dict[str, BathyCogYear]:

        if not self.bathy_data_path.exists():
            raise FileNotFoundError("Cannot access to bathy data, folder not found")

        bathy_cog_by_year = {byp.name:BathyCogYear(byp) for byp in self.bathy_data_path.iterdir()}
        
        return bathy_cog_by_year
    
    def get_tile(self, year: str, bb: BoundingBox) -> ImageData | None:

        bathy_year_manager = self.bathy_cog_by_year.get(year, None)
        tile = None

        if bathy_year_manager == None:
            logger.error(f"Bathy for year {year} not found.")
        else:
            tile = bathy_year_manager.get_tile(bb)

        return tile

    def get_depth(self, lon: float, lat: float, year: str) -> float | None:

        bathy_year_manager = self.bathy_cog_by_year.get(year, None)

        depth = None
        if bathy_year_manager == None:
            logger.error(f"Bathy for year {year} not found.")
        else:
            depth = bathy_year_manager.get_depth(lon, lat)

        return depth

