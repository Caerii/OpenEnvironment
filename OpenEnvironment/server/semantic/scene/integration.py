"""Scene Graph Integration - Helpers for terrain.py integration.

This module provides helper functions to bridge between the terrain generation
system and the semantic scene graph system.

Functions:
- Extract labels from commands
- Extract keywords from commands/actions
- Create entities from actions
- Update scene graph for actions
"""

import re
from typing import Dict, List, Optional
from .graph import TerrainSceneGraph
from .entity import SemanticEntity
from .entity_manager import EntityManager
from .relationship_inference import RelationshipInferencer


class SceneGraphIntegrator:
    """
    Integration helpers for connecting scene graph to terrain system.
    
    Provides utilities to:
    - Extract semantic labels from user commands
    - Extract keywords from commands/actions
    - Create semantic entities from actions
    - Update scene graph automatically
    """
    
    @staticmethod
    def extract_label(command: str, action: Dict) -> str:
        """
        Extract semantic label from command and action.
        
        Examples:
        - "create a desert with rolling dunes" + action{type:"dunes"} → "the dunes"
        - "add two mountains on the left" + action{type:"mountain", count:2} → "two mountains"
        - "add a valley" + action{type:"valley"} → "the valley"
        
        Args:
            command: User's original command
            action: Parsed action dictionary
            
        Returns:
            Semantic label string
        """
        feature_type = action.get("type", "")
        count = action.get("count", 1)
        
        if not feature_type:
            return ""
        
        # Pluralize feature type
        if feature_type == "dunes":
            plural = "dunes"
        elif feature_type.endswith("s"):
            plural = feature_type
        else:
            plural = feature_type + "s"
        
        # Try to extract from command context
        command_lower = command.lower()
        
        # Look for patterns like "two mountains", "the dunes", etc.
        patterns = [
            rf"(\w+)\s+{plural}",  # "two mountains", "three hills"
            rf"the\s+{plural}",    # "the mountains"
            rf"a\s+{feature_type}",  # "a mountain"
            rf"an\s+{feature_type}",  # "an valley"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                groups = match.groups()
                if groups:
                    prefix = groups[0]
                    # Check if prefix is a number word
                    number_words = {
                        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                        "a": 1, "an": 1, "couple": 2, "few": 2, "several": 3
                    }
                    if prefix in number_words:
                        num = number_words[prefix]
                        if num == 1:
                            return f"the {plural}"
                        else:
                            return f"{prefix} {plural}"
                    elif prefix == "the":
                        return f"the {plural}"
        
        # Default based on count
        if count == 1:
            return f"the {plural}"
        else:
            # Try to convert count to word
            count_words = {
                1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"
            }
            count_word = count_words.get(count, str(count))
            return f"{count_word} {plural}"
    
    @staticmethod
    def extract_keywords(command: str, action: Dict) -> List[str]:
        """
        Extract keywords from command and action.
        
        Keywords are terms that help identify and reference the entity.
        
        Args:
            command: User's original command
            action: Parsed action dictionary
            
        Returns:
            List of keyword strings
        """
        keywords = []
        feature_type = action.get("type", "")
        
        if not feature_type:
            return keywords
        
        # Add feature type as keyword
        keywords.append(feature_type)
        
        # Add plural form
        if feature_type == "dunes":
            keywords.append("dunes")
        elif feature_type.endswith("s"):
            keywords.append(feature_type)
        else:
            keywords.append(feature_type + "s")
        
        # Extract descriptive words from command
        command_lower = command.lower()
        
        # Common terrain descriptors
        descriptors = {
            "mountain": ["mountain", "mountains", "peak", "peaks", "summit"],
            "hill": ["hill", "hills", "mound", "rise"],
            "valley": ["valley", "valleys", "depression", "hollow"],
            "dunes": ["dune", "dunes", "sand", "desert", "sandy", "arid"],
            "cliff": ["cliff", "cliffs", "bluff", "escarpment"],
            "mesa": ["mesa", "mesas", "butte"],
            "plateau": ["plateau", "plateaus", "tableland"],
            "canyon": ["canyon", "canyons", "gorge", "ravine"],
            "slope": ["slope", "slopes", "incline", "hillside"],
            "crater": ["crater", "craters", "impact", "volcanic"],
            "ridge": ["ridge", "ridges", "spine", "crest"],
            "ravine": ["ravine", "ravines", "gully", "chasm"],
            "volcano": ["volcano", "volcanoes", "volcanic", "cone"],
            "pass": ["pass", "passes", "mountain pass", "gap"],
            "mound": ["mound", "mounds", "burial mound", "hillock"],
            "basin": ["basin", "basins", "depression", "bowl"],
            "pinnacle": ["pinnacle", "pinnacles", "spire", "spike"],
            "spur": ["spur", "spurs", "ridge", "extension"],
            "terraces": ["terrace", "terraces", "terracing", "steps", "step-like"],
        }
        
        if feature_type in descriptors:
            keywords.extend(descriptors[feature_type])
        
        # Extract adjectives from command
        adjectives = [
            "rolling", "steep", "tall", "large", "small", "deep", "wide",
            "narrow", "dramatic", "gentle", "rugged", "smooth"
        ]
        
        for adj in adjectives:
            if adj in command_lower:
                keywords.append(adj)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    @staticmethod
    def create_entity_from_action(action: Dict, feature_ids: List[int], 
                                 command: str, scene_graph: Optional[TerrainSceneGraph] = None) -> SemanticEntity:
        """
        Create a semantic entity from an action.
        
        Args:
            action: Parsed action dictionary
            feature_ids: List of feature IDs created by this action
            command: User's original command
            scene_graph: Optional scene graph for unique ID generation
            
        Returns:
            SemanticEntity instance
        """
        if not feature_ids:
            raise ValueError("Cannot create entity without feature IDs")
        
        feature_type = action.get("type", "unknown")
        count = action.get("count", len(feature_ids))
        
        # Generate unique entity ID
        # Try to find a unique ID by checking existing entities
        base_id = f"{feature_type}_{count}"
        entity_id = base_id
        
        if scene_graph:
            manager = EntityManager(scene_graph)
            counter = 1
            while manager.find_entity_by_id(entity_id) is not None:
                entity_id = f"{base_id}_{counter}"
                counter += 1
        else:
            # Fallback: use feature IDs to make it more unique
            entity_id = f"{base_id}_{min(feature_ids)}_{len(feature_ids)}"
        
        # Determine entity type
        if count > 1:
            entity_type = "group"
        else:
            entity_type = "feature"
        
        # Extract label
        label = SceneGraphIntegrator.extract_label(command, action)
        
        # Create entity
        entity = SemanticEntity(entity_id, entity_type, label)
        
        # Add feature references
        entity.add_feature_refs(feature_ids)
        
        # Add keywords
        keywords = SceneGraphIntegrator.extract_keywords(command, action)
        entity.add_keywords(keywords)
        
        # Set user intent
        entity.set_user_intent(command)
        
        # Set description
        description = f"{count} {feature_type}{'s' if count > 1 else ''}"
        if action.get("position", {}).get("region"):
            description += f" in the {action['position']['region']}"
        entity.set_description(description)
        
        return entity
    
    @staticmethod
    def update_scene_graph_for_action(scene_graph: TerrainSceneGraph,
                                     action: Dict, feature_ids: List[int],
                                     command: str, feature_data_list: Optional[List[Dict]] = None):
        """
        Update scene graph for an action (add entity, update feature nodes).
        
        Args:
            scene_graph: TerrainSceneGraph instance
            action: Parsed action dictionary
            feature_ids: List of feature IDs created by this action
            command: User's original command
            feature_data_list: Optional list of feature dictionaries (for storing positions/metadata)
        """
        if not feature_ids:
            return
        
        manager = EntityManager(scene_graph)
        
        # Create entity (pass scene_graph for unique ID generation)
        entity = SceneGraphIntegrator.create_entity_from_action(
            action, feature_ids, command, scene_graph
        )
        
        # Add entity to scene graph
        manager.add_entity(entity)
        
        # Infer and store spatial relationships
        inferencer = RelationshipInferencer(scene_graph)
        inferred_relationships = inferencer.infer_relationships_for_entity(
            entity.id, feature_ids, command
        )
        
        # Link relationships to entities
        for rel in inferred_relationships:
            entity.add_relationship_id(rel.relationship_id)
            # Also add to target entities
            for target_entity_id in rel.target_entity_ids:
                target_entity = manager.find_entity_by_id(target_entity_id)
                if target_entity:
                    target_entity.add_relationship_id(rel.relationship_id)
        
        # Update feature nodes (ensure they exist in graph)
        feature_type = action.get("type", "unknown")
        group_name = f"{feature_type.capitalize()}_Group"
        
        # Ensure group exists
        group = scene_graph.get_feature_group(group_name)
        if group is None:
            group = scene_graph.add_feature_group(group_name, entity.label)
        
        # Add/update feature nodes with feature data
        feature_data_map = {}
        if feature_data_list:
            for feat_data in feature_data_list:
                if "id" in feat_data:
                    feature_data_map[feat_data["id"]] = feat_data
        
        for feature_id in feature_ids:
            feature_node = scene_graph.find_feature_by_id(feature_id)
            if feature_node is None:
                # Create feature node
                feature_node = group.add_child(f"feature_{feature_id}")
                feature_node.feature_ids = [feature_id]
                feature_node.set_data("type", feature_type)
            
            # Store feature data for spatial queries
            if feature_id in feature_data_map:
                feat_data = feature_data_map[feature_id]
                # Store full feature data
                feature_node.set_data("feature", feat_data)
                # Store position directly for easy access
                if "x" in feat_data and "y" in feat_data:
                    feature_node.set_data("x", feat_data["x"])
                    feature_node.set_data("y", feat_data["y"])
                # Store box coordinates (for dunes, etc.)
                if "x0" in feat_data and "y0" in feat_data and "x1" in feat_data and "y1" in feat_data:
                    feature_node.set_data("x0", feat_data["x0"])
                    feature_node.set_data("y0", feat_data["y0"])
                    feature_node.set_data("x1", feat_data["x1"])
                    feature_node.set_data("y1", feat_data["y1"])
                # Store other metadata
                for key in ["radius", "height", "depth", "width", "length", "amp", "freq", "angle", "orientation", "steepness", "flatness", "falloff"]:
                    if key in feat_data:
                        feature_node.set_data(key, feat_data[key])
    
    @staticmethod
    def resolve_target_features(scene_graph: TerrainSceneGraph,
                               action: Dict) -> Optional[List[int]]:
        """
        Resolve target feature IDs from action.
        
        Uses target_feature_ids if provided, otherwise resolves via ReferenceResolver.
        
        Args:
            scene_graph: TerrainSceneGraph instance
            action: Parsed action dictionary
            
        Returns:
            List of feature IDs or None if not found
        """
        # Check if LLM provided target_feature_ids
        if action.get("target_feature_ids"):
            return action["target_feature_ids"]
        
        # Try to resolve from action type and modifiers
        if action.get("kind") in ("modify", "remove"):
            # Look for target reference in modifiers or type
            target = action.get("target")
            if target:
                from .reference_resolver import ReferenceResolver
                resolver = ReferenceResolver(scene_graph)
                return resolver.resolve(target)
            
            # Fall back to type-based resolution
            feature_type = action.get("type")
            if feature_type:
                # Get most recent of type
                from .reference_resolver import ReferenceResolver
                resolver = ReferenceResolver(scene_graph)
                return resolver.resolve_most_recent(feature_type)
        
        return None

    @staticmethod
    def cleanup_for_removed_features(scene_graph: TerrainSceneGraph,
                                    removed_feature_ids: List[int]):
        """
        Comprehensive cleanup when features are removed.
        
        This is the main cleanup function that should be called after
        features are removed. It handles:
        - Removing feature nodes from scene graph
        - Cleaning up entities (removing feature refs, removing orphaned entities)
        - Cleaning up relationships involving removed features
        
        Args:
            scene_graph: TerrainSceneGraph instance
            removed_feature_ids: List of feature IDs that were removed
        """
        if not removed_feature_ids:
            return
        
        manager = EntityManager(scene_graph)
        
        # 1. Remove feature nodes from scene graph
        for feature_id in removed_feature_ids:
            scene_graph.remove_feature(feature_id)
        
        # 2. Clean up entities (remove feature refs, remove orphaned entities)
        removed_entity_ids = manager.cleanup_for_removed_features(removed_feature_ids)
        
        # 3. Clean up relationships for removed features
        manager.cleanup_relationships_for_features(removed_feature_ids)
        
        # 4. Clean up relationships for removed entities
        for entity_id in removed_entity_ids:
            manager.cleanup_relationships_for_entity(entity_id)
        
        return {
            "removed_feature_ids": removed_feature_ids,
            "removed_entity_ids": removed_entity_ids
        }