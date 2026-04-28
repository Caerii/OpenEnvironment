"""
Tests for Mountain feature.

Validates:
- MountainParams validation
- Mountain stamp generation
- Mountain blending mode
- Mountain serialization
"""

import pytest
import numpy as np

from server.features.mountain import Mountain, MountainParams
from server.features.base import FeatureType, FeatureIdentity, FeatureGeometry, FeatureAppearance
from server.core.geometry import Position
from server.engine.stamping import BlendingMode


class TestMountainParams:
    """Tests for MountainParams validation."""
    
    def test_valid_defaults(self):
        """Default parameters should be valid."""
        params = MountainParams()
        assert params.radius == 56
        assert params.steepness == 1.0
    
    def test_valid_custom(self):
        """Custom valid parameters."""
        params = MountainParams(radius=80, steepness=1.5)
        assert params.radius == 80
        assert params.steepness == 1.5
    
    def test_radius_at_min_bound(self):
        """Minimum radius (15) should be valid."""
        params = MountainParams(radius=15)
        assert params.radius == 15
    
    def test_radius_at_max_bound(self):
        """Maximum radius (120) should be valid."""
        params = MountainParams(radius=120)
        assert params.radius == 120
    
    def test_invalid_radius_too_small(self):
        """Radius below 15 should be invalid."""
        with pytest.raises(ValueError, match="Mountain radius must be in"):
            MountainParams(radius=14)
    
    def test_invalid_radius_too_large(self):
        """Radius above 120 should be invalid."""
        with pytest.raises(ValueError, match="Mountain radius must be in"):
            MountainParams(radius=121)
    
    def test_steepness_at_min_bound(self):
        """Minimum steepness (0.5) should be valid."""
        params = MountainParams(steepness=0.5)
        assert params.steepness == 0.5
    
    def test_steepness_at_max_bound(self):
        """Maximum steepness (2.5) should be valid."""
        params = MountainParams(steepness=2.5)
        assert params.steepness == 2.5
    
    def test_invalid_steepness_too_low(self):
        """Steepness below 0.5 should be invalid."""
        with pytest.raises(ValueError, match="Mountain steepness must be in"):
            MountainParams(steepness=0.4)
    
    def test_invalid_steepness_too_high(self):
        """Steepness above 2.5 should be invalid."""
        with pytest.raises(ValueError, match="Mountain steepness must be in"):
            MountainParams(steepness=2.6)


class TestMountain:
    """Tests for Mountain feature."""
    
    def create_mountain(
        self,
        id=1,
        x=256,
        y=256,
        height=0.75,
        radius=56,
        steepness=1.0,
        label=None
    ) -> Mountain:
        """Helper to create mountain with custom parameters."""
        identity = FeatureIdentity(id, FeatureType.MOUNTAIN, label)
        geometry = FeatureGeometry(Position(x, y), radius)
        appearance = FeatureAppearance(height)
        params = MountainParams(radius, steepness)
        return Mountain(identity, geometry, appearance, params)
    
    def test_mountain_creation(self):
        """Create valid mountain."""
        mountain = self.create_mountain()
        assert mountain.id == 1
        assert mountain.type == FeatureType.MOUNTAIN
        assert mountain.position == Position(256, 256)
        assert mountain.height == 0.75
        assert mountain.params.radius == 56
    
    def test_mountain_with_label(self):
        """Create mountain with label."""
        mountain = self.create_mountain(label="the great peak")
        assert mountain.label == "the great peak"
    
    def test_bounding_radius_matches_params(self):
        """Bounding radius should be updated to match mountain radius."""
        mountain = self.create_mountain(radius=80)
        assert mountain.geometry.bounding_radius == 80
        assert mountain.bounds.radius == 80
    
    def test_get_blending_mode(self):
        """Mountains should use MAX blending."""
        mountain = self.create_mountain()
        assert mountain.get_blending_mode() == BlendingMode.MAX
    
    def test_get_stamp_returns_array(self):
        """get_stamp() should return 512x512 array."""
        mountain = self.create_mountain()
        stamp = mountain.get_stamp(seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert stamp.dtype == np.float32
    
    def test_get_stamp_non_zero(self):
        """Mountain stamp should have non-zero values."""
        mountain = self.create_mountain()
        stamp = mountain.get_stamp(seed=42)
        
        # Should have elevation > 0 near center
        center_value = stamp[256, 256]
        assert center_value > 0.1
    
    def test_get_stamp_deterministic(self):
        """Same seed should produce same stamp."""
        mountain = self.create_mountain()
        stamp1 = mountain.get_stamp(seed=42)
        stamp2 = mountain.get_stamp(seed=42)
        
        np.testing.assert_array_equal(stamp1, stamp2)
    
    def test_get_stamp_different_seeds(self):
        """Different seeds should produce different stamps (with noise)."""
        mountain = self.create_mountain()
        stamp1 = mountain.get_stamp(seed=42)
        stamp2 = mountain.get_stamp(seed=99)
        
        # Should be different (if noise is enabled)
        if mountain.use_noise:
            assert not np.array_equal(stamp1, stamp2)
    
    def test_get_type_specific_params(self):
        """Should return mountain-specific params."""
        mountain = self.create_mountain(radius=70, steepness=1.3)
        params = mountain.get_type_specific_params()
        
        assert params["radius"] == 70
        assert params["steepness"] == 1.3
    
    def test_to_dict(self):
        """to_dict() should include all properties."""
        mountain = self.create_mountain(
            id=5,
            x=200,
            y=300,
            height=0.85,
            radius=70,
            steepness=1.4,
            label="peak"
        )
        
        data = mountain.to_dict()
        
        assert data["id"] == 5
        assert data["type"] == "mountain"
        assert data["x"] == 200
        assert data["y"] == 300
        assert data["height"] == 0.85
        assert data["radius"] == 70
        assert data["steepness"] == 1.4
        assert data["label"] == "peak"
    
    def test_from_dict_minimal(self):
        """from_dict() with minimal data should use defaults."""
        data = {
            "id": 1,
            "type": "mountain",
            "x": 100,
            "y": 200
        }
        
        mountain = Mountain.from_dict(data)
        
        assert mountain.id == 1
        assert mountain.position == Position(100, 200)
        assert mountain.height == 0.75  # Default
        assert mountain.params.radius == 56  # Default
        assert mountain.params.steepness == 1.0  # Default
    
    def test_from_dict_full(self):
        """from_dict() with full data."""
        data = {
            "id": 7,
            "type": "mountain",
            "x": 250,
            "y": 350,
            "height": 0.9,
            "use_noise": False,
            "label": "the summit",
            "radius": 80,
            "steepness": 1.8
        }
        
        mountain = Mountain.from_dict(data)
        
        assert mountain.id == 7
        assert mountain.position == Position(250, 350)
        assert mountain.height == 0.9
        assert mountain.use_noise is False
        assert mountain.label == "the summit"
        assert mountain.params.radius == 80
        assert mountain.params.steepness == 1.8
    
    def test_round_trip_serialization(self):
        """to_dict() → from_dict() should preserve all properties."""
        original = self.create_mountain(
            id=3,
            x=150,
            y=250,
            height=0.82,
            radius=65,
            steepness=1.25,
            label="test peak"
        )
        
        data = original.to_dict()
        restored = Mountain.from_dict(data)
        
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.position == original.position
        assert restored.height == original.height
        assert restored.label == original.label
        assert restored.params.radius == original.params.radius
        assert restored.params.steepness == original.params.steepness
    
    def test_repr(self):
        """__repr__ should be informative."""
        mountain = self.create_mountain(label="peak")
        repr_str = repr(mountain)
        
        assert "Mountain" in repr_str
        assert "id=1" in repr_str
        assert "'peak'" in repr_str

