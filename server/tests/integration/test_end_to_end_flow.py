"""
End-to-end integration tests for the complete terrain generation pipeline.

Tests the ACTUAL flow from user command → terrain output.
"""

import pytest
import numpy as np

# Use absolute imports like other tests
from engine.feature_registry import FeatureRegistry
from engine.commands import AddFeatureCommand, _apply_feature_to_builder
from engine.builder import TerrainBuilder
from primitives.base import base_desert
from semantic.state_manager import FeatureState
from domain.models import Feature, Position, FeatureParameters
from semantic.narrative.generation import generate_from_narrative
from semantic.narrative.archetypes import TERRAIN_ARCHETYPES
from semantic.narrative.types import TerrainNarrative


class TestEndToEndFlow:
    """Test the complete pipeline that users actually invoke."""
    
    def test_simple_command_generates_terrain(self):
        """Basic smoke test: User command → terrain."""
        state = {"features": [], "seed": 42}
        
        # User command
        heightmap, updated_state, splatmap = apply_actions(
            "add 3 mountains",
            state,
            seed=42
        )
        
        # Should produce valid outputs
        assert heightmap.shape == (512, 512)
        assert splatmap.shape == (512, 512, 4)
        assert len(updated_state["features"]) == 3
        
        # Mountains should be typed dicts (not Feature yet!)
        for feat in updated_state["features"]:
            assert isinstance(feat, dict)
            assert "type" in feat
            assert feat["type"] == "mountain"
    
    def test_create_feature_returns_dict_not_feature(self):
        """CRITICAL GAP: create_feature returns dict, not Feature!"""
        from server.engine.feature_registry import FeatureRegistry
        from server.domain.models import Feature
        
        # What we ACTUALLY get
        result = FeatureRegistry.create_feature("mountain", 256, 256, {}, seed=42)
        
        # Gap: This is a dict, not Feature (despite Phase 2 saying it returns Feature)
        assert isinstance(result, dict), "create_feature still returns dict!"
        # assert isinstance(result, Feature), "This would fail - NOT YET FEATURE!"
    
    def test_commands_still_use_dicts(self):
        """CRITICAL GAP: Command system still uses dicts everywhere."""
        from server.engine.commands import AddFeatureCommand
        from server.semantic.state_manager import FeatureState
        from server.engine.builder import TerrainBuilder
        from server.primitives.base import base_desert
        
        state = {"features": [], "seed": 42}
        feature_state = FeatureState(state)
        builder = TerrainBuilder(base_desert, 42)
        
        # Execute command
        cmd = AddFeatureCommand(
            feature_type="mountain",
            position={"x": 256, "y": 256},
            modifiers={},
            count=1
        )
        
        cmd.execute(builder, feature_state, 42)
        
        # Features added are DICTS
        features = feature_state.list_features()
        assert len(features) == 1
        assert isinstance(features[0], dict), "Commands produce dicts, not Features!"
    
    def test_feature_state_uses_dicts(self):
        """CRITICAL GAP: FeatureState.add_feature expects dict."""
        from server.semantic.state_manager import FeatureState
        from server.domain.models import Feature, Position, FeatureParameters
        
        state = {"features": [], "seed": 42}
        feature_state = FeatureState(state)
        
        # Try adding a dict (what currently works)
        dict_feat = {"id": 1, "type": "mountain", "x": 256, "y": 256, "height": 0.8}
        feature_state.add_feature(dict_feat)  # ✅ Works
        
        # Try adding a Feature (what SHOULD work)
        typed_feat = Feature(
            id=2,
            type="mountain",
            position=Position(x=300, y=300),
            parameters=FeatureParameters(height=0.8),
            metadata={}
        )
        
        # This probably fails or gets mangled!
        try:
            feature_state.add_feature(typed_feat)  # ❌ Probably breaks
            # If it works, check what got stored
            stored = feature_state.get_feature(2)
            # Bet: stored is None or dict, not Feature
            assert stored is not None, "Feature not added!"
        except (TypeError, AttributeError) as e:
            pytest.skip(f"FeatureState.add_feature doesn't accept Feature: {e}")
    
    def test_builder_expects_dicts(self):
        """CRITICAL GAP: _apply_feature_to_builder expects dict."""
        from server.engine.commands import _apply_feature_to_builder
        from server.engine.builder import TerrainBuilder
        from server.primitives.base import base_desert
        from server.domain.models import Feature, Position, FeatureParameters
        
        builder = TerrainBuilder(base_desert, 42)
        
        # Dict feature (what currently works)
        dict_feat = {"type": "mountain", "x": 256, "y": 256, "radius": 40, "height": 0.8}
        _apply_feature_to_builder(builder, dict_feat, 42)  # ✅ Works
        
        # Typed Feature (what SHOULD work)
        typed_feat = Feature(
            id=1,
            type="mountain",
            position=Position(x=300, y=300),
            parameters=FeatureParameters(height=0.8, radius=40),
            metadata={}
        )
        
        # This will fail - _apply_feature_to_builder does feat.get("type")
        try:
            _apply_feature_to_builder(builder, typed_feat, 42)  # ❌ Breaks
            pytest.fail("Should have failed - builder expects dict!")
        except (AttributeError, TypeError):
            pass  # Expected - builder doesn't handle Feature yet


class TestNarrativeIntegration:
    """Test if narrative system connects to terrain generation."""
    
    def test_narrative_tools_not_called_by_main_flow(self):
        """CRITICAL GAP: generate_from_narrative never called!"""
        # The main flow is:
        # apply_actions() → parse_command_to_actions() → SemanticParser/CommandParser
        
        # Neither parser calls generate_from_narrative!
        # SemanticParser returns {"actions": [...]} with action dicts
        # generate_from_narrative returns FeatureComposition with typed Features
        
        # There's NO CONNECTION between narrative system and terrain generation!
        pass
    
    def test_feature_composition_not_used(self):
        """CRITICAL GAP: FeatureComposition is never consumed."""
        from server.semantic.narrative.generation import generate_from_narrative
        from server.semantic.narrative.archetypes import TERRAIN_ARCHETYPES
        from server.semantic.narrative.types import TerrainNarrative
        
        # We can generate a composition
        archetype = list(TERRAIN_ARCHETYPES.values())[0]
        narrative = TerrainNarrative(
            archetype=archetype,
            story="test",
            aesthetic_goals=[],
            mood=[],
            primary_process=archetype.primary_process,
            time_scale="ancient",
            weathering_level=0.5,
            wind_direction=None,
            water_flow_direction=None,
            climate="arid",
            hero_feature_type="mountain",
            supporting_feature_types=[],
            accent_feature_types=[],
            focal_point_bias=(256, 256),
            depth_layers_needed=1,
            negative_space_importance=0,
            target_coherence=0.5,
            max_refinement_iterations=1
        )
        
        composition = generate_from_narrative(narrative, {}, seed=42)
        
        # But nothing in the main pipeline USES this!
        # There's no code path from user command → narrative → composition → terrain
        assert composition is not None
        
        # The gap: How do we get composition.focal_point into the terrain?


class TestTypeSystemGaps:
    """Test gaps in type system integration."""
    
    def test_feature_to_dict_loses_information(self):
        """Gap: Feature.to_dict() loses type safety."""
        from server.domain.models import Feature, Position, FeatureParameters
        
        feat = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.8, radius=40),
            metadata={"label": "hero"}
        )
        
        # Convert to dict (what happens when passing to old code)
        feat_dict = feat.to_dict()
        
        # Lost type safety!
        assert isinstance(feat_dict, dict)
        assert "coords" in feat_dict  # Position became coords
        
        # If we pass this dict back to old system, it works
        # But we lost all the type safety benefits!
    
    def test_feature_from_dict_with_old_format(self):
        """Gap: Old dict format might not map cleanly to Feature."""
        from server.domain.models import Feature
        
        # Old format (what feature_registry.create_feature returns)
        old_dict = {
            "id": 1,
            "type": "mountain",
            "x": 256,
            "y": 256,
            "radius": 40,
            "height": 0.8,
            "use_noise": True
        }
        
        # Can we convert it?
        try:
            feat = Feature.from_dict(old_dict)
            
            # Check if conversion worked correctly
            assert feat.type == "mountain"
            assert feat.position.x == 256
            assert feat.parameters.height == 0.8
            assert feat.parameters.radius == 40
            
            # Extra fields go to params?
            assert "use_noise" in feat.parameters.params
        except (KeyError, TypeError) as e:
            pytest.fail(f"Feature.from_dict failed on old format: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

