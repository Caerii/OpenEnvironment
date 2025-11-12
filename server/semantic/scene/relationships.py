"""Spatial Relationships - Track spatial relationships between features.

This module provides classes for tracking and querying spatial relationships
like "between", "near", "to the left of", etc.
"""

from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of spatial relationships."""
    BETWEEN = "between"
    NEAR = "near"
    FAR_FROM = "far_from"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    ABOVE = "above"
    BELOW = "below"
    AROUND = "around"
    SURROUNDS = "surrounds"
    PART_OF = "part_of"
    CONTAINS = "contains"


class SpatialRelationship:
    """
    Represents a spatial relationship between features.
    
    Tracks semantic spatial relationships like "valley between mountains"
    or "hill near the dunes".
    
    Attributes:
        relationship_id: Unique identifier
        relationship_type: Type of relationship (RelationshipType enum)
        source_entity_id: ID of source entity (the entity with the relationship)
        target_entity_ids: List of target entity IDs (what it relates to)
        distance: Optional distance measurement
        angle: Optional angle/direction measurement
        confidence: Confidence score (0.0-1.0)
        metadata: Additional metadata
    """
    
    def __init__(self, relationship_id: str, relationship_type: RelationshipType,
                 source_entity_id: str, target_entity_ids: List[str],
                 distance: Optional[float] = None, angle: Optional[float] = None,
                 confidence: float = 1.0, metadata: Optional[Dict] = None):
        """
        Initialize a spatial relationship.
        
        Args:
            relationship_id: Unique identifier
            relationship_type: Type of relationship
            source_entity_id: Source entity ID
            target_entity_ids: List of target entity IDs
            distance: Optional distance
            angle: Optional angle/direction
            confidence: Confidence score (0.0-1.0)
            metadata: Additional metadata
        """
        self.relationship_id = relationship_id
        self.relationship_type = relationship_type
        self.source_entity_id = source_entity_id
        self.target_entity_ids = target_entity_ids
        self.distance = distance
        self.angle = angle
        self.confidence = confidence
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "id": self.relationship_id,
            "type": self.relationship_type.value,
            "source_entity_id": self.source_entity_id,
            "target_entity_ids": self.target_entity_ids,
            "distance": self.distance,
            "angle": self.angle,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SpatialRelationship':
        """Deserialize from dictionary."""
        return cls(
            relationship_id=data["id"],
            relationship_type=RelationshipType(data["type"]),
            source_entity_id=data["source_entity_id"],
            target_entity_ids=data["target_entity_ids"],
            distance=data.get("distance"),
            angle=data.get("angle"),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        return f"SpatialRelationship({self.relationship_type.value}, {self.source_entity_id} -> {self.target_entity_ids})"


class RelationshipManager:
    """
    Manages spatial relationships between entities.
    
    Provides CRUD operations for relationships and relationship queries.
    """
    
    def __init__(self):
        """Initialize relationship manager."""
        self.relationships: Dict[str, SpatialRelationship] = {}
        self._next_id = 1
    
    def add_relationship(self, relationship: SpatialRelationship) -> str:
        """
        Add a relationship.
        
        Args:
            relationship: SpatialRelationship instance
            
        Returns:
            Relationship ID
        """
        if not relationship.relationship_id:
            relationship.relationship_id = f"rel_{self._next_id}"
            self._next_id += 1
        
        self.relationships[relationship.relationship_id] = relationship
        return relationship.relationship_id
    
    def create_relationship(self, relationship_type: RelationshipType,
                          source_entity_id: str, target_entity_ids: List[str],
                          distance: Optional[float] = None, angle: Optional[float] = None,
                          confidence: float = 1.0, metadata: Optional[Dict] = None) -> SpatialRelationship:
        """
        Create and add a relationship.
        
        Args:
            relationship_type: Type of relationship
            source_entity_id: Source entity ID
            target_entity_ids: Target entity IDs
            distance: Optional distance
            angle: Optional angle
            confidence: Confidence score
            metadata: Additional metadata
            
        Returns:
            Created SpatialRelationship
        """
        rel_id = f"rel_{self._next_id}"
        self._next_id += 1
        
        relationship = SpatialRelationship(
            relationship_id=rel_id,
            relationship_type=relationship_type,
            source_entity_id=source_entity_id,
            target_entity_ids=target_entity_ids,
            distance=distance,
            angle=angle,
            confidence=confidence,
            metadata=metadata
        )
        
        self.add_relationship(relationship)
        return relationship
    
    def get_relationship(self, relationship_id: str) -> Optional[SpatialRelationship]:
        """Get relationship by ID."""
        return self.relationships.get(relationship_id)
    
    def get_relationships_by_source(self, source_entity_id: str) -> List[SpatialRelationship]:
        """Get all relationships for a source entity."""
        return [rel for rel in self.relationships.values() 
                if rel.source_entity_id == source_entity_id]
    
    def get_relationships_by_target(self, target_entity_id: str) -> List[SpatialRelationship]:
        """Get all relationships targeting an entity."""
        return [rel for rel in self.relationships.values() 
                if target_entity_id in rel.target_entity_ids]
    
    def get_relationships_by_type(self, relationship_type: RelationshipType) -> List[SpatialRelationship]:
        """Get all relationships of a type."""
        return [rel for rel in self.relationships.values() 
                if rel.relationship_type == relationship_type]
    
    def find_relationships(self, source_entity_id: Optional[str] = None,
                          target_entity_id: Optional[str] = None,
                          relationship_type: Optional[RelationshipType] = None) -> List[SpatialRelationship]:
        """
        Find relationships matching criteria.
        
        Args:
            source_entity_id: Filter by source entity
            target_entity_id: Filter by target entity
            relationship_type: Filter by relationship type
            
        Returns:
            List of matching relationships
        """
        results = list(self.relationships.values())
        
        if source_entity_id:
            results = [rel for rel in results if rel.source_entity_id == source_entity_id]
        
        if target_entity_id:
            results = [rel for rel in results if target_entity_id in rel.target_entity_ids]
        
        if relationship_type:
            results = [rel for rel in results if rel.relationship_type == relationship_type]
        
        return results
    
    def find_relationship(self, relationship_id: str) -> Optional[SpatialRelationship]:
        """
        Find a relationship by ID.
        
        Args:
            relationship_id: Relationship ID to find
            
        Returns:
            SpatialRelationship or None if not found
        """
        return self.relationships.get(relationship_id)
    
    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship."""
        if relationship_id in self.relationships:
            del self.relationships[relationship_id]
            return True
        return False
    
    def get_all_relationships(self) -> List[SpatialRelationship]:
        """Get all relationships."""
        return list(self.relationships.values())
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "relationships": [rel.to_dict() for rel in self.relationships.values()],
            "next_id": self._next_id
        }
    
    def from_dict(self, data: Dict):
        """Deserialize from dictionary."""
        self.relationships = {}
        
        # Handle both dict format and direct list format
        if isinstance(data, dict):
            relationships_list = data.get("relationships", [])
            next_id = data.get("next_id", len(self.relationships) + 1)
        elif isinstance(data, list):
            # If data is a list directly
            relationships_list = data
            next_id = len(data) + 1
        else:
            relationships_list = []
            next_id = 1
        
        for rel_data in relationships_list:
            try:
                rel = SpatialRelationship.from_dict(rel_data)
                self.relationships[rel.relationship_id] = rel
            except Exception as e:
                logger.warning(f"Failed to deserialize relationship: {e}")
                continue
        
        self._next_id = next_id

