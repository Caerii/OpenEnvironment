"""Mound generation primitives - Small rounded hills."""
import numpy as np
from ..utils import clamp01
from noise import pnoise2
from ..engine.config import RES

def generate_mound(cx: int, cy: int, radius: int, height: float, 
                   use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a mound (small rounded hill) heightmap stamp.
    
    Similar to hill but smaller scale.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius (typically 20-30 pixels)
        height: Peak height (typically 0.15-0.25)
        use_noise: Whether to add noise detail
        seed: Random seed for noise
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Gaussian falloff (gentle slope)
    sigma = max(1.0, radius / 2.0)
    stamp = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add subtle noise detail
    if use_noise:
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Multi-octave noise
        amplitude = 1.0
        frequency = 0.02
        persistence = 0.5
        lacunarity = 2.0
        octaves = 3
        
        noise_value = 0.0
        freq = frequency
        amp = amplitude
        
        for _ in range(octaves):
            noise_value += amp * pnoise2(
                (xx + seed) * freq,
                (yy + seed) * freq,
                octaves=1
            )
            freq *= lacunarity
            amp *= persistence
        
        # Subtle noise variation
        noise_strength = dist_normalized * 0.03  # ±3% variation
        stamp += noise_value * noise_strength * height
    
    return stamp.astype(np.float32)


