"""
Feature domain objects for terrain generation.

This module provides type-safe feature representations, replacing the previous
dict-based approach with proper OOP abstractions.
"""

from .base import (
    Feature,
    FeatureType,
    FeatureIdentity,
    FeatureGeometry,
    FeatureAppearance,
)

__all__ = [
    "Feature",
    "FeatureType",
    "FeatureIdentity",
    "FeatureGeometry",
    "FeatureAppearance",
]

