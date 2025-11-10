"""
Narrative generation tools for ReAct agent.

These tools enable the agent to generate aesthetically coherent terrain
using geological storytelling and composition principles.
"""

import time
import logging
from typing import Dict, Any, Iterable, List

from .base import ToolResult, success_result, error_result
from ..evaluation import compute_feature_metrics, evaluate_aesthetic_quality, features_to_dicts

logger = logging.getLogger(__name__)


def generate_narrative_composition(
    scene_state: Dict[str, Any],
    command: str
) -> Dict[str, Any]:
    """
    Generate a narrative-driven feature composition.
    
    This tool creates aesthetically coherent terrain by:
    1. Matching command to terrain archetype (Wind Architect, Water's Legacy, etc.)
    2. Developing geological narrative with natural forces
    3. Generating composed features (focal, supporting, accent)
    4. Applying composition principles (golden ratio, rule of thirds)
    
    Use this for AESTHETIC/CREATIVE commands like:
    - "create dramatic mountains"
    - "design a serene valley"
    - "build a rugged landscape"
    - "make beautiful rolling dunes"
    
    Do NOT use for PRECISE commands like:
    - "add mountain at 100 100" (use spatial tools instead)
    - "make the mountain taller" (use query + modify tools)
    
    Args:
        scene_state: Current scene state for context
        command: User's aesthetic/creative command
    
    Returns:
        ToolResult with:
        {
            "actions": List[Dict],           # Ready-to-use action dictionaries
            "narrative": str,                # The geological story
            "archetype": str,                # Matched archetype name
            "focal_type": str,               # Hero feature type
            "supporting_types": List[str],   # Supporting feature types
            "feature_count": int,            # Total features generated
            "composition_strategy": str      # Composition approach used
        }
    
    Example:
        Input: "create dramatic mountains"
        Output: {
            "actions": [
                {"kind": "add", "type": "mountain", "count": 1, "position": {...}, "modifiers": {"height": 0.9}},
                {"kind": "add", "type": "mountain", "count": 2, "position": {...}, "modifiers": {"height": 0.7}},
                {"kind": "add", "type": "cliff", "count": 1, "position": {...}}
            ],
            "narrative": "Ancient tectonic uplift created towering peaks...",
            "archetype": "Ancient Uplift",
            "focal_type": "mountain",
            "supporting_types": ["mountain", "cliff"],
            "feature_count": 4
        }
    """
    start_time = time.time()
    
    logger.info(f"Narrative tool: Generating composition for '{command[:50]}...'")
    
    try:
        # Step 1: Develop terrain narrative
        from ..narrative.narrative_dev import develop_terrain_narrative
        
        logger.debug("Step 1: Developing terrain narrative...")
        narrative = develop_terrain_narrative(command, scene_state)
        
        if not narrative:
            logger.warning("Failed to develop narrative from command")
            return error_result(
                "Failed to develop narrative - command may be too vague or not aesthetic in nature",
                "generate_narrative_composition",
                start_time
            )
        
        logger.info(f"Narrative developed: archetype={narrative.archetype.name}, hero={narrative.hero_feature_type}")
        
        # Step 2: Generate feature composition from narrative
        from ..narrative.generation import generate_from_narrative
        
        logger.debug("Step 2: Generating feature composition...")
        composition = generate_from_narrative(narrative, scene_state, seed=scene_state.get("seed", 42))
        
        if not composition:
            logger.warning("Failed to generate composition from narrative")
            return error_result(
                "Failed to generate feature composition from narrative",
                "generate_narrative_composition",
                start_time
            )
        
        # Count features
        feature_count = 0
        if composition.focal_point:
            feature_count += 1
        feature_count += len(composition.supporting_features)
        feature_count += len(composition.accent_features)
        feature_count += len(composition.background_features)
        feature_count += len(composition.foreground_features)
        
        logger.info(f"Composition generated: {feature_count} features total")
        
        # Step 3: Convert composition to action dictionaries
        from ..narrative.converters import composition_to_actions
        
        logger.debug("Step 3: Converting composition to actions...")
        actions = composition_to_actions(composition)
        
        if not actions:
            logger.warning("Failed to convert composition to actions")
            return error_result(
                "Failed to convert composition to actions - composition may be empty",
                "generate_narrative_composition",
                start_time
            )
        
        logger.info(f"Actions generated: {len(actions)} actions ready")
        logger.debug(f"Narrative actions: {actions}")

        composition_features = _composition_features(composition)
        feature_dicts = features_to_dicts(composition_features)
        metrics = compute_feature_metrics(feature_dicts)
        quality = evaluate_aesthetic_quality(metrics)

        # Build result
        result_data = {
            "actions": actions,
            "narrative": narrative.story,
            "archetype": narrative.archetype.name,
            "focal_type": narrative.hero_feature_type,
            "supporting_types": narrative.supporting_feature_types,
            "accent_types": narrative.accent_feature_types,
            "feature_count": feature_count,
            "composition_strategy": f"Focal: {narrative.hero_feature_type}, Supporting: {len(composition.supporting_features)}, Accent: {len(composition.accent_features)}",
            "aesthetic_goals": [goal.value for goal in narrative.aesthetic_goals],
            "mood": narrative.mood,
            "golden_ratio_used": composition.golden_ratio_used,
            "rule_of_thirds_used": composition.rule_of_thirds_used,
            "metrics": metrics,
            "quality": quality,
        }
        
        logger.info(
            f"Narrative composition complete: {len(actions)} actions, "
            f"{feature_count} features, archetype={narrative.archetype.name}"
        )
        
        return success_result(
            result_data,
            "generate_narrative_composition",
            start_time
        )
    
    except ImportError as e:
        logger.error(f"Import error in narrative tool: {e}", exc_info=True)
        return error_result(
            f"Narrative system not available: {str(e)}",
            "generate_narrative_composition",
            start_time
        )
    except Exception as e:
        logger.error(f"Unexpected error in narrative tool: {e}", exc_info=True)
        return error_result(
            f"Unexpected error during narrative generation: {str(e)}",
            "generate_narrative_composition",
            start_time
        )


# Future tool for iterative refinement
def refine_narrative_composition(
    scene_state: Dict[str, Any],
    composition: Dict[str, Any],
    feedback: str
) -> Dict[str, Any]:
    """
    Refine an existing narrative composition based on feedback.
    
    This tool allows iterative improvement of generated terrain.
    
    Args:
        scene_state: Current scene state
        composition: Previous composition result
        feedback: User feedback or aesthetic critique
    
    Returns:
        Refined composition with updated actions
    
    Note: This is a placeholder for future implementation.
          The agent can currently only generate new compositions.
    """
    start_time = time.time()
    
    # TODO: Implement iterative refinement
    return error_result(
        "Composition refinement not yet implemented - generate new composition instead",
        "refine_narrative_composition",
        start_time
    )


def should_use_narrative(command: str) -> bool:
    """Heuristic to determine if a command should use the narrative system."""
    if not command:
        return False

    cmd_lower = command.lower()

    narrative_keywords = [
        "create", "design", "build", "generate", "craft", "make",
        "beautiful", "dramatic", "serene", "rugged", "majestic",
        "stunning", "gorgeous", "breathtaking", "picturesque",
        "landscape", "scene", "terrain", "vista", "composition",
        "organic", "natural", "interesting", "varied"
    ]

    simple_keywords = [
        "add", "remove", "delete", "modify", "taller", "shorter",
        "wider", "narrower", "mountain", "valley", "dunes", "cliff",
        "plateau", "canyon"
    ]

    has_narrative = any(kw in cmd_lower for kw in narrative_keywords)
    has_simple = any(kw in cmd_lower for kw in simple_keywords if kw not in {"mountain", "valley", "dunes", "cliff", "plateau", "canyon"})

    if has_narrative and not has_simple:
        return True

    if has_narrative and has_simple:
        narrative_score = sum(cmd_lower.count(kw) for kw in narrative_keywords)
        simple_score = sum(cmd_lower.count(kw) for kw in simple_keywords)
        return narrative_score >= simple_score

    # Commands mentioning landscape/scene without narrative adjectives but lacking explicit modifiers
    if "landscape" in cmd_lower or "scene" in cmd_lower:
        return True

    return False


def _composition_features(composition: Any) -> Iterable[Any]:
    features: List[Any] = []
    if getattr(composition, "focal_point", None):
        features.append(composition.focal_point)
    features.extend(getattr(composition, "supporting_features", []) or [])
    features.extend(getattr(composition, "accent_features", []) or [])
    return features

