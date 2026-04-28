"""Basin generation primitives - Large flat depressions."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from ..engine.config import RES

def generate_basin(cx: int, cy: int, radius: int, depth: float,
                   flatness: float = 0.5) -> np.ndarray:
    """
    Generate a basin (large flat depression) heightmap stamp.
    
    Similar to valley but larger and with optional flat bottom.
    
    Args:
        cx, cy: Center coordinates
        radius: Basin radius (typically 100-150 pixels)
        depth: Maximum depth (0-1)
        flatness: How flat the bottom is (0.0 = bowl, 1.0 = completely flat)
        
    Returns:
        512x512 heightmap stamp (negative values to subtract)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    dist = np.sqrt(dist_sq)
    
    # Create depression
    sigma = max(1.0, radius / 2.5)
    
    if flatness > 0.0:
        # Flat bottom with smooth transition to edges
        normalized_dist = np.clip(dist / radius, 0.0, 1.0)
        
        # Flat center region
        flat_radius = radius * flatness * 0.7
        flat_mask = dist <= flat_radius
        
        # Bowl-shaped edges
        edge_mask = dist > flat_radius
        edge_factor = np.exp(-(dist - flat_radius)**2 / (2.0 * sigma * sigma))
        
        # Combine: flat center + bowl edges
        carve = np.zeros_like(dist)
        carve[flat_mask] = depth  # Flat bottom
        carve[edge_mask] = depth * edge_factor[edge_mask]  # Bowl edges
        
    else:
        # Pure bowl shape
        carve = depth * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    return carve.astype(np.float32)

