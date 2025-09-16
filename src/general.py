from pathlib import Path
from rio_tiler.models import ImageData

from .base import ParametersCOG
from .bathy import BathyManager
from .ortho import OrthoManager
from .pred_drone import PredDroneManager
from .pred_asv import PredASVManager

from enum import Enum

class ManagerType(Enum):
    BATHY = "bathy"
    PRED_DRONE = "pred_drone"
    PRED_ASV = "pred_asv"
    ORTHO = "ortho"
    IGN="ign"

    def get_attribution(type: str) -> str:
        if type == ManagerType.IGN.value: return "Géoservices@IGN-France"
        return "Ifemer DOI"
    
    def get_displayable_name(type: str) -> str:

        if type == ManagerType.BATHY.value: return "Bathymetry"
        if type == ManagerType.PRED_DRONE.value: return "Habitat map by drone"
        if type == ManagerType.PRED_ASV.value: return "Habitat map by ASV"
        if type == ManagerType.ORTHO.value: return "Orthophoto"
        if type == ManagerType.IGN.value: return "IGN BDORTHO"

        return "No found"

class GeneralManager:

    def __init__(self, data_path: Path) -> None:
        
        self.bathy_manager = BathyManager(Path(data_path, ManagerType.BATHY.value))
        self.ortho_manager = OrthoManager(Path(data_path, ManagerType.ORTHO.value))
        self.pred_drone_manager = PredDroneManager(Path(data_path, ManagerType.PRED_DRONE.value))
        self.pred_asv_manager = PredASVManager(Path(data_path, ManagerType.PRED_ASV.value))
        self.ign_manager = OrthoManager(Path(data_path, ManagerType.IGN.value))


    def get_tile(self, collection_type: str, year: str, params: ParametersCOG) -> ImageData | None:
        
        tile = None
        if collection_type == ManagerType.BATHY.value:
            tile = self.bathy_manager.get_tile(year, params)
        elif collection_type == ManagerType.ORTHO.value:
            tile = self.ortho_manager.get_tile(year, params)
        elif collection_type == ManagerType.PRED_DRONE.value:
            tile = self.pred_drone_manager.get_tile(year, params)
        elif collection_type == ManagerType.IGN.value:
            tile = self.ign_manager.get_tile(year, params)
        return tile
    
    def get_tile_with_species(self, collection_type: str, year: str, specie: str, params: ParametersCOG) -> ImageData | None:
        
        tile = None
        if collection_type == ManagerType.PRED_ASV.value:
            tile = self.pred_asv_manager.get_tile(year, specie, params)
        return tile
    

    def get_depth(self, lon: float, lat: float, year: str) -> float | None:
        return self.bathy_manager.get_depth(lon, lat, year)
        

    def get_prediction(self, lon: float, lat: float, year: str) -> str | None:
        return self.pred_drone_manager.get_prediction(lon, lat, year)
        