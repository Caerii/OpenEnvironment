"""Shared helpers for running the narrative pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .narrative_dev import develop_terrain_narrative
from .generation import generate_from_narrative
from .converters import composition_to_actions
from ..evaluation import compute_feature_metrics, evaluate_aesthetic_quality, features_to_dicts


def run_narrative_pipeline(
    command: str,
    scene_state: Dict[str, Any] | None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run the narrative pipeline and return (actions, metadata)."""

    scene_state = scene_state or {}

    narrative = develop_terrain_narrative(command, scene_state)
    if not narrative:
        return [], {}

    seed = scene_state.get("seed") if isinstance(scene_state, dict) else None

    composition = generate_from_narrative(narrative, scene_state, seed=seed)
    actions = composition_to_actions(composition)
    if not actions:
        return [], {}

    features = []
    if composition.focal_point:
        features.append(composition.focal_point)
    features.extend(composition.supporting_features)
    features.extend(composition.accent_features)

    feature_dicts = features_to_dicts(features)
    metrics = compute_feature_metrics(feature_dicts)
    quality = evaluate_aesthetic_quality(metrics)

    metadata: Dict[str, Any] = {
        "archetype": narrative.archetype.name,
        "aesthetic_goals": [goal.value for goal in narrative.aesthetic_goals],
        "mood": narrative.mood,
        "story": narrative.story,
        "focal_type": narrative.hero_feature_type,
        "supporting_types": narrative.supporting_feature_types,
        "accent_types": narrative.accent_feature_types,
        "metrics": metrics,
        "quality": quality,
    }

    return actions, metadata
