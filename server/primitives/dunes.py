"""Dune generation primitives."""
import numpy as np
from noise import pnoise2
from ..utils import clamp01
from typing import Tuple
from ..engine.config import RES

def generate_dunes(region: Tuple[int, int, int, int], amp: float = 0.08, freq: float = 18.0, 
                   angle_deg: float = 20.0, seed: int = 0) -> np.ndarray:
    """
    Generate rolling dunes using multi-octave directional Perlin noise.
    
    Improved with research-backed parameters:
    - 4 octaves for natural detail
    - Persistence 0.5 for balanced variation
    - Lacunarity 2.0 for standard frequency increase
    
    Args:
        region: (x0, y0, x1, y1) bounding box
        amp: Amplitude of dune height variation
        freq: Frequency of dune patterns (lower = larger dunes)
        angle_deg: Wind direction angle (affects dune orientation)
        seed: Random seed
        
    Returns:
        512x512 heightmap stamp with smooth edge blending
    """
    x0, y0, x1, y1 = region
    ang = np.deg2rad(angle_deg)
    cs, sn = np.cos(ang), np.sin(ang)
    
    dunes = np.zeros((RES, RES), dtype=np.float32)
    
    # Use optimized fractal_noise (82x faster than nested loops with pnoise2)
    from ..utils.noise import fractal_noise
    from ..utils import normalize01
    
    # Create coordinate arrays for the region
    yy, xx = np.mgrid[y0:y1, x0:x1]
    
    # Rotate coordinates to align with wind direction
    xr = (xx*cs + yy*sn) / freq
    yr = (-xx*sn + yy*cs) / freq
    
    # Generate multi-octave noise with proper parameters (4 octaves, persistence=0.5, lacunarity=2.0)
    noise = fractal_noise(
        xr, yr,
        octaves=4,
        persistence=0.5,
        lacunarity=2.0,
        scale=1.0,  # Frequency scale
        seed=seed
    )
    
    # Normalize to 0-1 range, then scale
    normalized = normalize01(noise)
    dunes[y0:y1, x0:x1] = amp * normalized
    
    # Create smooth falloff mask at edges
    feather_distance = min(40, (x1 - x0) // 4, (y1 - y0) // 4)  # Adaptive feathering
    
    # Create distance maps from edges
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance from each edge
    dist_left = np.maximum(0, xx - x0)
    dist_right = np.maximum(0, x1 - xx)
    dist_top = np.maximum(0, yy - y0)
    dist_bottom = np.maximum(0, y1 - yy)
    
    # Minimum distance to any edge
    min_dist = np.minimum(np.minimum(dist_left, dist_right), 
                         np.minimum(dist_top, dist_bottom))
    
    # Create smooth falloff mask
    falloff_mask = np.clip(min_dist / feather_distance, 0.0, 1.0)
    
    # Apply smooth falloff to dune values
    dunes[:] = dunes * falloff_mask
    
    return dunes

def generate_dune_mask(region: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Generate a smooth mask marking dune areas for splatmap assignment.
    
    Args:
        region: (x0, y0, x1, y1) bounding box
        
    Returns:
        512x512 mask (1.0 in dune areas, 0.0 elsewhere) with smooth edges
    """
    x0, y0, x1, y1 = region
    mask = np.zeros((RES, RES), dtype=np.float32)
    
    # Create smooth falloff at edges for better blending
    feather_distance = min(40, (x1 - x0) // 4, (y1 - y0) // 4)
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance from each edge
    dist_left = np.maximum(0, xx - x0)
    dist_right = np.maximum(0, x1 - xx)
    dist_top = np.maximum(0, yy - y0)
    dist_bottom = np.maximum(0, y1 - yy)
    
    # Minimum distance to any edge
    min_dist = np.minimum(np.minimum(dist_left, dist_right), 
                         np.minimum(dist_top, dist_bottom))
    
    # Create smooth falloff mask (1.0 in center, fading to 0.0 at edges)
    # For pixels inside the region, use falloff; outside, use 0
    inside_region = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    
    # Calculate falloff: 1.0 when far from edge, 0.0 at edge
    falloff_mask = np.clip(min_dist / feather_distance, 0.0, 1.0)
    
    # Apply falloff only inside region
    mask[inside_region] = falloff_mask[inside_region]
    
    return mask

