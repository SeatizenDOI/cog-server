import io
import functools
import numpy as np
from PIL import Image
from pathlib import Path

@functools.lru_cache()
def retrieve_transparent_image(transparent_path: Path) -> io.BytesIO:
    buf_transparent = io.BytesIO()
    img = Image.open(transparent_path)
    img.save(buf_transparent, "PNG")

    return buf_transparent

