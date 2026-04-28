"""
Query tools for scene understanding.

These tools allow the LLM to query the current scene state,
get feature details, understand spatial relationships, and
gather information needed for informed decision-making.
"""

import logging
from typing import Dict, List, Optional, Any
from ..scene import TerrainSceneGraph, EntityManager, SceneGraphSerializer

logger = logging.getLogger(__name__)


def query_entities(
    scene_state: Dict,
    label: Optional[str] = None,
    keyword: Optional[str] = None,
    entity_type: Optional[str] = None,
    created_after: Optional[float] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Query scene entities by various criteria.
    
    This tool allows the LLM to search for entities matching specific criteria.
    Useful for: "Find all mountains", "Find entities with keyword 'tall'", etc.
    
    Args:
        scene_state: Current terrain state
        label: Filter by label (e.g., "the mountains")
        keyword: Filter by keyword (e.g., "tall", "steep")
        entity_type: Filter by type ("feature" or "group")
        created_after: Unix timestamp - only entities created after this
        limit: Maximum number of results
        
    Returns:
        {
            "count": int,
            "entities": [
                {
                    "id": str,
                    "label": str,
                    "type": str,
                    "feature_refs": List[int],
                    "keywords": List[str],
                    "description": str,
                    "created_at": float
                }
            ]
        }
    """
    try:
        if "semantic_scene" not in scene_state:
            return {"count": 0, "entities": [], "error": "No scene graph available"}
        
        scene_graph = SceneGraphSerializer.from_dict(scene_state["semantic_scene"])
        manager = EntityManager(scene_graph)
        entities = manager.get_all_entities()
        
        # Apply filters
        filtered = entities
        
        if label:
            label_lower = label.lower()
            filtered = [e for e in filtered if label_lower in e.label.lower()]
        
        if keyword:
            keyword_lower = keyword.lower()
            filtered = [e for e in filtered if any(keyword_lower in k.lower() for k in e.keywords)]
        
        if entity_type:
            filtered = [e for e in filtered if e.type == entity_type]
        
        if created_after:
            filtered = [e for e in filtered if e.created_at > created_after]
        
        # Limit results
        filtered = filtered[:limit]
        
        # Format results
        results = []
        for entity in filtered:
            results.append({
                "id": entity.id,
                "label": entity.label,
                "type": entity.type,
                "feature_refs": entity.feature_refs,
                "keywords": entity.keywords,
                "description": entity.description,
                "created_at": entity.created_at
            })
        
        return {
            "count": len(results),
            "entities": results,
            "total_entities": len(entities)
        }
        
    except Exception as e:
        logger.error(f"query_entities failed: {e}", exc_info=True)
        return {"count": 0, "entities": [], "error": str(e)}


def get_feature_details(
    scene_state: Dict,
    feature_ids: List[int]
) -> Dict[str, Any]:
    """
    Get detailed information about specific features.
    
    This tool provides complete feature attributes including position,
    size, height, and other parameters. Essential for understanding
    existing features before modification.
    
    Args:
        scene_state: Current terrain state
        feature_ids: List of feature IDs to query
        
    Returns:
        {
            "features": [
                {
                    "id": int,
                    "type": str,
                    "x": int,
                    "y": int,
                    "attributes": {
                        "radius": int,
                        "height": float,
                        "steepness": float,
                        ...
                    }
                }
            ]
        }
    """
    try:
        if isinstance(feature_ids, int):  # tolerate single ID
            feature_ids = [feature_ids]
        elif not isinstance(feature_ids, list):
            feature_ids = list(feature_ids)

        features = scene_state.get("features", [])
        
        # Find matching features
        results = []
        for feat in features:
            if feat.get("id") in feature_ids:
                # Extract core info
                feature_info = {
                    "id": feat["id"],
                    "type": feat.get("type", "unknown"),
                    "x": feat.get("x"),
                    "y": feat.get("y"),
                    "attributes": {}
                }
                
                # Collect all attributes (excluding id, type, x, y)
                for key, value in feat.items():
                    if key not in ["id", "type", "x", "y"]:
                        feature_info["attributes"][key] = value
                
                results.append(feature_info)
        
        return {
            "count": len(results),
            "features": results
        }
        
    except Exception as e:
        logger.error(f"get_feature_details failed: {e}", exc_info=True)
        return {"count": 0, "features": [], "error": str(e)}


def get_spatial_relationships(
    scene_state: Dict,
    reference_ids: List[int],
    relationship_type: str = "centroid"
) -> Dict[str, Any]:
    """
    Calculate spatial relationships relative to reference features.
    
    This tool helps the LLM understand spatial positioning by calculating
    centroids, bounding boxes, and positions for various spatial relationships.
    
    Args:
        scene_state: Current terrain state
        reference_ids: Feature IDs to use as reference
        relationship_type: Type of calculation
            - "centroid": Calculate center point
            - "bounding_box": Get min/max bounds
            - "nearby_positions": Positions around the reference (for "around")
            - "between_position": Midpoint (for "between" two features)
            - "north_of": Position north of reference
            - "south_of": Position south of reference
            - "east_of": Position east of reference
            - "west_of": Position west of reference
            
    Returns:
        {
            "relationship_type": str,
            "reference_ids": List[int],
            "result": {
                "position": [x, y] or List[[x, y]],
                "bounding_box": {"min_x": int, "max_x": int, "min_y": int, "max_y": int},
                "region": str  # "left", "center", "right", etc.
            }
        }
    """
    try:
        features = scene_state.get("features", [])
        
        # Get reference feature positions
        positions = []
        for feat in features:
            if feat.get("id") in reference_ids:
                x = feat.get("x")
                y = feat.get("y")
                if x is not None and y is not None:
                    positions.append((x, y))
        
        if not positions:
            return {"error": "No valid positions found for reference IDs"}
        
        # Calculate based on relationship type
        result = {}
        
        if relationship_type == "centroid":
            avg_x = sum(p[0] for p in positions) // len(positions)
            avg_y = sum(p[1] for p in positions) // len(positions)
            result["position"] = [avg_x, avg_y]
            result["region"] = _determine_region(avg_x, avg_y)
            
        elif relationship_type == "bounding_box":
            min_x = min(p[0] for p in positions)
            max_x = max(p[0] for p in positions)
            min_y = min(p[1] for p in positions)
            max_y = max(p[1] for p in positions)
            result["bounding_box"] = {
                "min_x": min_x, "max_x": max_x,
                "min_y": min_y, "max_y": max_y
            }
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            result["center"] = [center_x, center_y]
            result["region"] = _determine_region(center_x, center_y)
            
        elif relationship_type == "between_position":
            if len(positions) >= 2:
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)
                result["position"] = [avg_x, avg_y]
            else:
                result["error"] = "Need at least 2 positions for 'between'"
                
        elif relationship_type in ["north_of", "south_of", "east_of", "west_of"]:
            avg_x = sum(p[0] for p in positions) // len(positions)
            avg_y = sum(p[1] for p in positions) // len(positions)
            offset = 80  # Default offset distance
            
            if relationship_type == "north_of":
                result["position"] = [avg_x, max(0, avg_y - offset)]
            elif relationship_type == "south_of":
                result["position"] = [avg_x, min(511, avg_y + offset)]
            elif relationship_type == "east_of":
                result["position"] = [min(511, avg_x + offset), avg_y]
            elif relationship_type == "west_of":
                result["position"] = [max(0, avg_x - offset), avg_y]
                
        elif relationship_type == "nearby_positions":
            # Calculate positions around the reference in a circular pattern
            avg_x = sum(p[0] for p in positions) // len(positions)
            avg_y = sum(p[1] for p in positions) // len(positions)
            radius = 100
            count = 6  # Default: 6 positions around
            
            import math
            nearby = []
            for i in range(count):
                angle = (2 * math.pi * i) / count
                x = int(avg_x + radius * math.cos(angle))
                y = int(avg_y + radius * math.sin(angle))
                # Clamp to bounds
                x = max(0, min(511, x))
                y = max(0, min(511, y))
                nearby.append([x, y])
            
            result["positions"] = nearby
            result["pattern"] = "circular"
            result["center"] = [avg_x, avg_y]
        
        return {
            "relationship_type": relationship_type,
            "reference_ids": reference_ids,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"get_spatial_relationships failed: {e}", exc_info=True)
        return {"error": str(e)}


def query_scene_summary(scene_state: Dict) -> Dict[str, Any]:
    """
    Get high-level scene composition and statistics.
    
    Provides an overview of the entire terrain including feature counts,
    spatial distribution, and recent activity. Useful for understanding
    the big picture before making decisions.
    
    Args:
        scene_state: Current terrain state
        
    Returns:
        {
            "total_features": int,
            "feature_type_distribution": {"mountain": 5, "valley": 3, ...},
            "entity_count": int,
            "entity_type_distribution": {"feature": 8, "group": 2},
            "spatial_distribution": {
                "left": 3,
                "center": 5,
                "right": 2
            },
            "recent_entities": List[str]  # Last 5 entity labels
        }
    """
    try:
        features = scene_state.get("features", [])
        
        # Feature type distribution
        feature_types = {}
        spatial_dist = {"left": 0, "center": 0, "right": 0}
        
        for feat in features:
            feat_type = feat.get("type", "unknown")
            feature_types[feat_type] = feature_types.get(feat_type, 0) + 1
            
            # Spatial distribution
            x = feat.get("x", 256)
            if x < 170:
                spatial_dist["left"] += 1
            elif x < 341:
                spatial_dist["center"] += 1
            else:
                spatial_dist["right"] += 1
        
        # Entity info
        entities = []
        entity_type_dist = {}
        if "semantic_scene" in scene_state:
            try:
                scene_graph = SceneGraphSerializer.from_dict(scene_state["semantic_scene"])
                manager = EntityManager(scene_graph)
                entities = manager.get_all_entities()
                
                for entity in entities:
                    entity_type_dist[entity.type] = entity_type_dist.get(entity.type, 0) + 1
            except:
                pass
        
        recent_labels = [e.label for e in entities[-5:]] if entities else []
        
        return {
            "total_features": len(features),
            "feature_type_distribution": feature_types,
            "entity_count": len(entities),
            "entity_type_distribution": entity_type_dist,
            "spatial_distribution": spatial_dist,
            "recent_entities": recent_labels
        }
        
    except Exception as e:
        logger.error(f"query_scene_summary failed: {e}", exc_info=True)
        return {"error": str(e)}


def _determine_region(x: int, y: int) -> str:
    """Helper to determine spatial region from coordinates."""
    region_x = "left" if x < 170 else ("center" if x < 341 else "right")
    region_y = "top" if y < 170 else ("center" if y < 341 else "bottom")
    
    if region_y == "center" and region_x == "center":
        return "center"
    elif region_y == "center":
        return region_x
    elif region_x == "center":
        return region_y
    else:
        return f"{region_y}-{region_x}"

