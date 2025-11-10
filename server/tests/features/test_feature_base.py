"""
Tests for Feature base classes.

Validates:
- FeatureIdentity validation
- FeatureGeometry validation
- FeatureAppearance validation
- Feature ABC properties and methods
"""

import pytest
import time
import numpy as np

from server.features.base import (
    Feature,
    FeatureType,
    FeatureIdentity,
    FeatureGeometry,
    FeatureAppearance,
)
from server.core.geometry import Position
from server.engine.stamping import BlendingMode


class TestFeatureType:
    """Tests for FeatureType enum."""
    
    def test_all_core_primitives_defined(self):
        """All 6 core primitives should be defined."""
        assert FeatureType.MOUNTAIN.value == "mountain"
        assert FeatureType.VALLEY.value == "valley"
        assert FeatureType.DUNES.value == "dunes"
        assert FeatureType.CLIFF.value == "cliff"
        assert FeatureType.PLATEAU.value == "plateau"
        assert FeatureType.CANYON.value == "canyon"
    
    def test_enum_count(self):
        """Should have exactly 6 core types."""
        assert len(FeatureType) == 6


class TestFeatureIdentity:
    """Tests for FeatureIdentity."""
    
    def test_valid_identity_minimal(self):
        """Create identity with minimal fields."""
        identity = FeatureIdentity(id=1, type=FeatureType.MOUNTAIN)
        assert identity.id == 1
        assert identity.type == FeatureType.MOUNTAIN
        assert identity.label is None
        assert isinstance(identity.created_at, float)
    
    def test_valid_identity_with_label(self):
        """Create identity with label."""
        identity = FeatureIdentity(
            id=5,
            type=FeatureType.VALLEY,
            label="the great valley"
        )
        assert identity.id == 5
        assert identity.label == "the great valley"
    
    def test_invalid_negative_id(self):
        """Negative IDs should be invalid."""
        with pytest.raises(ValueError, match="Feature ID must be non-negative"):
            FeatureIdentity(id=-1, type=FeatureType.MOUNTAIN)
    
    def test_created_at_timestamp(self):
        """created_at should be a valid Unix timestamp."""
        before = time.time()
        identity = FeatureIdentity(id=1, type=FeatureType.MOUNTAIN)
        after = time.time()
        
        assert before <= identity.created_at <= after


class TestFeatureGeometry:
    """Tests for FeatureGeometry."""
    
    def test_valid_geometry(self):
        """Create valid geometry."""
        pos = Position(256, 256)
        geometry = FeatureGeometry(position=pos, bounding_radius=50)
        assert geometry.position == pos
        assert geometry.bounding_radius == 50
    
    def test_invalid_zero_radius(self):
        """Zero bounding radius should be invalid."""
        with pytest.raises(ValueError, match="Bounding radius must be positive"):
            FeatureGeometry(Position(100, 100), bounding_radius=0)
    
    def test_invalid_negative_radius(self):
        """Negative bounding radius should be invalid."""
        with pytest.raises(ValueError, match="Bounding radius must be positive"):
            FeatureGeometry(Position(100, 100), bounding_radius=-10)
    
    def test_bounds_property(self):
        """bounds property should return Circle."""
        pos = Position(256, 256)
        geometry = FeatureGeometry(position=pos, bounding_radius=50)
        bounds = geometry.bounds
        
        assert bounds.center == pos
        assert bounds.radius == 50


class TestFeatureAppearance:
    """Tests for FeatureAppearance."""
    
    def test_valid_appearance(self):
        """Create valid appearance."""
        appearance = FeatureAppearance(height=0.75, use_noise=True)
        assert appearance.height == 0.75
        assert appearance.use_noise is True
    
    def test_valid_appearance_defaults(self):
        """use_noise should default to True."""
        appearance = FeatureAppearance(height=0.5)
        assert appearance.use_noise is True
    
    def test_height_at_zero(self):
        """Height of 0.0 should be valid."""
        appearance = FeatureAppearance(height=0.0)
        assert appearance.height == 0.0
    
    def test_height_at_one(self):
        """Height of 1.0 should be valid."""
        appearance = FeatureAppearance(height=1.0)
        assert appearance.height == 1.0
    
    def test_invalid_negative_height(self):
        """Negative height should be invalid."""
        with pytest.raises(ValueError, match="Height must be in"):
            FeatureAppearance(height=-0.1)
    
    def test_invalid_height_exceeds_one(self):
        """Height exceeding 1.0 should be invalid."""
        with pytest.raises(ValueError, match="Height must be in"):
            FeatureAppearance(height=1.1)


class ConcreteTestFeature(Feature):
    """Concrete implementation of Feature for testing."""
    
    def get_stamp(self, seed: int) -> np.ndarray:
        """Return dummy stamp."""
        return np.zeros((512, 512), dtype=np.float32)
    
    def get_blending_mode(self) -> BlendingMode:
        """Return dummy blending mode."""
        return BlendingMode.MAX
    
    def get_type_specific_params(self) -> dict:
        """Return dummy params."""
        return {"test_param": 123}
    
    @classmethod
    def from_dict(cls, data: dict):
        """Dummy from_dict."""
        identity = FeatureIdentity(
            id=data["id"],
            type=FeatureType(data["type"]),
            label=data.get("label")
        )
        geometry = FeatureGeometry(
            position=Position(data["x"], data["y"]),
            bounding_radius=50
        )
        appearance = FeatureAppearance(
            height=data.get("height", 0.5),
            use_noise=data.get("use_noise", True)
        )
        return cls(identity, geometry, appearance)


class TestFeatureABC:
    """Tests for Feature abstract base class."""
    
    def test_cannot_instantiate_abstract_feature(self):
        """Cannot instantiate Feature directly."""
        identity = FeatureIdentity(1, FeatureType.MOUNTAIN)
        geometry = FeatureGeometry(Position(256, 256), 50)
        appearance = FeatureAppearance(0.75)
        
        with pytest.raises(TypeError):
            Feature(identity, geometry, appearance)
    
    def test_concrete_feature_properties(self):
        """Test all property accessors."""
        identity = FeatureIdentity(5, FeatureType.MOUNTAIN, "peak")
        geometry = FeatureGeometry(Position(100, 200), 50)
        appearance = FeatureAppearance(0.85, use_noise=False)
        
        feature = ConcreteTestFeature(identity, geometry, appearance)
        
        # Identity properties
        assert feature.id == 5
        assert feature.type == FeatureType.MOUNTAIN
        assert feature.label == "peak"
        assert isinstance(feature.created_at, float)
        
        # Geometry properties
        assert feature.position == Position(100, 200)
        assert feature.bounds.center == Position(100, 200)
        assert feature.bounds.radius == 50
        
        # Appearance properties
        assert feature.height == 0.85
        assert feature.use_noise is False
    
    def test_overlaps_with_overlapping_features(self):
        """Features with overlapping bounds should return True."""
        f1 = ConcreteTestFeature(
            FeatureIdentity(1, FeatureType.MOUNTAIN),
            FeatureGeometry(Position(100, 100), 50),
            FeatureAppearance(0.5)
        )
        f2 = ConcreteTestFeature(
            FeatureIdentity(2, FeatureType.VALLEY),
            FeatureGeometry(Position(120, 100), 50),
            FeatureAppearance(0.5)
        )
        
        assert f1.overlaps_with(f2)
        assert f2.overlaps_with(f1)  # Symmetric
    
    def test_overlaps_with_separate_features(self):
        """Features with non-overlapping bounds should return False."""
        f1 = ConcreteTestFeature(
            FeatureIdentity(1, FeatureType.MOUNTAIN),
            FeatureGeometry(Position(100, 100), 50),
            FeatureAppearance(0.5)
        )
        f2 = ConcreteTestFeature(
            FeatureIdentity(2, FeatureType.VALLEY),
            FeatureGeometry(Position(300, 300), 50),
            FeatureAppearance(0.5)
        )
        
        assert not f1.overlaps_with(f2)
    
    def test_to_dict_serialization(self):
        """to_dict() should include all properties."""
        feature = ConcreteTestFeature(
            FeatureIdentity(7, FeatureType.CANYON, "the great canyon"),
            FeatureGeometry(Position(256, 384), 80),
            FeatureAppearance(0.65, use_noise=True)
        )
        
        data = feature.to_dict()
        
        assert data["id"] == 7
        assert data["type"] == "canyon"
        assert data["x"] == 256
        assert data["y"] == 384
        assert data["height"] == 0.65
        assert data["use_noise"] is True
        assert data["label"] == "the great canyon"
        assert data["test_param"] == 123  # From get_type_specific_params()
    
    def test_to_dict_no_label(self):
        """to_dict() should handle None label."""
        feature = ConcreteTestFeature(
            FeatureIdentity(1, FeatureType.MOUNTAIN),
            FeatureGeometry(Position(100, 100), 50),
            FeatureAppearance(0.5)
        )
        
        data = feature.to_dict()
        assert data["label"] is None
    
    def test_from_dict_round_trip(self):
        """from_dict(to_dict()) should preserve properties."""
        original = ConcreteTestFeature(
            FeatureIdentity(9, FeatureType.PLATEAU, "mesa"),
            FeatureGeometry(Position(150, 250), 70),
            FeatureAppearance(0.8, use_noise=False)
        )
        
        data = original.to_dict()
        restored = ConcreteTestFeature.from_dict(data)
        
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.label == original.label
        assert restored.position == original.position
        assert restored.height == original.height
        assert restored.use_noise == original.use_noise
    
    def test_repr_with_label(self):
        """__repr__ should be human-readable with label."""
        feature = ConcreteTestFeature(
            FeatureIdentity(1, FeatureType.MOUNTAIN, "peak"),
            FeatureGeometry(Position(100, 200), 50),
            FeatureAppearance(0.75)
        )
        
        repr_str = repr(feature)
        assert "ConcreteTestFeature" in repr_str
        assert "id=1" in repr_str
        assert "'peak'" in repr_str
        assert "pos=(100,200)" in repr_str
        assert "height=0.75" in repr_str
    
    def test_repr_without_label(self):
        """__repr__ should work without label."""
        feature = ConcreteTestFeature(
            FeatureIdentity(2, FeatureType.VALLEY),
            FeatureGeometry(Position(50, 75), 30),
            FeatureAppearance(0.5)
        )
        
        repr_str = repr(feature)
        assert "ConcreteTestFeature" in repr_str
        assert "id=2" in repr_str
        assert "pos=(50,75)" in repr_str


class TestFeatureIntegration:
    """Integration tests for Feature working with geometry types."""
    
    def test_feature_position_is_validated(self):
        """Feature position must be valid Position."""
        identity = FeatureIdentity(1, FeatureType.MOUNTAIN)
        appearance = FeatureAppearance(0.5)
        
        # Valid position
        geometry = FeatureGeometry(Position(256, 256), 50)
        feature = ConcreteTestFeature(identity, geometry, appearance)
        assert feature.position == Position(256, 256)
        
        # Invalid position should fail at Position creation
        with pytest.raises(ValueError):
            Position(-10, 100)
    
    def test_feature_bounds_is_circle(self):
        """Feature bounds should be a valid Circle."""
        feature = ConcreteTestFeature(
            FeatureIdentity(1, FeatureType.MOUNTAIN),
            FeatureGeometry(Position(200, 300), 75),
            FeatureAppearance(0.5)
        )
        
        bounds = feature.bounds
        assert bounds.center == Position(200, 300)
        assert bounds.radius == 75
        assert bounds.area() > 0

