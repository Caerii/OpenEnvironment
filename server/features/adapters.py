"""
Adapters between typed Feature objects and Dict-based legacy system.

This bridges the new type-safe world with the existing dict-based code,
allowing gradual migration without breaking anything.
"""

import logging
from typing import Dict, Any

from .base import Feature, FeatureType
from .mountain import Mountain


logger = logging.getLogger(__name__)


def feature_to_dict(feature: Feature) -> Dict[str, Any]:
    """
    Convert typed Feature to dict (for backward compatibility).
    
    This allows new code to create typed features while old code
    still expects dicts.
    
    Args:
        feature: Typed Feature instance
        
    Returns:
        Dictionary compatible with existing system
        
    Examples:
        >>> mountain = Mountain(...)
        >>> feat_dict = feature_to_dict(mountain)
        >>> feat_dict["type"]
        'mountain'
    """
    return feature.to_dict()


def feature_from_dict(data: Dict[str, Any]) -> Feature:
    """
    Convert dict to typed Feature (adapter for migration).
    
    This allows old code to pass dicts while new code works with types.
    
    Args:
        data: Dictionary with feature properties
        
    Returns:
        Typed Feature instance
        
    Raises:
        ValueError: If feature type is unknown or data is invalid
        NotImplementedError: If feature type not yet implemented
        
    Examples:
        >>> data = {"id": 1, "type": "mountain", "x": 256, "y": 256}
        >>> feature = feature_from_dict(data)
        >>> isinstance(feature, Mountain)
        True
    """
    feature_type = data.get("type")
    
    if not feature_type:
        raise ValueError("Feature dict missing 'type' field")
    
    try:
        ftype = FeatureType(feature_type)
    except ValueError:
        raise ValueError(f"Unknown feature type: {feature_type}")
    
    # Dispatch to concrete class
    if ftype == FeatureType.MOUNTAIN:
        return Mountain.from_dict(data)
    elif ftype == FeatureType.VALLEY:
        # TODO: Implement when Valley is ready
        raise NotImplementedError("Valley not yet implemented in typed system")
    elif ftype == FeatureType.DUNES:
        # TODO: Implement when Dunes is ready
        raise NotImplementedError("Dunes not yet implemented in typed system")
    elif ftype == FeatureType.CLIFF:
        # TODO: Implement when Cliff is ready
        raise NotImplementedError("Cliff not yet implemented in typed system")
    elif ftype == FeatureType.PLATEAU:
        # TODO: Implement when Plateau is ready
        raise NotImplementedError("Plateau not yet implemented in typed system")
    elif ftype == FeatureType.CANYON:
        # TODO: Implement when Canyon is ready
        raise NotImplementedError("Canyon not yet implemented in typed system")
    else:
        raise ValueError(f"Unhandled feature type: {ftype}")


def validate_feature_dict(data: Dict[str, Any]) -> bool:
    """
    Check if a dict can be converted to a typed Feature.
    
    Used to gradually migrate dict-based code.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        True if dict is valid and type is implemented, False otherwise
        
    Examples:
        >>> validate_feature_dict({"type": "mountain", "x": 100, "y": 200, "id": 1})
        True
        >>> validate_feature_dict({"type": "unknown", "x": 100})
        False
    """
    try:
        feature_from_dict(data)
        return True
    except (ValueError, KeyError, TypeError, NotImplementedError):
        return False


def is_feature_type_implemented(feature_type: str) -> bool:
    """
    Check if a feature type has a typed implementation.
    
    Args:
        feature_type: Feature type string (e.g., "mountain")
        
    Returns:
        True if implemented, False otherwise
        
    Examples:
        >>> is_feature_type_implemented("mountain")
        True
        >>> is_feature_type_implemented("valley")
        False
    """
    try:
        ftype = FeatureType(feature_type)
    except ValueError:
        return False
    
    # Only mountain is currently implemented
    return ftype == FeatureType.MOUNTAIN

