"""Spur generation primitives - Ridges extending from mountains."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from typing import Tuple
from ..engine.config import RES


def generate_spur(start: Tuple[int, int], end: Tuple[int, int],
                 width: int, base_height: float, end_height: float = 0.0,
                 steepness: float = 0.7) -> np.ndarray:
    """
    Generate a spur (ridge extending from elevated area) heightmap stamp.
    
    Creates a ridge that decreases in height from start to end.
    
    Args:
        start: (x, y) start coordinates (attached to mountain, higher elevation)
        end: (x, y) end coordinates (extends outward, lower elevation)
        width: Spur width perpendicular to line
        base_height: Height at start (0-1)
        end_height: Height at end (0-1, typically 0.0 or small)
        steepness: How steep the sides are (0.0 = gradual, 1.0 = steep)
        
    Returns:
        512x512 heightmap stamp
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along spur
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    # Unit vector along spur
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along spur (0 = start, 1 = end)
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    along_normalized = np.clip(along / length, 0.0, 1.0)
    
    # Distance perpendicular to spur
    perp = dx * px + dy * py
    
    # Height decreases linearly from start to end
    height_along = base_height * (1.0 - along_normalized) + end_height * along_normalized
    
    # Spur extends along its length
    along_mask = (along >= 0) & (along <= length)
    
    # Height falls off perpendicular to spur
    half_width = width / 2.0
    perp_dist = np.abs(perp)
    
    # Exponential falloff for sides
    falloff = np.exp(-perp_dist / (half_width * (1.0 - steepness + 0.1)))
    
    # Height is maximum along center line, decreases toward ends
    stamp = height_along * falloff * along_mask.astype(float)
    
    return stamp.astype(np.float32)

