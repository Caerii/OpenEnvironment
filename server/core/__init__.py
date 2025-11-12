"""
Core domain types for terrain generation.

This module provides the foundational type-safe primitives used throughout
the terrain generation system.
"""

from .geometry import Position, Region, Circle

__all__ = [
    "Position",
    "Region",
    "Circle",
]

