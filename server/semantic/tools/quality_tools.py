"""
Quality evaluation and refinement tools for ReAct agent.

These tools enable the agent to evaluate terrain quality and refine
compositions based on quality feedback.
"""

import copy
import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from .base import ToolResult, success_result, error_result

# Import from evaluation.py module directly (avoiding package conflict)
# evaluation.py is a module, evaluation/ is a package - we need the module
import importlib.util
import sys
from pathlib import Path

# Import evaluation.py as a module (not the package)
evaluation_module_path = Path(__file__).parent.parent / "evaluation.py"
spec = importlib.util.spec_from_file_location("semantic.evaluation_module", evaluation_module_path)
evaluation_module = importlib.util.module_from_spec(spec)
sys.modules["semantic.evaluation_module"] = evaluation_module
spec.loader.exec_module(evaluation_module)

# Import functions from the module
compute_feature_metrics = evaluation_module.compute_feature_metrics
compute_texture_metrics = evaluation_module.compute_texture_metrics
evaluate_quality_rubric = evaluation_module.evaluate_quality_rubric
summarize_quality_rubric = evaluation_module.summarize_quality_rubric
features_to_dicts = evaluation_module.features_to_dicts
DEFAULT_QUALITY_RUBRIC = evaluation_module.DEFAULT_QUALITY_RUBRIC
from ..config import (
    TEXTURE_COVERAGE_THRESHOLDS,
    TEXTURE_DIFF_THRESHOLD,
    TEXTURE_GAP_MIN_PIXELS,
    MAX_FEATURES_TO_ANALYZE,
    NEARBY_FEATURE_RADIUS,
    MAX_NEARBY_FEATURES_TO_SUGGEST,
    get_parameter_modification,
    TERRAIN_CENTER_X,
    TERRAIN_CENTER_Y,
    DEFAULT_SEED,
    DEFAULT_QUALITY_THRESHOLD,
)
from ..state.initializer import StateInitializer
from ..features.types import (
    get_features_for_texture,
    is_rock_feature,
    is_sand_feature,
    get_texture_contribution,
)
# Import from evaluation package (evaluation/warning_types.py)
from ..evaluation.warning_types import (
    WarningCategory,
    QualityWarning,
    classify_warning,
)
try:
    from ..rubric_evolution import RubricEvolutionService
    RUBRIC_EVOLUTION_AVAILABLE = True
except ImportError:
    RUBRIC_EVOLUTION_AVAILABLE = False
    RubricEvolutionService = None

logger = logging.getLogger(__name__)


def evaluate_terrain_quality(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    render_preview: bool = True,
    command: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate terrain quality from proposed actions.
    
    This tool applies actions temporarily, renders terrain, and evaluates
    against the quality rubric. Use this to check if your generated
    terrain meets aesthetic quality standards.
    
    Args:
        scene_state: Current scene state
        actions: List of action dictionaries to evaluate
        render_preview: Whether to render heightmap/splatmap for texture metrics
    
    Returns:
        ToolResult with:
        {
            "overall_score": float,           # 0.0-1.0 overall quality
            "composition_score": float,       # Composition quality (0.0-1.0)
            "texture_score": float,          # Texture quality (0.0-1.0)
            "warnings": List[str],           # Quality warnings
            "details": Dict,                 # Detailed breakdown
            "meets_threshold": bool,         # Whether score >= 0.8
            "summary": str                   # Human-readable summary
        }
    
    Example:
        Input: actions=[{"kind": "add", "type": "mountain", ...}, ...]
        Output: {
            "overall_score": 0.75,
            "composition_score": 0.80,
            "texture_score": 0.70,
            "warnings": ["Feature diversity is low", "Height variation is minimal"],
            "meets_threshold": false
        }
    """
    start_time = time.time()
    
    logger.info(f"Evaluating quality for {len(actions)} actions")
    
    try:
        if not actions:
            return error_result(
                "No actions provided to evaluate",
                "evaluate_terrain_quality",
                start_time
            )
        
        # Compute feature metrics from actions
        # Convert actions to feature dicts for metrics
        feature_dicts = []
        for action in actions:
            if action.get("kind") == "add":
                feature_dict = {
                    "type": action.get("type"),
                    "x": action.get("x") or action.get("position", {}).get("x", 0),
                    "y": action.get("y") or action.get("position", {}).get("y", 0),
                    **action.get("modifiers", {})
                }
                feature_dicts.append(feature_dict)
        
        feature_metrics = compute_feature_metrics(feature_dicts)
        
        # Initialize texture metrics (will be computed if render_preview=True)
        texture_metrics = {
            "channel_coverage": {},
            "coverage_entropy": 0.0,
            "rock_slope_corr": 0.0,
            "snow_height_corr": 0.0,
            "sand_low_corr": 0.0,
        }
        
        # Render terrain if requested
        if render_preview:
            try:
                heightmap, splatmap = _render_terrain_preview(actions, scene_state)
                if heightmap is not None and splatmap is not None:
                    texture_metrics = compute_texture_metrics(heightmap, splatmap)
                    logger.info("Computed texture metrics from rendered preview")
                else:
                    logger.warning("Failed to render preview, using default texture metrics")
            except Exception as e:
                logger.warning(f"Failed to render preview: {e}", exc_info=True)
        
        # Get context-aware rubric - prefer narrative context if available
        rubric = None
        narrative_meta = scene_state.get("_narrative_meta", {})
        narrative_constraints = scene_state.get("_narrative", {})
        
        # Build command from narrative if available and no explicit command
        if narrative_meta and not command:
            archetype = narrative_meta.get("archetype", "")
            goals = " ".join(narrative_meta.get("aesthetic_goals", []))
            command = f"{archetype} {goals}".strip()
            logger.info(f"Using narrative context for quality evaluation: {command}")
        
        # Get archetype and goals from narrative_meta (preferred over command string)
        archetype_name = None
        aesthetic_goals_list = None
        if narrative_meta:
            archetype_name = narrative_meta.get("archetype", "")
            aesthetic_goals_list = narrative_meta.get("aesthetic_goals", [])
        
        if (command or archetype_name) and RUBRIC_EVOLUTION_AVAILABLE:
            try:
                import os
                gemini_key = os.environ.get("GEMINI_API_KEY")
                if gemini_key:
                    evolution_service = RubricEvolutionService(gemini_key)
                    # Pass archetype + goals directly (preferred) or fallback to command
                    context_rubric = evolution_service.generate_context_rubric(
                        command or "",
                        DEFAULT_QUALITY_RUBRIC,
                        archetype=archetype_name,
                        aesthetic_goals=aesthetic_goals_list
                    )
                    # Extract the adapted rubric from context
                    context_info = context_rubric.get("_context", {})
                    if context_info:
                        # Merge context thresholds into base rubric
                        rubric = _merge_context_rubric(DEFAULT_QUALITY_RUBRIC, context_info)
                        context_type = context_info.get('context_type', 'unknown')
                        logger.info(f"Using context-aware rubric for: {context_type} (archetype={archetype_name or 'none'})")
            except Exception as e:
                logger.warning(f"Failed to generate context rubric: {e}, using default", exc_info=True)
        
        # Check against narrative constraints if available
        if narrative_constraints:
            # Validate feature types match narrative preferences
            feature_prefs = narrative_constraints.get("feature_preferences", {})
            # Log for debugging - will be used in refinement feedback
            logger.debug(f"Narrative constraints available: archetype={narrative_constraints.get('archetype')}, "
                        f"feature_prefs={list(feature_prefs.keys())}")
        
        # Evaluate against quality rubric
        quality_result = evaluate_quality_rubric(feature_metrics, texture_metrics, rubric)
        
        overall_score = quality_result.get("overall_score", 0.0)
        composition_score = quality_result.get("categories", {}).get("composition", {}).get("score", 0.0)
        texture_score = quality_result.get("categories", {}).get("textures", {}).get("score", 0.0)
        warnings = quality_result.get("warnings", [])
        
        # Generate summary
        summary = summarize_quality_rubric(quality_result, max_warnings=5)
        
        result_data = {
            "overall_score": round(overall_score, 3),
            "composition_score": round(composition_score, 3),
            "texture_score": round(texture_score, 3),
            "warnings": warnings,
            "details": quality_result.get("categories", {}),
            "meets_threshold": overall_score >= DEFAULT_QUALITY_THRESHOLD,
            "summary": summary,
            "feature_metrics": feature_metrics,
            "texture_metrics": texture_metrics if render_preview else None,
        }
        
        logger.info(
            f"Quality evaluation complete: overall={overall_score:.3f}, "
            f"composition={composition_score:.3f}, texture={texture_score:.3f}"
        )
        
        return success_result(
            result_data,
            "evaluate_terrain_quality",
            start_time
        )
    
    except Exception as e:
        logger.error(f"Quality evaluation failed: {e}", exc_info=True)
        return error_result(
            f"Quality evaluation failed: {str(e)}",
            "evaluate_terrain_quality",
            start_time
        )


def refine_composition(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    quality_warnings: List[str],
    max_refinements: int = 5
) -> Dict[str, Any]:
    """
    Refine terrain composition based on quality warnings.
    
    This tool analyzes quality warnings and suggests refinements to improve
    the terrain composition. Use this after evaluate_terrain_quality when
    quality score is below 0.8.
    
    Args:
        scene_state: Current scene state
        actions: Original actions to refine
        quality_warnings: List of warning messages from quality evaluation
        max_refinements: Maximum number of refinements to apply
    
    Returns:
        ToolResult with:
        {
            "refined_actions": List[Dict],   # Refined action list
            "changes_made": List[str],        # Description of changes
            "expected_improvement": str       # Expected quality improvement
        }
    
    Example:
        Input: 
            actions=[...],
            quality_warnings=["Feature diversity is low", "Height variation is minimal"]
        Output: {
            "refined_actions": [...],
            "changes_made": [
                "Added 2 diverse feature types",
                "Increased height variation by 0.15"
            ]
        }
    """
    start_time = time.time()
    
    logger.info(f"Refining composition based on {len(quality_warnings)} warnings")
    
    try:
        if not actions:
            return error_result(
                "No actions provided to refine",
                "refine_composition",
                start_time
            )
        
        refined_actions = copy.deepcopy(actions)
        changes_made = []
        
        # Analyze warnings and apply refinements
        # CRITICAL: Check texture issues FIRST (most important bottleneck)
        # Convert string warnings to structured warnings
        structured_warnings = []
        for warning in quality_warnings:
            if isinstance(warning, str):
                category = classify_warning(warning)
                structured_warnings.append(QualityWarning(
                    category=category,
                    message=warning,
                    severity=0.5  # Default severity
                ))
            elif isinstance(warning, QualityWarning):
                structured_warnings.append(warning)
            else:
                # Fallback
                structured_warnings.append(QualityWarning(
                    category=WarningCategory.TEXTURE_COVERAGE,
                    message=str(warning),
                    severity=0.5
                ))
        
        # Separate texture warnings from others
        texture_warnings = [w for w in structured_warnings if w.is_texture_warning()]
        other_warnings = [w for w in structured_warnings if not w.is_texture_warning()]
        
        # Process texture warnings first
        texture_fixed = False
        if texture_warnings:
            logger.info(f"Processing {len(texture_warnings)} texture warnings (highest priority)")
            
            # Try texture analysis and parameter modification first
            try:
                # Analyze texture-feature relationships
                texture_analysis_result = analyze_texture_feature_relationship(
                    scene_state, refined_actions, render_preview=True
                )
                
                if texture_analysis_result.get("success"):
                    texture_analysis = texture_analysis_result.get("data", {})
                    texture_gaps = texture_analysis.get("texture_gaps", [])
                    
                    # Build modifications from texture gaps
                    modifications = []
                    for gap in texture_gaps[:3]:  # Top 3 gaps
                        suggested_changes = gap.get("suggested_changes", [])
                        modifications.extend(suggested_changes)
                    
                    # Apply parameter modifications
                    if modifications:
                        mod_result = modify_feature_parameters(
                            scene_state, refined_actions, modifications
                        )
                        if mod_result.get("success"):
                            mod_data = mod_result.get("data", {})
                            refined_actions = mod_data.get("refined_actions", refined_actions)
                            changes_made.extend(mod_data.get("changes_made", []))
                            logger.info(f"Applied {len(modifications)} parameter modifications for texture")
                            texture_fixed = True
            
            except Exception as e:
                logger.warning(f"Texture analysis failed, using fallback: {e}", exc_info=True)
            
            # Fallback: Add features for texture balance (if analysis didn't work)
            if not texture_fixed:
                added = _add_features_for_texture_balance(refined_actions, scene_state)
                if added:
                    changes_made.append(f"Added {len(added)} features to improve texture distribution")
                    refined_actions.extend(added)
                    texture_fixed = True
                else:
                    # Last resort: Adjust positions (less effective)
                    refined_actions = _adjust_positions_for_extent(refined_actions)
                    changes_made.append("Adjusted feature positions (texture optimization attempted)")
                    texture_fixed = True
        
        # Process other warnings using structured categories
        for warning in other_warnings[:max_refinements]:
            if warning.category == WarningCategory.FEATURE_COUNT:
                added = _add_supporting_features(refined_actions, scene_state)
                if added:
                    changes_made.append(f"Added {len(added)} supporting features")
                    refined_actions.extend(added)
            
            elif warning.category == WarningCategory.DIVERSITY:
                added = _add_diverse_features(refined_actions, scene_state)
                if added:
                    changes_made.append(f"Added {len(added)} diverse feature types")
                    refined_actions.extend(added)
            
            elif warning.category == WarningCategory.SPATIAL_EXTENT:
                refined_actions = _adjust_positions_for_extent(refined_actions)
                changes_made.append("Adjusted feature positions to increase spatial spread")
            
            elif warning.category == WarningCategory.HEIGHT_VARIATION:
                refined_actions = _adjust_heights_for_variation(refined_actions)
                changes_made.append("Increased height variation across features")
        
        if not changes_made:
            changes_made.append("No automatic refinements could be applied - consider manual adjustments")
        
        result_data = {
            "refined_actions": refined_actions,
            "changes_made": changes_made,
            "expected_improvement": (
                "Expected quality improvement: +0.1-0.3. Re-evaluate with evaluate_terrain_quality."
            ),
            "original_action_count": len(actions),
            "refined_action_count": len(refined_actions),
        }
        
        logger.info(f"Refinement complete: {len(changes_made)} changes made")
        
        return success_result(
            result_data,
            "refine_composition",
            start_time
        )
    
    except Exception as e:
        logger.error(f"Composition refinement failed: {e}", exc_info=True)
        return error_result(
            f"Refinement failed: {str(e)}",
            "refine_composition",
            start_time
        )


def render_preview(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Render terrain preview from actions.
    
    This tool applies actions and renders heightmap/splatmap previews.
    Use this to visualize terrain before finalizing actions.
    
    Args:
        scene_state: Current scene state
        actions: Actions to render
    
    Returns:
        ToolResult with:
        {
            "heightmap_preview": str,        # Base64 encoded preview (optional)
            "splatmap_preview": str,          # Base64 encoded preview (optional)
            "dimensions": Dict,               # Heightmap dimensions
            "stats": Dict                     # Basic statistics
        }
    """
    start_time = time.time()
    
    logger.info(f"Rendering preview for {len(actions)} actions")
    
    try:
        heightmap, splatmap = _render_terrain_preview(actions, scene_state)
        
        if heightmap is None or splatmap is None:
            return error_result(
                "Failed to render terrain preview",
                "render_preview",
                start_time
            )
        
        # Compute basic stats
        height_min = float(heightmap.min())
        height_max = float(heightmap.max())
        height_mean = float(heightmap.mean())
        height_std = float(heightmap.std())
        
        result_data = {
            "dimensions": {
                "width": int(heightmap.shape[1]),
                "height": int(heightmap.shape[0])
            },
            "stats": {
                "height_min": round(height_min, 3),
                "height_max": round(height_max, 3),
                "height_mean": round(height_mean, 3),
                "height_std": round(height_std, 3),
            },
            "splatmap_channels": {
                "grass": float(splatmap[:, :, 0].mean()),
                "rock": float(splatmap[:, :, 1].mean()),
                "sand": float(splatmap[:, :, 2].mean()),
                "snow": float(splatmap[:, :, 3].mean()),
            },
            # Note: Base64 encoding can be added later if needed for visualization
            "preview_available": True,
        }
        
        logger.info("Preview rendered successfully")
        
        return success_result(
            result_data,
            "render_preview",
            start_time
        )
    
    except Exception as e:
        logger.error(f"Preview rendering failed: {e}", exc_info=True)
        return error_result(
            f"Preview rendering failed: {str(e)}",
            "render_preview",
            start_time
        )


# Helper functions

def _merge_context_rubric(base_rubric: Dict[str, Any], context_info: Dict[str, Any]) -> Dict[str, Any]:
    """Merge context-specific thresholds into base rubric."""
    import copy
    merged = copy.deepcopy(base_rubric)
    
    thresholds = context_info.get("thresholds", {})
    if not thresholds:
        return merged
    
    # Update composition thresholds
    comp = merged.setdefault("composition", {})
    for key, values in thresholds.items():
        # Skip texture coverage keys (handled separately)
        if key.endswith("_coverage") or key in ["coverage_targets", "entropy", "rock_slope_corr", "snow_height_corr", "sand_low_corr"]:
            continue
            
        if isinstance(values, dict):
            # Progressive thresholds: use minimum as threshold
            if "minimum" in values:
                comp[f"min_{key}"] = values["minimum"]
        elif isinstance(values, (int, float)):
            comp[f"min_{key}"] = values
    
    # Update texture thresholds
    tex = merged.setdefault("textures", {})
    
    # Handle coverage targets - convert individual coverage keys to coverage_targets format
    coverage_targets = tex.get("coverage_targets", {})
    
    # Check for individual coverage keys (sand_coverage, grass_coverage, etc.)
    for key, values in thresholds.items():
        if key.endswith("_coverage"):
            texture_name = key.replace("_coverage", "")
            if isinstance(values, dict):
                # Convert {minimum: [min, max], good: [min, max], excellent: [min, max]} to (min, max)
                if "minimum" in values:
                    min_val = values["minimum"]
                    if isinstance(min_val, (list, tuple)) and len(min_val) == 2:
                        coverage_targets[texture_name] = tuple(min_val)
                    elif isinstance(min_val, (int, float)):
                        # Single value - use as minimum, no maximum
                        coverage_targets[texture_name] = (min_val, 1.0)
            elif isinstance(values, (list, tuple)) and len(values) == 2:
                coverage_targets[texture_name] = tuple(values)
            elif isinstance(values, (int, float)):
                # Single value - use as minimum, no maximum
                coverage_targets[texture_name] = (values, 1.0)
    
    # Also check for coverage_targets key directly
    if "coverage_targets" in thresholds:
        ct_from_thresholds = thresholds["coverage_targets"]
        if isinstance(ct_from_thresholds, dict):
            for texture_name, bounds in ct_from_thresholds.items():
                # Handle different bounds formats
                if isinstance(bounds, dict):
                    # Handle dict format: {'minimum': [min, max], 'good': [min, max], ...}
                    if "minimum" in bounds:
                        min_val = bounds["minimum"]
                        if isinstance(min_val, (list, tuple)) and len(min_val) == 2:
                            coverage_targets[texture_name] = tuple(min_val)
                        elif isinstance(min_val, (int, float)):
                            coverage_targets[texture_name] = (min_val, 1.0)
                        else:
                            logger.debug(f"Skipping invalid minimum value for {texture_name}: {min_val}")
                    else:
                        logger.debug(f"No 'minimum' key in bounds dict for {texture_name}: {bounds}")
                elif isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                    coverage_targets[texture_name] = tuple(bounds)
                elif isinstance(bounds, (int, float)):
                    coverage_targets[texture_name] = (bounds, 1.0)
                else:
                    logger.warning(f"Invalid bounds format for {texture_name}: {bounds} (type: {type(bounds)})")
    
    # Ensure all coverage_targets are tuples
    for texture_name, bounds in list(coverage_targets.items()):
        if not isinstance(bounds, tuple) or len(bounds) != 2:
            logger.warning(f"Fixing invalid bounds for {texture_name}: {bounds}")
            if isinstance(bounds, list) and len(bounds) == 2:
                coverage_targets[texture_name] = tuple(bounds)
            else:
                # Remove invalid entry
                del coverage_targets[texture_name]
    
    if coverage_targets:
        tex["coverage_targets"] = coverage_targets
    
    # Handle other texture metrics
    for metric in ["entropy", "rock_slope_corr", "snow_height_corr", "sand_low_corr"]:
        if metric in thresholds:
            values = thresholds[metric]
            if isinstance(values, dict) and "minimum" in values:
                tex[f"min_{metric}"] = values["minimum"]
            elif isinstance(values, (int, float)):
                tex[f"min_{metric}"] = values
    
    return merged


def _render_terrain_preview(
    actions: List[Dict[str, Any]],
    scene_state: Dict[str, Any]
) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Render terrain from actions and return heightmap/splatmap."""
    try:
        # Use bootstrap to ensure proper import environment
        import sys
        from pathlib import Path
        
        # Ensure server directory is in path
        server_dir = Path(__file__).parent.parent.parent
        server_dir_str = str(server_dir)
        if server_dir_str not in sys.path:
            sys.path.insert(0, server_dir_str)
        
        # Bootstrap the environment first
        try:
            from server.bootstrap import ensure_bootstrapped
            ensure_bootstrapped()
        except ImportError:
            # If bootstrap not available, try direct import
            pass
        
        # Now try to import - bootstrap should have set up the environment
        try:
            from server.terrain import apply_actions
            from server.orchestration import build_final_terrain
        except ImportError:
            # Fallback: import directly (when server dir is parent)
            parent_dir = server_dir.parent
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            from server.terrain import apply_actions
            from server.orchestration import build_final_terrain
        
        # Create temporary state using StateInitializer
        temp_state = StateInitializer.initialize(scene_state)
        
        # Apply actions - apply_actions expects (command, state, ...) signature
        # Returns: (heightmap, updated_state, splatmap)
        try:
            heightmap, updated_state, splatmap = apply_actions(
                cmd="",  # Empty command, using direct_actions
                state=temp_state,
                direct_actions=actions,
                seed=temp_state.get("seed", DEFAULT_SEED)
            )
            
            if heightmap is None or splatmap is None:
                logger.warning("Failed to render terrain preview - got None values")
                return None, None
            
            logger.debug(f"Successfully rendered terrain: heightmap shape={heightmap.shape}, splatmap shape={splatmap.shape}")
            return heightmap, splatmap
        except Exception as render_error:
            logger.error(f"Error during apply_actions: {render_error}", exc_info=True)
            return None, None
    
    except Exception as e:
        logger.error(f"Terrain rendering error: {e}", exc_info=True)
        return None, None


def _add_supporting_features(
    existing_actions: List[Dict[str, Any]],
    scene_state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Add supporting features to increase feature count."""
    # Simple heuristic: add 1-2 supporting features
    # In a full implementation, this would use narrative generation
    added = []
    
    # Find focal feature position
    focal_pos = None
    for action in existing_actions:
        if action.get("label") == "focal":
            focal_pos = {
                "x": action.get("x") or action.get("position", {}).get("x", TERRAIN_CENTER_X),
                "y": action.get("y") or action.get("position", {}).get("y", TERRAIN_CENTER_Y),
            }
            break
    
    if not focal_pos:
        # Use scene center
        focal_pos = {"x": TERRAIN_CENTER_X, "y": TERRAIN_CENTER_Y}
    
    # Add 1-2 supporting features
    import random
    rng = random.Random(scene_state.get("seed", DEFAULT_SEED))
    
    supporting_types = ["valley", "plateau", "cliff"]
    for i in range(min(2, 5 - len(existing_actions))):
        if len(existing_actions) >= 5:
            break
        
        feature_type = rng.choice(supporting_types)
        angle = rng.uniform(0, 2 * np.pi)
        distance = rng.uniform(80, 120)
        
        new_action = {
            "kind": "add",
            "type": feature_type,
            "x": int(focal_pos["x"] + distance * np.cos(angle)),
            "y": int(focal_pos["y"] + distance * np.sin(angle)),
            "modifiers": {
                "height": rng.uniform(0.4, 0.7) if feature_type != "valley" else None,
                "depth": rng.uniform(0.3, 0.5) if feature_type == "valley" else None,
                "radius": rng.uniform(40, 70),
            },
            "label": f"supporting_{len(existing_actions)}"
        }
        added.append(new_action)
    
    return added


def _add_diverse_features(
    existing_actions: List[Dict[str, Any]],
    scene_state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Add features of different types to increase diversity."""
    existing_types = {action.get("type") for action in existing_actions}
    all_types = ["mountain", "valley", "dunes", "cliff", "plateau", "canyon"]
    missing_types = [t for t in all_types if t not in existing_types]
    
    if not missing_types:
        return []
    
    added = []
    import random
    rng = random.Random(scene_state.get("seed", DEFAULT_SEED))
    
    # Add 1-2 diverse types
    for feature_type in missing_types[:2]:
        if len(existing_actions) >= 6:
            break
        
        # Find a good position (away from existing features)
        x = rng.randint(100, 400)
        y = rng.randint(100, 400)
        
        new_action = {
            "kind": "add",
            "type": feature_type,
            "x": x,
            "y": y,
            "modifiers": {
                "height": rng.uniform(0.4, 0.8) if feature_type != "valley" else None,
                "depth": rng.uniform(0.3, 0.5) if feature_type == "valley" else None,
                "radius": rng.uniform(50, 80),
            },
            "label": f"diverse_{feature_type}"
        }
        added.append(new_action)
    
    return added


def _adjust_positions_for_extent(
    actions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Adjust feature positions to increase spatial extent."""
    if len(actions) < 2:
        return actions
    
    # Calculate current extent
    positions = []
    for action in actions:
        x = action.get("x") or action.get("position", {}).get("x", TERRAIN_CENTER_X)
        y = action.get("y") or action.get("position", {}).get("y", TERRAIN_CENTER_Y)
        positions.append((x, y))
    
    if not positions:
        return actions
    
    # Calculate centroid
    centroid_x = sum(p[0] for p in positions) / len(positions)
    centroid_y = sum(p[1] for p in positions) / len(positions)
    
    # Spread features further from centroid
    adjusted = []
    for i, action in enumerate(actions):
        new_action = copy.deepcopy(action)
        x = positions[i][0]
        y = positions[i][1]
        
        # Move away from centroid by 20-30%
        dx = x - centroid_x
        dy = y - centroid_y
        scale = 1.25  # Increase distance by 25%
        
        new_x = int(centroid_x + dx * scale)
        new_y = int(centroid_y + dy * scale)
        
        # Clamp to valid range
        new_x = max(50, min(462, new_x))
        new_y = max(50, min(462, new_y))
        
        if "x" in new_action:
            new_action["x"] = new_x
        if "y" in new_action:
            new_action["y"] = new_y
        if "position" in new_action:
            new_action["position"]["x"] = new_x
            new_action["position"]["y"] = new_y
        
        adjusted.append(new_action)
    
    return adjusted


def _adjust_heights_for_variation(
    actions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Adjust feature heights to increase variation."""
    if len(actions) < 2:
        return actions
    
    adjusted = []
    heights = []
    
    # Collect current heights
    for action in actions:
        modifiers = action.get("modifiers", {})
        height = modifiers.get("height") or modifiers.get("depth") or 0.5
        heights.append(height)
    
    if not heights:
        return actions
    
    # Calculate target variation
    current_std = np.std(heights) if len(heights) > 1 else 0.0
    target_std = 0.15  # Target std of 0.15
    
    if current_std >= target_std:
        return actions  # Already has good variation
    
    # Increase variation by scaling heights
    mean_height = np.mean(heights)
    scale_factor = target_std / (current_std + 0.01)  # Avoid division by zero
    
    for i, action in enumerate(actions):
        new_action = copy.deepcopy(action)
        modifiers = new_action.get("modifiers", {})
        
        if "height" in modifiers:
            new_height = mean_height + (heights[i] - mean_height) * scale_factor
            modifiers["height"] = max(0.2, min(1.0, new_height))
        elif "depth" in modifiers:
            new_depth = mean_height + (heights[i] - mean_height) * scale_factor
            modifiers["depth"] = max(0.2, min(0.8, new_depth))
        
        new_action["modifiers"] = modifiers
        adjusted.append(new_action)
    
    return adjusted


def _add_features_for_texture_balance(
    existing_actions: List[Dict[str, Any]],
    scene_state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Add features to improve texture distribution."""
    # Add dunes for sand, cliffs for rock
    added = []
    
    has_dunes = any(a.get("type") == "dunes" for a in existing_actions)
    has_cliff = any(a.get("type") == "cliff" for a in existing_actions)
    
    import random
    rng = random.Random(scene_state.get("seed", DEFAULT_SEED))
    
    if not has_dunes:
        # Add dunes for sand texture
        new_action = {
            "kind": "add",
            "type": "dunes",
            "x": rng.randint(100, 400),
            "y": rng.randint(100, 400),
            "modifiers": {
                "radius": rng.uniform(60, 90),
            },
            "label": "texture_dunes"
        }
        added.append(new_action)
    
    if not has_cliff and len(existing_actions) + len(added) < 6:
        # Add cliff for rock texture
        new_action = {
            "kind": "add",
            "type": "cliff",
            "x": rng.randint(100, 400),
            "y": rng.randint(100, 400),
            "modifiers": {
                "height": rng.uniform(0.5, 0.8),
                "length": rng.uniform(70, 100),
                "steepness": 0.9,
            },
            "label": "texture_cliff"
        }
        added.append(new_action)
    
    return added


def analyze_texture_feature_relationship(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    render_preview: bool = True
) -> Dict[str, Any]:
    """Analyze which features contribute to which texture regions."""
    start_time = time.time()
    logger.info(f"Analyzing texture-feature relationships for {len(actions)} actions")
    
    try:
        if not render_preview or not actions:
            return error_result(
                "Texture analysis requires render_preview=True and actions",
                "analyze_texture_feature_relationship",
                start_time
            )
        
        heightmap_full, splatmap_full = _render_terrain_preview(actions, scene_state)
        if heightmap_full is None or splatmap_full is None:
            return error_result(
                "Failed to render terrain for analysis",
                "analyze_texture_feature_relationship",
                start_time
            )
        
        feature_contributions = {}
        max_features_to_analyze = min(MAX_FEATURES_TO_ANALYZE, len(actions))
        
        for i in range(max_features_to_analyze):
            actions_without = actions[:i] + actions[i+1:]
            heightmap_partial, splatmap_partial = _render_terrain_preview(actions_without, scene_state)
            
            if heightmap_partial is None or splatmap_partial is None:
                continue
            
            texture_diff = splatmap_full.astype(np.float32) - splatmap_partial.astype(np.float32)
            contributions = {
                "grass_coverage": float(np.maximum(0, texture_diff[:, :, 0]).mean()),
                "rock_coverage": float(np.maximum(0, texture_diff[:, :, 1]).mean()),
                "sand_coverage": float(np.maximum(0, texture_diff[:, :, 2]).mean()),
                "snow_coverage": float(np.maximum(0, texture_diff[:, :, 3]).mean()),
            }
            
            mask = np.any(np.abs(texture_diff) > TEXTURE_DIFF_THRESHOLD, axis=2)
            if np.any(mask):
                coords = np.where(mask)
                if len(coords[0]) > 0 and len(coords[1]) > 0:
                    contributions["affected_region"] = (
                        int(coords[1].min()), int(coords[0].min()),
                        int(coords[1].max()), int(coords[0].max())
                    )
            
            feature_contributions[f"action_{i}"] = {
                **contributions,
                "feature_type": actions[i].get("type", "unknown"),
                "action_id": i,
            }
        
        texture_gaps = []
        channel_names = ["grass", "rock", "sand", "snow"]
        
        # Use adaptive thresholds from config
        for channel_idx, channel_name in enumerate(channel_names):
            threshold = TEXTURE_COVERAGE_THRESHOLDS.get(channel_name, 0.05)
            channel_coverage = splatmap_full[:, :, channel_idx]
            low_coverage_mask = channel_coverage < threshold
            
            if np.any(low_coverage_mask):
                coords = np.where(low_coverage_mask)
                if len(coords[0]) > TEXTURE_GAP_MIN_PIXELS:
                    x0, y0 = int(coords[1].min()), int(coords[0].min())
                    x1, y1 = int(coords[1].max()), int(coords[0].max())
                    
                    nearby_features = []
                    for j, action in enumerate(actions):
                        pos = action.get("position", {})
                        x = pos.get("x") or action.get("x", TERRAIN_CENTER_X)
                        y = pos.get("y") or action.get("y", TERRAIN_CENTER_Y)
                        radius = NEARBY_FEATURE_RADIUS
                        if (x0 - radius <= x <= x1 + radius) and (y0 - radius <= y <= y1 + radius):
                            nearby_features.append(j)
                    
                    # Use adaptive parameter modifications from config
                    suggested_changes = []
                    for feat_id in nearby_features[:MAX_NEARBY_FEATURES_TO_SUGGEST]:
                        feat_type = actions[feat_id].get("type", "")
                        modifiers = actions[feat_id].get("modifiers", {})
                        current_radius = modifiers.get("radius", 50)  # Default radius
                        
                        # Calculate gap size (normalized)
                        gap_size = float(channel_coverage[low_coverage_mask].mean())
                        
                        # Get adaptive modification from config
                        modification = get_parameter_modification(
                            channel_name,
                            feat_type,
                            current_radius
                        )
                        
                        if modification:
                            suggested_changes.append({
                                "action_id": feat_id,
                                **modification,
                                "reason": f"Increase {feat_type} size to add {channel_name} coverage (adaptive: {modification.get('radius', 0):.1f})"
                            })
                    
                    texture_gaps.append({
                        "region": (x0, y0, x1, y1),
                        "needed_texture": channel_name,
                        "current_coverage": float(channel_coverage[low_coverage_mask].mean()),
                        "nearby_features": nearby_features,
                        "suggested_changes": suggested_changes
                    })
        
        return success_result({
            "feature_contributions": feature_contributions,
            "texture_gaps": texture_gaps[:5],
            "analysis_summary": f"Analyzed {max_features_to_analyze} features, found {len(texture_gaps)} texture gaps"
        }, "analyze_texture_feature_relationship", start_time)
    
    except Exception as e:
        logger.error(f"Texture-feature analysis failed: {e}", exc_info=True)
        return error_result(f"Analysis failed: {str(e)}", "analyze_texture_feature_relationship", start_time)


def modify_feature_parameters(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    modifications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Modify feature parameters to affect texture distribution."""
    start_time = time.time()
    logger.info(f"Modifying {len(modifications)} feature parameters")
    
    try:
        if not actions:
            return error_result("No actions provided", "modify_feature_parameters", start_time)
        
        refined_actions = copy.deepcopy(actions)
        changes_made = []
        
        for mod in modifications:
            action_id = mod.get("action_id")
            if action_id is None or action_id >= len(refined_actions):
                continue
            
            action = refined_actions[action_id]
            modifiers = action.setdefault("modifiers", {})
            feature_type = action.get("type", "unknown")
            reason = mod.get("reason", "Improve texture distribution")
            param_changes = []
            
            if "radius" in mod:
                current_radius = modifiers.get("radius", 50)
                radius_change = mod["radius"]
                modifiers["radius"] = max(20, min(200, current_radius + radius_change))
                param_changes.append(f"radius {current_radius:.0f} → {modifiers['radius']:.0f}")
            
            if "height" in mod:
                current_height = modifiers.get("height", 0.5)
                height_change = mod["height"]
                modifiers["height"] = max(0.1, min(1.5, current_height + height_change))
                param_changes.append(f"height {current_height:.2f} → {modifiers['height']:.2f}")
            
            if "depth" in mod:
                current_depth = modifiers.get("depth", 0.3)
                depth_change = mod["depth"]
                modifiers["depth"] = max(0.1, min(0.8, current_depth + depth_change))
                param_changes.append(f"depth {current_depth:.2f} → {modifiers['depth']:.2f}")
            
            if param_changes:
                changes_made.append(f"Action {action_id} ({feature_type}): {', '.join(param_changes)} - {reason}")
        
        if not changes_made:
            return error_result("No valid modifications", "modify_feature_parameters", start_time)
        
        return success_result({
            "refined_actions": refined_actions,
            "changes_made": changes_made,
            "modifications_applied": len(changes_made),
        }, "modify_feature_parameters", start_time)
    
    except Exception as e:
        logger.error(f"Parameter modification failed: {e}", exc_info=True)
        return error_result(f"Modification failed: {str(e)}", "modify_feature_parameters", start_time)

