"""Semantic Scene Graph System - Public API.

This module provides the main interface for the semantic scene graph system.
Import from here for all public APIs.

Example:
    from semantic.scene import TerrainSceneGraph
    
    graph = TerrainSceneGraph()
    graph.add_feature_group("Mountains", "the mountains")
"""

# Core graph structure
from .node import SceneNode
from .graph import TerrainSceneGraph

# Entity system
from .entity import SemanticEntity
from .entity_manager import EntityManager

# Reference resolution
from .reference_resolver import ReferenceResolver

# Query system
from .query import QueryEngine

# Relationships
from .relationships import RelationshipType, SpatialRelationship, RelationshipManager

# Relationship inference
from .relationship_inference import RelationshipInferencer

# Serialization
from .serialization import SceneGraphSerializer

# Integration
from .integration import SceneGraphIntegrator

__all__ = [
    # Core
    "SceneNode",
    "TerrainSceneGraph",
    
    # Entity system
    "SemanticEntity",
    "EntityManager",
    
    # Reference resolution
    "ReferenceResolver",
    
    # Relationships
    "RelationshipType",
    "SpatialRelationship",
    "RelationshipManager",
    "RelationshipInferencer",
    
    # Query system
    "QueryEngine",
    
    # Serialization
    "SceneGraphSerializer",
    
    # Integration
    "SceneGraphIntegrator",
]

