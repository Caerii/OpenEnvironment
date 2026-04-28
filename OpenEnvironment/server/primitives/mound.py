"""Mound generation primitives - Small rounded hills."""
import numpy as np
from ..utils import clamp01
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
        # Use optimized fractal_noise (82x faster than nested loops with pnoise2)
        from ..utils.noise import fractal_noise
        
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Generate multi-octave noise (3 octaves, persistence=0.5, lacunarity=2.0)
        noise_map = fractal_noise(
            xx + seed, yy + seed,
            octaves=3,
            persistence=0.5,
            lacunarity=2.0,
            scale=0.02,
            seed=seed
        )
        
        # Subtle noise variation
        noise_strength = dist_normalized * 0.03  # ±3% variation
        from ..utils import normalize01
        noise_normalized = normalize01(noise_map)
        stamp += (noise_normalized - 0.5) * noise_strength * height
    
    return stamp.astype(np.float32)


