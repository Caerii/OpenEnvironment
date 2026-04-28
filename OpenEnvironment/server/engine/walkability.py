"""Walkability heuristics for terrain navigation.

Provides cost-based and threshold-based walkability analysis using:
- Slope gradient (steepness)
- Terrain type (from splatmap: grass, rock, sand, snow)
- Feature masks (cliffs, dunes)
- Height-based restrictions
"""
import numpy as np
from typing import Tuple, Optional, Dict
from scipy.ndimage import gaussian_filter
from ..utils import sobel_slope


class WalkabilityConfig:
    """Configuration for walkability heuristics."""
    
    def __init__(
        self,
        # Slope thresholds (0-1, where 1.0 = maximum gradient)
        max_walkable_slope: float = 0.6,  # ~35° max walkable
        impassable_slope: float = 0.85,   # ~50° impassable (cliffs)
        steep_penalty_slope: float = 0.4, # ~22° starts getting difficult
        
        # Terrain type multipliers (1.0 = normal, >1.0 = harder)
        grass_cost: float = 1.0,      # Easy walking
        sand_cost: float = 1.3,       # Slightly harder (sinking)
        rock_cost: float = 1.8,       # Much harder (uneven)
        snow_cost: float = 2.0,       # Very hard (slippery, deep)
        
        # Feature-specific penalties
        cliff_penalty: float = 10.0,  # Massive cost (effectively impassable)
        dune_penalty: float = 1.2,    # Moderate penalty (soft sand)
        
        # Height restrictions (0-1 normalized)
        min_height: Optional[float] = None,  # Below sea level / too deep
        max_height: Optional[float] = None,    # Too high (altitude sickness)
        
        # Smoothing
        smooth_costs: bool = True,
        smoothing_sigma: float = 1.0
    ):
        self.max_walkable_slope = max_walkable_slope
        self.impassable_slope = impassable_slope
        self.steep_penalty_slope = steep_penalty_slope
        self.grass_cost = grass_cost
        self.sand_cost = sand_cost
        self.rock_cost = rock_cost
        self.snow_cost = snow_cost
        self.cliff_penalty = cliff_penalty
        self.dune_penalty = dune_penalty
        self.min_height = min_height
        self.max_height = max_height
        self.smooth_costs = smooth_costs
        self.smoothing_sigma = smoothing_sigma


# Default configuration (human walkability)
DEFAULT_CONFIG = WalkabilityConfig()

# Easier configuration (for vehicles/robots)
VEHICLE_CONFIG = WalkabilityConfig(
    max_walkable_slope=0.4,  # ~22° max
    impassable_slope=0.6,    # ~35° impassable
    steep_penalty_slope=0.25,
    sand_cost=1.5,           # Vehicles struggle in sand
    snow_cost=3.0            # Vehicles very difficult in snow
)

# More lenient configuration (for agile characters)
AGILE_CONFIG = WalkabilityConfig(
    max_walkable_slope=0.75,  # ~48° max (climbing)
    impassable_slope=0.95,    # ~72° impassable
    steep_penalty_slope=0.5,
    rock_cost=1.4,           # Better at rock climbing
    snow_cost=1.5
)


def calculate_walkability_cost(
    heightmap: np.ndarray,
    splatmap: Optional[np.ndarray] = None,
    cliff_mask: Optional[np.ndarray] = None,
    dune_mask: Optional[np.ndarray] = None,
    config: WalkabilityConfig = DEFAULT_CONFIG
) -> np.ndarray:
    """
    Calculate movement cost map for pathfinding.
    
    Lower values = easier to walk, higher values = harder/impassable.
    Values typically range from 1.0 (easy) to 10.0+ (impassable).
    
    Args:
        heightmap: 512x512 heightmap (0-1 normalized)
        splatmap: Optional 512x512x4 RGBA splatmap (grass, rock, sand, snow)
        cliff_mask: Optional 512x512 mask marking cliff areas (0-1)
        dune_mask: Optional 512x512 mask marking dune areas (0-1)
        config: Walkability configuration
        
    Returns:
        512x512 cost map (higher = harder to traverse)
    """
    costs = np.ones_like(heightmap, dtype=np.float32)
    
    # 1. Slope-based cost (steep = harder)
    slope = sobel_slope(heightmap)
    
    # Impassable areas (very steep)
    impassable_mask = slope > config.impassable_slope
    costs[impassable_mask] = config.cliff_penalty
    
    # Steep penalty (difficult but walkable)
    steep_mask = (slope > config.steep_penalty_slope) & ~impassable_mask
    # Quadratic penalty: cost increases with slope
    slope_factor = ((slope[steep_mask] - config.steep_penalty_slope) / 
                    (config.max_walkable_slope - config.steep_penalty_slope))
    costs[steep_mask] += slope_factor * 2.0  # Up to 3x cost
    
    # Above max walkable slope (but not impassable) = very high cost
    too_steep_mask = (slope > config.max_walkable_slope) & ~impassable_mask
    costs[too_steep_mask] += 5.0
    
    # 2. Terrain type multipliers (from splatmap)
    if splatmap is not None:
        grass = splatmap[:, :, 0]
        rock = splatmap[:, :, 1]
        sand = splatmap[:, :, 2]
        snow = splatmap[:, :, 3]
        
        # Weighted terrain cost based on texture blending
        terrain_cost = (
            grass * config.grass_cost +
            rock * config.rock_cost +
            sand * config.sand_cost +
            snow * config.snow_cost
        )
        costs *= terrain_cost
    
    # 3. Feature-specific penalties
    if cliff_mask is not None:
        cliff_mask_normalized = np.clip(cliff_mask, 0.0, 1.0)
        # Strong penalty where cliffs exist
        costs += cliff_mask_normalized * config.cliff_penalty
    
    if dune_mask is not None:
        dune_mask_normalized = np.clip(dune_mask, 0.0, 1.0)
        # Moderate penalty for dunes
        costs += dune_mask_normalized * (config.dune_penalty - 1.0)
    
    # 4. Height restrictions
    if config.min_height is not None:
        too_low = heightmap < config.min_height
        costs[too_low] += 3.0  # Penalty for too low (water, deep valleys)
    
    if config.max_height is not None:
        too_high = heightmap > config.max_height
        costs[too_high] += 2.0  # Penalty for too high (altitude)
    
    # 5. Smooth costs for more natural pathfinding
    if config.smooth_costs:
        costs = gaussian_filter(costs, sigma=config.smoothing_sigma)
    
    return costs


def calculate_walkability_mask(
    heightmap: np.ndarray,
    splatmap: Optional[np.ndarray] = None,
    cliff_mask: Optional[np.ndarray] = None,
    config: WalkabilityConfig = DEFAULT_CONFIG
) -> np.ndarray:
    """
    Calculate binary walkability mask (walkable vs impassable).
    
    Args:
        heightmap: 512x512 heightmap (0-1 normalized)
        splatmap: Optional 512x512x4 RGBA splatmap
        cliff_mask: Optional 512x512 cliff mask
        config: Walkability configuration
        
    Returns:
        512x512 boolean mask (True = walkable, False = impassable)
    """
    slope = sobel_slope(heightmap)
    
    # Start with slope-based walkability
    walkable = slope <= config.max_walkable_slope
    
    # Cliffs are impassable
    if cliff_mask is not None:
        cliff_areas = cliff_mask > 0.3  # Threshold for cliff detection
        walkable = walkable & ~cliff_areas
    
    # Very steep slopes are impassable
    very_steep = slope > config.impassable_slope
    walkable = walkable & ~very_steep
    
    # Height restrictions
    if config.min_height is not None:
        too_low = heightmap < config.min_height
        walkable = walkable & ~too_low
    
    if config.max_height is not None:
        too_high = heightmap > config.max_height
        walkable = walkable & ~too_high
    
    return walkable


def calculate_difficulty_zones(
    heightmap: np.ndarray,
    splatmap: Optional[np.ndarray] = None,
    cliff_mask: Optional[np.ndarray] = None,
    dune_mask: Optional[np.ndarray] = None,
    config: WalkabilityConfig = DEFAULT_CONFIG
) -> Dict[str, np.ndarray]:
    """
    Calculate difficulty zones for visualization/analysis.
    
    Returns:
        Dictionary with zone masks:
        - "easy": Easy terrain (cost < 1.5)
        - "moderate": Moderate difficulty (cost 1.5-3.0)
        - "hard": Hard terrain (cost 3.0-6.0)
        - "very_hard": Very hard (cost 6.0-10.0)
        - "impassable": Impassable (cost >= 10.0)
    """
    costs = calculate_walkability_cost(
        heightmap, splatmap, cliff_mask, dune_mask, config
    )
    
    return {
        "easy": costs < 1.5,
        "moderate": (costs >= 1.5) & (costs < 3.0),
        "hard": (costs >= 3.0) & (costs < 6.0),
        "very_hard": (costs >= 6.0) & (costs < 10.0),
        "impassable": costs >= 10.0
    }


def get_steepness_angle(slope_value: float, height_scale: float = 50.0) -> float:
    """
    Convert slope value (0-1) to angle in degrees.
    
    Args:
        slope_value: Normalized slope (0-1)
        height_scale: Height scale factor (meters per height unit)
        
    Returns:
        Angle in degrees
    """
    # Slope is gradient magnitude normalized to [0, 1]
    # Assuming 1 unit = 1 pixel, and height_scale meters per height unit
    # Gradient = dh/dx, so angle = arctan(gradient)
    # But we need to account for the normalization
    
    # Rough approximation: max slope of 1.0 ≈ 45° for typical terrain
    # More accurate: angle ≈ arctan(slope_value * height_scale / pixel_size)
    # For 512x512 terrain, pixel_size ≈ 1.0, so angle ≈ arctan(slope_value * height_scale)
    import math
    return math.degrees(math.atan(slope_value * height_scale / 1.0))


def find_walkable_path_cost(
    start: Tuple[int, int],
    end: Tuple[int, int],
    cost_map: np.ndarray,
    heuristic_weight: float = 1.0
) -> float:
    """
    Estimate path cost between two points using A* heuristic.
    
    This is a simple heuristic - for actual pathfinding, use a proper
    A* implementation with the cost_map.
    
    Args:
        start: (x, y) start position
        end: (x, y) end position
        cost_map: 512x512 cost map
        heuristic_weight: Weight for heuristic (1.0 = A*, >1.0 = weighted)
        
    Returns:
        Estimated total cost
    """
    sx, sy = start
    ex, ey = end
    
    # Manhattan distance heuristic
    dx = abs(ex - sx)
    dy = abs(ey - sy)
    manhattan_dist = dx + dy
    
    # Sample cost along straight-line path
    steps = max(dx, dy, 1)
    x_coords = np.linspace(sx, ex, steps).astype(int)
    y_coords = np.linspace(sy, ey, steps).astype(int)
    x_coords = np.clip(x_coords, 0, cost_map.shape[1] - 1)
    y_coords = np.clip(y_coords, 0, cost_map.shape[0] - 1)
    
    path_costs = cost_map[y_coords, x_coords]
    path_cost = np.sum(path_costs)
    
    # Heuristic estimate
    avg_cost = np.mean(cost_map)
    heuristic = manhattan_dist * avg_cost * heuristic_weight
    
    return path_cost + heuristic

