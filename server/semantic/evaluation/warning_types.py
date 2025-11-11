"""
Structured warning types for quality evaluation.

Replaces brittle string matching with type-safe warning categories.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class WarningCategory(Enum):
    """Categories of quality warnings."""
    
    # Texture warnings
    TEXTURE_COVERAGE = "texture_coverage"  # Coverage outside desired range
    TEXTURE_DISTRIBUTION = "texture_distribution"  # Poor texture distribution
    TEXTURE_ALIGNMENT = "texture_alignment"  # Texture not aligned with geometry
    
    # Composition warnings
    FEATURE_COUNT = "feature_count"  # Too few/many features
    DIVERSITY = "diversity"  # Low feature type diversity
    SPATIAL_EXTENT = "spatial_extent"  # Features too clustered
    HEIGHT_VARIATION = "height_variation"  # Low height variation


@dataclass
class QualityWarning:
    """Structured quality warning."""
    
    category: WarningCategory
    message: str
    severity: float  # 0.0-1.0, how severe the issue is
    
    # Optional context
    affected_texture: Optional[str] = None  # For texture warnings
    affected_features: Optional[List[int]] = None  # Feature IDs affected
    suggested_fix: Optional[str] = None  # Suggested remediation
    
    def __str__(self) -> str:
        """String representation for backward compatibility."""
        return self.message
    
    def is_texture_warning(self) -> bool:
        """Check if this is a texture-related warning."""
        return self.category in [
            WarningCategory.TEXTURE_COVERAGE,
            WarningCategory.TEXTURE_DISTRIBUTION,
            WarningCategory.TEXTURE_ALIGNMENT,
        ]


def classify_warning(warning_text: str) -> WarningCategory:
    """
    Classify a warning text into a category.
    
    This is a fallback for backward compatibility with string warnings.
    """
    warning_lower = warning_text.lower()
    
    # Texture warnings
    if "texture" in warning_lower or "coverage" in warning_lower:
        if any(t in warning_lower for t in ["grass", "rock", "sand", "snow"]):
            return WarningCategory.TEXTURE_COVERAGE
        elif "distribution" in warning_lower or "entropy" in warning_lower:
            return WarningCategory.TEXTURE_DISTRIBUTION
        elif "align" in warning_lower or "correlation" in warning_lower:
            return WarningCategory.TEXTURE_ALIGNMENT
        else:
            return WarningCategory.TEXTURE_COVERAGE  # Default
    
    # Composition warnings
    if "feature count" in warning_lower or "add more" in warning_lower:
        return WarningCategory.FEATURE_COUNT
    elif "diversity" in warning_lower or "contrasting" in warning_lower:
        return WarningCategory.DIVERSITY
    elif "extent" in warning_lower or "spread" in warning_lower:
        return WarningCategory.SPATIAL_EXTENT
    elif "height" in warning_lower or "elevation" in warning_lower or "variance" in warning_lower:
        return WarningCategory.HEIGHT_VARIATION
    
    # Default
    return WarningCategory.TEXTURE_COVERAGE

