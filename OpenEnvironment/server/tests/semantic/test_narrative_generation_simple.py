"""
Simplified tests for generate_from_narrative focusing on typed output.
"""

from __future__ import annotations

from typing import Dict

import pytest

from server.semantic.narrative.generation import generate_from_narrative, _determine_feature_hierarchy
from server.semantic.narrative.narrative_dev import develop_terrain_narrative
from server.semantic.narrative.archetypes import TERRAIN_ARCHETYPES
from server.semantic.narrative.types import TerrainNarrative
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


def create_minimal_narrative(command: str = "create dramatic mountains", seed: int = 42) -> tuple[TerrainNarrative, Dict]:
    scene = _make_scene(seed)
    narrative = develop_terrain_narrative(command, scene)
    assert narrative is not None
    return narrative, scene


class TestGenerateFromNarrativeSimple:
    """Simplified tests focusing on core functionality."""

    def test_returns_typed_feature_composition(self):
        narrative, scene = create_minimal_narrative()
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        assert composition is not None
        assert composition.focal_point is not None

    def test_focal_point_is_typed_feature(self):
        narrative, scene = create_minimal_narrative()
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        assert isinstance(composition.focal_point, Feature)

    def test_focal_has_valid_position(self):
        narrative, scene = create_minimal_narrative()
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        assert composition.focal_point.position.x == 205
        assert composition.focal_point.position.y == 136

    def test_focal_has_valid_parameters(self):
        narrative, scene = create_minimal_narrative()
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        params = composition.focal_point.parameters
        assert any(
            getattr(params, attr, None) is not None
            for attr in ("height", "depth", "radius")
        ) or bool(getattr(params, "params", {}))

    def test_supporting_features_are_typed_list(self):
        narrative, scene = create_minimal_narrative("design serene valley")
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        assert isinstance(composition.supporting_features, list)
        for feat in composition.supporting_features:
            assert isinstance(feat, Feature)

    def test_accent_features_are_typed_list(self):
        narrative, scene = create_minimal_narrative("generate beautiful dunes")
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        for feat in composition.accent_features:
            assert isinstance(feat, Feature)

    def test_features_can_generate_stamps(self):
        from server.engine.feature_registry import FeatureRegistry

        narrative, scene = create_minimal_narrative()
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])

        focal = composition.focal_point
        generator = FeatureRegistry._generators.get(focal.type)
        stamp = generator.generate_stamp(focal, seed=scene["seed"])
        assert stamp.shape == (512, 512)

    def test_deterministic_generation(self):
        narrative, scene = create_minimal_narrative(seed=123)
        comp1 = generate_from_narrative(narrative, scene, seed=scene["seed"])
        comp2 = generate_from_narrative(narrative, scene, seed=scene["seed"])
        assert comp1.focal_point.type == comp2.focal_point.type
        assert comp1.focal_point.position == comp2.focal_point.position

    def test_different_seeds_produce_variation(self):
        narrative, scene = create_minimal_narrative(seed=77)
        comp1 = generate_from_narrative(narrative, scene, seed=42)
        comp2 = generate_from_narrative(narrative, scene, seed=99)

        focal1 = comp1.focal_point.to_dict()
        focal2 = comp2.focal_point.to_dict()

        assert focal1 != focal2, "Different seeds should produce different focal parameters"

    def test_feature_hierarchy_mapping(self):
        wind_narrative, _ = create_minimal_narrative("generate beautiful dunes")
        hierarchy1 = _determine_feature_hierarchy(wind_narrative, __import__('random').Random(42))
        assert "dunes" in hierarchy1["focal"]

    def test_no_dict_pollution(self):
        narrative, scene = create_minimal_narrative()
        composition = generate_from_narrative(narrative, scene, seed=scene["seed"])
        assert not isinstance(composition.focal_point, dict)
        assert all(not isinstance(f, dict) for f in composition.supporting_features)
        assert all(not isinstance(f, dict) for f in composition.accent_features)

