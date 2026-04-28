"""TerrainSceneGraph - Main scene graph manager for terrain features.

This module provides the high-level scene graph interface, managing the
hierarchical structure and providing operations for adding features,
querying nodes, and managing semantic entities.

Architecture:
    /World
      /Features          # Geometric features (mountains, valleys, etc.)
        /Mountain_Group
          /feature_1
          /feature_2
      /Semantics         # Semantic entities (labels, descriptions)
        /dunes_1
        /mountains_1
"""

from typing import Dict, Optional, List
from .node import SceneNode
from .relationships import RelationshipManager


class TerrainSceneGraph:
    """
    Main scene graph manager for terrain features.
    
    Provides USD-inspired hierarchical structure with:
    - Feature organization (/World/Features)
    - Semantic entity tracking (/World/Semantics)
    - Path-based querying
    - Reference resolution support
    
    Attributes:
        root: Root node (/World)
        features_root: Features container (/World/Features)
        semantics_root: Semantics container (/World/Semantics)
    """
    
    def __init__(self):
        """Initialize an empty scene graph with root structure."""
        self.root = SceneNode("/World")
        self.features_root = self.root.add_child("Features")
        self.semantics_root = self.root.add_child("Semantics")
        self.relationship_manager = RelationshipManager()  # Spatial relationships
    
    def add_feature_group(self, name: str, semantic_label: Optional[str] = None) -> SceneNode:
        """
        Add a feature group (collection of related features).
        
        Args:
            name: Group name (e.g., "Mountain_Group")
            semantic_label: Optional semantic label (e.g., "the mountains")
            
        Returns:
            The created group node
            
        Example:
            group = graph.add_feature_group("Mountains", "the mountains")
            # Creates: /World/Features/Mountains
        """
        group = self.features_root.add_child(name)
        if semantic_label:
            group.set_data("semantic_label", semantic_label)
        return group
    
    def get_feature_group(self, name: str) -> Optional[SceneNode]:
        """
        Get a feature group by name.
        
        Args:
            name: Group name
            
        Returns:
            Group node or None if not found
        """
        return self.features_root.get_child(name)
    
    def add_feature(self, feature_data: Dict, group_path: Optional[str] = None) -> SceneNode:
        """
        Add a feature to the scene graph.
        
        Args:
            feature_data: Feature dictionary (must have 'id' key)
            group_path: Optional group path (e.g., "Mountain_Group")
                       If None, creates a default group
            
        Returns:
            The created feature node
            
        Example:
            feature = graph.add_feature(
                {"id": 1, "type": "mountain", "x": 128, "y": 256},
                group_path="Mountain_Group"
            )
            # Creates: /World/Features/Mountain_Group/feature_1
        """
        feature_id = feature_data.get("id")
        if feature_id is None:
            raise ValueError("Feature data must have 'id' key")
        
        # Determine group
        if group_path:
            group = self.features_root.get_child_by_path(group_path)
            if group is None:
                # Create group if it doesn't exist
                group = self.add_feature_group(group_path)
        else:
            # Use feature type as default group
            feature_type = feature_data.get("type", "unknown")
            group_name = f"{feature_type.capitalize()}_Group"
            group = self.features_root.get_child(group_name)
            if group is None:
                group = self.add_feature_group(group_name)
        
        # Create feature node
        feature_name = f"feature_{feature_id}"
        feature_node = group.add_child(feature_name)
        feature_node.feature_ids = [feature_id]
        feature_node.data = feature_data.copy()
        feature_node.set_data("type", feature_data.get("type"))
        
        return feature_node
    
    def find_feature_by_id(self, feature_id: int) -> Optional[SceneNode]:
        """
        Find a feature node by feature ID.
        
        Args:
            feature_id: Feature ID to find
            
        Returns:
            Feature node or None if not found
        """
        for node in self.features_root.traverse():
            if feature_id in node.feature_ids:
                return node
        return None
    
    def find_features_by_type(self, feature_type: str) -> List[SceneNode]:
        """
        Find all feature nodes of a given type.
        
        Args:
            feature_type: Feature type (e.g., "mountain", "valley")
            
        Returns:
            List of feature nodes matching the type
        """
        results = []
        for node in self.features_root.traverse():
            if node.get_data("type") == feature_type:
                results.append(node)
        return results
    
    def get_feature_groups(self) -> List[SceneNode]:
        """
        Get all feature groups (direct children of Features).
        
        Returns:
            List of feature group nodes
        """
        return list(self.features_root.children.values())
    
    def get_all_features(self) -> List[SceneNode]:
        """
        Get all feature nodes (excluding groups).
        
        Returns:
            List of all feature nodes
        """
        features = []
        for node in self.features_root.traverse():
            # Skip groups (nodes with children are groups)
            if node.feature_ids:
                features.append(node)
        return features
    
    def get_feature_ids(self) -> List[int]:
        """
        Get all feature IDs in the scene graph.
        
        Returns:
            List of all feature IDs
        """
        feature_ids = []
        for node in self.features_root.traverse():
            feature_ids.extend(node.feature_ids)
        return feature_ids
    
    def remove_feature(self, feature_id: int) -> bool:
        """
        Remove a feature from the scene graph.
        
        Args:
            feature_id: Feature ID to remove
            
        Returns:
            True if feature was removed, False if not found
        """
        node = self.find_feature_by_id(feature_id)
        if node and node.parent:
            # Remove from parent's children
            node.parent.children = {
                name: child 
                for name, child in node.parent.children.items() 
                if child != node
            }
            return True
        return False
    
    def query(self, path_pattern: str) -> List[SceneNode]:
        """
        Query nodes by path pattern (USD-style).
        
        Supports:
        - Absolute paths: "/World/Features/Mountains/*"
        - Relative paths: "Mountains/*"
        - Wildcards: "*", "Mountain_*"
        
        Args:
            path_pattern: Path pattern to match
            
        Returns:
            List of matching nodes
            
        Example:
            # Get all mountains
            mountains = graph.query("/World/Features/*/feature_*")
            
            # Get all children of Mountain_Group
            children = graph.query("/World/Features/Mountain_Group/*")
        """
        # For now, simple pattern matching
        # Full pattern matching can be added in query.py module
        
        if path_pattern.endswith('/*'):
            # Get all children of parent
            parent_path = path_pattern[:-2]
            parent = self.root.get_child_by_path(parent_path)
            if parent:
                return list(parent.children.values())
            return []
        
        # Direct path lookup
        node = self.root.get_child_by_path(path_pattern)
        if node:
            return [node]
        
        return []
    
    def get_node_by_path(self, path: str) -> Optional[SceneNode]:
        """
        Get a node by absolute or relative path.
        
        Args:
            path: Node path (e.g., "/World/Features/Mountains")
            
        Returns:
            Node at path or None if not found
        """
        return self.root.get_child_by_path(path)
    
    def to_dict(self) -> Dict:
        """
        Serialize scene graph to dictionary.
        
        Returns:
            Dictionary representation of scene graph
        """
        return {
            "version": 1,
            "root": self.root.to_dict()
        }
    
    def from_dict(self, data: Dict):
        """
        Deserialize scene graph from dictionary.
        
        Args:
            data: Dictionary representation
        """
        if "root" in data:
            self.root = SceneNode.from_dict(data["root"])
            # Rebuild references to features_root and semantics_root
            self.features_root = self.root.get_child_by_path("/World/Features")
            self.semantics_root = self.root.get_child_by_path("/World/Semantics")
            
            # Ensure they exist if loading old format
            if self.features_root is None:
                self.features_root = self.root.add_child("Features")
            if self.semantics_root is None:
                self.semantics_root = self.root.add_child("Semantics")
    
    def __repr__(self) -> str:
        """String representation of scene graph."""
        feature_count = len(self.get_feature_ids())
        group_count = len(self.get_feature_groups())
        return f"TerrainSceneGraph(features={feature_count}, groups={group_count})"

