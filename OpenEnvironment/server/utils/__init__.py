"""Utility functions for terrain generation."""
import numpy as np
from scipy.ndimage import gaussian_filter

def normalize01(h: np.ndarray, allow_depth: bool = False) -> np.ndarray:
    """
    Normalize array to [0, 1] range with robust handling of edge cases.
    
    Handles:
    - Flat terrain (all same values)
    - NaN/Inf values
    - Empty arrays
    
    Args:
        h: Input array
        allow_depth: If True, preserves negative values for valleys and values > 1 for peaks
        
    Returns:
        Normalized array (with depth preservation if allow_depth=True)
    """
    h = np.asarray(h, dtype=np.float32)
    
    # Handle NaN and Inf
    if np.any(~np.isfinite(h)):
        h = np.nan_to_num(h, nan=0.0, posinf=1.0, neginf=0.0)
    
    # Handle empty or constant arrays
    h_min = h.min()
    h_max = h.max()
    
    if h_max == h_min:
        # Flat terrain - return zeros (or constant value if desired)
        return np.zeros_like(h)
    
    if allow_depth:
        # DON'T normalize when allowing depth - just return as-is
        # This preserves negative values for valleys and values > 1.0 for peaks
        # The shader will handle the extended range
        return h
    else:
        # Standard normalization to [0, 1]
        h_normalized = (h - h_min) / (h_max - h_min)
        # Clamp to [0, 1] (should be redundant but safe)
        h_normalized = np.clip(h_normalized, 0.0, 1.0)
        return h_normalized

def clamp01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 0.0, 1.0)

def smooth_mask(radius_px: int) -> np.ndarray:
    r = radius_px
    y, x = np.ogrid[-r:r+1, -r:r+1]
    d2 = x*x + y*y
    m = (d2 <= r*r).astype(np.float32)
    return gaussian_filter(m, sigma=radius_px*0.25)

def lerp(a, b, t):
    return a*(1.0-t) + b*t

def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    """
    Smooth interpolation function (industry standard for texture blending).
    
    Provides smoother transitions than linear interpolation.
    Returns 0.0 for x <= edge0, 1.0 for x >= edge1, smooth curve in between.
    
    Args:
        edge0: Lower edge
        edge1: Upper edge
        x: Input values
        
    Returns:
        Smoothly interpolated values [0, 1]
    """
    # Handle edge case where edge0 == edge1 (avoid divide by zero)
    if abs(edge1 - edge0) < 1e-8:
        return np.where(x <= edge0, 0.0, 1.0).astype(np.float32)
    
    t = (x - edge0) / (edge1 - edge0)
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def percentiles(h: np.ndarray, p_lo=90, p_hi=97):
    return np.percentile(h, p_lo), np.percentile(h, p_hi)

def sobel_slope(h: np.ndarray) -> np.ndarray:
    """
    Calculate slope proxy using gradient magnitude.
    
    Args:
        h: Heightmap array
        
    Returns:
        Normalized slope values [0, 1]
    """
    gy, gx = np.gradient(h.astype(np.float32))
    s = np.sqrt(gx*gx + gy*gy)
    s = s / (s.max() + 1e-8)
    return s

# Re-export noise functions for convenience
from .noise import fractal_noise

__all__ = [
    'normalize01',
    'clamp01',
    'smooth_mask',
    'lerp',
    'smoothstep',
    'percentiles',
    'sobel_slope',
    'fractal_noise'
]


