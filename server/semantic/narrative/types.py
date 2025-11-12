"""
Type definitions for the narrative generation system.

These types represent the core data structures used for geological storytelling,
aesthetic reasoning, and terrain composition.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, TYPE_CHECKING
from enum import Enum

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from domain.models import Feature
else:
    # At runtime, use absolute import
    try:
        from domain.models import Feature
    except ImportError:
        # Fallback for when running tests
        Feature = Any  # type: ignore


class AestheticGoal(Enum):
    """Aesthetic qualities that terrain can embody."""
    # Scale & Drama
    DRAMATIC = "dramatic"
    VAST = "vast"
    INTIMATE = "intimate"
    MONUMENTAL = "monumental"
    
    # Mood & Atmosphere
    SERENE = "serene"
    MYSTERIOUS = "mysterious"
    HARSH = "harsh"
    INVITING = "inviting"
    DESOLATE = "desolate"
    
    # Visual Qualities
    RUGGED = "rugged"
    SMOOTH = "smooth"
    ORGANIC = "organic"
    GEOMETRIC = "geometric"
    LAYERED = "layered"
    
    # Color & Texture
    WARM = "warm"
    COOL = "cool"
    VARIED = "varied"
    UNIFORM = "uniform"


class GeologicalProcess(Enum):
    """Primary geological processes that shape terrain."""
    # Water-based
    FLUVIAL_EROSION = "fluvial_erosion"        # River/stream cutting
    GLACIAL_CARVING = "glacial_carving"        # Ice sculpting
    LACUSTRINE_DEPOSITION = "lacustrine"       # Lake deposits
    
    # Wind-based
    AEOLIAN_DEPOSITION = "aeolian_deposition"  # Wind-blown sand
    AEOLIAN_EROSION = "aeolian_erosion"        # Wind scouring
    
    # Tectonic
    TECTONIC_UPLIFT = "tectonic_uplift"        # Mountain building
    VOLCANIC_FORMATION = "volcanic"            # Lava flows, cones
    FAULT_DISPLACEMENT = "fault_displacement"  # Cliff/scarp formation
    
    # Weathering
    CHEMICAL_WEATHERING = "chemical"           # Dissolution, oxidation
    MECHANICAL_WEATHERING = "mechanical"       # Freeze-thaw, thermal
    
    # Depositional
    ALLUVIAL_DEPOSITION = "alluvial"           # River deposits
    COLLUVIAL_DEPOSITION = "colluvial"         # Slope deposits


@dataclass
class TerrainArchetype:
    """
    Represents a terrain archetype - a geological story template.
    
    Archetypes combine process, mood, and typical feature patterns
    to guide coherent terrain generation.
    """
    name: str
    description: str
    primary_process: GeologicalProcess
    secondary_processes: List[GeologicalProcess]
    typical_aesthetics: List[AestheticGoal]
    
    # Feature preferences (which primitives to favor)
    primary_features: List[str]  # ["mountain", "valley", ...]
    secondary_features: List[str]
    accent_features: List[str]
    
    # Parameter biases
    height_range: Tuple[float, float]  # (min, max) typical heights
    scale_bias: float  # 0.0-2.0, affects radii/spacing (1.0 = default)
    smoothness_bias: float  # 0.0-2.0, affects noise/weathering (1.0 = default)
    
    # Spatial patterns
    clustering_tendency: float  # 0.0-1.0, how much features group
    directional_alignment: Optional[float]  # 0-360 degrees, or None
    
    # Splatmap preferences
    preferred_textures: Dict[str, float]  # {"grass": 0.3, "rock": 0.4, ...}


@dataclass
class TerrainNarrative:
    """
    Complete terrain narrative - the geological story guiding generation.
    
    This is the output of develop_terrain_narrative and input to other tools.
    """
    # Core narrative
    archetype: TerrainArchetype
    story: str  # Human-readable geological story
    
    # Aesthetic intent
    aesthetic_goals: List[AestheticGoal]
    mood: List[str]  # Free-form mood descriptors
    
    # Geological constraints
    primary_process: GeologicalProcess
    time_scale: str  # "young", "mature", "ancient"
    weathering_level: float  # 0.0-1.0 (fresh → heavily weathered)
    
    # Environmental parameters
    wind_direction: Optional[float]  # 0-360 degrees, if relevant
    water_flow_direction: Optional[float]  # 0-360 degrees, if relevant
    climate: str  # "arid", "temperate", "alpine", "tropical"
    
    # Feature guidance
    hero_feature_type: Optional[str]  # Primary focal point type
    supporting_feature_types: List[str]  # Supporting cast
    accent_feature_types: List[str]  # Contrast/variety
    
    # Composition hints
    focal_point_bias: Tuple[float, float]  # (x, y) normalized 0-1, or None for center
    depth_layers_needed: int  # 2-4 recommended
    negative_space_importance: float  # 0.0-1.0
    
    # Quality targets
    target_coherence: float  # 0.0-1.0, minimum acceptable score
    max_refinement_iterations: int  # How many iterations to try


@dataclass
class SpatialConstraints:
    """
    Spatial constraints derived from geological processes and narrative.
    
    These constrain where features CAN be placed for geological plausibility.
    """
    # Valid placement zones per feature type
    valid_zones: Dict[str, List[Tuple[int, int, int, int]]]  # type → [(x_min, x_max, y_min, y_max)]
    
    # Wind-related constraints
    wind_direction: Optional[float]
    wind_shadow_zones: List[Tuple[int, int, float]]  # [(x, y, radius)]
    windward_zones: List[Tuple[int, int, int, int]]  # [(x_min, x_max, y_min, y_max)]
    leeward_zones: List[Tuple[int, int, int, int]]
    
    # Water-related constraints
    flow_paths: List[List[Tuple[int, int]]]  # [[(x1,y1), (x2,y2), ...]]
    deposition_zones: List[Tuple[int, int, float]]  # [(x, y, radius)]
    erosion_zones: List[Tuple[int, int, float]]
    
    # Tectonic/structural constraints
    fault_lines: List[Tuple[int, int, int, int]]  # [(x1, y1, x2, y2)]
    uplift_zones: List[Tuple[int, int, float]]
    resistant_zones: List[Tuple[int, int, float]]  # Harder rock
    
    # Clustering constraints
    clustering_centers: List[Tuple[int, int]]  # Natural grouping points
    exclusion_zones: List[Tuple[int, int, float]]  # No features here
    
    # Directional alignment
    preferred_orientations: Dict[str, float]  # type → angle in degrees


@dataclass
class FeatureComposition:
    """
    Planned composition of features before generation.
    
    MIGRATION NOTE: Now uses typed Feature instead of Dict[str, Any]!
    This provides type safety and validation for narrative-generated features.
    """
    # Focal hierarchy (TYPED FEATURES!)
    focal_point: Optional['Feature']  # Typed Feature instance!
    supporting_features: List['Feature']  # List of typed Features!
    accent_features: List['Feature']  # List of typed Features!
    background_features: List['Feature']  # List of typed Features!
    foreground_features: List['Feature']  # List of typed Features!
    
    # Depth layers (for rendering/visual hierarchy)
    depth_layers: List[Dict[str, Any]]  # [{"z_order": 1, "feature_ids": [...]}, ...]
    
    # Negative space (intentional empty areas)
    negative_space_zones: List[Tuple[int, int, int, int]]  # [(x_min, x_max, y_min, y_max)]
    
    # Compositional principles applied
    golden_ratio_used: bool
    rule_of_thirds_used: bool
    leading_lines: List[Tuple[int, int, int, int]]  # Visual flow lines
    
    # Rhythm and repetition
    rhythmic_elements: List[List[str]]  # Groups of features forming patterns
    variation_pattern: str  # "decreasing", "increasing", "alternating", "random"


@dataclass
class CoherenceScores:
    """
    Quality scores for evaluating terrain coherence.
    
    This is the output of evaluate_narrative_coherence.
    """
    # Core quality dimensions (0.0-1.0)
    geological_plausibility: float  # Do features make geological sense?
    spatial_coherence: float        # Do features relate properly in space?
    aesthetic_quality: float        # Does it look good?
    splatmap_coverage: float       # Are all 4 RGBA channels well-used?
    walkability: float             # Can player navigate terrain?
    narrative_alignment: float     # Does it match the story?
    
    # Overall score (weighted average)
    overall: float
    
    # Detailed issues
    issues: List[Dict[str, str]]  # [{"type": "aesthetic", "severity": "medium", "description": "..."}]
    
    # Recommendations for improvement
    recommendations: List[Dict[str, Any]]  # [{"action": "add", "type": "dunes", ...}]
    
    # Metrics
    feature_count: int
    feature_density: float  # Features per unit area
    height_variation: float  # Std dev of heights
    clustering_score: float  # How clustered vs scattered


@dataclass
class ParameterInference:
    """
    Inferred parameters for a feature based on aesthetic goals and role.
    """
    # Inferred values
    height: Optional[float]
    radius: Optional[int]
    width: Optional[int]
    depth: Optional[float]
    steepness: Optional[float]
    spacing: Optional[int]
    direction: Optional[float]
    use_noise: Optional[bool]
    
    # Rationale
    rationale: str  # Why these parameters?
    
    # Confidence
    confidence: float  # 0.0-1.0


@dataclass
class NarrativeRefinement:
    """
    Refinement suggestions for improving terrain quality.
    
    This is the output of refine_narrative.
    """
    # Problems detected
    problems: List[Dict[str, Any]]  # Prioritized list of issues
    
    # Suggested fixes
    add_features: List[Dict[str, Any]]  # Features to add
    modify_features: List[Dict[str, Any]]  # Features to modify
    remove_features: List[int]  # Feature IDs to remove
    
    # Expected improvement
    expected_score_improvement: float  # Estimated score delta
    
    # Iteration strategy
    should_continue: bool  # More refinement needed?
    iteration_count: int
    max_iterations: int

