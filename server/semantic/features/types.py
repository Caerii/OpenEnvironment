"""
Feature type constants and groups.

Provides canonical feature types and texture contribution mappings.
"""

from typing import Dict, List, Set

# Canonical feature types (should match FeatureRegistry)
ALL_FEATURE_TYPES = [
    "mountain", "valley", "dunes", "cliff", "plateau", "canyon",
    "hill", "mesa", "slope", "crater", "ridge", "ravine",
    "volcano", "pass", "mound", "basin", "pinnacle", "spur", "terraces"
]

# Feature type groups (for texture contribution)
ROCK_FEATURES: Set[str] = {"mountain", "cliff"}
SAND_FEATURES: Set[str] = {"dunes", "dune"}  # Handle both singular and plural
GRASS_FEATURES: Set[str] = {"valley", "plateau"}
SNOW_FEATURES: Set[str] = {"mountain"}  # High elevation features

# Feature-to-texture contribution mapping
# Maps feature types to their typical texture contributions (normalized 0-1)
FEATURE_TEXTURE_CONTRIBUTION: Dict[str, Dict[str, float]] = {
    "mountain": {"rock": 0.4, "snow": 0.2, "grass": 0.1},
    "dunes": {"sand": 0.6, "rock": 0.1},
    "dune": {"sand": 0.6, "rock": 0.1},  # Singular form
    "cliff": {"rock": 0.7, "grass": 0.1},
    "valley": {"grass": 0.5, "rock": 0.2},
    "plateau": {"grass": 0.4, "rock": 0.3},
    "canyon": {"rock": 0.6, "grass": 0.2},
    "hill": {"grass": 0.4, "rock": 0.3},
    "mesa": {"rock": 0.5, "grass": 0.3},
}

# Helper functions
def get_features_for_texture(texture_name: str) -> List[str]:
    """
    Get feature types that contribute to a texture.
    
    Args:
        texture_name: Texture name ("grass", "rock", "sand", "snow")
    
    Returns:
        List of feature types that contribute to this texture
    """
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

def is_grass_feature(feat_type: str) -> bool:
    """Check if feature contributes to grass texture."""
    return feat_type in GRASS_FEATURES

def is_snow_feature(feat_type: str) -> bool:
    """Check if feature contributes to snow texture."""
    return feat_type in SNOW_FEATURES

def get_texture_contribution(feat_type: str, texture_name: str) -> float:
    """
    Get texture contribution value for a feature type.
    
    Args:
        feat_type: Feature type
        texture_name: Texture name
    
    Returns:
        Contribution value (0.0-1.0), or 0.0 if no contribution
    """
    contribs = FEATURE_TEXTURE_CONTRIBUTION.get(feat_type, {})
    return contribs.get(texture_name, 0.0)



