"""Mountain and hill generation primitives."""
import numpy as np
from noise import pnoise2
from ..utils import clamp01
from ..engine.config import RES

def generate_mountain(cx: int, cy: int, radius: int, height: float, steepness: float = 1.0,
                      use_noise: bool = True, seed: int = 0) -> np.ndarray:
    """
    Generate a mountain heightmap stamp with optional noise-based detail.
    
    Improved with research-backed techniques:
    - Multi-octave noise overlay for natural variation
    - Noise-based height variation to prevent uniform appearance
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius of mountain
        height: Peak height (0-1)
        steepness: Controls how steep the sides are (1.0 = normal, >1.0 = steeper)
        use_noise: Whether to add fractal noise detail (recommended)
        seed: Random seed for noise generation
        
    Returns:
        512x512 heightmap stamp (to be blended with terrain)
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist_sq = dx*dx + dy*dy
    
    # Gaussian falloff with steepness control
    sigma = max(1.0, radius / (2.0 * steepness))
    stamp = height * np.exp(-dist_sq / (2.0 * sigma * sigma))
    
    # Add fractal noise detail for natural variation
    if use_noise:
        # Generate noise overlay with multi-octave fractal noise
        # Scale noise based on distance from center (more noise at edges)
        dist = np.sqrt(dist_sq)
        dist_normalized = np.clip(dist / radius, 0.0, 1.0)
        
        # Noise is stronger at edges, weaker at peak
        noise_strength = dist_normalized * 0.1  # ±10% variation
        
        # Multi-octave noise for detail (4 octaves, persistence=0.5, lacunarity=2.0)
        amplitude = 1.0
        frequency = 0.01  # Low frequency for large-scale variation
        persistence = 0.5
        lacunarity = 2.0
        octaves = 4
        
        # Generate noise value for each pixel
        noise_map = np.zeros_like(xx, dtype=np.float32)
        
        for y in range(RES):
            for x in range(RES):
                noise_value = 0.0
                amp = amplitude
                freq = frequency
                
                for i in range(octaves):
                    n = pnoise2(x * freq, y * freq,
                               octaves=1, repeatx=1024, repeaty=1024,
                               base=seed + i)
                    noise_value += amp * n
                    amp *= persistence
                    freq *= lacunarity
                
                noise_map[y, x] = noise_value
        
        # Normalize noise
        max_amplitude = sum([persistence ** i for i in range(octaves)])
        noise_normalized = (noise_map / max_amplitude + 1.0) * 0.5  # [-1,1] -> [0,1]
        
        # Apply noise variation (centered around 1.0)
        noise_factor = 1.0 + noise_strength * (noise_normalized - 0.5) * 2.0
        stamp = stamp * noise_factor
    
    return stamp

def generate_hill(cx: int, cy: int, radius: int, height: float) -> np.ndarray:
    """
    Generate a gentle hill heightmap stamp.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius
        height: Peak height (0-1)
        
    Returns:
        512x512 heightmap stamp
    """
    # Hills are just gentler mountains
    return generate_mountain(cx, cy, radius, height, steepness=0.7)

def generate_mesa(cx: int, cy: int, radius: int, height: float, flatness: float = 0.3) -> np.ndarray:
    """
    Generate a mesa (flat-topped hill) heightmap stamp.
    
    Args:
        cx, cy: Center coordinates
        radius: Base radius
        height: Top height (0-1)
        flatness: How flat the top is (0.0 = pointy, 1.0 = perfectly flat)
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    dist = np.sqrt(dx*dx + dy*dy)
    
    # Flat top with steep sides
    top_radius = radius * (1.0 - flatness)
    slope_radius = radius - top_radius
    
    stamp = np.zeros_like(dx, dtype=np.float32)
    
    # Flat top
    mask_top = dist <= top_radius
    stamp[mask_top] = height
    
    # Steep sides
    mask_slope = (dist > top_radius) & (dist <= radius)
    if np.any(mask_slope):
        slope_dist = dist[mask_slope] - top_radius
        slope_factor = 1.0 - (slope_dist / slope_radius)
        stamp[mask_slope] = height * slope_factor * 0.7  # Steep drop
    
    return stamp

def generate_plateau(cx: int, cy: int, width: int, length: int, height: float, orientation: float = 0.0) -> np.ndarray:
    """
    Generate a plateau (flat elevated area) heightmap stamp.
    
    Args:
        cx, cy: Center coordinates
        width: Width of plateau
        length: Length of plateau
        height: Elevation height (0-1)
        orientation: Rotation angle in degrees
        
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
    
    # Rectangular plateau with rounded edges
    wx, wy = width / 2.0, length / 2.0
    dist_x = np.abs(xr) / wx
    dist_y = np.abs(yr) / wy
    
    # Elliptical falloff
    dist_norm = np.sqrt(dist_x*dist_x + dist_y*dist_y)
    
    # Flat center with smooth falloff
    stamp = np.zeros_like(dx, dtype=np.float32)
    mask = dist_norm <= 1.0
    stamp[mask] = height
    
    # Smooth edge falloff
    mask_edge = (dist_norm > 1.0) & (dist_norm <= 1.5)
    if np.any(mask_edge):
        edge_dist = dist_norm[mask_edge] - 1.0
        edge_factor = np.exp(-edge_dist * 3.0)  # Sharp falloff
        stamp[mask_edge] = height * edge_factor
    
    return stamp

