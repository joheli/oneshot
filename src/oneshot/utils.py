import base64
from pathlib import Path
import cv2
import mimetypes
from time import perf_counter
from typing import Callable, TypeVar, Tuple

def b64enc(fl: Path) -> str:
    try:
        with fl.open(mode = "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        return b64
    except OSError as e:
        # Any OS-related file error ends up here
        print(f"Could not open/read file {fl}: {e}")
        
def guess_image_mime(path: Path) -> str:
    """
    Return MIME type for common image formats based on file extension.
    Falls back to 'application/octet-stream' if unknown.
    """
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        # sensible generic default
        return "application/octet-stream"
    return mime
        
def rescale(frame, scales = (0.8, 0.3)):
    width = int(frame.shape[1] * scales[0])
    height = int(frame.shape[0] * scales[1])
    dimensions = (width, height)
    return cv2.resize(frame, dimensions, interpolation=cv2.INTER_AREA)

def cv2_to_base64(img_bgr) -> str:
    # Encode to JPEG (or PNG) in memory
    ok, buf = cv2.imencode('.jpg', img_bgr)
    if not ok:
        raise RuntimeError("cv2.imencode failed")
    # buf is a 1D uint8 array → bytes → base64 string
    img_bytes = buf.tobytes()
    return base64.b64encode(img_bytes).decode('utf-8')  # UTF‑8 string for JSON

T = TypeVar("T")

def measure_time(func: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    start = perf_counter()
    result = func(*args, **kwargs)
    end = perf_counter()
    return result, end - start
    
if __name__ == "__main__":
    #b = b64enc(Path("demo/resized.jpg"))
    b = guess_image_mime(Path("README.md"))
    print(b)