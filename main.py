import logging
import morecantile
from pathlib import Path
from fastapi import FastAPI, Response, Query, HTTPException
from starlette.middleware.cors import CORSMiddleware
from rio_tiler.profiles import img_profiles

from src.general import GeneralManager, ManagerType
from src.base import ParametersCOG
from src.tools import retrieve_transparent_image

GLOBAL_DATA_PATH = Path("./data")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auto-Discovery Multi-COG Tile Server", docs_url=None, redoc_url=None)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development - be more specific in production)
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Setup bathy
general_manager = GeneralManager(GLOBAL_DATA_PATH)


@app.get("/{collection_name}/{year}/{z}/{x}/{y}.png")
async def serve_collection_tile(collection_name: str, year: str, z: int, x: int, y: int, asv: bool = True) -> Response:
    """Serve tiles from a predefined COG collection"""

    try:
        # Get bounding box from x, y, z
        tms = morecantile.tms.get("WebMercatorQuad")  # default TiTiler TMS
        bb = tms.bounds(x, y, z)
        params = ParametersCOG(x, y, z, bb, with_asv=asv)


        tile = general_manager.get_tile(collection_name, year, params)

        if tile == None:
            png_data = retrieve_transparent_image(Path(GLOBAL_DATA_PATH, "transparent.png")).getvalue()
        else:
            png_data = tile.render(img_format="PNG", add_mask=False, **img_profiles.get("png"))
        
        return Response(
            png_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*"  # Allow CORS
            }
        ) 
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/{collection_name}/{year}/{specie}/{z}/{x}/{y}.png")
async def serve_collection_tile(collection_name: str, year: str, specie: str, z: int, x: int, y: int) -> Response:
    """Serve tiles from a predefined COG collection"""

    try:
        # Get bounding box from x, y, z
        tms = morecantile.tms.get("WebMercatorQuad")  # default TiTiler TMS
        bb = tms.bounds(x, y, z)
        params = ParametersCOG(x, y, z, bb, with_asv=False)


        tile = general_manager.get_tile_with_species(collection_name, year, specie, params)

        if tile == None:
            png_data = retrieve_transparent_image(Path(GLOBAL_DATA_PATH, "transparent.png")).getvalue()
        else:
            png_data = tile.render(img_format="PNG", add_mask=False, **img_profiles.get("png"))
        
        return Response(
            png_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*"  # Allow CORS
            }
        ) 
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/depth")
async def get_depth(lon: float = Query(...), lat: float = Query(...), years: list[str] = Query(...)) -> dict:
    """Return depth at clicked point."""

    try:
        depth_value = None
        for year in years:
            depth_value = general_manager.get_depth(lon, lat, year)
            print(year, depth_value)
            if depth_value != None: break

        return {
            "lon": lon, 
            "lat": lat, 
            "depth": None if depth_value == None else float(depth_value)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/prediction")
async def get_prediction(lon: float = Query(...), lat: float = Query(...), years: list[str] = Query(...)) -> dict:
    """Return prediction at clicked point."""

    try:
        pred_value = None
        for year in years:
            pred_value = general_manager.get_prediction(lon, lat, year)
            if pred_value != None: break
        
        return {
            "lon": lon, 
            "lat": lat, 
            "pred": pred_value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/depthOrprediction")
async def get_prediction(lon: float = Query(...), lat: float = Query(...), layers_id: list[str] = Query(...)) -> dict:
    """Return prediction or depth at clicked point."""

    try:
        layer_type, value = "", None
        for layer_id in layers_id:
            if ManagerType.PRED_ASV.value in layer_id: continue
            layer_split = layer_id.split("_")
            layer_year = layer_split[-1]
            layer_type = '_'.join(layer_split[0:len(layer_split)-1])
            if ManagerType.BATHY.value in layer_id:
                value = general_manager.get_depth(lon, lat, layer_year)
            elif ManagerType.PRED_DRONE.value in layer_id:
                value = general_manager.get_prediction(lon, lat, layer_year)

            if value != None: break

        return {
            "lon": lon, 
            "lat": lat, 
            "type": layer_type,
            "value": value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/layers")
async def get_layers():

    layers = []
    try:
        for type_path in sorted(list(GLOBAL_DATA_PATH.iterdir())):
            if not type_path.is_dir() or type_path.name == ManagerType.PRED_ASV.value: continue
            for year in sorted(list(type_path.iterdir())):
                layers.append({
                    "id": f"{type_path.name}_{year.name}",
                    "name": f"{ManagerType.get_displayable_name(type_path.name)} {year.name}",
                    "url": f"/{type_path.name}/{year.name}"+"/{z}/{x}/{y}.png",
                    "attribution": ManagerType.get_attribution(type_path.name),
                    "description":  ManagerType.get_description(type_path.name)
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return layers


@app.get("/filters-asv")
async def get_filters():
    asv_color =  general_manager.pred_asv_manager.get_color_pred_asv_by_specie()

    filters = {
        "species": [{"name":s, "color": '#%02x%02x%02x' % tuple(asv_color.get(s, [127, 127, 127]))}  for s in general_manager.pred_asv_manager.species], 
        "years": sorted([int(y.name) for y in general_manager.pred_asv_manager.pred_data_path.iterdir() if y.is_dir()])
    }

    return filters


@app.get("/get-layer")
async def get_specific_layer(year: str, specie: str):

    test_path = Path(GLOBAL_DATA_PATH, "pred_asv", year)
    if not test_path.exists():
        return HTTPException(404, "Cannot find the selected year")

    if specie not in general_manager.pred_asv_manager.species:
        return HTTPException(404, "Cannot find the selected specie")

    layer = {
        "id": f"{ManagerType.PRED_ASV.value}_{year}_{specie}",
        "name": f"{ManagerType.get_displayable_name(ManagerType.PRED_ASV.value)} {year} {specie}",
        "url": f"/{ManagerType.PRED_ASV.value}/{year}/{specie}"+"/{z}/{x}/{y}.png",
        "attribution": ManagerType.get_attribution(ManagerType.PRED_ASV.value),
        "description":  ManagerType.get_description(ManagerType.PRED_ASV.value)
    }

    return layer