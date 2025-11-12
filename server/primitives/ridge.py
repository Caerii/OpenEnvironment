"""Ridge generation primitives - Linear elevated features."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from typing import Tuple
from ..engine.config import RES

def generate_ridge(start: Tuple[int, int], end: Tuple[int, int], 
                   height: float, width: int, steepness: float = 0.8) -> np.ndarray:
    """
    Generate a ridge (linear elevated feature) heightmap stamp.
    
    Similar to canyon but inverted (positive elevation).
    Uses smooth falloff for natural blending.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        width: Ridge width perpendicular to line
        height: Maximum height (0-1)
        steepness: How steep the sides are (0.0 = gradual, 1.0 = steep)
        
    Returns:
        512x512 heightmap stamp
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along ridge
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    # Unit vector along ridge
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along ridge (0 = start, 1 = end)
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    
    # Distance perpendicular to ridge
    perp = dx * px + dy * py
    
    # Width falloff - use smoother falloff
    half_width = width / 2.0
    perp_dist = np.abs(perp)
    width_norm = perp_dist / half_width
    
    # Use smoother falloff based on steepness
    # Lower steepness = smoother falloff
    # Higher steepness = sharper falloff
    falloff_factor = 1.0 + (1.0 - steepness) * 2.0  # 1.0 to 3.0
    falloff = np.exp(-width_norm * falloff_factor)
    
    # Smooth falloff at edges using smoothstep-like function
    # This creates gentler transitions
    smooth_falloff = falloff * (1.0 - np.clip(width_norm - 0.5, 0.0, 1.0) ** 2)
    
    # Edge blending at start/end of ridge
    edge_blend = 20.0  # pixels for smooth edge transitions
    edge_factor = np.ones_like(along)
    
    # Smooth start edge
    if np.any(along >= 0) and np.any(along < edge_blend):
        mask = (along >= 0) & (along < edge_blend)
        edge_factor[mask] = np.clip(along[mask] / edge_blend, 0.0, 1.0)
    
    # Smooth end edge
    if np.any(along <= length) and np.any(along > length - edge_blend):
        mask = (along <= length) & (along > length - edge_blend)
        edge_factor[mask] = np.clip((length - along[mask]) / edge_blend, 0.0, 1.0)
    
    # Ensure we only affect area along the ridge
    along_mask = (along >= 0) & (along <= length)
    
    # Height is maximum along the center line, falls off smoothly
    stamp = height * smooth_falloff * edge_factor * along_mask.astype(float)
    
    # Apply Gaussian smoothing for even smoother edges
    stamp = gaussian_filter(stamp, sigma=1.5)
    
    return stamp.astype(np.float32)

def generate_ridge_mask(start: Tuple[int, int], end: Tuple[int, int], 
                        width: int) -> np.ndarray:
    """
    Generate a mask for ridge texture blending.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        width: Ridge width
        
    Returns:
        512x512 mask
    """
    sx, sy = start
    ex, ey = end
    
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    ux = dx_line / length
    uy = dy_line / length
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    perp = dx * px + dy * py
    
    along_mask = (along >= 0) & (along <= length)
    perp_mask = np.abs(perp) <= width / 2.0
    
    mask = (along_mask & perp_mask).astype(np.float32)
    mask = gaussian_filter(mask, sigma=2.0)
    
    return mask

