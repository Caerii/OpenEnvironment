"""Inference and validation tools."""

from typing import Dict, Any, List


def infer_feature_parameters(
    scene_state: Dict[str, Any],
    feature_type: str,
    user_modifiers: List[str],
    position: List[int]
) -> Dict[str, Any]:
    """Infer appropriate parameters based on modifiers."""
    params = {}
    
    for mod in user_modifiers:
        if mod in ["tall", "high"]:
            params["height"] = 0.85
        elif mod in ["gentle", "low"]:
            params["height"] = 0.3
        elif mod in ["wide", "large"]:
            params["radius"] = 70
        elif mod in ["steep"]:
            params["steepness"] = 0.9
    
    return {"suggested_parameters": params}

def suggest_modification(
    scene_state: Dict[str, Any],
    feature_ids: List[int],
    modification_type: str,
    intensity: str = "moderate"
) -> Dict[str, Any]:
    """Suggest parameter changes for modifications."""
    multipliers = {"slightly": 1.1, "moderate": 1.3, "much": 1.6}
    mult = multipliers.get(intensity, 1.3)
    
    return {
        "modification_type": modification_type,
        "intensity": intensity,
        "multiplier": mult
    }

def validate_action(scene_state: Dict[str, Any], action: Dict) -> Dict[str, Any]:
    """Validate if action is semantically valid."""
    issues = []
    
    if "position" in action:
        pos = action["position"]
        if "coords" in pos:
            x, y = pos["coords"]
            if not (0 <= x <= 511) or not (0 <= y <= 511):
                issues.append("Position out of bounds (0-511)")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }

