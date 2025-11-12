"""Pass generation primitives - Depressed corridors between elevated areas."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from typing import Tuple
from ..engine.config import RES


def generate_pass(start: Tuple[int, int], end: Tuple[int, int], 
                  width: int, depth: float, elevation: float = 0.3) -> np.ndarray:
    """
    Generate a mountain pass (depressed corridor) heightmap stamp.
    
    Creates a lowered pathway between elevated areas.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        width: Pass width perpendicular to direction
        depth: How much lower than surrounding terrain (0-1)
        elevation: Base elevation of pass floor (0-1)
        
    Returns:
        512x512 heightmap stamp (negative values to subtract)
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along pass
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    # Unit vector along pass
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along pass
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    
    # Distance perpendicular to pass
    perp = dx * px + dy * py
    
    # Pass extends along its length
    along_mask = (along >= 0) & (along <= length)
    
    # Depth falls off perpendicular to pass
    half_width = width / 2.0
    perp_dist = np.abs(perp)
    
    # Smooth falloff for natural blending
    falloff = np.exp(-perp_dist / (half_width * 0.5))
    
    # Create depression in pass
    # Depth is maximum at center line
    carve = depth * falloff * along_mask.astype(float)
    
    return carve.astype(np.float32)

