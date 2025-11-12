"""
Tests for generate_from_narrative - verifies narrative → typed Feature pipeline.
"""

from __future__ import annotations

from typing import Dict

import pytest

from server.semantic.narrative.generation import generate_from_narrative
from server.semantic.narrative.narrative_dev import develop_terrain_narrative
from server.semantic.narrative.archetypes import TERRAIN_ARCHETYPES
from server.semantic.narrative.types import AestheticGoal, TerrainNarrative
from server.domain.models import Feature


def _make_scene(seed: int = 42) -> Dict:
    return {
        "features": [],
        "seed": seed,
        "semantic_scene": {
            "version": 1,
            "root": {"path": "/World", "name": "World", "data": {}, "feature_ids": [], "children": {}},
            "entities": [],
            "relationships": {"relationships": [], "next_id": 1}
        }
    }


def _create_narrative(command: str, seed: int = 42) -> tuple[TerrainNarrative, Dict]:
    scene = _make_scene(seed)
    narrative = develop_terrain_narrative(command, scene)
    assert narrative is not None, f"Narrative development failed for command: {command}"
    return narrative, scene


class TestGenerateFromNarrative:
    """Test narrative → typed Features generation."""

    def test_generates_typed_features(self):
        narrative, scene = _create_narrative("create dramatic mountains")
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        assert composition.focal_point is not None
        assert isinstance(composition.focal_point, Feature)
        total_features = 1 if composition.focal_point else 0
        total_features += len(composition.supporting_features)
        total_features += len(composition.accent_features)
        assert total_features >= 1

    def test_supporting_features_are_typed(self):
        narrative, scene = _create_narrative("design layered cliffs")
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        # Supporting features may be optional for some archetypes, but when present they must be typed
        for feature in composition.supporting_features:
            assert isinstance(feature, Feature)
            assert 0 <= feature.position.x <= 512
            assert 0 <= feature.position.y <= 512

    def test_accent_features_are_typed(self):
        narrative, scene = _create_narrative("add dramatic valleys with accents")
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        for feature in composition.accent_features:
            assert isinstance(feature, Feature)

    def test_focal_uses_golden_ratio(self):
        narrative, scene = _create_narrative("create dramatic mountains")
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        assert composition.focal_point.position.x == 205
        assert composition.focal_point.position.y == 136

    def test_different_archetypes_produce_different_features(self):
        focal_types = []
        commands = [
            "create dramatic mountains",  # Ancient uplift
            "design serene valley",       # Fluvial
            "generate beautiful dunes"    # Aeolian
        ]
        for cmd in commands:
            narrative, scene = _create_narrative(cmd)
            composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
            focal_types.append(composition.focal_point.type)

        assert len(set(focal_types)) >= 2

    def test_deterministic_with_same_seed(self):
        narrative, scene = _create_narrative("create dramatic mountains", seed=100)
        comp1 = generate_from_narrative(narrative, scene, seed=scene["seed"])
        comp2 = generate_from_narrative(narrative, scene, seed=scene["seed"])

        assert comp1.focal_point.type == comp2.focal_point.type
        assert comp1.focal_point.position.x == comp2.focal_point.position.x
        assert comp1.focal_point.position.y == comp2.focal_point.position.y

    def test_features_have_valid_parameters(self):
        narrative, scene = _create_narrative("create rugged mountains", seed=123)
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        focal = composition.focal_point
        assert focal.parameters.height is not None or focal.parameters.depth is not None

        for feature in composition.supporting_features + composition.accent_features:
            assert feature.parameters is not None

    def test_features_can_generate_stamps(self):
        narrative, scene = _create_narrative("create dramatic mountains", seed=321)
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        from server.engine.feature_registry import FeatureRegistry

        focal = composition.focal_point
        generator = FeatureRegistry._generators.get(focal.type)
        stamp = generator.generate_stamp(focal, seed=scene["seed"])
        assert stamp.shape == (512, 512)

    def test_composition_metadata(self):
        narrative, scene = _create_narrative("create composed mountains", seed=77)
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        assert composition.golden_ratio_used is True
        assert composition.rule_of_thirds_used in {True, False}

