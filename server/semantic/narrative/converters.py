"""
Converters between narrative types and action dicts.

THE BRIDGE: Connects narrative system to terrain generation pipeline.
"""

from typing import Dict, List, Any
import logging

try:
    from ...domain.models import Feature, Position, FeatureParameters
except ImportError:
    from domain.models import Feature, Position, FeatureParameters  # type: ignore

logger = logging.getLogger(__name__)


def _ensure_feature(feat: Any) -> Feature:
    if isinstance(feat, Feature):
        return feat
    if isinstance(feat, dict):
        data = feat.copy()
        data.setdefault("id", 0)
        return Feature.from_dict(data)
    if hasattr(feat, "to_dict") and hasattr(feat, "parameters"):
        return feat  # duck type Feature-like objects
    raise TypeError(f"Unsupported feature type: {type(feat)}")


def _ensure_position_obj(position: Any) -> Position:
    if isinstance(position, Position):
        return position
    if isinstance(position, dict):
        return Position.from_dict(position)
    if hasattr(position, "x") and hasattr(position, "y"):
        return position  # Assume Position-like object
    raise TypeError(f"Unsupported position type: {type(position)}")


def composition_to_actions(composition: 'FeatureComposition') -> List[Dict]:
    """
    Convert FeatureComposition → action dicts for main pipeline.
    
    This is the CRITICAL BRIDGE between narrative system and terrain generation.
    
    Args:
        composition: Generated feature composition with typed Features
    
    Returns:
        List of action dicts for execute_add_actions()
    
    Example:
        ```python
        composition = generate_from_narrative(narrative, {}, seed=42)
        actions = composition_to_actions(composition)
        # Now actions can be passed to execute_add_actions()
        ```
    """
    actions = []
    
    # Add focal point (hero feature)
    if composition.focal_point:
        action = _feature_to_action(_ensure_feature(composition.focal_point), label="focal")
        if action:
            actions.append(action)
    
    # Add supporting features (context)
    for i, feat in enumerate(composition.supporting_features):
        action = _feature_to_action(_ensure_feature(feat), label=f"supporting_{i}")
        if action:
            actions.append(action)
    
    # Add accent features (visual interest)
    for i, feat in enumerate(composition.accent_features):
        action = _feature_to_action(_ensure_feature(feat), label=f"accent_{i}")
        if action:
            actions.append(action)
    
    # Add background features (if any)
    for i, feat in enumerate(composition.background_features):
        action = _feature_to_action(_ensure_feature(feat), label=f"background_{i}")
        if action:
            actions.append(action)
    
    # Add foreground features (if any)
    for i, feat in enumerate(composition.foreground_features):
        action = _feature_to_action(_ensure_feature(feat), label=f"foreground_{i}")
        if action:
            actions.append(action)
    
    logger.info(f"Converted composition to {len(actions)} actions")
    
    return actions


def _feature_to_action(feat: 'Feature', label: str = "") -> Dict:
    """
    Convert single Feature → action dict.
    
    Args:
        feat: Typed Feature instance
        label: Optional label for scene graph tracking
    
    Returns:
        Action dict compatible with AddFeatureCommand
    """
    try:
        feat = _ensure_feature(feat)
        position_dict = _position_to_dict(feat.position)
        action = {
            "kind": "add",
            "type": feat.type,
            "position": position_dict,
            "modifiers": _params_to_modifiers(feat.parameters),
            "count": 1
        }

        # Backward compatibility: expose absolute position at top-level when available.
        if "x" in position_dict and "y" in position_dict:
            action["x"] = position_dict["x"]
            action["y"] = position_dict["y"]
        
        # Add label if provided (for scene graph)
        if label:
            action["label"] = label
        
        return action
    
    except (AttributeError, KeyError) as e:
        logger.warning(f"Failed to convert feature to action: {e}")
        return None


def _position_to_dict(position) -> Dict:
    """Convert Position → position dict."""
    try:
        position = _ensure_position_obj(position)

        if position.is_absolute():
            return {"x": position.x, "y": position.y}
        elif position.is_region():
            return {"region": position.region}
        elif position.is_relative():
            return {
                "relative_to": position.relative_to,
                "offset_x": position.offset_x,
                "offset_y": position.offset_y
            }
        else:
            # Default to center
            return {"region": "center"}
    except AttributeError:
        # Fallback: try to extract x, y directly
        if hasattr(position, 'x') and hasattr(position, 'y'):
            return {"x": position.x, "y": position.y}
        return {"region": "center"}


def _params_to_modifiers(params: 'FeatureParameters') -> Dict:
    """
    Convert FeatureParameters → modifier dict.
    
    Translates typed parameters back to modifier format for variation engine.
    """
    if isinstance(params, dict):
        params = FeatureParameters.from_dict(params)

    modifiers: Dict[str, Any] = {}

    # Helper to copy attribute if present
    def _maybe(attr: str):
        value = getattr(params, attr, None)
        if value is not None:
            modifiers[attr] = value

    # Core geometry
    for attr in ("height", "depth", "radius", "steepness", "width", "length"):
        _maybe(attr)

    # Orientation / directionality
    for attr in ("orientation", "direction"):
        _maybe(attr)

    # Noise / variation parameters
    for attr in ("use_noise", "falloff", "amp", "freq", "angle"):
        _maybe(attr)

    # Any additional parameters stored in params.params
    extra = getattr(params, "params", None)
    if isinstance(extra, dict):
        # Do not overwrite explicit attributes unless provided
        for key, value in extra.items():
            modifiers.setdefault(key, value)

    return modifiers


def actions_to_composition(actions: List[Dict], seed: int = 42) -> 'FeatureComposition':
    """
    REVERSE: Convert action dicts → FeatureComposition.
    
    Useful for round-trip testing and for converting old actions to new format.
    
    Args:
        actions: List of action dicts
        seed: Seed for feature generation
    
    Returns:
        FeatureComposition with typed Features
    """
    from ...engine.feature_registry import FeatureRegistry
    from .types import FeatureComposition
    
    focal = None
    supporting = []
    accents = []
    
    for i, action in enumerate(actions):
        try:
            # Create feature using registry
            ftype = action["type"]
            pos = action["position"]
            modifiers = action.get("modifiers", {})
            
            cx = pos.get("x", 256)
            cy = pos.get("y", 256)
            
            feat = FeatureRegistry.create_feature(ftype, cx, cy, modifiers, seed + i)
            
            if feat is None:
                continue
            
            # Categorize based on label or order
            label = action.get("label", "")
            if "focal" in label or i == 0:
                focal = feat
            elif "supporting" in label or i < 4:
                supporting.append(feat)
            else:
                accents.append(feat)
        
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to convert action to feature: {e}")
            continue
    
    return FeatureComposition(
        focal_point=focal,
        supporting_features=supporting,
        accent_features=accents,
        background_features=[],
        foreground_features=[],
        depth_layers=[],
        negative_space_zones=[],
        golden_ratio_used=False,
        rule_of_thirds_used=False,
        leading_lines=[],
        rhythmic_elements=[],
        variation_pattern="organic"
    )

