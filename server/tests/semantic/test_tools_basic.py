"""
Basic tests for semantic tools.

These tests verify that tools work correctly with sample scene states.
"""

import pytest
from server.semantic.tools.query_tools import (
    query_entities,
    get_feature_details,
    get_spatial_relationships,
    query_scene_summary
)
from server.semantic.tools.spatial_tools import (
    calculate_position,
    calculate_region_positions
)


# Sample scene state for testing
SAMPLE_SCENE_STATE = {
    "features": [
        {
            "id": 1,
            "type": "mountain",
            "x": 100,
            "y": 200,
            "radius": 50,
            "height": 0.8,
            "use_noise": True
        },
        {
            "id": 2,
            "type": "mountain",
            "x": 300,
            "y": 250,
            "radius": 60,
            "height": 0.9,
            "use_noise": True
        },
        {
            "id": 3,
            "type": "valley",
            "x": 200,
            "y": 225,
            "radius": 40,
            "depth": 0.5
        }
    ],
    "semantic_scene": {
        "version": 1,
        "root": {
            "path": "/World",
            "name": "World",
            "data": {},
            "feature_ids": [],
            "children": {}
        },
        "entities": [
            {
                "id": "mountain_group_1",
                "type": "group",
                "label": "the mountains",
                "keywords": ["mountains", "peaks", "tall"],
                "description": "2 mountains",
                "feature_refs": [1, 2],
                "metadata": {},
                "created_at": 1000.0,
                "user_intent": "add mountains",
                "relationship_ids": []
            },
            {
                "id": "valley_1",
                "type": "feature",
                "label": "the valley",
                "keywords": ["valley", "low", "depression"],
                "description": "1 valley",
                "feature_refs": [3],
                "metadata": {},
                "created_at": 1100.0,
                "user_intent": "add valley",
                "relationship_ids": []
            }
        ],
        "relationships": {
            "relationships": [],
            "next_id": 1
        }
    },
    "seed": 12345,
    "next_id": 4
}


class TestQueryTools:
    """Test query tools."""
    
    def test_query_entities_by_label(self):
        """Test querying entities by label."""
        result = query_entities(
            SAMPLE_SCENE_STATE,
            label="the mountains"
        )
        
        assert result["count"] == 1
        assert len(result["entities"]) == 1
        assert result["entities"][0]["label"] == "the mountains"
        assert result["entities"][0]["feature_refs"] == [1, 2]
    
    def test_query_entities_by_keyword(self):
        """Test querying entities by keyword."""
        result = query_entities(
            SAMPLE_SCENE_STATE,
            keyword="tall"
        )
        
        assert result["count"] >= 1
        assert any("tall" in e["keywords"] for e in result["entities"])
    
    def test_get_feature_details(self):
        """Test getting feature details."""
        result = get_feature_details(
            SAMPLE_SCENE_STATE,
            feature_ids=[1, 2]
        )
        
        assert result["count"] == 2
        assert len(result["features"]) == 2
        
        # Check feature 1
        feat1 = next(f for f in result["features"] if f["id"] == 1)
        assert feat1["type"] == "mountain"
        assert feat1["x"] == 100
        assert feat1["y"] == 200
        assert "radius" in feat1["attributes"]
        assert feat1["attributes"]["radius"] == 50
    
    def test_get_spatial_relationships_centroid(self):
        """Test calculating centroid of features."""
        result = get_spatial_relationships(
            SAMPLE_SCENE_STATE,
            reference_ids=[1, 2],
            relationship_type="centroid"
        )
        
        assert "result" in result
        assert "position" in result["result"]
        # Centroid of (100,200) and (300,250) should be (200,225)
        assert result["result"]["position"] == [200, 225]
        assert result["result"]["region"] in ["center", "center-left"]
    
    def test_get_spatial_relationships_between(self):
        """Test calculating position between features."""
        result = get_spatial_relationships(
            SAMPLE_SCENE_STATE,
            reference_ids=[1, 2],
            relationship_type="between_position"
        )
        
        assert "result" in result
        assert "position" in result["result"]
        # Between (100,200) and (300,250) should be (200,225)
        assert result["result"]["position"] == [200, 225]
    
    def test_query_scene_summary(self):
        """Test getting scene summary."""
        result = query_scene_summary(SAMPLE_SCENE_STATE)
        
        assert result["total_features"] == 3
        assert result["feature_type_distribution"]["mountain"] == 2
        assert result["feature_type_distribution"]["valley"] == 1
        assert result["entity_count"] == 2


class TestSpatialTools:
    """Test spatial calculation tools."""
    
    def test_calculate_position_between(self):
        """Test calculating position with 'between' relationship."""
        result = calculate_position(
            SAMPLE_SCENE_STATE,
            reference_ids=[1, 2],
            relationship="between"
        )
        
        assert result["position"] == [200, 225]
        assert "region" in result
    
    def test_calculate_position_near(self):
        """Test calculating position with 'near' relationship."""
        result = calculate_position(
            SAMPLE_SCENE_STATE,
            reference_ids=[1],
            relationship="near"
        )
        
        # Should be close to (100, 200) but offset
        assert 80 <= result["position"][0] <= 120
        assert 180 <= result["position"][1] <= 220
    
    def test_calculate_position_north_of(self):
        """Test calculating position north of reference."""
        result = calculate_position(
            SAMPLE_SCENE_STATE,
            reference_ids=[1],
            relationship="north_of",
            offset_distance=50
        )
        
        # Should be north (smaller y) of (100, 200)
        assert result["position"][0] == 100  # Same x
        assert result["position"][1] == 150  # y - 50
    
    def test_calculate_position_by_region(self):
        """Test calculating position by explicit region."""
        result = calculate_position(
            SAMPLE_SCENE_STATE,
            region="center"
        )
        
        assert result["region"] == "center"
        assert result["calculation_method"] == "explicit_region"
        # Center region should be around (256, 256)
        assert 170 <= result["position"][0] <= 341
        assert 170 <= result["position"][1] <= 341
    
    def test_calculate_region_positions_circular(self):
        """Test generating circular pattern positions."""
        result = calculate_region_positions(
            SAMPLE_SCENE_STATE,
            count=6,
            reference_ids=[1],
            pattern="circular",
            radius=50
        )
        
        assert result["count"] == 6
        assert len(result["positions"]) == 6
        assert result["pattern"] == "circular"
        # Center should be at feature 1's position
        assert result["center"] == [100, 200]
    
    def test_calculate_region_positions_scattered(self):
        """Test generating scattered positions."""
        result = calculate_region_positions(
            SAMPLE_SCENE_STATE,
            count=5,
            pattern="scattered",
            radius=80
        )
        
        assert result["count"] == 5
        assert len(result["positions"]) == 5
        assert result["pattern"] == "scattered"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

