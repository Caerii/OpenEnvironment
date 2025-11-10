"""
Narrative generation system for geological storytelling.

This module provides tools for developing terrain narratives that guide
aesthetic and geologically plausible terrain generation.
"""

from .types import (
    TerrainNarrative,
    TerrainArchetype,
    GeologicalProcess,
    SpatialConstraints,
    FeatureComposition,
    CoherenceScores,
    AestheticGoal
)

from .archetypes import TERRAIN_ARCHETYPES, get_archetype

__all__ = [
    "TerrainNarrative",
    "TerrainArchetype",
    "GeologicalProcess",
    "SpatialConstraints",
    "FeatureComposition",
    "CoherenceScores",
    "AestheticGoal",
    "TERRAIN_ARCHETYPES",
    "get_archetype",
]

