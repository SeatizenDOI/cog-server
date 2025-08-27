import logging
import morecantile
import numpy as np
from pathlib import Path
from fastapi import FastAPI, Response, Query
from starlette.middleware.cors import CORSMiddleware
from rio_tiler.profiles import img_profiles

from src.general import GeneralManager
from src.base import ParametersCOG
from src.tools import retrieve_transparent_image

GLOBAL_DATA_PATH = Path("./data")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auto-Discovery Multi-COG Tile Server")

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
                # "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*"  # Allow CORS
            }
        ) 
        
    except Exception as e:
        logger.error(f"Error serving tile {collection_name}/{z}/{x}/{y}: {e}")


@app.get("/depth")
async def get_depth(lon: float = Query(...), lat: float = Query(...), year: str = Query(...)) -> dict:
    """Return depth at clicked point."""

    try:
        depth_value = general_manager.get_depth(lon, lat, year)

        return {
            "lon": lon, 
            "lat": lat, 
            "depth": None if depth_value == None or np.isnan(depth_value) else float(depth_value)
        }
    except Exception as e:
        logger.error(f"Get POint : {e}")


@app.get("/prediction")
async def get_depth(lon: float = Query(...), lat: float = Query(...), year: str = Query(...)) -> dict:
    """Return prediction at clicked point."""

    try:
        pred_value = general_manager.get_prediction(lon, lat, year)

        return {
            "lon": lon, 
            "lat": lat, 
            "pred": pred_value
        }
    except Exception as e:
        logger.error(f"Get POint : {e}")
