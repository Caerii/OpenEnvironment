"""Stamping engine - Places primitives onto terrain heightmap."""
import numpy as np
from typing import Optional
from ..utils import clamp01
from scipy.ndimage import gaussian_filter, distance_transform_edt

RES = 512

class BlendingMode:
    """Blending mode constants."""
    MAX = "max"          # Take maximum (mountains/hills merge upward)
    MIN = "min"          # Take minimum (valleys carve downward)
    ADD = "add"          # Add heights (accumulative)
    SUBTRACT = "subtract" # Subtract heights (carving)
    WEIGHTED = "weighted" # Weighted average
    REPLACE = "replace"  # Replace existing (no blending)

def stamp_primitive(h: np.ndarray, stamp: np.ndarray, mode: str = BlendingMode.MAX) -> None:
    """
    Stamp a primitive onto the heightmap using specified blending mode.
    
    Args:
        h: Heightmap to modify (in-place)
        stamp: Primitive stamp to apply
        mode: Blending mode (see BlendingMode)
    """
    if mode == BlendingMode.MAX:
        np.maximum(h, stamp, out=h)
    elif mode == BlendingMode.MIN:
        np.minimum(h, stamp, out=h)
    elif mode == BlendingMode.ADD:
        # Allow values to exceed 1.0 for tall mountains
        h[:] = h + stamp
    elif mode == BlendingMode.SUBTRACT:
        # Allow values to go below 0.0 for deep valleys (no clipping!)
        h[:] = h - stamp
    elif mode == BlendingMode.WEIGHTED:
        # Weighted blend: 70% existing, 30% new
        h[:] = 0.7*h + 0.3*stamp
    elif mode == BlendingMode.REPLACE:
        # Replace where stamp is non-zero
        mask = stamp > 0.001
        h[mask] = stamp[mask]
    else:
        # Default to max
        np.maximum(h, stamp, out=h)

def blend_features(h: np.ndarray, stamps: list, modes: list = None) -> None:
    """
    Apply multiple stamps with their respective blending modes.
    
    Args:
        h: Heightmap to modify (in-place)
        stamps: List of primitive stamps
        modes: List of blending modes (defaults to MAX for all)
    """
    if modes is None:
        modes = [BlendingMode.MAX] * len(stamps)
    
    for stamp, mode in zip(stamps, modes):
        stamp_primitive(h, stamp, mode)

def apply_smoothing(h: np.ndarray, sigma: float = 0.8) -> None:
    """
    Apply Gaussian smoothing to blend seams.
    
    Args:
        h: Heightmap to smooth (in-place)
        sigma: Smoothing radius
    """
    h[:] = gaussian_filter(h, sigma=sigma)

def apply_adaptive_smoothing(h: np.ndarray, base_sigma: float = 0.8,
                            feature_mask: Optional[np.ndarray] = None,
                            preserve_edges: bool = True) -> None:
    """
    Apply feature-aware adaptive smoothing that preserves feature boundaries.
    
    Uses distance transforms to identify edges and applies less smoothing
    near edges, more smoothing in flat areas.
    
    Research-backed technique: Preserves sharp features (cliffs) while
    smoothing flat areas for natural appearance.
    
    Args:
        h: Heightmap to smooth (in-place)
        base_sigma: Base smoothing radius
        feature_mask: Optional binary mask marking feature areas (for edge detection)
        preserve_edges: Whether to preserve sharp edges (cliffs, steep slopes)
    """
    if not preserve_edges:
        # Simple uniform smoothing if not preserving edges
        apply_smoothing(h, base_sigma)
        return
    
    # Calculate slope to identify steep areas
    from ..utils import sobel_slope
    slope = sobel_slope(h)
    
    # Identify steep edges (cliffs, steep slopes)
    # Use threshold to find areas that should be preserved
    steep_threshold = 0.4  # Adjust based on desired edge sharpness
    steep_mask = slope > steep_threshold
    
    # Calculate distance from steep edges
    # This determines how much smoothing to apply
    dist_from_edge = distance_transform_edt(~steep_mask)
    
    # Adaptive sigma: less smoothing near edges, more in flat areas
    # Smoothing radius increases with distance from edge
    edge_distance_threshold = 10.0  # Pixels
    
    # Apply variable smoothing using multiple passes with different sigma
    # For simplicity, use a weighted approach based on distance
    smoothed_full = gaussian_filter(h, sigma=base_sigma * 1.5)  # More smoothing in flat areas
    smoothed_edge = gaussian_filter(h, sigma=base_sigma * 0.3)   # Less smoothing near edges
    
    # Blend based on distance from edge
    blend_factor = np.clip(dist_from_edge / edge_distance_threshold, 0.0, 1.0)
    blend_factor = blend_factor ** 2  # Smooth transition
    
    # Apply adaptive smoothing
    h[:] = smoothed_edge * (1.0 - blend_factor) + smoothed_full * blend_factor
