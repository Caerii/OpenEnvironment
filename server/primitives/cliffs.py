"""Cliff generation primitives - Steep vertical drops."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter
from ..engine.config import RES

def generate_cliff(cx: int, cy: int, length: int, height: float, orientation: float = 0.0,
                   steepness: float = 0.9) -> np.ndarray:
    """
    Generate a cliff (steep vertical drop) heightmap stamp.
    
    Args:
        cx, cy: Center coordinates
        length: Length of cliff face
        height: Height of cliff (0-1)
        orientation: Rotation angle in degrees (0 = north-facing)
        steepness: How steep the drop is (0.0 = gradual, 1.0 = vertical wall)
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    
    # Rotate coordinates
    ang = np.deg2rad(orientation)
    cos_a, sin_a = np.cos(ang), np.sin(ang)
    xr = dx * cos_a + dy * sin_a
    yr = -dx * sin_a + dy * cos_a
    
    # Cliff is a linear feature perpendicular to orientation
    # Distance along cliff (parallel to cliff face)
    along_cliff = xr
    
    # Distance perpendicular to cliff (toward/away from cliff)
    perp_dist = yr
    
    # Cliff extends along its length
    half_length = length / 2.0
    along_mask = np.abs(along_cliff) <= half_length
    
    # Create steep drop-off
    # Use exponential falloff for sharp edge
    drop_off = np.exp(-np.abs(perp_dist) / (10.0 * (1.0 - steepness + 0.1)))
    
    # Height is maximum at the cliff edge, drops off quickly
    # Positive perp_dist = on the high side, negative = on the low side
    stamp = np.zeros_like(dx, dtype=np.float32)
    
    # High side (positive perp_dist) - gradual rise
    high_mask = (perp_dist >= 0) & along_mask
    if np.any(high_mask):
        high_falloff = np.exp(-perp_dist[high_mask] / 20.0)
        stamp[high_mask] = height * high_falloff * 0.3  # Slight rise before cliff
    
    # Low side (negative perp_dist) - steep drop
    low_mask = (perp_dist < 0) & along_mask
    if np.any(low_mask):
        # Steep drop with exponential falloff
        drop_dist = -perp_dist[low_mask]
        drop_factor = np.exp(-drop_dist / (8.0 * (1.0 - steepness + 0.1)))
        stamp[low_mask] = height * drop_factor
    
    # Add smooth falloff at cliff ends
    end_blend = 30.0
    end_mask = along_mask & (np.abs(along_cliff) > half_length - end_blend)
    if np.any(end_mask):
        end_dist = np.abs(along_cliff[end_mask]) - (half_length - end_blend)
        end_factor = np.exp(-end_dist / end_blend)
        stamp[end_mask] *= end_factor
    
    # Smooth the edges slightly
    stamp = gaussian_filter(stamp, sigma=0.5)
    
    return stamp


def generate_cliff_mask(cx: int, cy: int, length: int, orientation: float = 0.0,
                        width: int = 8) -> np.ndarray:
    """
    Generate a mask marking cliff areas for splatmap assignment (rock texture).
    
    Args:
        cx, cy: Center coordinates
        length: Length of cliff face
        orientation: Rotation angle in degrees
        width: Width of cliff mask (pixels)
        
    Returns:
        512x512 mask (1.0 at cliff face, 0.0 elsewhere)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    
    # Rotate coordinates
    ang = np.deg2rad(orientation)
    cos_a, sin_a = np.cos(ang), np.sin(ang)
    xr = dx * cos_a + dy * sin_a
    yr = -dx * sin_a + dy * cos_a
    
    # Distance along and perpendicular to cliff
    along_cliff = xr
    perp_dist = np.abs(yr)
    
    half_length = length / 2.0
    
    # Mask for cliff face (steep area)
    mask = (np.abs(along_cliff) <= half_length) & (perp_dist <= width)
    
    # Create smooth falloff
    result = np.zeros((RES, RES), dtype=np.float32)
    
    # Perpendicular falloff
    perp_factor = np.exp(-perp_dist / (width / 2.0))
    
    # Along-cliff falloff at ends
    along_factor = np.ones_like(along_cliff)
    end_blend = 20.0
    end_mask = np.abs(along_cliff) > half_length - end_blend
    if np.any(end_mask):
        end_dist = np.abs(along_cliff[end_mask]) - (half_length - end_blend)
        along_factor[end_mask] = np.exp(-end_dist / end_blend)
    
    result[mask] = perp_factor[mask] * along_factor[mask]
    
    return result

