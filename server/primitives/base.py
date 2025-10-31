"""Base biome generation functions."""
import numpy as np
from noise import pnoise2
from ..utils import normalize01

RES = 512

def base_flat(seed=0) -> np.ndarray:
    """
    Generate a perfectly flat base terrain (for reset functionality).
    
    Args:
        seed: Random seed (unused, kept for consistency)
        
    Returns:
        512x512 heightmap array (all zeros, normalized to 0-1 range)
    """
    h = np.zeros((RES, RES), dtype=np.float32)
    return h

def base_desert(seed=0) -> np.ndarray:
    """
    Generate a base desert biome - low, mostly flat, dune-friendly.
    
    Improved with multi-octave noise (4 octaves) for better natural variation.
    
    Args:
        seed: Random seed for deterministic generation
        
    Returns:
        512x512 heightmap array (normalized 0-1)
    """
    h = np.zeros((RES, RES), dtype=np.float32)
    
    # Improved: Multi-octave noise for natural variation
    # Research-backed parameters: 4 octaves, persistence=0.5, lacunarity=2.0
    amplitude = 1.0
    frequency = 1.0 / 512.0
    persistence = 0.5
    lacunarity = 2.0
    octaves = 4
    
    for y in range(RES):
        for x in range(RES):
            noise_value = 0.0
            amp = amplitude
            freq = frequency
            
            for i in range(octaves):
                n = pnoise2(x * freq, y * freq, octaves=1,
                           repeatx=1024, repeaty=1024, base=seed + i)
                noise_value += amp * n
                amp *= persistence
                freq *= lacunarity
            
            # Normalize by max possible amplitude
            max_amplitude = sum([persistence ** i for i in range(octaves)])
            normalized = (noise_value / max_amplitude + 1.0) * 0.5  # [-1,1] -> [0,1]
            h[y, x] = 0.03 * normalized
    
    h = normalize01(h) * 0.15  # Keep it low
    return h

def base_forest(seed=0) -> np.ndarray:
    """
    Generate a base forest biome - slightly rolling hills.
    
    Args:
        seed: Random seed for deterministic generation
        
    Returns:
        512x512 heightmap array (normalized 0-1)
    """
    h = np.zeros((RES, RES), dtype=np.float32)
    for y in range(RES):
        for x in range(RES):
            h[y, x] = 0.05 * pnoise2(x/512.0, y/512.0, octaves=3, repeatx=1024, repeaty=1024, base=seed)
    h = normalize01(h) * 0.25  # Moderate elevation
    return h

def base_arctic(seed=0) -> np.ndarray:
    """
    Generate a base arctic biome - cold, smooth, glacier-friendly.
    
    Args:
        seed: Random seed for deterministic generation
        
    Returns:
        512x512 heightmap array (normalized 0-1)
    """
    h = np.zeros((RES, RES), dtype=np.float32)
    for y in range(RES):
        for x in range(RES):
            h[y, x] = 0.04 * pnoise2(x/512.0, y/512.0, octaves=2, repeatx=1024, repeaty=1024, base=seed)
    h = normalize01(h) * 0.3 + 0.5  # Higher base elevation (snow level)
    return h

