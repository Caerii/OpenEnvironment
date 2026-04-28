"""Terraces generation primitives - Step-like multi-level features."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from typing import Tuple
from ..engine.config import RES


def generate_terraces(region: Tuple[int, int, int, int], levels: int,
                     height_per_level: float, width_per_level: int,
                     direction: float = 0.0) -> np.ndarray:
    """
    Generate terraces (step-like multi-level feature) heightmap stamp.
    
    Creates multiple flat levels stacked vertically.
    
    Args:
        region: (x0, y0, x1, y1) bounding box
        levels: Number of terrace levels
        height_per_level: Height increase per level (0-1)
        width_per_level: Width of each terrace level
        direction: Direction of terrace progression (angle in degrees)
        
    Returns:
        512x512 heightmap stamp
    """
    x0, y0, x1, y1 = region
    
    # Calculate center
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    
    # Calculate region size
    region_width = x1 - x0
    region_height = y1 - y0
    max_dim = max(region_width, region_height)
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Rotate coordinates based on direction
    ang = np.deg2rad(direction)
    cos_a, sin_a = np.cos(ang), np.sin(ang)
    
    dx = xx - cx
    dy = yy - cy
    
    # Rotate
    xr = dx * cos_a + dy * sin_a
    yr = -dx * sin_a + dy * cos_a
    
    # Determine which level each point belongs to
    # Levels progress perpendicular to direction
    # Clamp to region
    mask = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    
    # Distance perpendicular to direction (this determines level)
    perp_dist = yr
    
    # Offset to center levels
    perp_dist = perp_dist + max_dim / 2.0
    
    # Calculate level for each point
    level_index = np.clip(perp_dist / width_per_level, 0, levels - 1).astype(int)
    
    # Height increases with level
    stamp = np.zeros((RES, RES), dtype=np.float32)
    
    for level in range(levels):
        level_mask = (level_index == level) & mask
        level_height = level * height_per_level
        
        # Smooth transitions between levels
        dist_to_level = np.abs(perp_dist - level * width_per_level)
        transition = np.exp(-dist_to_level / (width_per_level * 0.3))
        
        stamp[level_mask] = level_height * transition[level_mask]
    
    # Smooth overall
    stamp = gaussian_filter(stamp, sigma=1.0)
    
    return stamp.astype(np.float32)

