"""
Semantic Tools for ReAct Reasoning.

This module provides MCP-style tools that the LLM can call during multi-turn reasoning
to understand the scene, calculate positions, resolve references, and make informed decisions.
"""

from .query_tools import (
    query_entities,
    get_feature_details,
    get_spatial_relationships,
    query_scene_summary
)

from .spatial_tools import (
    calculate_position,
    calculate_region_positions,
    get_region_bounds
)

from .resolution_tools import (
    resolve_reference,
    resolve_temporal_reference,
    resolve_attribute_filter
)

from .inference_tools import (
    infer_feature_parameters,
    suggest_modification,
    validate_action
)

__all__ = [
    # Query tools
    'query_entities',
    'get_feature_details',
    'get_spatial_relationships',
    'query_scene_summary',
    
    # Spatial tools
    'calculate_position',
    'calculate_region_positions',
    'get_region_bounds',
    
    # Resolution tools
    'resolve_reference',
    'resolve_temporal_reference',
    'resolve_attribute_filter',
    
    # Inference tools
    'infer_feature_parameters',
    'suggest_modification',
    'validate_action',
]

