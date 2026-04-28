"""Base biome generation functions."""
import numpy as np
from ..utils import normalize01
from ..engine.config import RES

def base_flat(seed=-1) -> np.ndarray:
    """
    Generate a gently rolling hilly base terrain (for reset functionality).
    
    Uses multi-scale fractal noise with lower persistence for smooth, gentle hills
    combined with Gaussian filtering to avoid grid-like appearance.
    
    Args:
        seed: Random seed for deterministic generation (-1 = auto-generate random seed)
        
    Returns:
        512x512 heightmap array (normalized 0-1 range, moderate hilly variation)
    """
    import random
    import time
    
    # Auto-generate random seed if seed is -1
    if seed == -1:
        seed = random.randint(0, 2**31 - 1)
    
    from ..utils.noise import fractal_noise
    from scipy.ndimage import gaussian_filter
    
    # Use multi-scale fractal noise for natural variation (not grid-like)
    xx, yy = np.meshgrid(np.arange(RES), np.arange(RES))
    
    # Large-scale hills (overall terrain shape) - multi-octave for natural variation
    large_hills = fractal_noise(
        xx, yy,
        octaves=4,  # Multi-scale resolution
        persistence=0.3,  # Lower persistence = smoother (less high-frequency detail)
        lacunarity=2.0,
        scale=128.0,  # Large hills
        seed=seed
    )
    
    # Medium-scale hills (regional variation) - multi-octave
    medium_hills = fractal_noise(
        xx, yy,
        octaves=3,  # Multi-scale resolution
        persistence=0.25,  # Lower persistence = smoother
        lacunarity=2.5,
        scale=64.0,  # Medium hills
        seed=seed + 1000
    )
    
    # Small-scale detail (texture) - but with low persistence to keep it smooth
    small_detail = fractal_noise(
        xx, yy,
        octaves=2,  # Multi-scale resolution
        persistence=0.2,  # Very low persistence = smooth detail
        lacunarity=3.0,
        scale=32.0,  # Small detail
        seed=seed + 2000
    )
    
    # Combine: large hills (60%) + medium hills (30%) + detail (10%)
    combined = large_hills * 0.6 + medium_hills * 0.3 + small_detail * 0.1
    
    # Apply Gaussian smoothing for soft, gentle hills (smooths out grid-like artifacts)
    h = gaussian_filter(combined, sigma=8.0)  # Smooth out the hills
    
    # Add Gaussian blobs for natural global height differences
    import random
    rng = random.Random(seed + 5000)
    h_with_blobs = h.copy()
    
    # Add 3-5 Gaussian hills of varying sizes for natural global variation
    num_blobs = rng.randint(3, 6)
    for _ in range(num_blobs):
        cx = rng.randint(RES // 4, 3 * RES // 4)
        cy = rng.randint(RES // 4, 3 * RES // 4)
        radius = rng.randint(40, 100)
        height = rng.uniform(0.08, 0.15)
        
        # Gaussian falloff
        dx = xx - cx
        dy = yy - cy
        dist_sq = dx*dx + dy*dy
        sigma = radius / 2.0
        blob = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
        h_with_blobs += blob
    
    # Normalize and scale to moderate hilly range (0.0 to 0.25)
    h = normalize01(h_with_blobs) * 0.25
    
    return h.astype(np.float32)

def base_desert(seed=-1) -> np.ndarray:
    """
    Generate a base desert biome - soft rolling hills with dunes.
    
    Creates a hilly desert landscape with multi-scale elevation variation,
    Gaussian blobs for global height differences, and explicit dunes.
    Uses smoothed multi-scale noise.
    
    Args:
        seed: Random seed for deterministic generation (-1 = auto-generate random seed)
        
    Returns:
        512x512 heightmap array (normalized 0-1)
    """
    import random
    
    # Auto-generate random seed if seed is -1
    if seed == -1:
        seed = random.randint(0, 2**31 - 1)
    
    from ..utils.noise import fractal_noise
    from scipy.ndimage import gaussian_filter
    
    xx, yy = np.meshgrid(np.arange(RES), np.arange(RES))
    
    # Large-scale desert hills (multi-octave for natural variation)
    large_hills = fractal_noise(
        xx, yy,
        octaves=4,  # Multi-scale resolution
        persistence=0.3,  # Lower persistence = smoother
        lacunarity=2.0,
        scale=128.0,  # Large rolling hills
        seed=seed
    )
    
    # Medium-scale valleys (multi-octave)
    medium_features = fractal_noise(
        xx, yy,
        octaves=3,  # Multi-scale resolution
        persistence=0.25,  # Lower persistence = smoother
        lacunarity=2.5,
        scale=64.0,  # Medium valleys
        seed=seed + 1000
    )
    
    # Small-scale texture (multi-octave but smooth)
    small_detail = fractal_noise(
        xx, yy,
        octaves=2,  # Multi-scale resolution
        persistence=0.2,  # Very low persistence = smooth detail
        lacunarity=3.0,
        scale=32.0,  # Small detail
        seed=seed + 2000
    )
    
    # Combine: large hills (55%) + medium features (35%) + detail (10%)
    combined = large_hills * 0.55 + medium_features * 0.35 + small_detail * 0.1
    
    # Apply Gaussian smoothing for soft, gentle hills
    h = gaussian_filter(combined, sigma=6.0)  # Smooth out the hills
    
    # Add Gaussian blobs for natural global height differences
    rng = random.Random(seed + 5000)
    h_with_blobs = h.copy()
    
    # Add 4-6 Gaussian hills of varying sizes for natural global variation
    num_hills = rng.randint(4, 7)
    for _ in range(num_hills):
        cx = rng.randint(RES // 4, 3 * RES // 4)
        cy = rng.randint(RES // 4, 3 * RES // 4)
        radius = rng.randint(50, 120)
        height = rng.uniform(0.06, 0.12)
        
        # Gaussian falloff
        dx = xx - cx
        dy = yy - cy
        dist_sq = dx*dx + dy*dy
        sigma = radius / 2.0
        blob = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
        h_with_blobs += blob
    
    # Add dunes COVERING THE ENTIRE MAP using directional noise
    # Primary wind direction (dominant dune pattern)
    primary_angle = rng.uniform(0, 360)
    primary_amp = rng.uniform(0.05, 0.09)
    primary_freq = rng.uniform(16.0, 24.0)
    
    # Generate primary dune pattern across entire map
    ang = np.deg2rad(primary_angle)
    cs, sn = np.cos(ang), np.sin(ang)
    
    # Rotate coordinates to align with wind direction
    xr = (xx*cs + yy*sn) / primary_freq
    yr = (-xx*sn + yy*cs) / primary_freq
    
    # Generate multi-octave noise for primary dunes
    primary_dunes = fractal_noise(
        xr, yr,
        octaves=4,
        persistence=0.4,
        lacunarity=2.0,
        scale=1.0,
        seed=seed + 3000
    )
    
    # Normalize and apply primary dunes
    from ..utils import normalize01
    primary_dunes_normalized = normalize01(primary_dunes)
    h_with_blobs += primary_amp * primary_dunes_normalized
    
    # Add secondary dune pattern (cross-wind) for more natural variation
    secondary_angle = primary_angle + rng.uniform(60, 120)  # Perpendicular-ish
    secondary_amp = rng.uniform(0.02, 0.04)  # Weaker secondary pattern
    secondary_freq = rng.uniform(20.0, 30.0)
    
    ang2 = np.deg2rad(secondary_angle)
    cs2, sn2 = np.cos(ang2), np.sin(ang2)
    xr2 = (xx*cs2 + yy*sn2) / secondary_freq
    yr2 = (-xx*sn2 + yy*cs2) / secondary_freq
    
    secondary_dunes = fractal_noise(
        xr2, yr2,
        octaves=3,
        persistence=0.3,
        lacunarity=2.0,
        scale=1.0,
        seed=seed + 4000
    )
    
    secondary_dunes_normalized = normalize01(secondary_dunes)
    h_with_blobs += secondary_amp * secondary_dunes_normalized
    
    # Normalize and scale to moderate hilly desert range
    h = normalize01(h_with_blobs) * 0.20  # Hilly but not too high
    
    return h.astype(np.float32)

def base_forest(seed=-1) -> np.ndarray:
    """
    Generate a base forest biome - beautiful rolling hills and valleys.
    
    Creates a hilly forest landscape with multi-scale elevation variation and
    Gaussian blobs for natural global height differences. Uses smoothed multi-scale noise
    for beautiful rolling hills similar to arctic quality.
    
    Args:
        seed: Random seed for deterministic generation (-1 = auto-generate random seed)
        
    Returns:
        512x512 heightmap array (normalized 0-1)
    """
    import random
    
    # Auto-generate random seed if seed is -1
    if seed == -1:
        seed = random.randint(0, 2**31 - 1)
    
    from ..utils.noise import fractal_noise
    from scipy.ndimage import gaussian_filter
    
    xx, yy = np.meshgrid(np.arange(RES), np.arange(RES))
    
    # Large-scale rolling hills (multi-octave for natural variation) - larger scale for more rolling
    large_hills = fractal_noise(
        xx, yy,
        octaves=4,  # Multi-scale resolution
        persistence=0.3,  # Lower persistence = smoother
        lacunarity=2.0,
        scale=110.0,  # Large rolling hills (increased from 96 for more rolling)
        seed=seed
    )
    
    # Medium-scale valleys and ridges (multi-octave) - larger scale
    medium_features = fractal_noise(
        xx, yy,
        octaves=3,  # Multi-scale resolution
        persistence=0.25,  # Lower persistence = smoother
        lacunarity=2.3,
        scale=55.0,  # Medium valleys/ridges (increased from 48)
        seed=seed + 1000
    )
    
    # Small-scale detail (multi-octave but smooth)
    small_detail = fractal_noise(
        xx, yy,
        octaves=2,  # Multi-scale resolution
        persistence=0.2,  # Very low persistence = smooth detail
        lacunarity=2.8,
        scale=28.0,  # Small detail (increased from 24)
        seed=seed + 2000
    )
    
    # Combine: large hills (65%) + medium features (30%) + detail (5%) - more emphasis on rolling
    combined = large_hills * 0.65 + medium_features * 0.3 + small_detail * 0.05
    
    # Apply Gaussian smoothing for soft, gentle hills (more smoothing like arctic)
    h = gaussian_filter(combined, sigma=8.0)  # Increased smoothing (from 7.0)
    
    # Add forest-specific primitives using the actual forest primitive functions
    rng = random.Random(seed + 5000)
    h_with_forest_features = h.copy()
    
    from ..primitives.forest import generate_grove, generate_forest_hill, generate_forest_clearing, generate_forest_valley
    
    # Add 4-6 groves (small tree clusters on gentle hills)
    num_groves = rng.randint(4, 7)
    for i in range(num_groves):
        cx = rng.randint(RES // 5, 4 * RES // 5)
        cy = rng.randint(RES // 5, 4 * RES // 5)
        radius = rng.randint(30, 50)
        height = rng.uniform(0.10, 0.18)
        
        grove_stamp = generate_grove(cx, cy, radius, height, use_noise=True, seed=seed + 6000 + i)
        h_with_forest_features += grove_stamp  # Add positive hills
    
    # Add 3-5 forest hills (larger hills suitable for trees)
    num_forest_hills = rng.randint(3, 6)
    for i in range(num_forest_hills):
        cx = rng.randint(RES // 4, 3 * RES // 4)
        cy = rng.randint(RES // 4, 3 * RES // 4)
        radius = rng.randint(50, 80)
        height = rng.uniform(0.20, 0.30)
        
        forest_hill_stamp = generate_forest_hill(cx, cy, radius, height, use_noise=True, seed=seed + 7000 + i)
        h_with_forest_features += forest_hill_stamp  # Add positive hills
    
    # Add 2-4 forest clearings (gentle depressions for meadows)
    num_clearings = rng.randint(2, 5)
    for i in range(num_clearings):
        cx = rng.randint(RES // 4, 3 * RES // 4)
        cy = rng.randint(RES // 4, 3 * RES // 4)
        radius = rng.randint(40, 70)
        depth = rng.uniform(0.05, 0.12)
        
        clearing_stamp = generate_forest_clearing(cx, cy, radius, depth, use_noise=True, seed=seed + 8000 + i)
        h_with_forest_features += clearing_stamp  # Add negative depressions
    
    # Add 1-3 forest valleys (larger depressions, often with streams)
    num_valleys = rng.randint(1, 4)
    for i in range(num_valleys):
        cx = rng.randint(RES // 4, 3 * RES // 4)
        cy = rng.randint(RES // 4, 3 * RES // 4)
        radius = rng.randint(60, 100)
        depth = rng.uniform(0.15, 0.25)
        
        valley_stamp = generate_forest_valley(cx, cy, radius, depth, use_noise=True, seed=seed + 9000 + i)
        h_with_forest_features += valley_stamp  # Add negative depressions
    
    # Normalize and scale to moderate hilly forest range with good elevation variation
    h = normalize01(h_with_forest_features, allow_depth=True) * 0.35  # Increased from 0.30 for more elevation
    
    return h.astype(np.float32)

def base_arctic(seed=-1) -> np.ndarray:
    """
    Generate a base arctic biome - soft hilly tundra and snow-covered peaks.
    
    Creates a hilly arctic landscape with multi-scale elevation variation and
    Gaussian blobs for natural global height differences. Uses smoothed multi-scale noise.
    
    Args:
        seed: Random seed for deterministic generation (-1 = auto-generate random seed)
        
    Returns:
        512x512 heightmap array (normalized 0-1)
    """
    import random
    
    # Auto-generate random seed if seed is -1
    if seed == -1:
        seed = random.randint(0, 2**31 - 1)
    
    from ..utils.noise import fractal_noise
    from scipy.ndimage import gaussian_filter
    
    xx, yy = np.meshgrid(np.arange(RES), np.arange(RES))
    
    # Large-scale arctic hills (multi-octave for natural variation)
    large_hills = fractal_noise(
        xx, yy,
        octaves=4,  # Multi-scale resolution
        persistence=0.3,  # Lower persistence = smoother
        lacunarity=2.0,
        scale=112.0,  # Large arctic hills
        seed=seed
    )
    
    # Medium-scale valleys and ridges (multi-octave)
    medium_features = fractal_noise(
        xx, yy,
        octaves=3,  # Multi-scale resolution
        persistence=0.25,  # Lower persistence = smoother
        lacunarity=2.4,
        scale=56.0,  # Medium valleys/ridges
        seed=seed + 1000
    )
    
    # Small-scale detail (multi-octave but very smooth for arctic)
    small_detail = fractal_noise(
        xx, yy,
        octaves=2,  # Multi-scale resolution
        persistence=0.15,  # Very low persistence = very smooth detail
        lacunarity=3.0,
        scale=28.0,  # Small detail
        seed=seed + 2000
    )
    
    # Combine: large hills (65%) + medium features (30%) + detail (5%)
    combined = large_hills * 0.65 + medium_features * 0.3 + small_detail * 0.05
    
    # Apply Gaussian smoothing for soft, gentle hills (extra smooth for arctic)
    h = gaussian_filter(combined, sigma=8.0)  # Smooth out the hills
    
    # Add Gaussian blobs for natural global height differences (snow-covered peaks)
    rng = random.Random(seed + 5000)
    h_with_blobs = h.copy()
    
    # Add 3-5 Gaussian peaks of varying sizes for natural global variation
    num_peaks = rng.randint(3, 6)
    for _ in range(num_peaks):
        cx = rng.randint(RES // 4, 3 * RES // 4)
        cy = rng.randint(RES // 4, 3 * RES // 4)
        radius = rng.randint(40, 100)
        height = rng.uniform(0.10, 0.18)  # Higher peaks for arctic
        
        # Gaussian falloff
        dx = xx - cx
        dy = yy - cy
        dist_sq = dx*dx + dy*dy
        sigma = radius / 2.0
        blob = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
        h_with_blobs += blob
    
    # Normalize and scale to higher arctic elevation with hills
    h = normalize01(h_with_blobs) * 0.25 + 0.5  # Higher base (snow level) with hills
    
    return h.astype(np.float32)

