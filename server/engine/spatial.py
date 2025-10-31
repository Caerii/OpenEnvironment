"""Spatial utilities - Position resolution and region handling."""
from typing import Tuple, List
import numpy as np

RES = 512

def region_box(keyword: str) -> Tuple[int, int, int, int]:
    """
    Convert spatial keyword to bounding box coordinates.
    
    Args:
        keyword: Region name (e.g., "top-left", "center", "right")
        
    Returns:
        (x0, y0, x1, y1) bounding box
    """
    T = RES // 3
    regions = {
        "top-left":      (0, 0, T, T),
        "top":           (T, 0, 2*T, T),
        "top-right":     (2*T, 0, RES, T),
        "left":          (0, T, T, 2*T),
        "center":        (T, T, 2*T, 2*T),
        "right":         (2*T, T, RES, 2*T),
        "bottom-left":   (0, 2*T, T, RES),
        "bottom":        (T, 2*T, 2*T, RES),
        "bottom-right":  (2*T, 2*T, RES, RES),
    }
    return regions.get(keyword, (T, T, 2*T, 2*T))  # Default to center

def random_point_in(box: Tuple[int, int, int, int], seed: int = 0) -> Tuple[int, int]:
    """
    Generate a deterministic random point within a bounding box.
    
    Args:
        box: (x0, y0, x1, y1) bounding box
        seed: Random seed for deterministic generation
        
    Returns:
        (x, y) coordinates
    """
    x0, y0, x1, y1 = box
    rng = np.random.RandomState(seed)
    return (rng.randint(x0, x1), rng.randint(y0, y1))

def random_points_in(box: Tuple[int, int, int, int], count: int, 
                     min_distance: int = 10, seed: int = 0) -> List[Tuple[int, int]]:
    """
    Generate multiple deterministic random points with minimum spacing.
    
    Args:
        box: (x0, y0, x1, y1) bounding box
        count: Number of points to generate
        min_distance: Minimum distance between points
        seed: Random seed for deterministic generation
        
    Returns:
        List of (x, y) coordinates
    """
    x0, y0, x1, y1 = box
    rng = np.random.RandomState(seed)
    points = []
    
    max_attempts = count * 10  # More attempts for better distribution
    for attempt in range(max_attempts):
        if len(points) >= count:
            break
        
        # Generate point with deterministic seed
        point_seed = (seed + attempt * 17) % (2**31)
        point_rng = np.random.RandomState(point_seed)
        point = (point_rng.randint(x0, x1), point_rng.randint(y0, y1))
        
        # Check minimum distance
        valid = True
        for existing in points:
            dx = point[0] - existing[0]
            dy = point[1] - existing[1]
            if dx*dx + dy*dy < min_distance*min_distance:
                valid = False
                break
        
        if valid:
            points.append(point)
    
    return points[:count]

def clamp_coords(x: int, y: int) -> Tuple[int, int]:
    """Clamp coordinates to valid range."""
    return (max(0, min(RES-1, x)), max(0, min(RES-1, y)))

