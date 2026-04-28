"""
Evaluation package for terrain quality assessment.

Consolidates metrics computation, quality rubrics, and warning types.
"""

from .metrics import (
    compute_feature_metrics,
    evaluate_aesthetic_quality,
    compute_texture_metrics,
    evaluate_quality_rubric,
    summarize_quality_rubric,
    features_to_dicts,
    DEFAULT_QUALITY_RUBRIC,
)
from .warning_types import WarningCategory, QualityWarning, classify_warning

__all__ = [
    "compute_feature_metrics",
    "evaluate_aesthetic_quality",
    "compute_texture_metrics",
    "evaluate_quality_rubric",
    "summarize_quality_rubric",
    "features_to_dicts",
    "DEFAULT_QUALITY_RUBRIC",
    "WarningCategory",
    "QualityWarning",
    "classify_warning",
]
