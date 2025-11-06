"""Walkability zone primitives - Reserve flat/walkable areas.

These primitives create flat zones using MIN blending to ensure terrain stays flat.
They follow the FeatureGenerator pattern for consistency.
"""
import numpy as np
from typing import Tuple
from scipy.ndimage import gaussian_filter
from ..engine.config import RES


def generate_flat_zone(cx: int, cy: int, radius: int, 
                       flatness: float = 0.0,
                       feather: int = 10) -> np.ndarray:
    """
    Generate a flat zone (circular reserved area).
    
    Creates a flat area that should remain walkable. Uses MIN blending
    to ensure terrain stays flat in this zone.
    
    Args:
        cx, cy: Center coordinates
        radius: Radius of flat zone
        flatness: Target height (0.0 = sea level, 0.5 = mid-level)
        feather: Edge feathering distance (for smooth blending)
        
    Returns:
        512x512 heightmap stamp (flat area, use MIN blending)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist = np.sqrt(dx*dx + dy*dy)
    
    # Create flat zone with smooth edges
    zone_mask = dist <= radius
    
    # Smooth falloff at edges
    falloff_dist = np.clip(dist - radius, 0, feather)
    falloff = np.exp(-falloff_dist / (feather * 0.3))
    
    # Create flat stamp (constant height)
    stamp = np.full((RES, RES), flatness, dtype=np.float32)
    
    # Apply smooth falloff at edges
    stamp[~zone_mask] = flatness + (1.0 - falloff[~zone_mask]) * 0.1
    
    # Smooth the entire stamp for natural blending
    stamp = gaussian_filter(stamp, sigma=feather * 0.5)
    
    return stamp


def generate_path(start: Tuple[int, int], end: Tuple[int, int],
                  width: int, flatness: float = 0.0,
                  feather: int = 8) -> np.ndarray:
    """
    Generate a linear path (walkable route).
    
    Creates a flat path between two points that should remain walkable.
    Uses MIN blending to ensure terrain stays flat along the path.
    
    Args:
        start: (x, y) start coordinates
        end: (x, y) end coordinates
        width: Path width in pixels
        flatness: Target height (0.0 = sea level, 0.5 = mid-level)
        feather: Edge feathering distance
        
    Returns:
        512x512 heightmap stamp (flat path, use MIN blending)
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along path
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        # Degenerate path, return small flat zone
        return generate_flat_zone(sx, sy, width // 2, flatness, feather)
    
    # Unit vector along path
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along path
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    
    # Distance perpendicular to path
    perp = dx * px + dy * py
    perp_dist = np.abs(perp)
    
    # Path extends along its length
    along_mask = (along >= 0) & (along <= length)
    
    # Path width with smooth falloff
    half_width = width / 2.0
    width_mask = perp_dist <= half_width
    
    # Smooth falloff perpendicular to path
    falloff_dist = np.clip(perp_dist - half_width, 0, feather)
    perp_falloff = np.exp(-falloff_dist / (feather * 0.3))
    
    # Smooth falloff at path ends
    end_blend = feather * 2
    end_dist_start = np.clip(-along, 0, end_blend)
    end_dist_end = np.clip(along - length, 0, end_blend)
    end_falloff = np.exp(-end_dist_start / (end_blend * 0.3)) * \
                  np.exp(-end_dist_end / (end_blend * 0.3))
    
    # Create flat stamp
    stamp = np.full((RES, RES), flatness + 0.1, dtype=np.float32)
    
    # Path area: flat
    path_mask = along_mask & width_mask
    stamp[path_mask] = flatness
    
    # Smooth transition at edges
    edge_mask = along_mask & ~width_mask
    stamp[edge_mask] = flatness + (1.0 - perp_falloff[edge_mask]) * 0.1
    
    # Apply end falloff
    stamp *= end_falloff
    stamp += (1.0 - end_falloff) * (flatness + 0.1)
    
    # Smooth the entire stamp
    stamp = gaussian_filter(stamp, sigma=feather * 0.5)
    
    return stamp


def generate_clearing(cx: int, cy: int, radius: int,
                     flatness: float = 0.0,
                     feather: int = 15) -> np.ndarray:
    """
    Generate a large clearing (open flat area).
    
    Similar to flat_zone but larger. Lower priority constraints.
    
    Args:
        cx, cy: Center coordinates
        radius: Radius of clearing
        flatness: Target height
        feather: Edge feathering distance
        
    Returns:
        512x512 heightmap stamp (flat clearing, use MIN blending)
    """
    return generate_flat_zone(cx, cy, radius, flatness, feather)
