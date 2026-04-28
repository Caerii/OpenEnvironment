"""Spatial resolution - Interprets position commands."""
from typing import Tuple, Optional, List, Dict
from ...engine.spatial import region_box, random_point_in, random_points_in, clamp_coords
from ...engine.config import RES

def resolve_position(position_spec: Optional[Dict], existing_features: List[Dict] = None, 
                    constraints = None, seed: int = 0) -> Tuple[int, int]:
    """
    Resolve a position specification to actual coordinates.
    
    Args:
        position_spec: Dictionary with "region", "coords", or relative positioning (or None)
        existing_features: List of existing features for relative positioning
        seed: Random seed for deterministic generation
        
    Returns:
        (x, y) coordinates
    """
    if existing_features is None:
        existing_features = []
    
    if position_spec is None:
        position_spec = {}
    
    # Direct coordinates
    if "coords" in position_spec and position_spec["coords"]:
        coords = position_spec["coords"]
        return clamp_coords(coords[0], coords[1])
    
    # Region-based
    if "region" in position_spec and position_spec["region"]:
        box = region_box(position_spec["region"])
        return random_point_in(box, seed)
    
    # Relative positioning (future)
    if "relative" in position_spec:
        return _resolve_relative(position_spec["relative"], existing_features, seed)
    
    # Default to center
    box = region_box("center")
    return random_point_in(box, seed)

def resolve_multiple_positions(position_spec: Optional[Dict], count: int, 
                               existing_features: List[Dict] = None,
                               min_distance: int = 20, constraints = None, seed: int = 0) -> List[Tuple[int, int]]:
    """
    Resolve multiple positions (e.g., "scattered", "three hills").
    
    Args:
        position_spec: Position specification or None
        count: Number of positions needed
        existing_features: Existing features for spacing
        min_distance: Minimum distance between positions
        seed: Random seed for deterministic generation
        
    Returns:
        List of (x, y) coordinates
    """
    if existing_features is None:
        existing_features = []
    
    if position_spec is None:
        position_spec = {}
    
    # Scattered distribution
    if position_spec.get("distribution") == "scattered":
        # Use entire terrain
        box = (0, 0, RES, RES)
        return random_points_in(box, count, min_distance, seed)
    
    # Region-based
    if "region" in position_spec and position_spec["region"]:
        box = region_box(position_spec["region"])
        return random_points_in(box, count, min_distance, seed)
    
    # Default to center region
    box = region_box("center")
    return random_points_in(box, count, min_distance, seed)

def _resolve_relative(relative_spec: Dict, existing_features: List[Dict], seed: int = 0) -> Tuple[int, int]:
    """
    Resolve relative positioning (e.g., "next to mountain", "between hills").
    
    Args:
        relative_spec: Relative positioning specification
        existing_features: Existing features to reference
        seed: Random seed for deterministic generation
        
    Returns:
        (x, y) coordinates
    """
    # TODO: Implement relative positioning logic
    # Examples:
    # - "next_to": {"type": "mountain", "id": 1, "direction": "north"}
    # - "between": {"type": "mountain", "ids": [1, 2]}
    # - "along_edge": {"edge": "north"}
    
    # For now, default to center
    box = region_box("center")
    return random_point_in(box, seed)

