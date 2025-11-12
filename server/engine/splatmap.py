"""Splatmap generation - Creates RGBA texture blending maps with feature awareness."""
import numpy as np
from ..utils import sobel_slope, percentiles, smoothstep
from scipy.ndimage import gaussian_filter

def generate_splatmap(heightmap: np.ndarray, dune_mask: np.ndarray = None,
                      cliff_mask: np.ndarray = None) -> np.ndarray:
    """
    Generate an enhanced 4-channel RGBA splatmap from heightmap.
    
    Channel mapping:
    - R = Grass (lowlands, gentle slopes)
    - G = Rock (steep slopes, cliffs)
    - B = Sand (dunes, flat low areas)
    - A = Snow (high elevations)
    
    Enhanced with:
    - Smoothstep interpolation for smoother transitions (research-backed)
    - Distance-based texture blending (smooth transitions)
    - Feature-aware textures (rock near cliffs)
    - Aspect-based snow assignment (north-facing slopes)
    
    Args:
        heightmap: 512x512 heightmap (0-1 normalized)
        dune_mask: Optional mask marking dune areas (512x512, 0-1)
        cliff_mask: Optional mask marking cliff areas (512x512, 0-1)
        
    Returns:
        512x512x4 RGBA splatmap (normalized per-pixel)
    """
    if dune_mask is None:
        dune_mask = np.zeros_like(heightmap)
    if cliff_mask is None:
        cliff_mask = np.zeros_like(heightmap)
    
    slope = sobel_slope(heightmap)
    h90, h97 = percentiles(heightmap, 90, 97)
    
    # Calculate aspect (north-facing = cooler, snow sticks better)
    gy, gx = np.gradient(heightmap.astype(np.float32))
    aspect = np.arctan2(-gy, gx)  # Direction of steepest ascent
    # North-facing slopes have aspect near 0 or 2π
    north_factor = np.abs(np.cos(aspect))  # Higher for north-facing
    
    # Enhanced Rock: Steep slopes + cliff areas
    # Use smoothstep for smoother transitions
    rock_slope = smoothstep(0.30, 0.75, slope)
    rock_cliff = cliff_mask * 0.8  # Strong rock texture at cliffs
    rock = np.clip(rock_slope * 0.7 + rock_cliff, 0, 1)
    
    # Smooth rock transitions
    rock = gaussian_filter(rock, sigma=2.0)
    rock = np.clip(rock, 0, 1)
    
    # Enhanced Snow: High elevation with smooth falloff and aspect-based assignment
    # Snow sticks better on north-facing slopes
    snow_raw = smoothstep(h90, h97, heightmap)
    snow_slope_factor = np.clip(1.0 - slope * 0.5, 0.5, 1.0)
    snow_aspect_factor = 0.7 + 0.3 * north_factor  # Boost north-facing
    snow = snow_raw * snow_slope_factor * snow_aspect_factor
    snow = gaussian_filter(snow, sigma=3.0)  # Smooth snow transitions
    snow = np.clip(snow, 0, 1)
    
    # Enhanced Sand: Dunes + flat low areas with smooth blending
    flat_factor = smoothstep(0.0, 0.25, 0.25 - slope)  # Smoothstep for flat areas
    low_factor = smoothstep(0.0, 0.4, 0.4 - heightmap)  # Smoothstep for low areas
    flat_low = flat_factor * low_factor
    sand_dunes = dune_mask * 0.9
    sand = np.clip(0.7 * sand_dunes + 0.3 * flat_low, 0, 1)
    sand = gaussian_filter(sand, sigma=2.5)  # Smooth sand transitions
    sand = np.clip(sand, 0, 1)
    
    # Enhanced Grass: Everything else with priority ordering
    # Grass fills areas not strongly claimed by other textures
    grass_base = np.clip(1.0 - np.maximum(np.maximum(rock * 0.8, snow * 0.7), sand * 0.8), 0, 1)
    
    # Prefer grass on moderate slopes at moderate elevations
    grass_preference = np.clip((0.4 - np.abs(slope - 0.2)) / 0.4, 0, 1)
    grass_preference *= np.clip((0.6 - np.abs(heightmap - 0.3)) / 0.6, 0, 1)
    
    grass = np.clip(grass_base * 0.7 + grass_preference * 0.3, 0, 1)
    grass = gaussian_filter(grass, sigma=2.0)
    grass = np.clip(grass, 0, 1)
    
    # Stack RGBA channels
    splat = np.stack([grass, rock, sand, snow], axis=-1)  # (H,W,4)
    
    # Normalize per pixel (weights must sum to 1.0)
    s = splat.sum(axis=-1, keepdims=True) + 1e-6
    splat /= s
    
    return splat.astype(np.float32)
