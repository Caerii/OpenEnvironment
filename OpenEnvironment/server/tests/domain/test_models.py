"""
Tests for domain models (Position, Feature, FeatureParameters, TerrainState).

Validates:
- Position specifications (absolute, region, relative)
- Feature creation and serialization
- TerrainState management
- Round-trip dict conversions
"""

import pytest
from server.domain.models import (
    Position,
    FeatureParameters,
    Feature,
    TerrainState,
    RegionType,
)


class TestPosition:
    """Tests for Position dataclass."""
    
    def test_absolute_position(self):
        """Create position with absolute coordinates."""
        pos = Position(x=100, y=200)
        assert pos.x == 100
        assert pos.y == 200
        assert pos.is_absolute()
        assert not pos.is_region()
        assert not pos.is_relative()
    
    def test_region_position(self):
        """Create position with named region."""
        pos = Position(region="center")
        assert pos.region == "center"
        assert not pos.is_absolute()
        assert pos.is_region()
        assert not pos.is_relative()
    
    def test_relative_position(self):
        """Create position relative to another feature."""
        pos = Position(relative_to="mountain1", offset_x=50, offset_y=30)
        assert pos.relative_to == "mountain1"
        assert pos.offset_x == 50
        assert pos.offset_y == 30
        assert not pos.is_absolute()
        assert not pos.is_region()
        assert pos.is_relative()
    
    def test_position_to_dict_absolute(self):
        """Serialize absolute position."""
        pos = Position(x=256, y=384)
        data = pos.to_dict()
        assert data["coords"] == [256, 384]
    
    def test_position_to_dict_region(self):
        """Serialize region position."""
        pos = Position(region="left")
        data = pos.to_dict()
        assert data["region"] == "left"
    
    def test_position_from_dict_absolute(self):
        """Deserialize absolute position."""
        data = {"coords": [100, 200]}
        pos = Position.from_dict(data)
        assert pos.x == 100
        assert pos.y == 200
    
    def test_position_from_dict_region(self):
        """Deserialize region position."""
        data = {"region": "center"}
        pos = Position.from_dict(data)
        assert pos.region == "center"
    
    def test_position_round_trip(self):
        """Round-trip serialization."""
        original = Position(x=150, y=250)
        data = original.to_dict()
        restored = Position.from_dict(data)
        assert restored.x == original.x
        assert restored.y == original.y


class TestFeatureParameters:
    """Tests for FeatureParameters dataclass."""
    
    def test_parameters_with_common_fields(self):
        """Create parameters with common fields."""
        params = FeatureParameters(
            height=0.75,
            radius=56,
            params={"steepness": 1.2, "use_noise": True}
        )
        assert params.height == 0.75
        assert params.radius == 56
        assert params.params["steepness"] == 1.2
    
    def test_parameters_to_dict(self):
        """Serialize parameters."""
        params = FeatureParameters(
            height=0.8,
            radius=60,
            params={"steepness": 1.5}
        )
        data = params.to_dict()
        assert data["height"] == 0.8
        assert data["radius"] == 60
        assert data["steepness"] == 1.5  # Flattened
    
    def test_parameters_from_dict(self):
        """Deserialize parameters."""
        data = {
            "height": 0.7,
            "radius": 50,
            "steepness": 1.0,
            "use_noise": True
        }
        params = FeatureParameters.from_dict(data)
        assert params.height == 0.7
        assert params.radius == 50
        assert params.params["steepness"] == 1.0
        assert params.params["use_noise"] is True
    
    def test_parameters_round_trip(self):
        """Round-trip serialization."""
        original = FeatureParameters(
            height=0.85,
            radius=70,
            params={"steepness": 1.3, "custom_param": 42}
        )
        data = original.to_dict()
        restored = FeatureParameters.from_dict(data)
        assert restored.height == original.height
        assert restored.radius == original.radius
        assert restored.params == original.params


class TestFeature:
    """Tests for Feature dataclass."""
    
    def test_feature_creation(self):
        """Create a feature."""
        pos = Position(x=256, y=256)
        params = FeatureParameters(height=0.75, radius=56)
        feature = Feature(
            id=1,
            type="mountain",
            position=pos,
            parameters=params
        )
        assert feature.id == 1
        assert feature.type == "mountain"
        assert feature.position.x == 256
        assert feature.parameters.height == 0.75
    
    def test_feature_to_dict(self):
        """Serialize feature to dict."""
        pos = Position(x=200, y=300)
        params = FeatureParameters(
            height=0.8,
            radius=60,
            params={"steepness": 1.2}
        )
        feature = Feature(
            id=5,
            type="mountain",
            position=pos,
            parameters=params,
            metadata={"label": "the peak"}
        )
        
        data = feature.to_dict()
        
        assert data["id"] == 5
        assert data["type"] == "mountain"
        assert data["x"] == 200
        assert data["y"] == 300
        assert data["height"] == 0.8
        assert data["radius"] == 60
        assert data["steepness"] == 1.2  # Flattened from params
        assert data["metadata"]["label"] == "the peak"
    
    def test_feature_from_dict(self):
        """Deserialize feature from dict."""
        data = {
            "id": 3,
            "type": "valley",
            "x": 150,
            "y": 250,
            "height": 0.6,
            "depth": 0.5,
            "radius": 80
        }
        
        feature = Feature.from_dict(data)
        
        assert feature.id == 3
        assert feature.type == "valley"
        assert feature.position.x == 150
        assert feature.position.y == 250
        assert feature.parameters.height == 0.6
        assert feature.parameters.depth == 0.5
        assert feature.parameters.radius == 80
    
    def test_feature_round_trip(self):
        """Round-trip serialization."""
        original = Feature(
            id=7,
            type="dunes",
            position=Position(x=100, y=400),
            parameters=FeatureParameters(
                height=0.4,
                params={"dune_spacing": 30}
            ),
            metadata={"created_at": "2024-01-01"}
        )
        
        data = original.to_dict()
        restored = Feature.from_dict(data)
        
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.position.x == original.position.x
        assert restored.parameters.height == original.parameters.height


class TestTerrainState:
    """Tests for TerrainState dataclass."""
    
    def test_terrain_state_creation(self):
        """Create empty terrain state."""
        state = TerrainState()
        assert state.features == []
        assert state.seed == 0
        assert state.next_id == 1
    
    def test_add_feature_assigns_id(self):
        """Adding feature assigns ID automatically."""
        state = TerrainState()
        feature = Feature(
            id=0,  # Will be assigned
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75)
        )
        
        assigned_id = state.add_feature(feature)
        
        assert assigned_id == 1
        assert feature.id == 1
        assert state.next_id == 2
        assert len(state.features) == 1
    
    def test_add_multiple_features(self):
        """Add multiple features with auto-incrementing IDs."""
        state = TerrainState()
        
        for i in range(3):
            feature = Feature(
                id=0,
                type="mountain",
                position=Position(x=100 * i, y=100 * i),
                parameters=FeatureParameters()
            )
            state.add_feature(feature)
        
        assert len(state.features) == 3
        assert state.next_id == 4
        assert state.features[0].id == 1
        assert state.features[1].id == 2
        assert state.features[2].id == 3
    
    def test_remove_feature(self):
        """Remove feature by ID."""
        state = TerrainState()
        feature = Feature(
            id=0,
            type="mountain",
            position=Position(x=100, y=100),
            parameters=FeatureParameters()
        )
        assigned_id = state.add_feature(feature)
        
        # Remove it
        result = state.remove_feature(assigned_id)
        
        assert result is True
        assert len(state.features) == 0
    
    def test_remove_nonexistent_feature(self):
        """Removing nonexistent feature returns False."""
        state = TerrainState()
        result = state.remove_feature(999)
        assert result is False
    
    def test_find_feature(self):
        """Find feature by ID."""
        state = TerrainState()
        feature = Feature(
            id=0,
            type="mountain",
            position=Position(x=100, y=100),
            parameters=FeatureParameters()
        )
        assigned_id = state.add_feature(feature)
        
        found = state.find_feature(assigned_id)
        
        assert found is not None
        assert found.id == assigned_id
    
    def test_list_features_by_type(self):
        """List features filtered by type."""
        state = TerrainState()
        
        # Add 2 mountains
        for i in range(2):
            state.add_feature(Feature(
                id=0,
                type="mountain",
                position=Position(x=100, y=100),
                parameters=FeatureParameters()
            ))
        
        # Add 1 valley
        state.add_feature(Feature(
            id=0,
            type="valley",
            position=Position(x=200, y=200),
            parameters=FeatureParameters()
        ))
        
        mountains = state.list_features_by_type("mountain")
        valleys = state.list_features_by_type("valley")
        
        assert len(mountains) == 2
        assert len(valleys) == 1
    
    def test_terrain_state_to_dict(self):
        """Serialize terrain state."""
        state = TerrainState(seed=42)
        state.add_feature(Feature(
            id=0,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56)
        ))
        
        data = state.to_dict()
        
        assert data["seed"] == 42
        assert data["next_id"] == 2
        assert len(data["features"]) == 1
        assert data["features"][0]["type"] == "mountain"
    
    def test_terrain_state_from_dict(self):
        """Deserialize terrain state."""
        data = {
            "features": [
                {
                    "id": 1,
                    "type": "mountain",
                    "x": 256,
                    "y": 256,
                    "height": 0.75,
                    "radius": 56
                }
            ],
            "seed": 42,
            "next_id": 2
        }
        
        state = TerrainState.from_dict(data)
        
        assert state.seed == 42
        assert state.next_id == 2
        assert len(state.features) == 1
        assert state.features[0].type == "mountain"
    
    def test_terrain_state_round_trip(self):
        """Round-trip serialization."""
        original = TerrainState(seed=123)
        original.add_feature(Feature(
            id=0,
            type="valley",
            position=Position(x=100, y=200),
            parameters=FeatureParameters(depth=0.6)
        ))
        
        data = original.to_dict()
        restored = TerrainState.from_dict(data)
        
        assert restored.seed == original.seed
        assert len(restored.features) == len(original.features)
        assert restored.features[0].type == original.features[0].type

