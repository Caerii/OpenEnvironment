"""
Tests for FeatureRegistry bridge pattern (dict + typed Feature support).

Validates that FeatureRegistry accepts both:
- Legacy dict format (backward compatibility)
- New typed Feature format (type safety)
"""

import pytest
import numpy as np

from server.engine.feature_registry import FeatureRegistry
from server.domain.models import Feature, Position, FeatureParameters
from server.engine.stamping import BlendingMode


class TestFeatureRegistryBridge:
    """Test bridge pattern for gradual migration."""
    
    def test_mountain_with_dict(self):
        """Legacy dict format should still work."""
        feat_dict = {
            "type": "mountain",
            "x": 256,
            "y": 256,
            "height": 0.75,
            "radius": 56
        }
        
        stamp = FeatureRegistry.generate_stamp("mountain", feat_dict, 42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert stamp[256, 256] > 0.1  # Mountain has elevation at center
    
    def test_mountain_with_feature(self):
        """New typed Feature should work."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56)
        )
        
        stamp = FeatureRegistry.generate_stamp(feature, 42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert stamp[256, 256] > 0.1
    
    def test_dict_and_feature_produce_same_result(self):
        """Dict and Feature should produce identical stamps."""
        # Dict version
        feat_dict = {
            "id": 1,
            "type": "mountain",
            "x": 256,
            "y": 256,
            "height": 0.75,
            "radius": 56,
            "use_noise": False  # Disable noise for deterministic test
        }
        stamp1 = FeatureRegistry.generate_stamp("mountain", feat_dict, 42)
        
        # Feature version
        feature = Feature.from_dict(feat_dict)
        stamp2 = FeatureRegistry.generate_stamp(feature, 42)
        
        # Should be identical
        np.testing.assert_array_equal(stamp1, stamp2)
    
    def test_valley_with_dict(self):
        """Valley with dict format."""
        feat_dict = {
            "type": "valley",
            "x": 256,
            "y": 256,
            "depth": 0.6,
            "radius": 80
        }
        
        stamp = FeatureRegistry.generate_stamp("valley", feat_dict, 42)
        
        assert stamp.shape == (512, 512)
        # Valley has depression at center (negative or reduced values)
        assert stamp[256, 256] < 1.0
    
    def test_valley_with_feature(self):
        """Valley with typed Feature."""
        feature = Feature(
            id=2,
            type="valley",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(depth=0.6, radius=80)
        )
        
        stamp = FeatureRegistry.generate_stamp(feature, 42)
        
        assert stamp.shape == (512, 512)
        assert stamp[256, 256] < 1.0
    
    def test_all_6_core_types_with_dict(self):
        """All 6 core primitives work with dict."""
        test_cases = [
            ("mountain", {"x": 256, "y": 256, "height": 0.75, "radius": 56}),
            ("valley", {"x": 256, "y": 256, "depth": 0.5, "radius": 80}),
            ("plateau", {"x": 256, "y": 256, "width": 80, "length": 120, "height": 0.5}),
            ("cliff", {"x": 256, "y": 256, "length": 80, "height": 0.55}),
            ("dunes", {"x0": 50, "y0": 50, "x1": 450, "y1": 450}),
            ("canyon", {"x0": 100, "y0": 100, "x1": 400, "y1": 400, "width": 12, "depth": 0.6}),
        ]
        
        for feature_type, params in test_cases:
            params["type"] = feature_type
            stamp = FeatureRegistry.generate_stamp(feature_type, params, 42)
            
            assert stamp.shape == (512, 512), f"{feature_type} failed"
            assert isinstance(stamp, np.ndarray), f"{feature_type} failed"
    
    def test_all_6_core_types_with_feature(self):
        """All 6 core primitives work with typed Feature."""
        test_cases = [
            Feature(1, "mountain", Position(x=256, y=256), FeatureParameters(height=0.75, radius=56)),
            Feature(2, "valley", Position(x=256, y=256), FeatureParameters(depth=0.5, radius=80)),
            Feature(3, "plateau", Position(x=256, y=256), FeatureParameters(height=0.5, width=80, params={"length": 120})),
            Feature(4, "cliff", Position(x=256, y=256), FeatureParameters(height=0.55, params={"length": 80})),
            Feature(5, "dunes", Position(x=0, y=0), FeatureParameters(params={"x0": 50, "y0": 50, "x1": 450, "y1": 450})),
            Feature(6, "canyon", Position(x=0, y=0), FeatureParameters(width=12, depth=0.6, params={"x0": 100, "y0": 100, "x1": 400, "y1": 400})),
        ]
        
        for feature in test_cases:
            stamp = FeatureRegistry.generate_stamp(feature, 42)
            
            assert stamp.shape == (512, 512), f"{feature.type} failed"
            assert isinstance(stamp, np.ndarray), f"{feature.type} failed"
    
    def test_blending_modes(self):
        """Blending modes should be correct for each type."""
        assert FeatureRegistry.get_blending_mode("mountain") == BlendingMode.MAX
        assert FeatureRegistry.get_blending_mode("valley") == BlendingMode.SUBTRACT
        assert FeatureRegistry.get_blending_mode("plateau") == BlendingMode.MAX
        assert FeatureRegistry.get_blending_mode("cliff") == BlendingMode.MAX
        assert FeatureRegistry.get_blending_mode("dunes") == BlendingMode.ADD
        assert FeatureRegistry.get_blending_mode("canyon") == BlendingMode.SUBTRACT
    
    def test_defaults(self):
        """Default parameters should be available."""
        mountain_defaults = FeatureRegistry.get_defaults("mountain")
        assert "radius" in mountain_defaults
        assert "height" in mountain_defaults
        assert mountain_defaults["radius"] == 56
        assert mountain_defaults["height"] == 0.75
    
    def test_feature_from_dict_round_trip(self):
        """Converting dict → Feature → dict should preserve data."""
        original_dict = {
            "type": "mountain",
            "id": 1,
            "x": 256,
            "y": 256,
            "height": 0.75,
            "radius": 56,
            "use_noise": True
        }
        
        # Convert to Feature
        feature = Feature.from_dict(original_dict)
        
        # Convert back to dict
        restored_dict = feature.to_dict()
        
        # Should match
        assert restored_dict["type"] == original_dict["type"]
        assert restored_dict["x"] == original_dict["x"]
        assert restored_dict["y"] == original_dict["y"]
        assert restored_dict["height"] == original_dict["height"]
        assert restored_dict["radius"] == original_dict["radius"]


class TestBackwardCompatibility:
    """Ensure existing code continues to work."""
    
    def test_legacy_calling_convention(self):
        """Old code using (type, dict, seed) should still work."""
        # This is how existing code calls FeatureRegistry
        stamp = FeatureRegistry.generate_stamp(
            "mountain",
            {"x": 256, "y": 256, "height": 0.75, "radius": 56},
            42
        )
        
        assert stamp.shape == (512, 512)
    
    def test_new_calling_convention(self):
        """New code using (Feature, seed) should work."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56)
        )
        
        stamp = FeatureRegistry.generate_stamp(feature, 42)
        
        assert stamp.shape == (512, 512)
    
    def test_both_conventions_coexist(self):
        """Both conventions should work in same codebase."""
        # Old way
        stamp1 = FeatureRegistry.generate_stamp(
            "mountain",
            {"x": 256, "y": 256, "height": 0.75, "radius": 56, "use_noise": False},
            42
        )
        
        # New way
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56, params={"use_noise": False})
        )
        stamp2 = FeatureRegistry.generate_stamp(feature, 42)
        
        # Should produce same result
        np.testing.assert_array_equal(stamp1, stamp2)

