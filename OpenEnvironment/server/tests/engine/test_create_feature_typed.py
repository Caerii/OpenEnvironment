"""
Tests for FeatureRegistry.create_feature() returning typed Feature.

Validates that create_feature() now returns typed Feature instances
instead of dicts, while preserving all variation intelligence.
"""

import pytest
from server.engine.feature_registry import FeatureRegistry
from server.domain.models import Feature, Position, FeatureParameters


class TestCreateFeatureTyped:
    """Test create_feature returns typed Feature."""
    
    def test_mountain_create_returns_feature(self):
        """create_feature should return typed Feature for mountain."""
        generator = FeatureRegistry._generators["mountain"]
        
        result = generator.create_feature(256, 256, {}, seed=42)
        
        # Should be a Feature instance
        assert isinstance(result, Feature)
        assert result.type == "mountain"
        assert result.position.x == 256
        assert result.position.y == 256
        assert result.parameters.height > 0
        assert result.parameters.radius > 0
    
    def test_valley_create_returns_feature(self):
        """create_feature should return typed Feature for valley."""
        generator = FeatureRegistry._generators["valley"]
        
        result = generator.create_feature(256, 256, {}, seed=42)
        
        assert isinstance(result, Feature)
        assert result.type == "valley"
        assert result.position.x == 256
        assert result.position.y == 256
        assert result.parameters.depth > 0
        assert result.parameters.radius > 0
    
    def test_plateau_create_returns_feature(self):
        """create_feature should return typed Feature for plateau."""
        generator = FeatureRegistry._generators["plateau"]
        
        result = generator.create_feature(256, 256, {}, seed=42)
        
        assert isinstance(result, Feature)
        assert result.type == "plateau"
        assert result.position.x == 256
        assert result.position.y == 256
        assert result.parameters.height > 0
        assert result.parameters.width > 0
    
    def test_cliff_create_returns_feature(self):
        """create_feature should return typed Feature for cliff."""
        generator = FeatureRegistry._generators["cliff"]
        
        result = generator.create_feature(256, 256, {}, seed=42)
        
        assert isinstance(result, Feature)
        assert result.type == "cliff"
        assert result.position.x == 256
        assert result.position.y == 256
        assert result.parameters.height > 0
    
    def test_variation_preserved(self):
        """Variation logic should still work with typed Features."""
        generator = FeatureRegistry._generators["mountain"]
        
        # Create two mountains with different seeds
        feat1 = generator.create_feature(256, 256, {}, seed=42)
        feat2 = generator.create_feature(256, 256, {}, seed=99)
        
        # Should have different heights (variation)
        assert feat1.parameters.height != feat2.parameters.height
        assert feat1.parameters.radius != feat2.parameters.radius
    
    def test_modifier_preserved(self):
        """Modifiers like 'taller' should still work."""
        generator = FeatureRegistry._generators["mountain"]
        
        # Create without modifier
        feat_normal = generator.create_feature(256, 256, {}, seed=42)
        
        # Create with 'taller' modifier
        feat_taller = generator.create_feature(256, 256, {"taller": True}, seed=42)
        
        # Taller should have greater height
        assert feat_taller.parameters.height > feat_normal.parameters.height
    
    def test_deterministic_with_same_seed(self):
        """Same seed should produce same Feature."""
        generator = FeatureRegistry._generators["mountain"]
        
        feat1 = generator.create_feature(256, 256, {}, seed=42)
        feat2 = generator.create_feature(256, 256, {}, seed=42)
        
        # Should have identical parameters
        assert feat1.parameters.height == feat2.parameters.height
        assert feat1.parameters.radius == feat2.parameters.radius
    
    def test_feature_can_be_serialized(self):
        """Feature should be convertible to dict for compatibility."""
        generator = FeatureRegistry._generators["mountain"]
        
        feature = generator.create_feature(256, 256, {}, seed=42)
        
        # Convert to dict
        feat_dict = feature.to_dict()
        
        assert isinstance(feat_dict, dict)
        assert feat_dict["type"] == "mountain"
        assert feat_dict["x"] == 256
        assert feat_dict["y"] == 256
        assert "height" in feat_dict
        assert "radius" in feat_dict
    
    def test_feature_round_trip(self):
        """Feature → dict → Feature should preserve data."""
        generator = FeatureRegistry._generators["mountain"]
        
        original = generator.create_feature(256, 256, {}, seed=42)
        
        # Convert to dict and back
        feat_dict = original.to_dict()
        restored = Feature.from_dict(feat_dict)
        
        # Should match
        assert restored.type == original.type
        assert restored.position.x == original.position.x
        assert restored.position.y == original.position.y
        assert restored.parameters.height == original.parameters.height
        assert restored.parameters.radius == original.parameters.radius
    
    def test_all_4_core_types(self):
        """All 4 core types should return typed Features."""
        core_types = ["mountain", "valley", "plateau", "cliff"]
        
        for feature_type in core_types:
            generator = FeatureRegistry._generators[feature_type]
            result = generator.create_feature(256, 256, {}, seed=42)
            
            assert isinstance(result, Feature), f"{feature_type} failed"
            assert result.type == feature_type, f"{feature_type} failed"


class TestGenerateStampWithTypedFeature:
    """Test that generate_stamp works with Features from create_feature."""
    
    def test_mountain_create_then_stamp(self):
        """Create typed Feature, then generate stamp."""
        generator = FeatureRegistry._generators["mountain"]
        
        # Create typed Feature
        feature = generator.create_feature(256, 256, {}, seed=42)
        
        # Generate stamp from typed Feature
        stamp = generator.generate_stamp(feature, seed=42)
        
        assert stamp.shape == (512, 512)
        assert stamp[256, 256] > 0.1  # Mountain has elevation
    
    def test_valley_create_then_stamp(self):
        """Create typed Feature, then generate stamp."""
        generator = FeatureRegistry._generators["valley"]
        
        feature = generator.create_feature(256, 256, {}, seed=42)
        stamp = generator.generate_stamp(feature, seed=42)
        
        assert stamp.shape == (512, 512)
        assert stamp[256, 256] < 1.0  # Valley has depression
    
    def test_end_to_end_workflow(self):
        """Full workflow: create → stamp → serialize."""
        generator = FeatureRegistry._generators["mountain"]
        
        # Step 1: Create typed Feature
        feature = generator.create_feature(256, 256, {"taller": True}, seed=42)
        assert isinstance(feature, Feature)
        
        # Step 2: Generate stamp
        stamp = generator.generate_stamp(feature, seed=42)
        assert stamp.shape == (512, 512)
        
        # Step 3: Serialize for storage
        feat_dict = feature.to_dict()
        assert feat_dict["type"] == "mountain"
        
        # Step 4: Restore from dict
        restored = Feature.from_dict(feat_dict)
        assert restored.parameters.height == feature.parameters.height

