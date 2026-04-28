"""Forest-specific terrain primitives."""
import numpy as np
from ..utils import clamp01
from ..engine.config import RES


def generate_grove(cx: int, cy: int, radius: int, height: float = 0.15,
                   use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a grove (cluster of trees on a gentle hill).
    
    Creates a rounded hill with smooth edges, suitable for forest groves.
    Similar to a mound but optimized for forest terrain.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius of grove (typically 30-50 pixels)
        height: Peak height (typically 0.10-0.20)
        use_noise: Whether to add noise detail
        seed: Random seed for noise generation
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Gentle Gaussian falloff for rounded hill
    sigma = max(1.0, radius / 2.0)
    stamp = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add subtle noise detail for natural variation
    if use_noise:
        from ..utils.noise import fractal_noise
        
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Generate multi-octave noise (3 octaves for gentle detail)
        noise_map = fractal_noise(
            xx + seed, yy + seed,
            octaves=3,
            persistence=0.4,
            lacunarity=2.0,
            scale=0.025,
            seed=seed
        )
        
        # Subtle noise variation (less than mountain since grove is gentler)
        noise_strength = dist_normalized * 0.04  # ±4% variation
        from ..utils import normalize01
        noise_normalized = normalize01(noise_map)
        stamp += (noise_normalized - 0.5) * noise_strength * height
    
    return stamp.astype(np.float32)


def generate_forest_hill(cx: int, cy: int, radius: int, height: float = 0.25,
                        use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a forest hill (larger than grove, gentle slopes for trees).
    
    Creates a rounded hill with smooth, gentle slopes suitable for forest coverage.
    Larger than groves, smaller than mountains.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius (typically 50-80 pixels)
        height: Peak height (typically 0.20-0.35)
        use_noise: Whether to add noise detail
        seed: Random seed for noise generation
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Gentle Gaussian falloff for smooth slopes
    sigma = max(1.0, radius / 1.8)  # Slightly steeper than grove
    stamp = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add noise detail for natural variation
    if use_noise:
        from ..utils.noise import fractal_noise
        
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Generate multi-octave noise (4 octaves for more detail)
        noise_map = fractal_noise(
            xx + seed, yy + seed,
            octaves=4,
            persistence=0.45,
            lacunarity=2.0,
            scale=0.02,
            seed=seed
        )
        
        # Moderate noise variation
        noise_strength = dist_normalized * 0.06  # ±6% variation
        from ..utils import normalize01
        noise_normalized = normalize01(noise_map)
        stamp += (noise_normalized - 0.5) * noise_strength * height
    
    return stamp.astype(np.float32)


def generate_forest_clearing(cx: int, cy: int, radius: int, depth: float = 0.08,
                            use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a forest clearing (gentle depression where trees are absent).
    
    Creates a shallow, rounded depression suitable for clearings or meadows
    within forest terrain.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius (typically 40-70 pixels)
        depth: Depression depth (typically 0.05-0.15)
        use_noise: Whether to add noise detail
        seed: Random seed for noise generation
        
    Returns:
        512x512 heightmap stamp (negative values for depression)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Gentle Gaussian falloff for rounded depression
    sigma = max(1.0, radius / 2.2)
    stamp = -depth * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add subtle noise detail
    if use_noise:
        from ..utils.noise import fractal_noise
        
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Generate multi-octave noise (3 octaves for gentle detail)
        noise_map = fractal_noise(
            xx + seed, yy + seed,
            octaves=3,
            persistence=0.35,
            lacunarity=2.0,
            scale=0.03,
            seed=seed
        )
        
        # Subtle noise variation
        noise_strength = dist_normalized * 0.03  # ±3% variation
        from ..utils import normalize01
        noise_normalized = normalize01(noise_map)
        stamp += (noise_normalized - 0.5) * noise_strength * depth
    
    return stamp.astype(np.float32)


def generate_forest_valley(cx: int, cy: int, radius: int, depth: float = 0.20,
                          use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a forest valley (larger depression, often with streams).
    
    Creates a deeper, wider depression suitable for forest valleys or streams.
    Larger than clearings, deeper and more pronounced.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius (typically 60-100 pixels)
        depth: Valley depth (typically 0.15-0.30)
        use_noise: Whether to add noise detail
        seed: Random seed for noise generation
        
    Returns:
        512x512 heightmap stamp (negative values for depression)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Gentle Gaussian falloff for rounded valley
    sigma = max(1.0, radius / 2.0)
    stamp = -depth * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add noise detail for natural variation
    if use_noise:
        from ..utils.noise import fractal_noise
        
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Generate multi-octave noise (4 octaves for more detail)
        noise_map = fractal_noise(
            xx + seed, yy + seed,
            octaves=4,
            persistence=0.4,
            lacunarity=2.0,
            scale=0.018,
            seed=seed
        )
        
        # Moderate noise variation
        noise_strength = dist_normalized * 0.05  # ±5% variation
        from ..utils import normalize01
        noise_normalized = normalize01(noise_map)
        stamp += (noise_normalized - 0.5) * noise_strength * depth
    
    return stamp.astype(np.float32)

