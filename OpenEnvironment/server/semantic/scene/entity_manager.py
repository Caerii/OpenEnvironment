"""EntityManager - Semantic entity CRUD operations.

This module manages semantic entities within the scene graph, providing
operations to create, store, query, and manage semantic entities.
"""

from typing import List, Optional, Dict
from .entity import SemanticEntity
from .graph import TerrainSceneGraph


class EntityManager:
    """
    Manager for semantic entities in the scene graph.
    
    Provides CRUD operations for semantic entities, linking them to
    feature nodes and enabling reference resolution.
    
    Attributes:
        scene_graph: Reference to the TerrainSceneGraph
    """
    
    def __init__(self, scene_graph: TerrainSceneGraph):
        """
        Initialize entity manager.
        
        Args:
            scene_graph: TerrainSceneGraph instance
        """
        self.scene_graph = scene_graph
    
    def add_entity(self, entity: SemanticEntity):
        """
        Add a semantic entity to the scene graph.
        
        If entity already exists, updates it instead of creating duplicate.
        
        Creates a node in /World/Semantics and links it to feature nodes.
        
        Args:
            entity: SemanticEntity to add
        """
        # Check if entity already exists
        existing_node = self.scene_graph.semantics_root.get_child(entity.id)
        if existing_node:
            # Update existing entity instead of creating duplicate
            # Get old feature refs for comparison
            old_refs = set(existing_node.feature_ids if existing_node.feature_ids else [])
            new_refs = set(entity.feature_refs)
            
            # Update entity data
            existing_node.data = entity.to_dict()
            existing_node.feature_ids = entity.feature_refs.copy()
            
            # Remove links from old features (no longer referenced)
            for feature_id in old_refs - new_refs:
                feature_node = self.scene_graph.find_feature_by_id(feature_id)
                if feature_node:
                    semantic_refs = feature_node.get_data("semantic_refs", [])
                    if entity.id in semantic_refs:
                        semantic_refs.remove(entity.id)
                        feature_node.set_data("semantic_refs", semantic_refs)
            
            # Add links to new features
            for feature_id in new_refs - old_refs:
                feature_node = self.scene_graph.find_feature_by_id(feature_id)
                if feature_node:
                    semantic_refs = feature_node.get_data("semantic_refs", [])
                    if entity.id not in semantic_refs:
                        semantic_refs.append(entity.id)
                        feature_node.set_data("semantic_refs", semantic_refs)
            
            return
        
        # Create entity node in semantics root
        entity_node = self.scene_graph.semantics_root.add_child(entity.id)
        entity_node.data = entity.to_dict()
        entity_node.feature_ids = entity.feature_refs.copy()
        
        # Link entity to feature nodes
        for feature_id in entity.feature_refs:
            feature_node = self.scene_graph.find_feature_by_id(feature_id)
            if feature_node:
                # Add semantic reference to feature node
                semantic_refs = feature_node.get_data("semantic_refs", [])
                if entity.id not in semantic_refs:
                    semantic_refs.append(entity.id)
                    feature_node.set_data("semantic_refs", semantic_refs)
    
    def cleanup_for_removed_features(self, removed_feature_ids: List[int]) -> List[str]:
        """
        Clean up entities when features are removed.
        
        Removes feature references from entities, removes entities that have
        no features left, and returns list of entity IDs that were removed.
        
        Args:
            removed_feature_ids: List of feature IDs that were removed
            
        Returns:
            List of entity IDs that were removed (orphaned entities)
        """
        if not removed_feature_ids:
            return []
        
        removed_entity_ids = []
        removed_feature_set = set(removed_feature_ids)
        
        # Get all entities
        all_entities = self.get_all_entities()
        
        for entity in all_entities:
            # Remove references to deleted features
            original_refs = set(entity.feature_refs)
            entity.feature_refs = [
                fid for fid in entity.feature_refs 
                if fid not in removed_feature_set
            ]
            
            # If entity has no features left, mark for removal
            if not entity.feature_refs:
                removed_entity_ids.append(entity.id)
            elif len(entity.feature_refs) != len(original_refs):
                # Update entity if feature refs changed
                self.update_entity(entity)
        
        # Remove orphaned entities
        for entity_id in removed_entity_ids:
            self.remove_entity(entity_id)
        
        return removed_entity_ids
    
    def cleanup_relationships_for_entity(self, entity_id: str):
        """
        Clean up relationships when an entity is removed.
        
        Removes relationships where this entity is source or target.
        
        Args:
            entity_id: Entity ID being removed
        """
        from .relationships import RelationshipManager
        
        if not hasattr(self.scene_graph, 'relationship_manager'):
            return
        
        rel_manager = self.scene_graph.relationship_manager
        
        # Find relationships involving this entity
        relationships = rel_manager.find_relationships(
            source_entity_id=entity_id
        )
        relationships.extend(
            rel_manager.find_relationships(target_entity_id=entity_id)
        )
        
        # Remove relationships
        removed_rel_ids = []
        for rel in relationships:
            rel_manager.remove_relationship(rel.relationship_id)
            removed_rel_ids.append(rel.relationship_id)
        
        # Remove relationship IDs from other entities
        if removed_rel_ids:
            all_entities = self.get_all_entities()
            for entity in all_entities:
                if entity.id != entity_id:
                    original_rel_ids = entity.relationship_ids.copy()
                    entity.relationship_ids = [
                        rel_id for rel_id in entity.relationship_ids
                        if rel_id not in removed_rel_ids
                    ]
                    if len(entity.relationship_ids) != len(original_rel_ids):
                        self.update_entity(entity)
    
    def cleanup_relationships_for_features(self, removed_feature_ids: List[int]):
        """
        Clean up relationships when features are removed.
        
        Removes relationships that reference the removed features.
        
        Args:
            removed_feature_ids: List of feature IDs that were removed
        """
        from .relationships import RelationshipManager
        
        if not hasattr(self.scene_graph, 'relationship_manager'):
            return
        
        removed_feature_set = set(removed_feature_ids)
        rel_manager = self.scene_graph.relationship_manager
        
        # Find all relationships
        all_relationships = rel_manager.get_all_relationships()
        
        # Find relationships referencing removed features
        relationships_to_remove = []
        for rel in all_relationships:
            # Check if relationship's feature IDs include removed features
            if any(fid in removed_feature_set for fid in rel.source_feature_ids):
                relationships_to_remove.append(rel.relationship_id)
            elif any(fid in removed_feature_set for fid in rel.target_feature_ids):
                relationships_to_remove.append(rel.relationship_id)
        
        # Remove relationships
        for rel_id in relationships_to_remove:
            rel_manager.remove_relationship(rel_id)
        
        # Clean up relationship IDs from entities
        all_entities = self.get_all_entities()
        for entity in all_entities:
            # Remove relationship IDs that no longer exist
            valid_rel_ids = [
                rel_id for rel_id in entity.relationship_ids
                if rel_manager.find_relationship(rel_id) is not None
            ]
            if len(valid_rel_ids) != len(entity.relationship_ids):
                entity.relationship_ids = valid_rel_ids
                self.update_entity(entity)
    
    def remove_entity(self, entity_id: str) -> bool:
        """
        Remove a semantic entity from the scene graph.
        
        Also cleans up relationships involving this entity.
        
        Args:
            entity_id: Entity ID to remove
            
        Returns:
            True if entity was removed, False if not found
        """
        entity_node = self.scene_graph.semantics_root.get_child(entity_id)
        if entity_node:
            # Clean up relationships first
            self.cleanup_relationships_for_entity(entity_id)
            
            # Remove from parent's children
            del self.scene_graph.semantics_root.children[entity_id]
            
            # Remove semantic references from feature nodes
            entity_data = entity_node.data
            feature_refs = entity_data.get("feature_refs", [])
            for feature_id in feature_refs:
                feature_node = self.scene_graph.find_feature_by_id(feature_id)
                if feature_node:
                    semantic_refs = feature_node.get_data("semantic_refs", [])
                    if entity_id in semantic_refs:
                        semantic_refs.remove(entity_id)
                        feature_node.set_data("semantic_refs", semantic_refs)
            
            return True
        return False
    
    def find_entity_by_id(self, entity_id: str) -> Optional[SemanticEntity]:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: Entity ID to find
            
        Returns:
            SemanticEntity or None if not found
        """
        entity_node = self.scene_graph.semantics_root.get_child(entity_id)
        if entity_node and entity_node.data:
            return SemanticEntity.from_dict(entity_node.data)
        return None
    
    def find_entity_by_label(self, label: str) -> Optional[SemanticEntity]:
        """
        Find an entity by its label.
        
        Args:
            label: Entity label (e.g., "the dunes", "two mountains")
            
        Returns:
            SemanticEntity or None if not found
        """
        for entity_node in self.scene_graph.semantics_root.traverse():
            if entity_node == self.scene_graph.semantics_root:
                continue
            
            if entity_node.data:
                entity = SemanticEntity.from_dict(entity_node.data)
                if entity.matches_label(label):
                    return entity
        
        return None
    
    def find_entities_by_type(self, entity_type: str) -> List[SemanticEntity]:
        """
        Find all entities of a given type.
        
        Args:
            entity_type: Entity type ("scene", "group", "composition", "feature")
            
        Returns:
            List of matching entities
        """
        entities = []
        for entity_node in self.scene_graph.semantics_root.traverse():
            if entity_node == self.scene_graph.semantics_root:
                continue
            
            if entity_node.data:
                entity = SemanticEntity.from_dict(entity_node.data)
                if entity.type == entity_type:
                    entities.append(entity)
        
        return entities
    
    def find_entities_matching(self, text: str) -> List[SemanticEntity]:
        """
        Find entities matching text (label or keywords).
        
        Args:
            text: Text to match against
            
        Returns:
            List of matching entities
        """
        entities = []
        for entity_node in self.scene_graph.semantics_root.traverse():
            if entity_node == self.scene_graph.semantics_root:
                continue
            
            if entity_node.data:
                entity = SemanticEntity.from_dict(entity_node.data)
                if entity.matches(text):
                    entities.append(entity)
        
        return entities
    
    def get_all_entities(self) -> List[SemanticEntity]:
        """
        Get all semantic entities.
        
        Returns:
            List of all entities
        """
        entities = []
        for entity_node in self.scene_graph.semantics_root.traverse():
            if entity_node == self.scene_graph.semantics_root:
                continue
            
            if entity_node.data:
                entity = SemanticEntity.from_dict(entity_node.data)
                entities.append(entity)
        
        return entities
    
    def update_entity(self, entity: SemanticEntity):
        """
        Update an existing entity.
        
        Args:
            entity: Updated entity (must have same ID)
        """
        entity_node = self.scene_graph.semantics_root.get_child(entity.id)
        if entity_node:
            # Update data
            entity_node.data = entity.to_dict()
            entity_node.feature_ids = entity.feature_refs.copy()
            
            # Update links to feature nodes
            old_refs = set(entity_node.get_data("old_feature_refs", []))
            new_refs = set(entity.feature_refs)
            
            # Remove links from old features
            for feature_id in old_refs - new_refs:
                feature_node = self.scene_graph.find_feature_by_id(feature_id)
                if feature_node:
                    semantic_refs = feature_node.get_data("semantic_refs", [])
                    if entity.id in semantic_refs:
                        semantic_refs.remove(entity.id)
                        feature_node.set_data("semantic_refs", semantic_refs)
            
            # Add links to new features
            for feature_id in new_refs - old_refs:
                feature_node = self.scene_graph.find_feature_by_id(feature_id)
                if feature_node:
                    semantic_refs = feature_node.get_data("semantic_refs", [])
                    if entity.id not in semantic_refs:
                        semantic_refs.append(entity.id)
                        feature_node.set_data("semantic_refs", semantic_refs)
            
            entity_node.set_data("old_feature_refs", entity.feature_refs.copy())
    
    def get_entity_count(self) -> int:
        """
        Get the total number of entities.
        
        Returns:
            Number of entities
        """
        count = 0
        for _ in self.scene_graph.semantics_root.traverse():
            if _ != self.scene_graph.semantics_root:
                count += 1
        return count

