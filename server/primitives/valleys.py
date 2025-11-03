"""Valley generation primitives."""
import numpy as np
from scipy.ndimage import gaussian_filter
from ..utils import clamp01
from typing import Tuple
from ..engine.config import RES

def generate_valley(cx: int, cy: int, radius: int, depth: float) -> np.ndarray:
    """
    Generate a valley heightmap stamp (negative elevation).
    
    Args:
        cx, cy: Center coordinates
        radius: Valley radius
        depth: Maximum depth (0-1)
        
    Returns:
        512x512 heightmap stamp (negative values to subtract)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Use a steeper falloff for more dramatic valleys
    sigma = max(1.0, radius / 2.5)  # Slightly steeper than before
    
    # Create deeper valley with stronger center carve
    # Use exponential falloff for natural valley shape
    carve = depth * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add a sharper drop-off near the center for more dramatic effect
    center_factor = np.exp(-dist_sq / (sigma * sigma * 0.5))
    carve = carve * (0.7 + 0.3 * center_factor)  # Deeper center
    
    return carve

def generate_canyon(start: Tuple[int, int], end: Tuple[int, int], width: int, depth: float, 
                   falloff: float = 0.5) -> np.ndarray:
    """
    Generate a canyon (linear cut) heightmap stamp.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        width: Canyon width in pixels
        depth: Maximum depth (0-1)
        falloff: How quickly depth falls off from center (0.0 = sharp, 1.0 = gradual)
        
    Returns:
        512x512 heightmap stamp (negative values to subtract)
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along canyon
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    # Unit vector along canyon
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along canyon (0 = start, 1 = end)
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    
    # Distance perpendicular to canyon
    perp = dx * px + dy * py
    
    # Width falloff
    width_norm = np.abs(perp) / (width / 2.0)
    
    # Depth falls off from center line
    depth_factor = np.exp(-width_norm * (1.0 / (falloff + 0.1)))
    
    # Also fall off at edges of canyon
    edge_factor = np.ones_like(along)
    edge_factor[along < 0] = 0.0
    edge_factor[along > length] = 0.0
    
    # Smooth edge transitions
    edge_blend = 20.0  # pixels
    if np.any(along >= 0) and np.any(along < edge_blend):
        mask = (along >= 0) & (along < edge_blend)
        edge_factor[mask] = along[mask] / edge_blend
    
    if np.any(along <= length) and np.any(along > length - edge_blend):
        mask = (along <= length) & (along > length - edge_blend)
        edge_factor[mask] = (length - along[mask]) / edge_blend
    
    canyon = depth * depth_factor * edge_factor
    return canyon

