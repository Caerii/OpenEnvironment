"""ReferenceResolver - Natural language reference resolution.

This module resolves natural language references like "the dunes" or
"the mountains" into feature IDs by using multiple resolution strategies.

Resolution Strategies (in order):
1. Entity label match (exact or contains)
2. Ordinal resolution ("first", "last", "second") - Checked early to avoid type conflicts
3. Most recent resolution ("most recent", "latest")
4. Entity keyword match (after ordinal check to avoid substring matches)
5. Feature type match (fallback - last resort)
"""

import re
from typing import List, Optional
from .graph import TerrainSceneGraph
from .entity_manager import EntityManager


class ReferenceResolver:
    """
    Resolves natural language references to feature IDs.
    
    Multi-strategy resolution system that tries multiple approaches
    to find the features referenced by natural language text.
    
    Example:
        resolver = ReferenceResolver(scene_graph)
        feature_ids = resolver.resolve("the dunes")
        # Returns: [1, 2, 3]
    """
    
    def __init__(self, scene_graph: TerrainSceneGraph):
        """
        Initialize reference resolver.
        
        Args:
            scene_graph: TerrainSceneGraph instance
        """
        self.scene_graph = scene_graph
        self.entity_manager = EntityManager(scene_graph)
    
    def resolve(self, text: str) -> List[int]:
        """
        Resolve natural language reference to feature IDs.
        
        Tries multiple strategies in order:
        1. Entity label match
        2. Entity keyword match
        3. Feature type match
        4. Ordinal resolution
        5. Most recent resolution
        
        Args:
            text: Natural language reference (e.g., "the dunes", "the mountains",
                  "last mountain", "first valley")
                  
        Returns:
            List of feature IDs (empty if not found)
            
        Example:
            resolver.resolve("the dunes") → [1, 2, 3]
            resolver.resolve("the mountains") → [4, 5]
            resolver.resolve("last mountain") → [5]
        """
        if not text or not text.strip():
            return []
        
        text_lower = text.lower().strip()
        
        # Strategy 1: Entity label match (exact or contains)
        result = self._resolve_by_label(text_lower)
        if result:
            return result
        
        # Strategy 2: Ordinal resolution ("first", "last", "second") - Check BEFORE keyword/type
        # because "first mountain" should resolve to ordinal, not all mountains
        result = self._resolve_ordinal(text_lower)
        if result:
            return result
        
        # Strategy 3: Most recent resolution - Check BEFORE keyword/type
        result = self._resolve_most_recent(text_lower)
        if result:
            return result
        
        # Strategy 4: Entity keyword match (after ordinal check)
        result = self._resolve_by_keyword(text_lower)
        if result:
            return result
        
        # Strategy 5: Feature type match (fallback - last resort)
        result = self._resolve_by_type(text_lower)
        if result:
            return result
        
        return []
    
    def _resolve_by_label(self, text: str) -> List[int]:
        """
        Strategy 1: Find entity by exact label match.
        
        Args:
            text: Text to match
            
        Returns:
            Feature IDs or empty list
        """
        entity = self.entity_manager.find_entity_by_label(text)
        if entity:
            return entity.feature_refs.copy()
        
        # Try without "the" prefix
        if text.startswith("the "):
            text_without_the = text[4:].strip()
            entity = self.entity_manager.find_entity_by_label(text_without_the)
            if entity:
                return entity.feature_refs.copy()
        
        return []
    
    def _resolve_by_keyword(self, text: str) -> List[int]:
        """
        Strategy 2: Find entities matching keywords.
        
        Args:
            text: Text to match
            
        Returns:
            Feature IDs or empty list
        """
        entities = self.entity_manager.find_entities_matching(text)
        
        # If multiple matches, prefer exact keyword matches
        exact_matches = [e for e in entities if any(kw == text for kw in e.keywords)]
        if exact_matches:
            # Return first exact match's feature refs
            return exact_matches[0].feature_refs.copy()
        
        # Return first match's feature refs
        if entities:
            return entities[0].feature_refs.copy()
        
        return []
    
    def _resolve_by_type(self, text: str) -> List[int]:
        """
        Strategy 3: Find features by type.
        
        Maps common terms to feature types:
        - "mountain", "mountains", "peak", "peaks" → "mountain"
        - "hill", "hills" → "hill"
        - "valley", "valleys" → "valley"
        - "dune", "dunes", "sand" → "dunes"
        - etc.
        
        Args:
            text: Text to match
            
        Returns:
            Feature IDs or empty list
        """
        # Remove "the" prefix
        text_clean = text.replace("the ", "").strip()
        
        # Map text to feature types
        type_mapping = {
            "mountain": "mountain",
            "mountains": "mountain",
            "peak": "mountain",
            "peaks": "mountain",
            "hill": "hill",
            "hills": "hill",
            "valley": "valley",
            "valleys": "valley",
            "dune": "dunes",
            "dunes": "dunes",
            "sand": "dunes",
            "desert": "dunes",
            "cliff": "cliff",
            "cliffs": "cliff",
            "mesa": "mesa",
            "mesas": "mesa",
            "plateau": "plateau",
            "plateaus": "plateau",
            "canyon": "canyon",
            "canyons": "canyon",
            "slope": "slope",
            "slopes": "slope",
        }
        
        # Try direct mapping
        feature_type = type_mapping.get(text_clean)
        if feature_type:
            return self._get_feature_ids_by_type(feature_type)
        
        # Try partial matching
        for key, feature_type in type_mapping.items():
            if key in text_clean or text_clean in key:
                return self._get_feature_ids_by_type(feature_type)
        
        return []
    
    def _get_feature_ids_by_type(self, feature_type: str) -> List[int]:
        """
        Get all feature IDs of a given type.
        
        Args:
            feature_type: Feature type (e.g., "mountain", "valley")
            
        Returns:
            List of feature IDs
        """
        feature_nodes = self.scene_graph.find_features_by_type(feature_type)
        feature_ids = []
        for node in feature_nodes:
            feature_ids.extend(node.feature_ids)
        return feature_ids
    
    def _resolve_ordinal(self, text: str) -> List[int]:
        """
        Strategy 4: Resolve ordinal references ("first", "last", "second").
        
        Supports:
        - "first mountain", "first valley"
        - "last mountain", "last valley"
        - "second mountain", "third hill"
        - "the last one", "the first one"
        
        Args:
            text: Text to match
            
        Returns:
            Feature IDs or empty list
        """
        # Ordinal patterns
        ordinal_patterns = [
            (r"^(first|1st)\s+(\w+)", 1),  # "first mountain" → 1st mountain
            (r"^(second|2nd)\s+(\w+)", 2),  # "second mountain" → 2nd mountain
            (r"^(third|3rd)\s+(\w+)", 3),   # "third mountain" → 3rd mountain
            (r"^(fourth|4th)\s+(\w+)", 4),
            (r"^(fifth|5th)\s+(\w+)", 5),
            (r"^(last|final)\s+(\w+)", -1),  # "last mountain" → last mountain
            (r"^the\s+(first|1st)\s+(\w+)", 1),
            (r"^the\s+(last|final)\s+(\w+)", -1),
            (r"^the\s+(last|final)\s+one", -1),  # "the last one"
        ]
        
        for pattern, ordinal in ordinal_patterns:
            match = re.search(pattern, text)
            if match:
                # Extract feature type
                groups = match.groups()
                if len(groups) >= 2:
                    feature_type_text = groups[-1]  # Last group is feature type
                    if feature_type_text == "one":
                        # "the last one" - need to infer type from context
                        # For now, try to find most recent entity
                        entities = self.entity_manager.get_all_entities()
                        if entities:
                            most_recent = max(entities, key=lambda e: e.created_at)
                            if ordinal == -1:
                                return most_recent.feature_refs.copy()
                            else:
                                # For first/second/etc, return first entity's refs
                                return entities[0].feature_refs.copy()
                    else:
                        # Resolve by type and ordinal
                        return self._resolve_by_type_and_ordinal(feature_type_text, ordinal)
        
        return []
    
    def _resolve_by_type_and_ordinal(self, feature_type_text: str, ordinal: int) -> List[int]:
        """
        Resolve features by type and ordinal position.
        
        Args:
            feature_type_text: Text describing feature type
            ordinal: Ordinal position (1=first, 2=second, -1=last)
            
        Returns:
            Feature IDs or empty list
        """
        # Map text to feature type
        type_mapping = {
            "mountain": "mountain", "mountains": "mountain",
            "hill": "hill", "hills": "hill",
            "valley": "valley", "valleys": "valley",
            "dune": "dunes", "dunes": "dunes",
            "cliff": "cliff", "cliffs": "cliff",
            "mesa": "mesa", "mesas": "mesa",
            "plateau": "plateau", "plateaus": "plateau",
            "canyon": "canyon", "canyons": "canyon",
            "slope": "slope", "slopes": "slope",
        }
        
        feature_type = type_mapping.get(feature_type_text)
        if not feature_type:
            return []
        
        # Get all features of this type
        feature_nodes = self.scene_graph.find_features_by_type(feature_type)
        
        if not feature_nodes:
            return []
        
        # Sort by creation order (assuming feature IDs are sequential)
        # Or by creation time if available
        feature_nodes.sort(key=lambda n: n.feature_ids[0] if n.feature_ids else 0)
        
        if ordinal == -1:
            # Last one
            return feature_nodes[-1].feature_ids.copy()
        elif ordinal > 0:
            # Nth one (1-indexed)
            if ordinal <= len(feature_nodes):
                return feature_nodes[ordinal - 1].feature_ids.copy()
        
        return []
    
    def _resolve_most_recent(self, text: str) -> List[int]:
        """
        Strategy 5: Resolve "most recent" references.
        
        Supports:
        - "most recent mountain"
        - "latest mountain"
        - "newest valley"
        
        Args:
            text: Text to match
            
        Returns:
            Feature IDs or empty list
        """
        # Check for "most recent", "latest", "newest"
        recent_patterns = [
            r"most\s+recent\s+(\w+)",
            r"latest\s+(\w+)",
            r"newest\s+(\w+)",
            r"recent\s+(\w+)",
        ]
        
        for pattern in recent_patterns:
            match = re.search(pattern, text)
            if match:
                feature_type_text = match.group(1)
                return self._resolve_by_type_and_ordinal(feature_type_text, -1)
        
        return []
    
    def resolve_by_label(self, label: str) -> List[int]:
        """
        Resolve reference by entity label only.
        
        Args:
            label: Entity label (e.g., "the dunes")
            
        Returns:
            Feature IDs or empty list
        """
        return self._resolve_by_label(label.lower().strip())
    
    def resolve_by_type(self, feature_type: str) -> List[int]:
        """
        Resolve reference by feature type only.
        
        Args:
            feature_type: Feature type (e.g., "mountain", "valley")
            
        Returns:
            Feature IDs or empty list
        """
        return self._get_feature_ids_by_type(feature_type)
    
    def resolve_most_recent(self, feature_type: str) -> List[int]:
        """
        Resolve most recent feature of a given type.
        
        Args:
            feature_type: Feature type (e.g., "mountain", "valley")
            
        Returns:
            Feature IDs or empty list
        """
        return self._resolve_by_type_and_ordinal(feature_type, -1)
    
    def resolve_ordinal(self, feature_type: str, ordinal: int) -> List[int]:
        """
        Resolve Nth feature of a given type.
        
        Args:
            feature_type: Feature type (e.g., "mountain", "valley")
            ordinal: Ordinal position (1=first, 2=second, -1=last)
            
        Returns:
            Feature IDs or empty list
        """
        return self._resolve_by_type_and_ordinal(feature_type, ordinal)

