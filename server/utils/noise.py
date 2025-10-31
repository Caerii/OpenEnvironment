"""Multi-octave fractal noise functions for natural terrain generation."""
import numpy as np
from noise import pnoise2

def fractal_noise(x: np.ndarray, y: np.ndarray, octaves: int = 4, 
                  persistence: float = 0.5, lacunarity: float = 2.0,
                  scale: float = 1.0, seed: int = 0) -> np.ndarray:
    """
    Generate fractal Brownian motion (fBm) noise.
    
    This is the standard multi-octave noise function used in professional
    terrain generation. Each octave adds detail at a different frequency.
    
    Args:
        x, y: Coordinate arrays (can be meshgrids or scalars)
        octaves: Number of noise layers (4-8 recommended for terrain)
        persistence: Amplitude decrease per octave (0.3-0.7 recommended)
                     Lower = smoother, Higher = rougher
        lacunarity: Frequency increase per octave (1.5-3.0 recommended)
                    Higher = more detail variation
        scale: Base frequency scale
        seed: Random seed for deterministic generation
        
    Returns:
        Noise value array (typically in range [-1, 1] before normalization)
        
    Research References:
    - Octaves 4-8: General best practice for terrain detail
    - Persistence 0.3-0.7: Provides natural variation
    - Lacunarity 1.5-3.0: Standard range for terrain
    """
    if isinstance(x, (int, float)):
        x = np.array([x])
        y = np.array([y])
    
    value = np.zeros_like(x, dtype=np.float32)
    amplitude = 1.0
    frequency = scale
    
    for i in range(octaves):
        # Generate noise at this octave
        noise_values = np.zeros_like(x, dtype=np.float32)
        
        # Handle vectorized noise generation
        if x.ndim == 0:
            # Scalar case
            noise_values = pnoise2(x * frequency, y * frequency,
                                  base=seed + i)
        else:
            # Array case - iterate if needed
            flat_shape = x.shape
            flat_x = x.flatten()
            flat_y = y.flatten()
            flat_noise = np.array([
                pnoise2(flat_x[j] * frequency, flat_y[j] * frequency,
                       base=seed + i)
                for j in range(len(flat_x))
            ])
            noise_values = flat_noise.reshape(flat_shape)
        
        value += amplitude * noise_values
        amplitude *= persistence
        frequency *= lacunarity
    
    return value


def fractal_noise_2d(shape: tuple, octaves: int = 4,
                     persistence: float = 0.5, lacunarity: float = 2.0,
                     scale: float = 1.0, seed: int = 0) -> np.ndarray:
    """
    Generate 2D fractal noise heightmap.
    
    Convenience function for generating fractal noise over a grid.
    
    Args:
        shape: (height, width) of output array
        octaves: Number of noise layers (4-8 recommended)
        persistence: Amplitude decrease per octave (0.3-0.7)
        lacunarity: Frequency increase per octave (1.5-3.0)
        scale: Base frequency scale (lower = larger features)
        seed: Random seed
        
    Returns:
        2D noise array (shape, dtype=np.float32)
    """
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    
    # Normalize coordinates to [0, 1] range
    x_norm = xx / max(w, h)
    y_norm = yy / max(w, h)
    
    # Generate fractal noise
    noise = np.zeros((h, w), dtype=np.float32)
    
    amplitude = 1.0
    frequency = scale
    
    for i in range(octaves):
        octave_noise = np.zeros((h, w), dtype=np.float32)
        
        for y in range(h):
            for x in range(w):
                octave_noise[y, x] = pnoise2(
                    x_norm[y, x] * frequency,
                    y_norm[y, x] * frequency,
                    octaves=1,  # Single octave per iteration
                    repeatx=1024,
                    repeaty=1024,
                    base=seed + i
                )
        
        noise += amplitude * octave_noise
        amplitude *= persistence
        frequency *= lacunarity
    
    return noise


def ridge_noise(x: np.ndarray, y: np.ndarray, octaves: int = 4,
                persistence: float = 0.5, lacunarity: float = 2.0,
                scale: float = 1.0, seed: int = 0) -> np.ndarray:
    """
    Generate ridge noise (abs of fractal noise) for mountain ranges.
    
    Creates sharp ridges and valleys, useful for mountain ranges.
    
    Args:
        x, y: Coordinate arrays
        octaves: Number of noise layers
        persistence: Amplitude decrease per octave
        lacunarity: Frequency increase per octave
        scale: Base frequency scale
        seed: Random seed
        
    Returns:
        Ridge noise array (positive values, sharper peaks)
    """
    noise = fractal_noise(x, y, octaves, persistence, lacunarity, scale, seed)
    # Convert to ridges: abs() creates sharp peaks
    return np.abs(noise)

