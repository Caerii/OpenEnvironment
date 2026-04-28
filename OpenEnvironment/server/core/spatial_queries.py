"""
Shared spatial query handling for terrain features.

This module provides common spatial query logic used by both parsers.
Extracts duplicated code from semantic/parser.py and parsing.py.
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def handle_spatial_query(command: str, context: Optional[Dict] = None) -> Optional[Dict]:
    """
    Handle spatial query commands like "find features near the dunes".
    
    Args:
        command: User command string
        context: Optional terrain state with semantic_scene
    
    Returns:
        Query result dictionary or None if not a query command
    
    Examples:
        >>> handle_spatial_query("find features near the dunes", state)
        {"queries": [{"type": "near", "reference": "dunes", "results": [1,2,3]}]}
        
        >>> handle_spatial_query("show mountains in the left half", state)
        {"queries": [{"type": "region", "region": "left", "results": [4,5]}]}
    """
    # Must have scene graph to do spatial queries
    if not context or "semantic_scene" not in context:
        return None
    
    command_lower = command.lower()
    
    # Check for query keywords
    query_keywords = ["find", "show", "locate", "where", "what", "list"]
    if not any(keyword in command_lower for keyword in query_keywords):
        return None
    
    try:
        from .semantic.scene import SceneGraphSerializer, QueryEngine, ReferenceResolver
        
        # Load scene graph
        scene_graph = SceneGraphSerializer.from_dict(context["semantic_scene"])
        query_engine = QueryEngine(scene_graph)
        resolver = ReferenceResolver(scene_graph)
        
        result = {"queries": []}
        
        # Handle "near X" queries
        if "near" in command_lower:
            ref_text = extract_reference_from_command(command_lower)
            if ref_text:
                ref_ids = resolver.resolve(ref_text)
                if ref_ids:
                    # Use first reference
                    nearby = query_engine.find_near_feature(ref_ids[0], radius=150)
                    feature_ids = query_engine.get_feature_ids(nearby)
                    result["queries"].append({
                        "type": "near",
                        "reference": ref_text,
                        "reference_feature_ids": [ref_ids[0]],
                        "results": feature_ids,
                        "count": len(feature_ids)
                    })
        
        # Handle "between X and Y" queries
        elif "between" in command_lower:
            # Complex - would need to find two anchor entities
            # For now, return empty
            pass
        
        # Handle "in region" queries
        elif "in" in command_lower and any(word in command_lower for word in ["left", "right", "center", "half", "region"]):
            if "left" in command_lower:
                region_features = query_engine.find_within_region((0, 0, 256, 512))
                region_name = "left"
            elif "right" in command_lower:
                region_features = query_engine.find_within_region((256, 0, 512, 512))
                region_name = "right"
            else:
                region_features = query_engine.find_within_region((0, 0, 512, 512))
                region_name = "all"
            
            feature_ids = query_engine.get_feature_ids(region_features)
            result["queries"].append({
                "type": "region",
                "region": region_name,
                "results": feature_ids,
                "count": len(feature_ids)
            })
        
        if result["queries"]:
            return result
            
    except (ImportError, AttributeError, KeyError, ValueError) as e:
        logger.debug(f"Spatial query handling failed: {e}")
    
    return None


def extract_reference_from_command(command_lower: str) -> Optional[str]:
    """
    Extract entity reference from command.
    
    Args:
        command_lower: Lowercased command string
    
    Returns:
        Reference text or None
    
    Examples:
        >>> extract_reference_from_command("near the dunes")
        "dunes"
        
        >>> extract_reference_from_command("mountains on the ridge")
        "mountains"
    """
    # Common patterns for entity references
    patterns = [
        r"the\s+(\w+)",           # "the dunes"
        r"(\w+)\s+on\s+the",      # "mountains on the"
        r"(\w+)\s+near",          # "mountains near"
        r"near\s+(?:the\s+)?(\w+)",  # "near dunes" or "near the dunes"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, command_lower)
        if match:
            return match.group(1)
    
    return None

