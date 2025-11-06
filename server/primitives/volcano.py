"""Volcano generation primitives - Cone-shaped mountains with optional craters."""
import numpy as np
from ..utils import clamp01
from ..engine.config import RES

def generate_volcano(cx: int, cy: int, base_radius: int, height: float,
                     crater_radius: float = 0.0, crater_depth: float = 0.0,
                     steepness: float = 1.0, use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a volcano (cone-shaped mountain) heightmap stamp.
    
    Creates a steep cone with optional crater at the top.
    
    Args:
        cx, cy: Center coordinates
        base_radius: Radius of volcano base
        height: Peak height (0-1)
        crater_radius: Radius of crater at top (0.0 = no crater, 0.1-0.3 = typical)
        crater_depth: Depth of crater (0.0 = no crater, 0.1-0.3 = typical)
        steepness: How steep the cone is (1.0 = normal, >1.0 = steeper)
        use_noise: Whether to add noise detail
        seed: Random seed for noise
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    dist = np.sqrt(dist_sq)
    
    # Create cone shape (steeper than mountain)
    # Height decreases linearly from center
    normalized_dist = np.clip(dist / base_radius, 0.0, 1.0)
    
    # Steep cone profile
    cone_height = height * (1.0 - normalized_dist) ** steepness
    
    # Add crater at top if specified
    if crater_radius > 0.0 and crater_depth > 0.0:
        crater_dist = dist / base_radius
        crater_mask = crater_dist < crater_radius
        
        # Crater depth decreases toward center
        crater_factor = np.exp(-crater_dist / (crater_radius * 0.5))
        crater_carve = crater_depth * crater_factor * crater_mask.astype(float)
        
        cone_height = cone_height - crater_carve
    
    # Add noise detail for natural variation
    if use_noise:
        # Use fractal_noise utility which handles arrays correctly
        from ..utils.noise import fractal_noise
        
        # Generate fractal noise with appropriate scale
        noise_value = fractal_noise(
            xx,
            yy,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            scale=0.01,  # Frequency scale
            seed=seed
        )
        
        # Scale noise based on distance from center
        dist_normalized = np.clip(dist / base_radius, 0.0, 1.0)
        noise_strength = dist_normalized * 0.05  # ±5% variation
        cone_height += noise_value * noise_strength
    
    # Ensure non-negative
    stamp = np.maximum(cone_height, 0.0)
    
    return stamp.astype(np.float32)


