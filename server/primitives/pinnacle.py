"""Pinnacle generation primitives - Very narrow, very tall peaks."""
import numpy as np
from ..utils import clamp01
from ..engine.config import RES

def generate_pinnacle(cx: int, cy: int, radius: int, height: float,
                     steepness: float = 2.0, use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a pinnacle (very narrow, very tall peak) heightmap stamp.
    
    Similar to mountain but with extreme parameters (narrow base, very tall).
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius (typically very small, 15-25 pixels)
        height: Peak height (typically 0.8-1.0 for dramatic effect)
        steepness: How steep the sides are (typically >1.5 for very steep)
        use_noise: Whether to add noise detail
        seed: Random seed for noise
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Very steep Gaussian falloff
    sigma = max(1.0, radius / (2.0 * steepness))
    stamp = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add noise detail for natural variation
    if use_noise:
        # Use optimized fractal_noise (82x faster than nested loops with pnoise2)
        from ..utils.noise import fractal_noise
        
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Generate multi-octave noise (4 octaves, persistence=0.5, lacunarity=2.0)
        noise_map = fractal_noise(
            xx + seed, yy + seed,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            scale=0.015,
            seed=seed
        )
        
        # Subtle noise variation (less than mountain since pinnacle is narrower)
        noise_strength = dist_normalized * 0.05  # ±5% variation
        from ..utils import normalize01
        noise_normalized = normalize01(noise_map)
        stamp += (noise_normalized - 0.5) * noise_strength * height
    
    return stamp.astype(np.float32)

