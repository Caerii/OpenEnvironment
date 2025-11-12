"""
Configuration constants for semantic terrain generation.

Centralizes all magic numbers, thresholds, and default values.
"""

from typing import Dict, List, Set

# Import terrain resolution from engine config
try:
    from ..engine.config import RES as TERRAIN_RESOLUTION
except ImportError:
    TERRAIN_RESOLUTION = 512  # Fallback

# Terrain bounds
TERRAIN_CENTER_X = TERRAIN_RESOLUTION // 2
TERRAIN_CENTER_Y = TERRAIN_RESOLUTION // 2
TERRAIN_BOUNDS_MIN = 32
TERRAIN_BOUNDS_MAX = TERRAIN_RESOLUTION - 32

# Texture Analysis Thresholds
TEXTURE_COVERAGE_THRESHOLDS: Dict[str, float] = {
    "grass": 0.15,
    "rock": 0.10,
    "sand": 0.05,
    "snow": 0.05,
}

TEXTURE_DIFF_THRESHOLD = 0.05  # 5% difference threshold for feature contribution
TEXTURE_GAP_MIN_PIXELS = 10  # Minimum gap size to report
MAX_FEATURES_TO_ANALYZE = 5  # Limit texture analysis depth (expensive operation)
NEARBY_FEATURE_RADIUS = 50  # Pixels - radius for finding nearby features
MAX_NEARBY_FEATURES_TO_SUGGEST = 2  # Top N features to suggest changes for

# Parameter Modification Strategies
# Format: {texture: {feature_type: {parameter: percentage_change}}}
PARAMETER_MODIFICATION_STRATEGIES: Dict[str, Dict[str, Dict[str, float]]] = {
    "sand": {
        "dunes": {"radius_percent": 0.2, "min_increment": 20, "max_increment": 50}
    },
    "rock": {
        "mountain": {"radius_percent": 0.15, "min_increment": 15, "max_increment": 40},
        "cliff": {"radius_percent": 0.15, "min_increment": 15, "max_increment": 40}
    },
    "grass": {
        "valley": {"radius_percent": 0.1, "min_increment": 10, "max_increment": 30}
    }
}

# Quality Evaluation Defaults
DEFAULT_QUALITY_THRESHOLD = 0.8
DEFAULT_MAX_REFINEMENTS = 5
DEFAULT_MAX_REFINEMENT_ITERATIONS = 5

# Feature Type Groups
ROCK_FEATURES: Set[str] = {"mountain", "cliff"}
SAND_FEATURES: Set[str] = {"dunes", "dune"}  # Handle both singular and plural
GRASS_FEATURES: Set[str] = {"valley", "plateau"}
SNOW_FEATURES: Set[str] = {"mountain"}  # High elevation features

# Feature-to-Texture Contribution Mapping
# Maps feature types to their typical texture contributions
FEATURE_TEXTURE_CONTRIBUTION: Dict[str, Dict[str, float]] = {
    "mountain": {"rock": 0.4, "snow": 0.2, "grass": 0.1},
    "dunes": {"sand": 0.6, "rock": 0.1},
    "dune": {"sand": 0.6, "rock": 0.1},  # Singular form
    "cliff": {"rock": 0.7, "grass": 0.1},
    "valley": {"grass": 0.5, "rock": 0.2},
    "plateau": {"grass": 0.4, "rock": 0.3},
}

# Default Values
DEFAULT_SEED = 42
DEFAULT_POSITION_X = TERRAIN_CENTER_X
DEFAULT_POSITION_Y = TERRAIN_CENTER_Y

# Position Jitter (for micro-variation)
POSITION_JITTER_X_RANGE = (-6, 6)
POSITION_JITTER_Y_RANGE = (-5, 5)

# Refinement Limits
MAX_REFINEMENT_ITERATIONS_NORMAL = 5
MAX_REFINEMENT_ITERATIONS_FALLBACK = 3

# Helper Functions
def get_features_for_texture(texture_name: str) -> List[str]:
    """Get feature types that contribute to a texture."""
    return [
        feat_type for feat_type, contribs in FEATURE_TEXTURE_CONTRIBUTION.items()
        if texture_name in contribs and contribs[texture_name] > 0.1
    ]

def is_rock_feature(feat_type: str) -> bool:
    """Check if feature contributes to rock texture."""
    return feat_type in ROCK_FEATURES

def is_sand_feature(feat_type: str) -> bool:
    """Check if feature contributes to sand texture."""
    return feat_type in SAND_FEATURES

def get_parameter_modification(
    texture_gap: str,
    feature_type: str,
    current_radius: float
) -> Dict[str, float]:
    """
    Get parameter modification strategy for texture gap.
    
    Returns adaptive modification based on current radius.
    """
    strategy = PARAMETER_MODIFICATION_STRATEGIES.get(texture_gap, {}).get(feature_type)
    if not strategy:
        return {}
    
    # Calculate percentage-based change
    radius_percent = strategy.get("radius_percent", 0.15)
    change = current_radius * radius_percent
    
    # Clamp to min/max
    min_inc = strategy.get("min_increment", 10)
    max_inc = strategy.get("max_increment", 50)
    change = max(min_inc, min(max_inc, change))
    
    return {"radius": change}



