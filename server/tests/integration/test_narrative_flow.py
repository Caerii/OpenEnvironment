"""
End-to-end integration tests for narrative system.

Tests the complete flow: command → narrative → features → terrain.
"""

import pytest
import numpy as np


class TestNarrativeFlow:
    """Test complete narrative → terrain flow."""
    
    def test_narrative_parser_generates_actions(self):
        """Test that NarrativeParser generates valid actions."""
        from semantic.narrative_parser import NarrativeParser
        
        parser = NarrativeParser()
        
        result = parser.parse("create dramatic mountains", scene_state={})
        
        # Should return actions
        assert "actions" in result
        assert len(result["actions"]) >= 1
        
        # Should include narrative for debugging
        assert "narrative" in result
        assert "composition" in result
        
        # Actions should be valid
        for action in result["actions"]:
            assert action["kind"] == "add"
            assert "type" in action
            assert "position" in action
    
    def test_composition_to_actions_conversion(self):
        """Test that FeatureComposition converts to valid actions."""
        from semantic.narrative.generation import generate_from_narrative
        from semantic.narrative.converters import composition_to_actions
        from semantic.narrative.archetypes import TERRAIN_ARCHETYPES
        from semantic.narrative.types import TerrainNarrative
        
        # Generate composition
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
        
        # Convert to actions
        actions = composition_to_actions(composition)
        
        # Should have actions for focal + supporting + accents
        assert len(actions) >= 1
        
        # All should be valid action dicts
        for action in actions:
            assert "kind" in action
            assert action["kind"] == "add"
            assert "type" in action
            assert "position" in action
            assert "modifiers" in action
    
    def test_feature_flows_through_state(self):
        """Test that typed Features flow through FeatureState without crashing."""
        from domain.models import Feature, Position, FeatureParameters
        from semantic.state_manager import FeatureState
        
        state = {"features": [], "seed": 42}
        fs = FeatureState(state)
        
        # Create typed Feature
        feat = Feature(
            id=0,  # Will be reassigned
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.8, radius=40),
            metadata={}
        )
        
        # Add to state (should not crash!)
        feat_id = fs.add_feature(feat)
        
        # Should be stored
        assert feat_id > 0
        stored = fs.find_feature(feature_id=feat_id)
        assert stored is not None
        assert stored["type"] == "mountain"
    
    def test_feature_flows_through_builder(self):
        """Test that typed Features can be applied to builder without crashing."""
        from domain.models import Feature, Position, FeatureParameters
        from engine.commands import _apply_feature_to_builder
        from engine.builder import TerrainBuilder
        from primitives.base import base_desert
        
        builder = TerrainBuilder(base_desert, 42)
        
        # Create typed Feature
        feat = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.8, radius=40),
            metadata={}
        )
        
        # Apply to builder (should not crash!)
        _apply_feature_to_builder(builder, feat, 42)
        
        # Builder should have applied it
        h, _, _ = builder.finalize()
        assert h[256, 256] > 0.5  # Mountain should be there
    
    def test_should_use_narrative_detection(self):
        """Test that narrative detection works correctly."""
        from semantic.narrative_parser import should_use_narrative
        
        # Narrative commands
        assert should_use_narrative("create dramatic mountains")
        assert should_use_narrative("make a beautiful landscape")
        assert should_use_narrative("epic mountain range")
        
        # Simple commands
        assert not should_use_narrative("remove mountain")
        assert not should_use_narrative("make taller")
        assert not should_use_narrative("add mountain")
    
    def test_actions_round_trip(self):
        """Test round-trip: actions → composition → actions."""
        from semantic.narrative.converters import composition_to_actions, actions_to_composition
        
        # Start with actions
        original_actions = [
            {"kind": "add", "type": "mountain", "position": {"x": 256, "y": 256}, "modifiers": {"height": 0.8}},
            {"kind": "add", "type": "valley", "position": {"x": 300, "y": 300}, "modifiers": {"depth": 0.6}}
        ]
        
        # Convert to composition
        composition = actions_to_composition(original_actions, seed=42)
        
        # Convert back to actions
        new_actions = composition_to_actions(composition)
        
        # Should have same number of actions
        assert len(new_actions) >= len(original_actions)
        
        # Should have same feature types
        original_types = {a["type"] for a in original_actions}
        new_types = {a["type"] for a in new_actions}
        assert original_types.issubset(new_types)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

