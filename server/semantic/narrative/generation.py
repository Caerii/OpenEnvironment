"""
Feature generation from narrative - THE MISSING LINK!

Converts TerrainNarrative → typed Feature instances.
This is the critical bridge between geological storytelling and actual terrain generation.
"""

import random
from typing import List, Dict, Tuple, Optional, Any, Iterable
import logging

from ...bootstrap import ensure_bootstrapped

ensure_bootstrapped()

from server.domain.models import Feature, Position, FeatureParameters
from server.engine.feature_registry import FeatureRegistry
from ..evaluation import compute_feature_metrics, evaluate_aesthetic_quality

from .types import TerrainNarrative, FeatureComposition, GeologicalProcess

logger = logging.getLogger(__name__)


def _ensure_feature_instance(feat: Any) -> Optional[Feature]:
    if isinstance(feat, Feature):
        return feat
    if isinstance(feat, dict):
        try:
            return Feature.from_dict(feat)
        except Exception as exc:
            logger.warning(f"Failed to convert dict to Feature: {exc}")
    return None


def generate_from_narrative(
    narrative: TerrainNarrative,
    scene_state: Dict,
    seed: int = None
) -> FeatureComposition:
    """
    THE MISSING LINK: Convert narrative → typed Features.
    
    This tool generates actual terrain features based on the geological
    narrative, applying constraints, spatial reasoning, and aesthetic goals.
    
    Args:
        narrative: Terrain narrative with story, archetype, constraints
        scene_state: Current scene state (for context)
        seed: Random seed (default: use narrative seed)
    
    Returns:
        FeatureComposition with typed Feature instances (not dicts!)
    
    Example:
        narrative = develop_terrain_narrative("dramatic mountains", {}, seed=42)
        composition = generate_from_narrative(narrative, {}, seed=42)
        
        # composition.focal_point is a typed Feature!
        assert isinstance(composition.focal_point, Feature)
        assert composition.focal_point.type == "mountain"
    """
    
    if seed is None:
        seed = narrative.seed if hasattr(narrative, 'seed') else 42
    
    rng = random.Random(seed)
    
    logger.info(f"Generating features from narrative (archetype: {narrative.archetype.name})")
    
    # Step 1: Determine feature hierarchy based on archetype
    feature_hierarchy = _determine_feature_hierarchy(narrative, rng)
    
    # Step 2: Generate focal point (hero feature)
    focal_point = _generate_focal_feature(narrative, feature_hierarchy, rng, seed)
    
    # Step 3: Generate supporting features (context)
    supporting_features = _generate_supporting_features(
        narrative, feature_hierarchy, focal_point, rng, seed
    )
    
    # Step 4: Generate accent features (visual interest)
    accent_features = _generate_accent_features(
        narrative, feature_hierarchy, focal_point, supporting_features, rng, seed
    )

    supporting_features, accent_features = _enforce_composition_safeguards(
        narrative,
        feature_hierarchy,
        focal_point,
        supporting_features,
        accent_features,
        rng,
        seed,
    )

    # Step 5: Construct composition
    composition = FeatureComposition(
        focal_point=focal_point,
        supporting_features=supporting_features,
        accent_features=accent_features,
        background_features=[],  # TODO: Implement background generation
        foreground_features=[],  # TODO: Implement foreground generation
        depth_layers=[],  # TODO: Implement depth layering
        negative_space_zones=[],  # TODO: Implement negative space
        golden_ratio_used=True,  # We use golden ratio for focal placement
        rule_of_thirds_used=False,
        leading_lines=[],
        rhythmic_elements=[],
        variation_pattern="organic"  # Default: organic variation
    )
    
    logger.info(
        f"Generated composition: 1 focal, {len(supporting_features)} supporting, "
        f"{len(accent_features)} accent features"
    )
    
    return composition


def _determine_feature_hierarchy(
    narrative: TerrainNarrative,
    rng: random.Random
) -> Dict[str, List[str]]:
    """
    Determine which feature types to use based on archetype.
    
    Maps geological process → appropriate feature types.
    """
    
    archetype = narrative.archetype
    process = archetype.primary_process
    
    # Map process → feature types
    if process == GeologicalProcess.TECTONIC_UPLIFT:
        # Ancient Uplift archetype
        return {
            "focal": ["mountain"],
            "supporting": ["plateau", "cliff"],
            "accent": ["valley"]
        }
    
    elif process == GeologicalProcess.FLUVIAL_EROSION:
        # Water's Legacy archetype
        return {
            "focal": ["valley", "canyon"],
            "supporting": ["plateau"],
            "accent": ["mountain", "cliff"]
        }
    
    elif process == GeologicalProcess.AEOLIAN_DEPOSITION:
        # Wind Architect archetype
        return {
            "focal": ["dunes"],
            "supporting": ["plateau"],
            "accent": ["cliff"]
        }
    
    elif process == GeologicalProcess.VOLCANIC_FORMATION:
        # Volcanic Birth archetype
        return {
            "focal": ["mountain"],  # volcano-like
            "supporting": ["cliff", "plateau"],
            "accent": ["valley"]
        }
    
    else:
        # Default/generic
        return {
            "focal": ["mountain", "valley"],
            "supporting": ["plateau", "cliff"],
            "accent": ["dunes"]
        }


def _generate_focal_feature(
    narrative: TerrainNarrative,
    feature_hierarchy: Dict[str, List[str]],
    rng: random.Random,
    seed: int
) -> Feature:
    """
    Generate the focal point - the hero feature that dominates the composition.
    
    Uses golden ratio for placement: focal at (205, 136) for 512×512 terrain.
    """
    
    # Select focal type
    focal_types = feature_hierarchy["focal"]
    focal_type = rng.choice(focal_types)
    
    # Golden ratio position (φ ≈ 0.618)
    # For 512×512: 512 * 0.4 = 205, 512 * 0.266 = 136
    focal_x = 205
    focal_y = 136
    
    # Generate feature using FeatureRegistry (returns typed Feature!)
    generator = FeatureRegistry._generators.get(focal_type)
    if not generator:
        logger.warning(f"No generator for focal type: {focal_type}, using mountain")
        generator = FeatureRegistry._generators["mountain"]
        focal_type = "mountain"
    
    # Apply narrative constraints as modifiers
    modifiers = _extract_modifiers_from_narrative(narrative, "focal")
    
    feature = generator.create_feature(focal_x, focal_y, modifiers, seed)
    
    logger.debug(f"Created focal feature: {focal_type} at ({focal_x}, {focal_y})")
    
    return feature


def _generate_supporting_features(
    narrative: TerrainNarrative,
    feature_hierarchy: Dict[str, List[str]],
    focal_point: Feature,
    rng: random.Random,
    seed: int
) -> List[Feature]:
    """
    Generate supporting features that provide context and balance.
    
    Positioned around focal point to create composition.
    """
    focal_point = _ensure_feature_instance(focal_point)
    if focal_point is None:
        raise ValueError("Focal point could not be converted to Feature")

    supporting_features: List[Feature] = []
    supporting_types = feature_hierarchy["supporting"]
    if not supporting_types:
        return []
    
    # Generate 2-4 supporting features
    n_supporting = rng.randint(2, 4)
    
    for i in range(n_supporting):
        # Select type
        support_type = rng.choice(supporting_types)
        
        # Position around focal, avoiding overlap
        # Use circular placement at varied distances
        angle = (i / n_supporting) * 360 + rng.uniform(-30, 30)
        distance = rng.uniform(80, 150)
        
        x = int(focal_point.position.x + distance * _cos_deg(angle))
        y = int(focal_point.position.y + distance * _sin_deg(angle))
        
        # Clamp to terrain bounds
        x = max(50, min(460, x))
        y = max(50, min(460, y))
        
        # Generate feature
        generator = FeatureRegistry._generators.get(support_type)
        if not generator:
            continue
        
        modifiers = _extract_modifiers_from_narrative(narrative, "supporting")
        feature = generator.create_feature(x, y, modifiers, seed + i + 1)
        feature = _ensure_feature_instance(feature)
        if not feature:
            continue
        
        supporting_features.append(feature)
        logger.debug(f"Created supporting feature: {support_type} at ({x}, {y})")
    
    return supporting_features


def _generate_accent_features(
    narrative: TerrainNarrative,
    feature_hierarchy: Dict[str, List[str]],
    focal_point: Feature,
    supporting_features: List[Feature],
    rng: random.Random,
    seed: int
) -> List[Feature]:
    """
    Generate accent features for visual interest and detail.
    
    Smaller, more distributed features that add richness.
    """
    
    focal_point = _ensure_feature_instance(focal_point)
    supporting_features = [
        sf for sf in ( _ensure_feature_instance(feat) for feat in supporting_features)
        if sf is not None
    ]
    if focal_point is None:
        raise ValueError("Focal point could not be converted to Feature for accent generation")

    accent_features: List[Feature] = []
    accent_types = feature_hierarchy["accent"]
    if not accent_types:
        return []

    # Generate 1-3 accent features with retries so we actually place them
    n_accents = rng.randint(1, 3)

    for i in range(n_accents):
        placed = False
        for attempt in range(8):
            accent_type = rng.choice(accent_types)

            x = rng.randint(80, 430)
            y = rng.randint(80, 430)

            min_distance = 60
            dist_to_focal = _distance(x, y, focal_point.position.x, focal_point.position.y)
            if dist_to_focal < min_distance:
                continue

            too_close = False
            for support in supporting_features:
                dist = _distance(x, y, support.position.x, support.position.y)
                if dist < min_distance:
                    too_close = True
                    break

            if too_close:
                continue

            generator = FeatureRegistry._generators.get(accent_type)
            if not generator:
                continue

            modifiers = _extract_modifiers_from_narrative(narrative, "accent")
            feature = generator.create_feature(x, y, modifiers, seed + n_accents + i + attempt + 1)
            feature = _ensure_feature_instance(feature)
            if feature is None:
                continue

            accent_features.append(feature)
            logger.debug(f"Created accent feature: {accent_type} at ({x}, {y})")
            placed = True
            break

        if not placed:
            logger.debug("Failed to place accent feature after retries")
     
    return accent_features


def _enforce_composition_safeguards(
    narrative: TerrainNarrative,
    feature_hierarchy: Dict[str, List[str]],
    focal_point: Feature,
    supporting_features: List[Feature],
    accent_features: List[Feature],
    rng: random.Random,
    seed: int,
) -> Tuple[List[Feature], List[Feature]]:
    """Ensure supporting/accent features exist and provide variety."""

    supporting = list(supporting_features or [])
    accent = list(accent_features or [])

    if not supporting:
        logger.debug("No supporting features generated; attempting fallback")
        supporting = _generate_supporting_features(
            narrative,
            feature_hierarchy,
            focal_point,
            rng,
            seed + 101,
        )

    if not supporting:
        fallback_type = _pick_alternate_type(
            feature_hierarchy.get("supporting", []),
            default="plateau",
        )
        fallback_feature = _spawn_feature_near(
            fallback_type,
            focal_point,
            narrative,
            rng,
            seed + 202,
            distance_range=(90, 140),
        )
        if fallback_feature:
            supporting.append(fallback_feature)

    if not accent:
        logger.debug("No accent features generated; attempting fallback")
        accent = _generate_accent_features(
            narrative,
            feature_hierarchy,
            focal_point,
            supporting,
            rng,
            seed + 303,
        )

    if not accent:
        fallback_type = _pick_alternate_type(
            feature_hierarchy.get("accent", []),
            default="valley",
            avoid={focal_point.type},
        )
        fallback_feature = _spawn_feature_near(
            fallback_type,
            focal_point,
            narrative,
            rng,
            seed + 404,
            distance_range=(140, 200),
            random_position=True,
        )
        if fallback_feature:
            accent.append(fallback_feature)

    all_types = {focal_point.type}
    all_types.update(feat.type for feat in supporting)
    all_types.update(feat.type for feat in accent)

    if len(all_types) < 2:
        extra_type = _pick_alternate_type(
            feature_hierarchy.get("accent", []) + feature_hierarchy.get("supporting", []),
            default="dunes",
            avoid=all_types,
        )
        extra_feature = _spawn_feature_near(
            extra_type,
            focal_point,
            narrative,
            rng,
            seed + 505,
            distance_range=(130, 210),
            random_position=True,
        )
        if extra_feature:
            accent.append(extra_feature)

    return supporting, accent


def _pick_alternate_type(candidates: List[str], default: str, avoid: Optional[Iterable[str]] = None) -> str:
    avoid_set = set(avoid or [])
    for feature_type in candidates:
        if feature_type not in avoid_set:
            return feature_type
    return default


def _spawn_feature_near(
    feature_type: str,
    focal_point: Feature,
    narrative: TerrainNarrative,
    rng: random.Random,
    seed: int,
    distance_range: Tuple[float, float],
    random_position: bool = False,
) -> Optional[Feature]:
    generator = FeatureRegistry._generators.get(feature_type)
    if not generator:
        logger.debug(f"No generator registered for fallback type '{feature_type}'")
        return None

    if random_position:
        x = rng.randint(70, 440)
        y = rng.randint(70, 440)
    else:
        distance = rng.uniform(*distance_range)
        angle = rng.uniform(0, 360)
        x = int(focal_point.position.x + distance * _cos_deg(angle))
        y = int(focal_point.position.y + distance * _sin_deg(angle))
        x = max(40, min(472, x))
        y = max(40, min(472, y))

    modifiers = _extract_modifiers_from_narrative(narrative, "accent")
    feature = generator.create_feature(x, y, modifiers, seed)
    return _ensure_feature_instance(feature)


def _extract_modifiers_from_narrative(
    narrative: TerrainNarrative,
    feature_role: str
) -> Dict:
    """
    Extract parameter modifiers from narrative aesthetic goals.
    
    Maps aesthetic terms → concrete modifiers.
    """
    
    modifiers: Dict[str, Any] = {}

    def add_percent(key: str, delta: float) -> None:
        modifiers[key] = modifiers.get(key, 0.0) + delta

    def ensure_bool(key: str, value: bool) -> None:
        if key not in modifiers:
            modifiers[key] = value

    for goal in narrative.aesthetic_goals:
        if goal.value == "dramatic":
            add_percent("height_percent", 30 if feature_role == "focal" else 15)
            add_percent("radius_percent", 10)
        elif goal.value == "vast":
            add_percent("radius_percent", 25)
            add_percent("width_percent", 20)
            add_percent("length_percent", 20)
        elif goal.value == "intimate":
            add_percent("radius_percent", -15)
            add_percent("height_percent", -10 if feature_role != "focal" else -5)
        elif goal.value == "serene":
            add_percent("height_percent", -12)
            add_percent("radius_percent", 15)
            ensure_bool("use_noise", False)
        elif goal.value == "rugged":
            ensure_bool("use_noise", True)
            modifiers.setdefault("steepness", 0.95)
        elif goal.value == "organic":
            ensure_bool("use_noise", True)
        elif goal.value == "smooth":
            ensure_bool("use_noise", False)
        elif goal.value == "layered" and feature_role != "accent":
            add_percent("width_percent", 10)
            add_percent("length_percent", 10)
        elif goal.value == "monumental" and feature_role == "focal":
            add_percent("height_percent", 20)
            add_percent("radius_percent", 20)

    if feature_role == "accent":
        add_percent("radius_percent", -20)
        add_percent("height_percent", -10)

    # Clamp percents to reasonable ranges
    for key in ["height_percent", "radius_percent", "width_percent", "length_percent"]:
        if key in modifiers:
            modifiers[key] = max(-40.0, min(80.0, modifiers[key]))

    return modifiers


def _cos_deg(degrees: float) -> float:
    """Cosine in degrees."""
    import math
    return math.cos(math.radians(degrees))


def _sin_deg(degrees: float) -> float:
    """Sine in degrees."""
    import math
    return math.sin(math.radians(degrees))


def _distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Euclidean distance."""
    import math
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

