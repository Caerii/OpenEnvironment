"""
Terrain archetypes - geological story templates.

These archetypes represent different geological narratives that can guide
coherent terrain generation. Each archetype combines process, mood, and
typical feature patterns.
"""

from typing import List
from .types import (
    TerrainArchetype,
    GeologicalProcess,
    AestheticGoal
)


# Core 6 Primitives for reference:
# 1. Mountain - Hero elevation (rock + snow)
# 2. Valley - Hero depression (grass + balance)
# 3. Dunes - Sand texture (ONLY source via dune_mask)
# 4. Cliff - Vertical drama (rock via cliff_mask)
# 5. Plateau - Flat zones (gameplay + unique geometry)
# 6. Canyon - Linear exploration (water stories)


TERRAIN_ARCHETYPES = {
    "wind_architect": TerrainArchetype(
        name="Wind Architect",
        description="Wind-sculpted deserts with dunes, mesas, and wind-carved formations",
        primary_process=GeologicalProcess.AEOLIAN_DEPOSITION,
        secondary_processes=[
            GeologicalProcess.AEOLIAN_EROSION,
            GeologicalProcess.MECHANICAL_WEATHERING
        ],
        typical_aesthetics=[
            AestheticGoal.VAST,
            AestheticGoal.SMOOTH,
            AestheticGoal.WARM,
            AestheticGoal.ORGANIC
        ],
        
        # Feature preferences
        primary_features=["dunes"],  # Dunes are THE defining feature
        secondary_features=["mesa", "plateau"],  # Erosion-resistant outcrops
        accent_features=["cliff"],  # Wind-carved cliffs
        
        # Parameter biases
        height_range=(0.2, 0.7),  # Generally moderate heights
        scale_bias=1.3,  # Larger, more majestic features
        smoothness_bias=1.5,  # Wind creates smooth forms
        
        # Spatial patterns
        clustering_tendency=0.7,  # Dunes cluster in dune fields
        directional_alignment=45.0,  # Aligned with prevailing wind (NE → SW)
        
        # Splatmap preferences
        preferred_textures={
            "grass": 0.10,  # Minimal vegetation
            "rock": 0.25,  # Exposed rock outcrops
            "sand": 0.60,  # Dominant sand
            "snow": 0.05   # Rare (high mesa tops)
        }
    ),
    
    "waters_legacy": TerrainArchetype(
        name="Water's Legacy",
        description="Ancient river valleys, canyons, and water-carved landscapes",
        primary_process=GeologicalProcess.FLUVIAL_EROSION,
        secondary_processes=[
            GeologicalProcess.ALLUVIAL_DEPOSITION,
            GeologicalProcess.CHEMICAL_WEATHERING
        ],
        typical_aesthetics=[
            AestheticGoal.LAYERED,
            AestheticGoal.DRAMATIC,
            AestheticGoal.INVITING,
            AestheticGoal.ORGANIC
        ],
        
        # Feature preferences
        primary_features=["valley", "canyon"],  # Water-carved features
        secondary_features=["plateau", "cliff"],  # Erosion-resistant caps
        accent_features=["mountain"],  # Surrounding highlands
        
        # Parameter biases
        height_range=(0.1, 0.8),  # Wide range (deep valleys, high plateaus)
        scale_bias=1.0,  # Natural scale
        smoothness_bias=0.7,  # Water creates some roughness
        
        # Spatial patterns
        clustering_tendency=0.4,  # Features spread along drainage
        directional_alignment=None,  # Varies with topography
        
        # Splatmap preferences
        preferred_textures={
            "grass": 0.40,  # Lush valley floors
            "rock": 0.35,  # Canyon walls
            "sand": 0.15,  # River deposits
            "snow": 0.10   # High peaks
        }
    ),
    
    "ancient_uplift": TerrainArchetype(
        name="Ancient Uplift",
        description="Tectonic mountains, fault scarps, and uplifted plateaus",
        primary_process=GeologicalProcess.TECTONIC_UPLIFT,
        secondary_processes=[
            GeologicalProcess.FAULT_DISPLACEMENT,
            GeologicalProcess.GLACIAL_CARVING
        ],
        typical_aesthetics=[
            AestheticGoal.MONUMENTAL,
            AestheticGoal.RUGGED,
            AestheticGoal.DRAMATIC,
            AestheticGoal.HARSH
        ],
        
        # Feature preferences
        primary_features=["mountain"],  # Dominant peaks
        secondary_features=["cliff", "plateau"],  # Fault scarps, uplifted blocks
        accent_features=["valley"],  # Glacial valleys
        
        # Parameter biases
        height_range=(0.4, 0.95),  # Tall, dramatic
        scale_bias=1.2,  # Massive features
        smoothness_bias=0.4,  # Very rugged
        
        # Spatial patterns
        clustering_tendency=0.6,  # Mountains cluster in ranges
        directional_alignment=None,  # Linear along fault zones
        
        # Splatmap preferences
        preferred_textures={
            "grass": 0.15,  # Sparse vegetation
            "rock": 0.45,  # Dominant exposed rock
            "sand": 0.05,  # Minimal
            "snow": 0.35   # Snow-capped peaks
        }
    ),
    
    "volcanic_birth": TerrainArchetype(
        name="Volcanic Birth",
        description="Volcanic cones, lava plateaus, and geothermal landscapes",
        primary_process=GeologicalProcess.VOLCANIC_FORMATION,
        secondary_processes=[
            GeologicalProcess.TECTONIC_UPLIFT,
            GeologicalProcess.CHEMICAL_WEATHERING
        ],
        typical_aesthetics=[
            AestheticGoal.DRAMATIC,
            AestheticGoal.GEOMETRIC,
            AestheticGoal.HARSH,
            AestheticGoal.MONUMENTAL
        ],
        
        # Feature preferences
        primary_features=["mountain"],  # Volcanic cones (use mountain)
        secondary_features=["plateau"],  # Lava plateaus
        accent_features=["cliff", "canyon"],  # Erosion features
        
        # Parameter biases
        height_range=(0.3, 0.9),  # Varied (plateaus to cones)
        scale_bias=1.1,  # Moderately large
        smoothness_bias=0.5,  # Rough lava textures
        
        # Spatial patterns
        clustering_tendency=0.5,  # Can be clustered or isolated
        directional_alignment=None,  # Radial around vents
        
        # Splatmap preferences
        preferred_textures={
            "grass": 0.10,  # Limited vegetation
            "rock": 0.60,  # Dominant lava rock
            "sand": 0.10,  # Ash deposits
            "snow": 0.20   # High peaks
        }
    ),
    
    "depositional_plains": TerrainArchetype(
        name="Depositional Plains",
        description="Gentle plains with subtle relief from sediment deposition",
        primary_process=GeologicalProcess.ALLUVIAL_DEPOSITION,
        secondary_processes=[
            GeologicalProcess.LACUSTRINE_DEPOSITION,
            GeologicalProcess.AEOLIAN_DEPOSITION
        ],
        typical_aesthetics=[
            AestheticGoal.SERENE,
            AestheticGoal.VAST,
            AestheticGoal.SMOOTH,
            AestheticGoal.INVITING
        ],
        
        # Feature preferences
        primary_features=["valley"],  # Gentle depressions
        secondary_features=["dunes"],  # Minor sand deposits
        accent_features=["plateau"],  # Isolated mesas
        
        # Parameter biases
        height_range=(0.05, 0.4),  # Low relief
        scale_bias=1.5,  # Broad, gentle features
        smoothness_bias=2.0,  # Very smooth
        
        # Spatial patterns
        clustering_tendency=0.3,  # Scattered
        directional_alignment=None,  # No strong alignment
        
        # Splatmap preferences
        preferred_textures={
            "grass": 0.60,  # Lush grasslands
            "rock": 0.10,  # Minimal
            "sand": 0.25,  # Some sandy areas
            "snow": 0.05   # Rare
        }
    ),
    
    "glacial_legacy": TerrainArchetype(
        name="Glacial Legacy",
        description="U-shaped valleys, moraines, and glacially-carved peaks",
        primary_process=GeologicalProcess.GLACIAL_CARVING,
        secondary_processes=[
            GeologicalProcess.TECTONIC_UPLIFT,
            GeologicalProcess.MECHANICAL_WEATHERING
        ],
        typical_aesthetics=[
            AestheticGoal.DRAMATIC,
            AestheticGoal.RUGGED,
            AestheticGoal.COOL,
            AestheticGoal.MONUMENTAL
        ],
        
        # Feature preferences
        primary_features=["valley"],  # U-shaped glacial valleys
        secondary_features=["mountain"],  # Carved peaks
        accent_features=["plateau", "cliff"],  # Hanging valleys, cirques
        
        # Parameter biases
        height_range=(0.2, 0.9),  # High relief
        scale_bias=1.3,  # Large scale
        smoothness_bias=0.6,  # Mix of smooth valleys and rough peaks
        
        # Spatial patterns
        clustering_tendency=0.5,  # Linear along glacial paths
        directional_alignment=None,  # Follow valley orientation
        
        # Splatmap preferences
        preferred_textures={
            "grass": 0.25,  # Alpine meadows
            "rock": 0.35,  # Exposed bedrock
            "sand": 0.05,  # Glacial till
            "snow": 0.35   # Abundant snow/ice
        }
    )
}


def get_archetype(name: str) -> TerrainArchetype:
    """
    Get terrain archetype by name.
    
    Args:
        name: Archetype name (case-insensitive, underscore or space)
        
    Returns:
        TerrainArchetype
        
    Raises:
        KeyError: If archetype not found
    """
    normalized = name.lower().replace(" ", "_").replace("-", "_")
    
    if normalized in TERRAIN_ARCHETYPES:
        return TERRAIN_ARCHETYPES[normalized]
    
    # Try matching by description
    for key, archetype in TERRAIN_ARCHETYPES.items():
        if normalized in archetype.name.lower() or normalized in archetype.description.lower():
            return archetype
    
    raise KeyError(f"Unknown archetype: {name}. Available: {list(TERRAIN_ARCHETYPES.keys())}")


def match_archetype_from_keywords(keywords: List[str]) -> TerrainArchetype:
    """
    Match archetype based on keywords in user command.
    
    Improved matching that:
    1. Checks for strong feature type combinations first
    2. Weights keywords by importance
    3. Considers archetype feature preferences
    
    Args:
        keywords: List of keywords from user command
        
    Returns:
        Best matching TerrainArchetype
    """
    keywords_lower = [k.lower() for k in keywords]
    
    # FIRST: Check for strong feature type combinations (override individual keywords)
    # Check for valley + hills/river combination (very strong signal for Water's Legacy)
    has_valley = "valley" in keywords_lower or "valleys" in keywords_lower
    has_hills = "hill" in keywords_lower or "hills" in keywords_lower
    has_river = "river" in keywords_lower or "rivers" in keywords_lower
    
    if has_valley and (has_hills or has_river):
        return TERRAIN_ARCHETYPES["waters_legacy"]
    
    if "dune" in keywords_lower or "dunes" in keywords_lower:
        if "desert" in keywords_lower or "sand" in keywords_lower:
            return TERRAIN_ARCHETYPES["wind_architect"]
    
    if "mountain" in keywords_lower or "mountains" in keywords_lower:
        if "peak" in keywords_lower or "peaks" in keywords_lower or "dramatic" in keywords_lower:
            return TERRAIN_ARCHETYPES["ancient_uplift"]
    
    if "volcano" in keywords_lower or "volcanic" in keywords_lower:
        return TERRAIN_ARCHETYPES["volcanic_birth"]
    
    if "glacier" in keywords_lower or "glacial" in keywords_lower:
        return TERRAIN_ARCHETYPES["glacial_legacy"]
    
    # Keyword weights (importance for matching)
    keyword_weights = {
        # Very strong signals
        "valley": 3.0,  # Very strong for Water's Legacy
        "river": 2.5,
        "dune": 3.0,   # Very strong for Wind Architect
        "dunes": 3.0,
        "desert": 2.5,
        "mountain": 2.0,
        "mountains": 2.0,
        "volcano": 3.0,
        "glacier": 3.0,
        
        # Moderate signals
        "canyon": 2.0,
        "sand": 2.0,
        "peak": 1.5,
        "peaks": 1.5,
        
        # Weak signals (could be multiple archetypes)
        "hill": 1.0,
        "hills": 1.0,
        "gentle": 1.0,
        "plain": 1.0,
        "plains": 1.0,
    }
    
    # Score each archetype based on keywords and feature preferences
    scores = {name: 0.0 for name in TERRAIN_ARCHETYPES.keys()}
    
    for keyword in keywords_lower:
        weight = keyword_weights.get(keyword, 1.0)
        
        # Check if keyword matches archetype's primary/secondary features
        for archetype_name, archetype in TERRAIN_ARCHETYPES.items():
            # Check primary features (higher weight)
            primary_features_lower = [f.lower() for f in archetype.primary_features]
            if keyword in primary_features_lower:
                scores[archetype_name] += weight * 2.0
            
            # Check secondary features (medium weight)
            secondary_features_lower = [f.lower() for f in archetype.secondary_features]
            if keyword in secondary_features_lower:
                scores[archetype_name] += weight * 1.0
            
            # Check accent features (lower weight)
            accent_features_lower = [f.lower() for f in archetype.accent_features]
            if keyword in accent_features_lower:
                scores[archetype_name] += weight * 0.5
    
    # Also check keyword map for additional matches
    keyword_map = {
        "desert": "wind_architect",
        "sand": "wind_architect",
        "sandy": "wind_architect",
        "wind": "wind_architect",
        "arid": "wind_architect",
        "water": "waters_legacy",
        "stream": "waters_legacy",
        "alpine": "ancient_uplift",
        "tectonic": "ancient_uplift",
        "lava": "volcanic_birth",
        "geothermal": "volcanic_birth",
        "grassland": "depositional_plains",
        "meadow": "depositional_plains",
        "ice": "glacial_legacy",
    }
    
    for keyword in keywords_lower:
        if keyword in keyword_map:
            weight = keyword_weights.get(keyword, 1.0)
            scores[keyword_map[keyword]] += weight
    
    # Get archetype with highest score
    best_archetype = max(scores, key=scores.get)
    
    if scores[best_archetype] == 0:
        # No matches, default to wind_architect (most visually distinct)
        return TERRAIN_ARCHETYPES["wind_architect"]
    
    return TERRAIN_ARCHETYPES[best_archetype]

