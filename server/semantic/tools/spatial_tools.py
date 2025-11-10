"""
Spatial calculation tools.

These tools help calculate positions for spatial relationships like
"near", "between", "around", and handle multi-position patterns.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def calculate_position(
    scene_state: Dict,
    reference_ids: Optional[List[int]] = None,
    relationship: str = "near",
    region: Optional[str] = None,
    offset_distance: int = 80
) -> Dict[str, Any]:
    """
    Calculate target position based on spatial reasoning.
    
    Handles various spatial relationships:
    - "near": Close to reference (within offset_distance)
    - "between": Midpoint between references
    - "around": Position in circular pattern around reference
    - "north_of", "south_of", "east_of", "west_of": Directional offsets
    - By region: "left", "center", "right", "top", "bottom", etc.
    
    Args:
        scene_state: Current terrain state
        reference_ids: Feature IDs to use as reference (optional)
        relationship: Type of spatial relationship
        region: Explicit region if no reference ("center", "left", etc.)
        offset_distance: Distance for directional offsets (default: 80)
        
    Returns:
        {
            "position": [x, y],
            "region": str,
            "calculation_method": str
        }
    """
    try:
        if reference_ids is not None and not isinstance(reference_ids, list):
            reference_ids = [reference_ids]
        
        # If explicit region specified, use that
        if region and not reference_ids:
            pos = _region_to_position(region)
            return {
                "position": pos,
                "region": region,
                "calculation_method": "explicit_region"
            }
        
        # Get reference positions
        if reference_ids:
            features = scene_state.get("features", [])
            positions = []
            for feat in features:
                if feat.get("id") in reference_ids:
                    x = feat.get("x")
                    y = feat.get("y")
                    if x is not None and y is not None:
                        positions.append((x, y))
            
            if not positions:
                # Fallback to center
                return {
                    "position": [256, 256],
                    "region": "center",
                    "calculation_method": "fallback_center",
                    "warning": "No valid reference positions found"
                }
            
            # Calculate based on relationship
            if relationship == "near":
                # Near = slight offset from centroid
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                # Add small random-ish offset
                offset_x = (avg_x * 7) % 40 - 20  # Deterministic "random"
                offset_y = (avg_y * 11) % 40 - 20
                pos = [
                    max(0, min(511, avg_x + offset_x)),
                    max(0, min(511, avg_y + offset_y))
                ]
                
            elif relationship == "between":
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                pos = [avg_x, avg_y]
                
            elif relationship == "north_of":
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                pos = [avg_x, max(0, avg_y - offset_distance)]
                
            elif relationship == "south_of":
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                pos = [avg_x, min(511, avg_y + offset_distance)]
                
            elif relationship == "east_of":
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                pos = [min(511, avg_x + offset_distance), avg_y]
                
            elif relationship == "west_of":
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                pos = [max(0, avg_x - offset_distance), avg_y]
                
            else:
                # Default to centroid
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                pos = [avg_x, avg_y]
            
            region_name = _determine_region(pos[0], pos[1])
            return {
                "position": pos,
                "region": region_name,
                "calculation_method": f"spatial_{relationship}"
            }
        
        # No references, use center as default
        return {
            "position": [256, 256],
            "region": "center",
            "calculation_method": "default_center"
        }
        
    except Exception as e:
        logger.error(f"calculate_position failed: {e}", exc_info=True)
        return {
            "position": [256, 256],
            "region": "center",
            "calculation_method": "error_fallback",
            "error": str(e)
        }


def calculate_region_positions(
    scene_state: Optional[Dict],
    count: int,
    reference_ids: Optional[List[int]] = None,
    pattern: str = "scattered",
    radius: int = 100,
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate multiple positions based on spatial pattern.
    
    Patterns:
    - "scattered": Random-ish positions in region
    - "circular": Positions around reference point
    - "line": Positions along a line
    - "grid": Evenly spaced grid
    
    Args:
        count: Number of positions to generate
        scene_state: Current terrain state (optional)
        reference_ids: Feature IDs for reference point (optional)
        pattern: Distribution pattern
        radius: Radius for circular pattern (default: 100)
        region: Region for scattered pattern
        
    Returns:
        {
            "count": int,
            "positions": List[[x, y]],
            "pattern": str,
            "center": [x, y]
        }
    """
    try:
        if reference_ids is not None and not isinstance(reference_ids, list):
            reference_ids = [reference_ids]

        # Determine center point
        center_x, center_y = 256, 256
        
        if reference_ids and scene_state:
            features = scene_state.get("features", [])
            positions = []
            for feat in features:
                if feat.get("id") in reference_ids:
                    x = feat.get("x")
                    y = feat.get("y")
                    if x is not None and y is not None:
                        positions.append((x, y))
            
            if positions:
                center_x = sum(p[0] for p in positions) // len(positions)
                center_y = sum(p[1] for p in positions) // len(positions)
        
        elif region:
            center_x, center_y = _region_to_position(region)
        
        # Generate positions based on pattern
        positions = []
        
        if pattern == "circular":
            for i in range(count):
                angle = (2 * math.pi * i) / count
                x = int(center_x + radius * math.cos(angle))
                y = int(center_y + radius * math.sin(angle))
                x = max(0, min(511, x))
                y = max(0, min(511, y))
                positions.append([x, y])
                
        elif pattern == "line":
            for i in range(count):
                t = i / max(1, count - 1)  # 0 to 1
                x = int(center_x + (t - 0.5) * radius * 2)
                y = center_y
                x = max(0, min(511, x))
                positions.append([x, y])
                
        elif pattern == "grid":
            grid_size = math.ceil(math.sqrt(count))
            spacing = radius // max(1, grid_size - 1)
            for i in range(count):
                row = i // grid_size
                col = i % grid_size
                x = center_x + (col - grid_size // 2) * spacing
                y = center_y + (row - grid_size // 2) * spacing
                x = max(0, min(511, x))
                y = max(0, min(511, y))
                positions.append([x, y])
                
        else:  # scattered (default)
            for i in range(count):
                # Deterministic "random" scatter
                offset_x = ((center_x + i * 37) % (radius * 2)) - radius
                offset_y = ((center_y + i * 53) % (radius * 2)) - radius
                x = max(0, min(511, center_x + offset_x))
                y = max(0, min(511, center_y + offset_y))
                positions.append([x, y])
        
        return {
            "count": len(positions),
            "positions": positions,
            "pattern": pattern,
            "center": [center_x, center_y]
        }
        
    except Exception as e:
        logger.error(f"calculate_region_positions failed: {e}", exc_info=True)
        return {
            "count": 0,
            "positions": [],
            "pattern": pattern,
            "error": str(e)
        }


def get_region_bounds(region: str) -> Dict[str, Any]:
    """
    Get coordinate bounds for a named region.
    
    Useful for understanding what "left", "center", "top-right", etc. mean
    in terms of actual coordinates.
    
    Args:
        region: Region name (e.g., "left", "center", "top-right")
        
    Returns:
        {
            "region": str,
            "bounds": {"min_x": int, "max_x": int, "min_y": int, "max_y": int},
            "center": [x, y]
        }
    """
    # Define region bounds
    region_map = {
        "left": {"min_x": 0, "max_x": 170, "min_y": 0, "max_y": 511},
        "center": {"min_x": 170, "max_x": 341, "min_y": 0, "max_y": 511},
        "right": {"min_x": 341, "max_x": 511, "min_y": 0, "max_y": 511},
        "top": {"min_x": 0, "max_x": 511, "min_y": 0, "max_y": 170},
        "middle": {"min_x": 0, "max_x": 511, "min_y": 170, "max_y": 341},
        "bottom": {"min_x": 0, "max_x": 511, "min_y": 341, "max_y": 511},
        "top-left": {"min_x": 0, "max_x": 170, "min_y": 0, "max_y": 170},
        "top-center": {"min_x": 170, "max_x": 341, "min_y": 0, "max_y": 170},
        "top-right": {"min_x": 341, "max_x": 511, "min_y": 0, "max_y": 170},
        "center-left": {"min_x": 0, "max_x": 170, "min_y": 170, "max_y": 341},
        "center-center": {"min_x": 170, "max_x": 341, "min_y": 170, "max_y": 341},
        "center-right": {"min_x": 341, "max_x": 511, "min_y": 170, "max_y": 341},
        "bottom-left": {"min_x": 0, "max_x": 170, "min_y": 341, "max_y": 511},
        "bottom-center": {"min_x": 170, "max_x": 341, "min_y": 341, "max_y": 511},
        "bottom-right": {"min_x": 341, "max_x": 511, "min_y": 341, "max_y": 511},
    }
    
    bounds = region_map.get(region, region_map["center"])
    center_x = (bounds["min_x"] + bounds["max_x"]) // 2
    center_y = (bounds["min_y"] + bounds["max_y"]) // 2
    
    return {
        "region": region,
        "bounds": bounds,
        "center": [center_x, center_y]
    }


def _region_to_position(region: str) -> Tuple[int, int]:
    """Convert region name to coordinates."""
    bounds_info = get_region_bounds(region)
    return tuple(bounds_info["center"])


def _determine_region(x: int, y: int) -> str:
    """Determine region from coordinates."""
    region_x = "left" if x < 170 else ("center" if x < 341 else "right")
    region_y = "top" if y < 170 else ("center" if y < 341 else "bottom")
    
    if region_y == "center" and region_x == "center":
        return "center"
    elif region_y == "center":
        return region_x
    elif region_x == "center":
        return region_y
    else:
        return f"{region_y}-{region_x}"

