"""
Helper functions for feature modification.

Extracted from terrain.py to support FeatureGenerator.modify_feature() implementations.
"""
from typing import Dict
from .config import RES


def apply_modifier_to_param(
    feat: Dict,
    param_name: str,
    modifiers: Dict,
    max_value: float,
    is_int: bool = False,
    modifier_keyword: str = None
) -> bool:
    """
    Apply percentage or keyword modifier to a feature parameter.
    
    Checks for both percentage modifiers (e.g., "height_percent": 20)
    and keyword modifiers (e.g., "taller": True).
    
    Args:
        feat: Feature dictionary (modified in-place)
        param_name: Parameter name (e.g., "height", "radius", "width")
        modifiers: Modifier dictionary
        max_value: Maximum allowed value for this parameter
        is_int: Whether to round to integer
        modifier_keyword: Keyword modifier to check (default: auto-detect from param_name)
    
    Returns:
        True if parameter was modified, False otherwise
    """
    # Auto-detect keyword if not provided
    if modifier_keyword is None:
        keyword_map = {
            "height": "taller",
            "depth": "deeper",
            "radius": "wider",
            "width": "wider",
            "base_height": "taller",
            "base_radius": "wider"
        }
        modifier_keyword = keyword_map.get(param_name, "wider")
    
    # Check if parameter exists in feature
    if param_name not in feat:
        return False
    
    current_value = feat[param_name]
    percent_key = f"{param_name}_percent"
    
    # Priority 1: Percentage modifier
    if modifiers.get(percent_key) is not None:
        multiplier = 1.0 + modifiers[percent_key] / 100.0
        new_value = current_value * multiplier
    # Priority 2: Keyword modifier
    elif modifiers.get(modifier_keyword):
        new_value = current_value * 1.3
    else:
        return False  # No modifier for this parameter
    
    # Apply max limit and type conversion
    new_value = min(max_value, new_value)
    feat[param_name] = int(new_value) if is_int else new_value
    
    return True

