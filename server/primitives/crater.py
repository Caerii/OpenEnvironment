"""Crater generation primitives - Impact craters and volcanic craters."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from ..engine.config import RES

def generate_crater(cx: int, cy: int, radius: int, depth: float, 
                   rim_height: float = 0.1, steepness: float = 1.0) -> np.ndarray:
    """
    Generate a crater heightmap stamp with elevated rim.
    
    Similar to valley but with positive rim around the perimeter.
    
    Args:
        cx, cy: Center coordinates
        radius: Crater radius (inner rim)
        depth: Maximum depth (0-1)
        rim_height: Height of elevated rim around crater (0-1)
        steepness: How steep the walls are (1.0 = normal, >1.0 = steeper)
        
    Returns:
        512x512 heightmap stamp (negative values in center, positive rim)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    dist = np.sqrt(dist_sq)
    
    # Create bowl depression (like valley)
    sigma = max(1.0, radius / (2.0 * steepness))
    carve = depth * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Create elevated rim around perimeter
    # Rim is at radius distance from center
    rim_dist = np.abs(dist - radius)
    rim_width = radius * 0.2  # Rim extends 20% of radius outward
    
    # Rim elevation peaks at radius distance
    rim_mask = rim_dist < rim_width
    rim_factor = np.exp(-rim_dist / (rim_width * 0.5))
    rim_elevation = rim_height * rim_factor * rim_mask.astype(float)
    
    # Combine: depression in center, rim around edge
    stamp = rim_elevation - carve
    
    return stamp.astype(np.float32)

def generate_crater_mask(cx: int, cy: int, radius: int) -> np.ndarray:
    """
    Generate a mask for crater texture blending.
    
    Marks the crater interior for special texture treatment.
    
    Args:
        cx, cy: Center coordinates
        radius: Crater radius
        
    Returns:
        512x512 mask (1.0 inside crater, 0.0 outside)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    mask = (dist_sq <= radius * radius).astype(np.float32)
    
    # Smooth edge
    mask = gaussian_filter(mask, sigma=2.0)
    
    return mask


