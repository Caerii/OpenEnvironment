"""Query Engine - Advanced spatial and metadata queries for scene graph.

Provides sophisticated querying capabilities including:
- Spatial queries (near, within, between, region)
- Metadata filtering with operators
- Query composition (AND, OR, NOT)
- Pattern matching
"""

import math
import re
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from .graph import TerrainSceneGraph
from .node import SceneNode


class QueryEngine:
    """
    Advanced query engine for scene graph with spatial capabilities.
    
    Supports:
    - Spatial queries (distance, region, between points)
    - Metadata filtering with operators ($gt, $lt, $in, etc.)
    - Query composition (AND, OR, NOT)
    - Path pattern matching
    """
    
    def __init__(self, scene_graph: TerrainSceneGraph):
        """
        Initialize query engine with scene graph.
        
        Args:
            scene_graph: TerrainSceneGraph instance to query
        """
        self.graph = scene_graph
    
    # ==================== Spatial Queries ====================
    
    def find_near(self, position: Tuple[int, int], radius: float = 50.0, 
                  feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features within radius of a position.
        
        Args:
            position: (x, y) center point
            radius: Search radius in pixels
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances within radius
            
        Example:
            # Find all mountains within 100 pixels of (256, 256)
            mountains = engine.find_near((256, 256), radius=100, feature_type="mountain")
        """
        x0, y0 = position
        results = []
        
        for node in self._get_queryable_nodes(feature_type):
            feat_pos = self._get_feature_position(node)
            if feat_pos is None:
                continue
            
            x, y = feat_pos
            distance = math.sqrt((x - x0)**2 + (y - y0)**2)
            
            if distance <= radius:
                results.append(node)
        
        return results
    
    def find_within_region(self, bounds: Tuple[int, int, int, int],
                          feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features within a rectangular region.
        
        Args:
            bounds: (x0, y0, x1, y1) bounding box
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances within bounds
            
        Example:
            # Find all features in left half of terrain
            features = engine.find_within_region((0, 0, 256, 512))
        """
        x0, y0, x1, y1 = bounds
        results = []
        
        for node in self._get_queryable_nodes(feature_type):
            feat_pos = self._get_feature_position(node)
            if feat_pos is None:
                continue
            
            x, y = feat_pos
            if x0 <= x <= x1 and y0 <= y <= y1:
                results.append(node)
        
        return results
    
    def find_between(self, start: Tuple[int, int], end: Tuple[int, int],
                    width: float = 50.0, feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features between two points (within a corridor).
        
        Args:
            start: (x0, y0) start point
            end: (x1, y1) end point
            width: Width of corridor (distance from line)
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances between points
            
        Example:
            # Find features between two mountains
            features = engine.find_between((100, 100), (400, 400), width=80)
        """
        x0, y0 = start
        x1, y1 = end
        
        # Calculate line segment length
        dx = x1 - x0
        dy = y1 - y0
        segment_length = math.sqrt(dx**2 + dy**2)
        
        if segment_length == 0:
            return []
        
        results = []
        
        for node in self._get_queryable_nodes(feature_type):
            feat_pos = self._get_feature_position(node)
            if feat_pos is None:
                continue
            
            px, py = feat_pos
            
            # Calculate distance from point to line segment
            # Using formula: distance = |(y2-y1)x - (x2-x1)y + x2y1 - y2x1| / sqrt((y2-y1)² + (x2-x1)²)
            numerator = abs(dy * px - dx * py + x1 * y0 - y1 * x0)
            distance = numerator / segment_length
            
            # Check if point is within width of line segment
            if distance <= width:
                # Also check if point is within segment bounds (projection)
                t = ((px - x0) * dx + (py - y0) * dy) / (segment_length * segment_length)
                if 0 <= t <= 1:
                    results.append(node)
        
        return results
    
    def find_near_feature(self, feature_id: int, radius: float = 50.0,
                         feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features near another feature.
        
        Args:
            feature_id: ID of reference feature
            radius: Search radius in pixels
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances near the reference feature
            
        Example:
            # Find all valleys near mountain 5
            valleys = engine.find_near_feature(5, radius=100, feature_type="valley")
        """
        ref_node = self.graph.find_feature_by_id(feature_id)
        if ref_node is None:
            return []
        
        ref_pos = self._get_feature_position(ref_node)
        if ref_pos is None:
            return []
        
        return self.find_near(ref_pos, radius, feature_type)
    
    def find_closest(self, position: Tuple[int, int], n: int = 1,
                    feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find the N closest features to a position.
        
        Args:
            position: (x, y) center point
            n: Number of closest features to return
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances, sorted by distance (closest first)
            
        Example:
            # Find 3 closest mountains to center
            closest = engine.find_closest((256, 256), n=3, feature_type="mountain")
        """
        x0, y0 = position
        candidates = []
        
        for node in self._get_queryable_nodes(feature_type):
            feat_pos = self._get_feature_position(node)
            if feat_pos is None:
                continue
            
            x, y = feat_pos
            distance = math.sqrt((x - x0)**2 + (y - y0)**2)
            candidates.append((distance, node))
        
        # Sort by distance and return top N
        candidates.sort(key=lambda x: x[0])
        return [node for _, node in candidates[:n]]
    
    def find_in_direction(self, position: Tuple[int, int], direction: float,
                          angle_range: float = 45.0, max_distance: float = 200.0,
                          feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features in a direction from a position.
        
        Args:
            position: (x, y) center point
            direction: Direction angle in degrees (0 = right, 90 = up, 180 = left, 270 = down)
            angle_range: Angular range in degrees (±angle_range/2 from direction)
            max_distance: Maximum distance to search
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances in the direction
            
        Example:
            # Find mountains to the right of center
            mountains = engine.find_in_direction((256, 256), direction=0, angle_range=30)
        """
        x0, y0 = position
        direction_rad = math.radians(direction)
        half_range_rad = math.radians(angle_range / 2)
        
        results = []
        
        for node in self._get_queryable_nodes(feature_type):
            feat_pos = self._get_feature_position(node)
            if feat_pos is None:
                continue
            
            x, y = feat_pos
            dx = x - x0
            dy = y - y0
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > max_distance:
                continue
            
            if distance == 0:
                continue
            
            # Calculate angle to feature
            angle_to_feature = math.atan2(dy, dx)
            
            # Normalize angles to [0, 2π]
            direction_norm = direction_rad % (2 * math.pi)
            angle_norm = angle_to_feature % (2 * math.pi)
            
            # Check if angle is within range
            diff = abs(angle_norm - direction_norm)
            if diff > math.pi:
                diff = 2 * math.pi - diff
            
            if diff <= half_range_rad:
                results.append(node)
        
        return results
    
    # ==================== Metadata Queries ====================
    
    def find_by_metadata(self, filters: Dict[str, Any],
                        feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features matching metadata filters.
        
        Supports operators:
        - {"height": {"$gt": 0.7}} - Greater than
        - {"height": {"$lt": 0.5}} - Less than
        - {"height": {"$gte": 0.7}} - Greater than or equal
        - {"height": {"$lte": 0.5}} - Less than or equal
        - {"type": {"$in": ["mountain", "hill"]}} - In list
        - {"label": {"$regex": "mountain.*"}} - Regex match
        
        Args:
            filters: Dictionary of metadata filters
            feature_type: Optional type filter (applied first)
            
        Returns:
            List of SceneNode instances matching filters
            
        Example:
            # Find tall mountains
            tall = engine.find_by_metadata({"height": {"$gt": 0.7}, "type": "mountain"})
        """
        results = []
        
        for node in self._get_queryable_nodes(feature_type):
            if self._matches_filters(node, filters):
                results.append(node)
        
        return results
    
    def find_by_type(self, feature_type: str) -> List[SceneNode]:
        """
        Find all features of a given type.
        
        Args:
            feature_type: Feature type (e.g., "mountain", "valley")
            
        Returns:
            List of SceneNode instances
        """
        return self.graph.find_features_by_type(feature_type)
    
    # ==================== Path Queries ====================
    
    def query_path(self, path_pattern: str) -> List[SceneNode]:
        """
        Query nodes by path pattern (USD-style).
        
        Supports:
        - "/World/Features/Mountains/*" - All children
        - "/World/Features/*/feature_*" - Pattern matching
        - "Mountains/*" - Relative paths
        
        Args:
            path_pattern: Path pattern to match
            
        Returns:
            List of matching SceneNode instances
        """
        # Enhanced pattern matching
        if '*' in path_pattern:
            return self._query_path_pattern(path_pattern)
        else:
            # Direct path lookup
            node = self.graph.get_node_by_path(path_pattern)
            return [node] if node else []
    
    def _query_path_pattern(self, pattern: str) -> List[SceneNode]:
        """Query with wildcard pattern matching."""
        # Convert pattern to regex
        # "/Features/*/Mountain_*" → r"/Features/.*/Mountain_.*"
        regex_pattern = pattern.replace('*', '[^/]*')
        regex_pattern = regex_pattern.replace('?', '.')
        
        # Escape special regex chars but keep our patterns
        regex_pattern = re.escape(regex_pattern).replace('\\[\\^/\\]\\*', '[^/]*').replace('\\.', '.')
        
        results = []
        for node in self.graph.root.traverse():
            if re.match(regex_pattern, node.path):
                results.append(node)
        
        return results
    
    # ==================== Query Composition ====================
    
    def and_(self, *queries: List[SceneNode]) -> List[SceneNode]:
        """
        Intersection of multiple queries (features in ALL results).
        
        Args:
            *queries: Multiple query result lists
            
        Returns:
            List of SceneNode instances in all queries
            
        Example:
            # Find mountains AND in left half
            mountains = engine.find_by_type("mountain")
            left_half = engine.find_within_region((0, 0, 256, 512))
            result = engine.and_(mountains, left_half)
        """
        if not queries:
            return []
        
        # Start with first query
        result = set(queries[0])
        
        # Intersect with each subsequent query
        for query_result in queries[1:]:
            result &= set(query_result)
        
        return list(result)
    
    def or_(self, *queries: List[SceneNode]) -> List[SceneNode]:
        """
        Union of multiple queries (features in ANY result).
        
        Args:
            *queries: Multiple query result lists
            
        Returns:
            List of SceneNode instances in any query
            
        Example:
            # Find mountains OR hills
            mountains = engine.find_by_type("mountain")
            hills = engine.find_by_type("hill")
            result = engine.or_(mountains, hills)
        """
        if not queries:
            return []
        
        # Union all queries
        result = set()
        for query_result in queries:
            result |= set(query_result)
        
        return list(result)
    
    def not_(self, query_result: List[SceneNode]) -> List[SceneNode]:
        """
        Complement of a query (features NOT in result).
        
        Args:
            query_result: Query result to complement
            
        Returns:
            List of SceneNode instances NOT in query_result
            
        Example:
            # Find all features EXCEPT mountains
            mountains = engine.find_by_type("mountain")
            others = engine.not_(mountains)
        """
        all_features = set(self.graph.get_all_features())
        query_set = set(query_result)
        return list(all_features - query_set)
    
    # ==================== Helper Methods ====================
    
    def _get_queryable_nodes(self, feature_type: Optional[str] = None) -> List[SceneNode]:
        """
        Get nodes to query (filtered by type if specified).
        
        Args:
            feature_type: Optional type filter
            
        Returns:
            List of SceneNode instances
        """
        if feature_type:
            return self.graph.find_features_by_type(feature_type)
        else:
            return self.graph.get_all_features()
    
    def _get_feature_position(self, node: SceneNode) -> Optional[Tuple[int, int]]:
        """
        Extract position from feature node.
        
        Handles both point features (x, y) and box features (x0, y0, x1, y1).
        For box features, returns center point.
        
        Args:
            node: SceneNode instance
            
        Returns:
            (x, y) position or None if not available
        """
        # Try to get position from node data
        feat_data = node.get_data("feature")
        if feat_data:
            # Check for box coordinates (dunes, etc.)
            if "x0" in feat_data and "y0" in feat_data and "x1" in feat_data and "y1" in feat_data:
                # Return center of box
                x0, y0 = feat_data["x0"], feat_data["y0"]
                x1, y1 = feat_data["x1"], feat_data["y1"]
                return ((x0 + x1) // 2, (y0 + y1) // 2)
            # Check for point coordinates
            elif "x" in feat_data and "y" in feat_data:
                return (feat_data["x"], feat_data["y"])
        
        # Try direct node data
        if "x0" in node.data and "y0" in node.data and "x1" in node.data and "y1" in node.data:
            x0, y0 = node.data["x0"], node.data["y0"]
            x1, y1 = node.data["x1"], node.data["y1"]
            return ((x0 + x1) // 2, (y0 + y1) // 2)
        elif "x" in node.data and "y" in node.data:
            return (node.data["x"], node.data["y"])
        
        return None
    
    def _matches_filters(self, node: SceneNode, filters: Dict[str, Any]) -> bool:
        """
        Check if node matches metadata filters.
        
        Args:
            node: SceneNode to check
            filters: Dictionary of filters
            
        Returns:
            True if node matches all filters
        """
        for key, value in filters.items():
            node_value = node.get_data(key)
            
            # Handle operators
            if isinstance(value, dict):
                if not self._matches_operator(node_value, value):
                    return False
            elif node_value != value:
                return False
        
        return True
    
    def _matches_operator(self, node_value: Any, operator: Dict[str, Any]) -> bool:
        """
        Check if node value matches operator.
        
        Args:
            node_value: Value from node
            operator: Operator dictionary (e.g., {"$gt": 0.7})
            
        Returns:
            True if matches
        """
        if "$gt" in operator:
            return node_value is not None and node_value > operator["$gt"]
        elif "$lt" in operator:
            return node_value is not None and node_value < operator["$lt"]
        elif "$gte" in operator:
            return node_value is not None and node_value >= operator["$gte"]
        elif "$lte" in operator:
            return node_value is not None and node_value <= operator["$lte"]
        elif "$in" in operator:
            return node_value in operator["$in"]
        elif "$regex" in operator:
            if not isinstance(node_value, str):
                return False
            pattern = operator["$regex"]
            return bool(re.search(pattern, node_value))
        else:
            # Unknown operator, try direct match
            return node_value == operator
        
        return False
    
    # ==================== Convenience Methods ====================
    
    def count(self, query_result: List[SceneNode]) -> int:
        """Count query results."""
        return len(query_result)
    
    def get_feature_ids(self, query_result: List[SceneNode]) -> List[int]:
        """Extract feature IDs from query results."""
        feature_ids = []
        for node in query_result:
            feature_ids.extend(node.feature_ids)
        return list(set(feature_ids))  # Remove duplicates
    
    def get_positions(self, query_result: List[SceneNode]) -> List[Tuple[int, int]]:
        """Extract positions from query results."""
        positions = []
        for node in query_result:
            pos = self._get_feature_position(node)
            if pos:
                positions.append(pos)
        return positions
    
    def get_bounds(self, query_result: List[SceneNode]) -> Optional[Tuple[int, int, int, int]]:
        """
        Get bounding box of query results.
        
        Returns:
            (x0, y0, x1, y1) bounding box or None if no features
        """
        positions = self.get_positions(query_result)
        if not positions:
            return None
        
        xs = [x for x, y in positions]
        ys = [y for x, y in positions]
        
        return (min(xs), min(ys), max(xs), max(ys))
    
    def get_center(self, query_result: List[SceneNode]) -> Optional[Tuple[int, int]]:
        """
        Get center point of query results.
        
        Returns:
            (x, y) center point or None if no features
        """
        positions = self.get_positions(query_result)
        if not positions:
            return None
        
        xs = [x for x, y in positions]
        ys = [y for x, y in positions]
        
        return (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))
    
    # ==================== Relationship Queries ====================
    
    def find_by_relationship(self, relationship_type: str, 
                            source_entity_id: Optional[str] = None,
                            target_entity_id: Optional[str] = None) -> List[SceneNode]:
        """
        Find features by spatial relationship.
        
        Args:
            relationship_type: Relationship type ("between", "near", "left_of", etc.)
            source_entity_id: Filter by source entity
            target_entity_id: Filter by target entity
            
        Returns:
            List of SceneNode instances matching relationship
        """
        from .relationships import RelationshipType
        
        try:
            rel_type = RelationshipType(relationship_type.lower())
        except ValueError:
            return []
        
        relationships = self.graph.relationship_manager.find_relationships(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=rel_type
        )
        
        # Get feature IDs from relationships
        feature_ids = set()
        for rel in relationships:
            source_entity = self._get_entity_by_id(rel.source_entity_id)
            if source_entity:
                feature_ids.update(source_entity.feature_refs)
        
        # Convert to SceneNodes
        results = []
        for feature_id in feature_ids:
            node = self.graph.find_feature_by_id(feature_id)
            if node:
                results.append(node)
        
        return results
    
    def find_related_to(self, entity_id: str, 
                       relationship_type: Optional[str] = None) -> List[SceneNode]:
        """
        Find features related to an entity.
        
        Args:
            entity_id: Entity ID
            relationship_type: Optional relationship type filter
            
        Returns:
            List of SceneNode instances related to entity
        """
        from .relationships import RelationshipType
        
        rel_type = None
        if relationship_type:
            try:
                rel_type = RelationshipType(relationship_type.lower())
            except ValueError:
                pass
        
        # Find relationships where this entity is source or target
        source_rels = self.graph.relationship_manager.get_relationships_by_source(entity_id)
        target_rels = self.graph.relationship_manager.get_relationships_by_target(entity_id)
        
        all_rels = source_rels + target_rels
        
        if rel_type:
            all_rels = [r for r in all_rels if r.relationship_type == rel_type]
        
        # Collect related entity IDs
        related_entity_ids = set()
        for rel in all_rels:
            if rel.source_entity_id == entity_id:
                related_entity_ids.update(rel.target_entity_ids)
            else:
                related_entity_ids.add(rel.source_entity_id)
        
        # Get features from related entities
        feature_ids = set()
        for related_entity_id in related_entity_ids:
            entity = self._get_entity_by_id(related_entity_id)
            if entity:
                feature_ids.update(entity.feature_refs)
        
        # Convert to SceneNodes
        results = []
        for feature_id in feature_ids:
            node = self.graph.find_feature_by_id(feature_id)
            if node:
                results.append(node)
        
        return results
    
    def _get_entity_by_id(self, entity_id: str):
        """Get entity by ID."""
        from .entity_manager import EntityManager
        manager = EntityManager(self.graph)
        return manager.find_entity_by_id(entity_id)

