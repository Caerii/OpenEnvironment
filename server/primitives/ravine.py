"""Ravine generation primitives - Narrow, steep valleys."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from typing import Tuple
from ..engine.config import RES

def generate_ravine(start: Tuple[int, int], end: Tuple[int, int],
                    width: int, depth: float, steepness: float = 1.2) -> np.ndarray:
    """
    Generate a ravine (narrow, steep valley) heightmap stamp.
    
    Similar to canyon but narrower and steeper.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        width: Ravine width (typically 5-8 pixels, narrower than canyon)
        depth: Maximum depth (0-1)
        steepness: How steep the walls are (typically >1.0 for very steep)
        
    Returns:
        512x512 heightmap stamp (negative values to subtract)
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along ravine
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    # Unit vector along ravine
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along ravine
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    
    # Distance perpendicular to ravine
    perp = dx * px + dy * py
    
    # Ravine extends along its length
    along_mask = (along >= 0) & (along <= length)
    
    # Very steep falloff from center
    half_width = width / 2.0
    perp_dist = np.abs(perp)
    
    # Steep exponential falloff
    falloff = np.exp(-perp_dist / (half_width * (1.0 / steepness)))
    
    # Depth is maximum at center line
    carve = depth * falloff * along_mask.astype(float)
    
    return carve.astype(np.float32)


