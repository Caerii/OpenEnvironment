"""Erosion system - Natural weathering and edge smoothing for terrain features."""
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation, binary_erosion
from ..utils import sobel_slope

def apply_edge_erosion(heightmap: np.ndarray, erosion_strength: float = 0.15,
                      erosion_radius: int = 3) -> np.ndarray:
    """
    Apply gentle erosion at feature edges to make them look more natural.
    
    This simulates weathering by slightly lowering heights at steep transitions
    and smoothing edges.
    
    Args:
        heightmap: Input heightmap (modified in-place)
        erosion_strength: How much to erode (0.0 = none, 1.0 = maximum)
        erosion_radius: Radius of erosion kernel (pixels)
    """
    # Calculate slope to find edges
    slope = sobel_slope(heightmap)
    
    # Find steep edges (where slope changes rapidly)
    # Use gradient of slope to detect edges
    gy, gx = np.gradient(slope)
    edge_strength = np.sqrt(gx*gx + gy*gy)
    edge_strength = edge_strength / (edge_strength.max() + 1e-6)
    
    # Create erosion mask (stronger erosion at steeper edges)
    erosion_mask = np.clip(edge_strength * 0.5 + slope * 0.5, 0.0, 1.0)
    
    # Apply slight height reduction at edges
    erosion_amount = erosion_strength * erosion_mask * 0.05  # Subtle effect
    heightmap[:] = np.clip(heightmap - erosion_amount, 0.0, 1.0)
    
    # Smooth edges slightly
    smoothed = gaussian_filter(heightmap, sigma=erosion_radius * 0.3)
    
    # Blend original with smoothed version based on edge strength
    blend_factor = erosion_mask * erosion_strength * 0.3
    heightmap[:] = heightmap * (1.0 - blend_factor) + smoothed * blend_factor


def apply_slope_erosion(heightmap: np.ndarray, erosion_amount: float = 0.02) -> np.ndarray:
    """
    Apply erosion based on slope (steeper areas erode more).
    
    Simulates natural weathering where steeper slopes are more exposed.
    
    Args:
        heightmap: Input heightmap (modified in-place)
        erosion_amount: Base erosion amount
    """
    slope = sobel_slope(heightmap)
    
    # Higher slopes erode more (exponential relationship)
    erosion_factor = np.power(slope, 1.5) * erosion_amount
    
    # Apply erosion
    heightmap[:] = np.clip(heightmap - erosion_factor, 0.0, 1.0)
    
    # Smooth to blend eroded areas
    smoothed = gaussian_filter(heightmap, sigma=1.0)
    blend = erosion_factor / (erosion_amount + 1e-6)
    blend = np.clip(blend, 0.0, 0.5)  # Limit blending
    
    heightmap[:] = heightmap * (1.0 - blend) + smoothed * blend


def apply_feature_edge_feathering(stamp: np.ndarray, feather_radius: int = 5) -> np.ndarray:
    """
    Apply smooth feathering to feature edges before stamping.
    
    This prevents hard edges when features are placed on terrain.
    
    Args:
        stamp: Feature stamp to feather
        feather_radius: Radius of feathering (pixels)
        
    Returns:
        Feather-stamped heightmap
    """
    # Detect edges of stamp (where value changes from 0)
    edge_mask = (stamp > 0.01) & (stamp < 0.99)
    
    if not np.any(edge_mask):
        return stamp
    
    # Create distance transform from edges
    from scipy.ndimage import distance_transform_edt
    
    # Binary mask of stamp
    binary_mask = stamp > 0.01
    
    # Distance from edges
    dist_from_edge = distance_transform_edt(binary_mask)
    
    # Feather mask: smooth transition at edges
    feather_mask = np.clip(dist_from_edge / feather_radius, 0.0, 1.0)
    
    # Apply feathering
    result = stamp * feather_mask
    
    # Preserve center values (don't feather everything)
    center_mask = dist_from_edge > feather_radius
    result[center_mask] = stamp[center_mask]
    
    return result

