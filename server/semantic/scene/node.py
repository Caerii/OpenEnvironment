"""SceneNode - USD-inspired prim node for hierarchical scene graph.

This module provides the basic building block for the scene graph system.
Each node represents a prim (primitive) in USD terminology - a node in
the hierarchical structure that can contain data and child nodes.
"""

from typing import Dict, Optional, Iterator, List
from collections import deque


class SceneNode:
    """
    USD-inspired scene graph node (prim).
    
    Represents a single node in the hierarchical scene graph with:
    - Path-based addressing (/World/Features/Mountains/Mountain_001)
    - Parent/child relationships
    - Data storage (feature IDs, metadata)
    - Traversal capabilities
    
    Attributes:
        path: Full path from root (e.g., "/World/Features/Mountains/Mountain_001")
        name: Node name (last segment of path)
        parent: Parent node (None for root)
        children: Dictionary of child nodes by name
        data: Dictionary for storing node data (feature IDs, metadata, etc.)
        feature_ids: List of feature IDs associated with this node
    """
    
    def __init__(self, path: str, parent: Optional['SceneNode'] = None):
        """
        Initialize a scene node.
        
        Args:
            path: Full path from root (e.g., "/World/Features/Mountains")
            parent: Parent node (None for root)
        """
        self.path = path
        self.name = path.split('/')[-1] if path != '/' else ''
        self.parent = parent
        self.children: Dict[str, 'SceneNode'] = {}
        self.data: Dict = {}
        self.feature_ids: List[int] = []
    
    def add_child(self, name: str) -> 'SceneNode':
        """
        Add a child node and return it.
        
        Args:
            name: Name of the child node
            
        Returns:
            The newly created child node
            
        Raises:
            ValueError: If child name already exists
        """
        if name in self.children:
            raise ValueError(f"Child '{name}' already exists in node '{self.path}'")
        
        # Build child path
        if self.path == '/':
            child_path = f'/{name}'
        else:
            child_path = f'{self.path}/{name}'
        
        child = SceneNode(child_path, parent=self)
        self.children[name] = child
        return child
    
    def get_child(self, name: str) -> Optional['SceneNode']:
        """
        Get a child node by name.
        
        Args:
            name: Name of the child node
            
        Returns:
            Child node or None if not found
        """
        return self.children.get(name)
    
    def get_child_by_path(self, path: str) -> Optional['SceneNode']:
        """
        Get a child node by relative or absolute path.
        
        Args:
            path: Relative path (e.g., "Mountains/Mountain_001") or
                  absolute path (e.g., "/World/Features/Mountains")
                  
        Returns:
            Node at path or None if not found
        """
        # Handle absolute paths
        if path.startswith('/'):
            # Start from root
            current = self
            while current.parent is not None:
                current = current.parent
            
            # Remove leading / and split
            path = path[1:]
            if not path:
                return current
            
            segments = path.split('/')
            
            # If first segment matches current node name, skip it
            if segments and segments[0] == current.name:
                segments = segments[1:]
        else:
            current = self
            segments = path.split('/')
        
        # Navigate path segments
        for segment in segments:
            if not segment:
                continue
            current = current.get_child(segment)
            if current is None:
                return None
        
        return current
    
    def traverse(self, depth_first: bool = True) -> Iterator['SceneNode']:
        """
        Traverse subtree starting from this node.
        
        Args:
            depth_first: If True, use depth-first traversal (default).
                        If False, use breadth-first traversal.
                        
        Yields:
            SceneNode instances in traversal order
        """
        if depth_first:
            # Depth-first traversal (DFS)
            yield self
            for child in self.children.values():
                yield from child.traverse(depth_first=True)
        else:
            # Breadth-first traversal (BFS)
            queue = deque([self])
            while queue:
                node = queue.popleft()
                yield node
                queue.extend(node.children.values())
    
    def get_all_descendants(self) -> List['SceneNode']:
        """
        Get all descendant nodes (excluding self).
        
        Returns:
            List of all descendant nodes
        """
        descendants = []
        for child in self.children.values():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_depth(self) -> int:
        """
        Get the depth of this node (distance from root).
        
        Returns:
            Depth (0 for root, 1 for root's children, etc.)
        """
        depth = 0
        current = self
        while current.parent is not None:
            depth += 1
            current = current.parent
        return depth
    
    def is_leaf(self) -> bool:
        """
        Check if this node is a leaf (has no children).
        
        Returns:
            True if node has no children, False otherwise
        """
        return len(self.children) == 0
    
    def is_root(self) -> bool:
        """
        Check if this node is the root node.
        
        Returns:
            True if node has no parent, False otherwise
        """
        return self.parent is None
    
    def add_feature_id(self, feature_id: int):
        """
        Add a feature ID to this node.
        
        Args:
            feature_id: Feature ID to add
        """
        if feature_id not in self.feature_ids:
            self.feature_ids.append(feature_id)
    
    def remove_feature_id(self, feature_id: int) -> bool:
        """
        Remove a feature ID from this node.
        
        Args:
            feature_id: Feature ID to remove
            
        Returns:
            True if feature ID was removed, False if not found
        """
        if feature_id in self.feature_ids:
            self.feature_ids.remove(feature_id)
            return True
        return False
    
    def set_data(self, key: str, value):
        """
        Set a data value in this node.
        
        Args:
            key: Data key
            value: Data value
        """
        self.data[key] = value
    
    def get_data(self, key: str, default=None):
        """
        Get a data value from this node.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        return self.data.get(key, default)
    
    def has_data(self, key: str) -> bool:
        """
        Check if node has a data key.
        
        Args:
            key: Data key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self.data
    
    def to_dict(self) -> Dict:
        """
        Serialize node to dictionary.
        
        Returns:
            Dictionary representation of node
        """
        return {
            "path": self.path,
            "name": self.name,
            "data": self.data.copy(),
            "feature_ids": self.feature_ids.copy(),
            "children": {
                name: child.to_dict() 
                for name, child in self.children.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict, parent: Optional['SceneNode'] = None) -> 'SceneNode':
        """
        Deserialize node from dictionary.
        
        Args:
            data: Dictionary representation
            parent: Parent node (None for root)
            
        Returns:
            Reconstructed SceneNode
        """
        node = cls(data["path"], parent=parent)
        node.data = data.get("data", {}).copy()
        node.feature_ids = data.get("feature_ids", []).copy()
        
        # Reconstruct children recursively
        for name, child_data in data.get("children", {}).items():
            child = cls.from_dict(child_data, parent=node)
            node.children[name] = child
        
        return node
    
    def __repr__(self) -> str:
        """String representation of node."""
        child_count = len(self.children)
        feature_count = len(self.feature_ids)
        return f"SceneNode(path='{self.path}', children={child_count}, features={feature_count})"

