"""Relationship Inference - Automatically detect spatial relationships.

This module provides utilities to infer spatial relationships from feature
arrangements, enabling automatic detection of relationships like "between",
"near", "to the left of", etc.
"""

import math
from typing import Dict, List, Optional, Tuple
from .relationships import RelationshipType, SpatialRelationship, RelationshipManager
from .graph import TerrainSceneGraph
from .entity_manager import EntityManager
from .query import QueryEngine


class RelationshipInferencer:
    """
    Infers spatial relationships from feature arrangements.
    
    Automatically detects relationships like:
    - "between": Feature between two other features
    - "near": Feature close to another feature
    - "to the left of": Feature positioned to the left
    - etc.
    """
    
    def __init__(self, scene_graph: TerrainSceneGraph):
        """
        Initialize relationship inferencer.
        
        Args:
            scene_graph: TerrainSceneGraph instance
        """
        self.scene_graph = scene_graph
        self.entity_manager = EntityManager(scene_graph)
        self.query_engine = QueryEngine(scene_graph)
        self.relationship_manager = scene_graph.relationship_manager
    
    def infer_relationships_for_entity(self, entity_id: str, 
                                      feature_ids: List[int],
                                      command: Optional[str] = None) -> List[SpatialRelationship]:
        """
        Infer relationships for a newly added entity.
        
        Args:
            entity_id: Entity ID to infer relationships for
            feature_ids: Feature IDs belonging to this entity
            command: Optional user command (for context)
            
        Returns:
            List of inferred relationships
        """
        relationships = []
        
        # Get entity
        entity = self.entity_manager.find_entity_by_id(entity_id)
        if not entity:
            return relationships
        
        # Get all other entities
        all_entities = self.entity_manager.get_all_entities()
        other_entities = [e for e in all_entities if e.id != entity_id]
        
        # For each feature in this entity
        for feature_id in feature_ids:
            feature_node = self.scene_graph.find_feature_by_id(feature_id)
            if not feature_node:
                continue
            
            feature_pos = self._get_feature_position(feature_node)
            if not feature_pos:
                continue
            
            # Check relationships with other features
            for other_entity in other_entities:
                for other_feature_id in other_entity.feature_refs:
                    other_node = self.scene_graph.find_feature_by_id(other_feature_id)
                    if not other_node:
                        continue
                    
                    other_pos = self._get_feature_position(other_node)
                    if not other_pos:
                        continue
                    
                    # Infer relationships
                    inferred = self._infer_relationship(
                        feature_id, feature_pos, entity_id,
                        other_feature_id, other_pos, other_entity.id,
                        command
                    )
                    
                    if inferred:
                        relationships.extend(inferred)
        
        # Check for "between" relationships (requires 2+ anchors)
        between_rels = self._infer_between_relationships(entity_id, feature_ids, command)
        relationships.extend(between_rels)
        
        return relationships
    
    def _infer_relationship(self, feature_id: int, feature_pos: Tuple[int, int],
                          source_entity_id: str,
                          other_feature_id: int, other_pos: Tuple[int, int],
                          target_entity_id: str,
                          command: Optional[str] = None) -> List[SpatialRelationship]:
        """
        Infer relationship between two features.
        
        Args:
            feature_id: Source feature ID
            feature_pos: Source feature position
            source_entity_id: Source entity ID
            other_feature_id: Other feature ID
            other_pos: Other feature position
            target_entity_id: Target entity ID
            command: Optional user command for context
            
        Returns:
            List of inferred relationships
        """
        relationships = []
        
        # Calculate distance
        dx = feature_pos[0] - other_pos[0]
        dy = feature_pos[1] - other_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check command context for explicit relationships
        if command:
            command_lower = command.lower()
            
            # "between"
            if "between" in command_lower:
                # Check if this feature is between two others
                # This is handled separately in _infer_between_relationships
                pass
            
            # "near" or "next to"
            if ("near" in command_lower or "next to" in command_lower or 
                "close to" in command_lower):
                if distance < 150:  # Threshold for "near"
                    rel = self.relationship_manager.create_relationship(
                        RelationshipType.NEAR,
                        source_entity_id,
                        [target_entity_id],
                        distance=distance,
                        confidence=0.8
                    )
                    relationships.append(rel)
            
            # "to the left of"
            if "left of" in command_lower or "left of" in command_lower:
                if dx < 0:  # Feature is to the left
                    rel = self.relationship_manager.create_relationship(
                        RelationshipType.LEFT_OF,
                        source_entity_id,
                        [target_entity_id],
                        distance=distance,
                        angle=math.degrees(math.atan2(dy, dx)),
                        confidence=0.9
                    )
                    relationships.append(rel)
            
            # "to the right of"
            if "right of" in command_lower:
                if dx > 0:  # Feature is to the right
                    rel = self.relationship_manager.create_relationship(
                        RelationshipType.RIGHT_OF,
                        source_entity_id,
                        [target_entity_id],
                        distance=distance,
                        angle=math.degrees(math.atan2(dy, dx)),
                        confidence=0.9
                    )
                    relationships.append(rel)
        
        # Auto-infer "near" if distance is small
        if distance < 100 and not any(r.relationship_type == RelationshipType.NEAR 
                                     for r in relationships):
            rel = self.relationship_manager.create_relationship(
                RelationshipType.NEAR,
                source_entity_id,
                [target_entity_id],
                distance=distance,
                confidence=0.6  # Lower confidence for auto-inference
            )
            relationships.append(rel)
        
        return relationships
    
    def _infer_between_relationships(self, entity_id: str, feature_ids: List[int],
                                     command: Optional[str] = None) -> List[SpatialRelationship]:
        """
        Infer "between" relationships.
        
        A feature is "between" two others if:
        1. It's approximately on the line segment between them
        2. Or user explicitly says "between"
        
        Args:
            entity_id: Entity ID
            feature_ids: Feature IDs
            command: Optional user command
            
        Returns:
            List of "between" relationships
        """
        relationships = []
        
        # Check if command mentions "between"
        explicit_between = False
        if command:
            command_lower = command.lower()
            if "between" in command_lower:
                explicit_between = True
        
        # For each feature in this entity
        for feature_id in feature_ids:
            feature_node = self.scene_graph.find_feature_by_id(feature_id)
            if not feature_node:
                continue
            
            feature_pos = self._get_feature_position(feature_node)
            if not feature_pos:
                continue
            
            # Find all other entities
            all_entities = self.entity_manager.get_all_entities()
            other_entities = [e for e in all_entities if e.id != entity_id]
            
            # Check pairs of other entities (anchors)
            for i, entity1 in enumerate(other_entities):
                for entity2 in other_entities[i+1:]:
                    # Get positions of anchor features
                    anchor_positions = []
                    for anchor_feature_id in entity1.feature_refs[:2]:  # Limit to 2 per entity
                        anchor_node = self.scene_graph.find_feature_by_id(anchor_feature_id)
                        if anchor_node:
                            anchor_pos = self._get_feature_position(anchor_node)
                            if anchor_pos:
                                anchor_positions.append((anchor_pos, entity1.id))
                    
                    for anchor_feature_id in entity2.feature_refs[:2]:
                        anchor_node = self.scene_graph.find_feature_by_id(anchor_feature_id)
                        if anchor_node:
                            anchor_pos = self._get_feature_position(anchor_node)
                            if anchor_pos:
                                anchor_positions.append((anchor_pos, entity2.id))
                    
                    # Check if this feature is between any pair of anchors
                    for (pos1, entity_id1), (pos2, entity_id2) in zip(anchor_positions[:-1], anchor_positions[1:]):
                        if self._is_between(feature_pos, pos1, pos2, threshold=80):
                            rel = self.relationship_manager.create_relationship(
                                RelationshipType.BETWEEN,
                                entity_id,
                                [entity_id1, entity_id2],
                                distance=self._distance_to_line_segment(feature_pos, pos1, pos2),
                                confidence=0.9 if explicit_between else 0.7
                            )
                            relationships.append(rel)
        
        return relationships
    
    def _is_between(self, point: Tuple[int, int], start: Tuple[int, int], 
                    end: Tuple[int, int], threshold: float = 80.0) -> bool:
        """
        Check if a point is between two other points (within threshold).
        
        Args:
            point: Point to check
            start: Start point of line segment
            end: End point of line segment
            threshold: Maximum distance from line segment
            
        Returns:
            True if point is between start and end
        """
        # Calculate distance from point to line segment
        distance = self._distance_to_line_segment(point, start, end)
        
        if distance > threshold:
            return False
        
        # Check if point is within segment bounds (projection)
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        segment_length = math.sqrt(dx**2 + dy**2)
        
        if segment_length == 0:
            return False
        
        # Project point onto line segment
        t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (segment_length * segment_length)
        
        # Check if projection is within segment bounds
        return 0 <= t <= 1
    
    def _distance_to_line_segment(self, point: Tuple[int, int], 
                                  start: Tuple[int, int], end: Tuple[int, int]) -> float:
        """Calculate distance from point to line segment."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        segment_length_sq = dx**2 + dy**2
        
        if segment_length_sq == 0:
            # Start and end are the same point
            dist = math.sqrt((point[0] - start[0])**2 + (point[1] - start[1])**2)
            return dist
        
        # Project point onto line segment
        t = max(0, min(1, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / segment_length_sq))
        
        # Closest point on segment
        closest_x = start[0] + t * dx
        closest_y = start[1] + t * dy
        
        # Distance to closest point
        dist = math.sqrt((point[0] - closest_x)**2 + (point[1] - closest_y)**2)
        return dist
    
    def _get_feature_position(self, node) -> Optional[Tuple[int, int]]:
        """Get feature position from node."""
        feat_data = node.get_data("feature")
        if feat_data:
            if "x0" in feat_data and "y0" in feat_data and "x1" in feat_data and "y1" in feat_data:
                x0, y0 = feat_data["x0"], feat_data["y0"]
                x1, y1 = feat_data["x1"], feat_data["y1"]
                return ((x0 + x1) // 2, (y0 + y1) // 2)
            elif "x" in feat_data and "y" in feat_data:
                return (feat_data["x"], feat_data["y"])
        
        if "x" in node.data and "y" in node.data:
            return (node.data["x"], node.data["y"])
        
        return None

