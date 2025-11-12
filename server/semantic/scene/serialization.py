"""Scene Graph Serialization - Save/load scene graph to/from dictionaries.

This module provides serialization utilities for persisting the scene graph
to terrain state and loading it back.
"""

from typing import Dict
import logging
from .graph import TerrainSceneGraph
from .entity import SemanticEntity
from .entity_manager import EntityManager

logger = logging.getLogger(__name__)
from .node import SceneNode


class SceneGraphSerializer:
    """
    Serializes and deserializes scene graphs.
    
    Provides methods to convert scene graphs to dictionaries (for JSON)
    and restore them from dictionaries.
    """
    
    @staticmethod
    def to_dict(scene_graph: TerrainSceneGraph) -> Dict:
        """
        Serialize scene graph to dictionary.
        
        Format:
        {
            "version": 1,
            "root": {...},  # SceneNode tree
            "entities": [...]  # List of entity dictionaries
        }
        
        Args:
            scene_graph: TerrainSceneGraph to serialize
            
        Returns:
            Dictionary representation
        """
        manager = EntityManager(scene_graph)
        entities = manager.get_all_entities()
        
        return {
            "version": 1,
            "root": scene_graph.root.to_dict(),
            "entities": [entity.to_dict() for entity in entities],
            "relationships": scene_graph.relationship_manager.to_dict()
        }
    
    @staticmethod
    def from_dict(data: Dict) -> TerrainSceneGraph:
        """
        Deserialize scene graph from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reconstructed TerrainSceneGraph
        """
        scene_graph = TerrainSceneGraph()
        
        # Restore root structure
        if "root" in data:
            scene_graph.root = SceneNode.from_dict(data["root"])
            # Rebuild references
            scene_graph.features_root = scene_graph.root.get_child_by_path("/World/Features")
            scene_graph.semantics_root = scene_graph.root.get_child_by_path("/World/Semantics")
            
            # Ensure they exist
            if scene_graph.features_root is None:
                scene_graph.features_root = scene_graph.root.add_child("Features")
            if scene_graph.semantics_root is None:
                scene_graph.semantics_root = scene_graph.root.add_child("Semantics")
        
        # Restore entities
        if "entities" in data:
            manager = EntityManager(scene_graph)
            for entity_data in data["entities"]:
                entity = SemanticEntity.from_dict(entity_data)
                manager.add_entity(entity)
        
        # Restore relationships
        if "relationships" in data:
            try:
                rel_data = data["relationships"]
                # Handle both dict and list formats
                if isinstance(rel_data, dict):
                    scene_graph.relationship_manager.from_dict(rel_data)
                elif isinstance(rel_data, list):
                    # Old format: just a list
                    scene_graph.relationship_manager.from_dict(rel_data)
            except Exception as e:
                logger.warning(f"Failed to load relationships: {e}")
                # Continue without relationships
        
        return scene_graph
    
    @staticmethod
    def validate(data: Dict) -> bool:
        """
        Validate dictionary structure.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
        
        if "version" not in data:
            return False
        
        if "root" not in data:
            return False
        
        if "entities" not in data:
            return False
        
        if not isinstance(data["entities"], list):
            return False
        
        return True

