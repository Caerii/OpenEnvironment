"""
Evaluation package for terrain quality assessment.

This package contains warning_types.py. The main evaluation functions
are in the parent evaluation.py module (not this package).
"""

# Only export warning_types from this package
from .warning_types import WarningCategory, QualityWarning, classify_warning

__all__ = [
    "WarningCategory",
    "QualityWarning",
    "classify_warning",
]

