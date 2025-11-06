"""Terrain generation orchestrator - Coordinates primitives, engine, and semantic layers."""
import re
import logging
import numpy as np
from typing import Dict, Tuple, List, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Import primitives
from .primitives.base import base_desert, base_flat
from .primitives.mountains import generate_mountain, generate_hill, generate_mesa, generate_plateau
from .primitives.valleys import generate_valley, generate_canyon
from .primitives.dunes import generate_dunes, generate_dune_mask
from .primitives.cliffs import generate_cliff, generate_cliff_mask
from .primitives.slopes import generate_slope, generate_slope_radial

# Import engine
from .engine.stamping import stamp_primitive, BlendingMode, apply_smoothing
from .engine.splatmap import generate_splatmap
from .engine.spatial import region_box, random_point_in, random_points_in
from .engine.builder import TerrainBuilder
from .engine.commands import create_command_from_dict, ActionCommand
from .engine.variation import VariationEngine, VARIATION_CONFIG
from .engine.feature_registry import FeatureRegistry
from .semantic.spatial_resolver import resolve_position, resolve_multiple_positions

# Import semantic
from .semantic.state_manager import FeatureState
from .semantic.scene import TerrainSceneGraph, SceneGraphSerializer, SceneGraphIntegrator
from .semantic.parser import SemanticParser

# Import utilities (export functions stay here for backward compatibility)
from .utils import normalize01, clamp01

# Note: to_png functions are kept in terrain.py for backward compatibility
# They can be moved to engine/output.py later if desired

from .engine.config import RES

# Keep old regex parser for fallback
def parse_command(cmd: str) -> Dict:
    """
    Legacy regex parser - kept for fallback.
    
    Improved to extract counts more granularly - associates numbers with specific feature types.
    """
    cmd_lower = cmd.lower()
    res = {"actions": []}
    
    # Expanded number word mapping
    number_words = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "dozen": 12,
        "a": 1, "an": 1, "couple": 2, "pair": 2, "few": 2, "several": 3, "many": 5
    }
    
    # Find all feature types mentioned
    feature_types = []
    registered_types = FeatureRegistry.get_registered_types()
    for ftype in registered_types:
        # Find all occurrences and their positions
        for match in re.finditer(rf"\b{re.escape(ftype)}\w*\b", cmd_lower):
            feature_types.append({
                "type": ftype,
                "start": match.start(),
                "end": match.end()
            })
    
    # Sort by position in command
    feature_types.sort(key=lambda x: x["start"])
    
    # If no features found, try to infer from context
    if not feature_types:
        # Default feature detection (old behavior)
        ftype = None
        for key in registered_types:
            if key in cmd_lower:
                ftype = key
                break
        
        if ftype:
            # Extract count before the feature type
            count = _extract_count_before_position(cmd_lower, cmd_lower.find(ftype), number_words)
            
            poskey = _extract_position(cmd_lower)
            coord = _extract_coords(cmd_lower)
            modifiers = _extract_modifiers(cmd_lower)
            
            res["actions"].append({
                "kind": _extract_kind(cmd_lower),
                "type": ftype,
                "count": count,
                "position": {"region": poskey, "coords": coord},
                "modifiers": modifiers
            })
        return res
    
    # Process each feature type found
    for feat_info in feature_types:
        ftype = feat_info["type"]
        feat_start = feat_info["start"]
        
        # Extract count immediately before this feature
        count = _extract_count_before_position(cmd_lower, feat_start, number_words)
        
        # Extract position context around this feature
        # Look for position words near this feature (within 50 chars)
        context_start = max(0, feat_start - 50)
        context_end = min(len(cmd_lower), feat_info["end"] + 50)
        context = cmd_lower[context_start:context_end]
        
        poskey = _extract_position(context)
        coord = _extract_coords(context)
        modifiers = _extract_modifiers(context)
        
        # Determine action kind (check if it applies to this specific feature)
        kind = _extract_kind(cmd_lower[:feat_start + 20])  # Check context before feature
        
        res["actions"].append({
            "kind": kind,
            "type": ftype,
            "count": count,
            "position": {"region": poskey, "coords": coord},
            "modifiers": modifiers
        })
    
    return res


def _extract_count_before_position(text: str, position: int, number_words: dict) -> int:
    """Extract numerical count immediately before a given position."""
    # Look back up to 30 characters before position
    lookback_start = max(0, position - 30)
    lookback_text = text[lookback_start:position]
    
    # Try to find number words or digits
    # Pattern: (number word/digit) + optional "of" + feature
    patterns = [
        r"(\d+)\s+(?:of\s+)?",  # "2 of" or "2 "
        rf"({'|'.join(re.escape(w) for w in number_words.keys())})\s+(?:of\s+)?",  # "two of" or "two "
        r"a\s+(?:of\s+)?",  # "a of" or "a "
        r"an\s+(?:of\s+)?",  # "an of" or "an "
    ]
    
    for pattern in patterns:
        match = re.search(pattern + r"$", lookback_text, re.IGNORECASE)
        if match:
            num_str = match.group(1) if match.groups() else None
            if num_str:
                if num_str.isdigit():
                    return int(num_str)
                elif num_str.lower() in number_words:
                    return number_words[num_str.lower()]
            else:
                # "a" or "an" pattern matched
                return 1
    
    # Default to 1 if no count found
    return 1


def _extract_position(text: str) -> str:
    """Extract position keyword from text."""
    poskey = None
    for k in ["top-left", "top-right", "bottom-left", "bottom-right", "top", "bottom", "left", "right", "center", "middle"]:
        if k in text:
            poskey = "center" if k == "middle" else k
            break
    return poskey


def _extract_coords(text: str) -> tuple:
    """Extract coordinate tuple from text."""
    m = re.search(r"\b(?:at\s*)?\(?(\d{1,3})\s*,\s*(\d{1,3})\)?", text)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
        x = max(0, min(RES-1, x))
        y = max(0, min(RES-1, y))
        return (x, y)
    return None


def _extract_modifiers(text: str) -> dict:
    """Extract modifier information from text."""
    taller = re.search(r"(taller|\+?(\d+)% taller|\+?(\d+)% height)", text)
    deeper = re.search(r"(deeper|\+?(\d+)% deeper)", text)
    wider = re.search(r"(wider|\+?(\d+)% wider|radius\s*(\d+))", text)
    
    modifiers = {
        "taller": bool(taller),
        "deeper": bool(deeper),
        "wider": bool(wider),
    }
    
    # Extract percentage values
    if taller and taller.groups()[1]:
        modifiers["height_percent"] = int(taller.group(2))
    if deeper and deeper.groups()[1]:
        modifiers["depth_percent"] = int(deeper.group(2))
    if wider and wider.groups()[1]:
        modifiers["width_percent"] = int(wider.group(2))
    
    return modifiers


def _extract_kind(text: str) -> str:
    """Extract action kind from text."""
    if "remove" in text or "delete" in text:
        return "remove"
    elif "modify" in text or "make" in text or "change" in text:
        return "modify"
    else:
        return "add"

def apply_actions(cmd: str, state: Dict, base_biome_fn=None, direct_actions: List[Dict] = None, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict, np.ndarray]:
    """
    Main orchestrator: Parse command, apply actions, generate terrain.
    
    This is the main entry point for terrain generation. It coordinates:
    1. Parsing commands into structured actions
    2. Managing scene graph state
    3. Executing actions (remove/modify, then add)
    4. Building final terrain from all features
    
    Args:
        cmd: Natural language command string (empty string = rebuild from state only)
        state: Current terrain state dictionary
        base_biome_fn: Optional function to generate base biome (defaults to base_desert)
        direct_actions: Optional list of action dictionaries (for compositional calls)
        
    Returns:
        (heightmap, updated_state, splatmap)
    """
    from .orchestration import (
        init_scene_graph,
        parse_command_to_actions,
        partition_actions,
        resolve_removal_targets,
        execute_state_actions,
        cleanup_scene_graph,
        execute_add_actions,
        update_scene_graph_for_additions,
        build_final_terrain
    )
    
    import random
    
    # Handle seed: -1 = auto-generate, None = use state seed, otherwise use provided seed
    if seed == -1:
        seed = random.randint(0, 2**31 - 1)
    elif seed is None:
        seed = state.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**31 - 1)
    
    state["seed"] = seed  # Update state with seed
    
    # Default to base_desert if no biome function specified
    if base_biome_fn is None:
        base_biome_fn = base_desert
    
    # Step 1: Initialize scene graph
    scene_graph = init_scene_graph(state)
    
    # Step 2: Parse command into actions
    actions = parse_command_to_actions(cmd, state, direct_actions)
    
    # Step 3: Initialize state manager
    feature_state = FeatureState(state)
    
    # Step 4: Partition actions into remove/modify vs add
    remove_modify_actions, add_actions = partition_actions(actions)
    
    # Step 5: Resolve removal targets using scene graph
    removal_ids = resolve_removal_targets(remove_modify_actions, scene_graph, feature_state)
    
    # Step 6: Execute remove/modify actions
    actually_removed_ids = execute_state_actions(remove_modify_actions, feature_state, seed)
    
    # Step 7: Clean up scene graph for removed features
    all_removed_ids = list(set(removal_ids) | actually_removed_ids)
    cleanup_scene_graph(scene_graph, all_removed_ids)
    
    # Step 8: Build terrain with existing features (after removals/modifications)
    builder = TerrainBuilder(base_biome_fn, seed)
    for feat in feature_state.list_features():
        _apply_feature_to_builder(builder, feat, seed)
    
    # Step 9: Execute add actions (creates and applies new features)
    created_features = execute_add_actions(add_actions, builder, feature_state, scene_graph, seed, cmd)
    
    # Step 10: Update scene graph for newly added features
    update_scene_graph_for_additions(scene_graph, created_features)
    
    # Step 11: Finalize terrain
    h, dune_mask_total, cliff_mask_total = builder.finalize()
    splat = builder.build_splatmap()
    
    # Save scene graph to state
    if scene_graph:
        try:
            state["semantic_scene"] = SceneGraphSerializer.to_dict(scene_graph)
        except (ValueError, AttributeError, TypeError) as e:
            logger.warning(f"Failed to save scene graph: {e}")
    
    # Update state with feature state
    updated_state = feature_state.to_dict()
    updated_state["semantic_scene"] = state.get("semantic_scene", {})
    
    return h, updated_state, splat

def _apply_feature_to_builder(builder: TerrainBuilder, feat: Dict, seed: int):
    """Apply a feature dictionary to builder (used by new architecture)."""
    from .engine.commands import _apply_feature_to_builder as apply_to_builder_impl
    apply_to_builder_impl(builder, feat, seed)


# ============================================================================
# Helper Functions for Feature Creation
# ============================================================================

def _apply_param_modifier_or_variation(
    base_value: float,
    modifiers: Dict,
    param_name: str,
    modifier_key: str,
    variation_config: Dict,
    variation_seed: int,
    is_int: bool = False
) -> float:
    """
    Generic logic for applying modifier or variation to a parameter.
    
    Priority order:
    1. Percentage modifier (e.g., "height_percent": 20 → 120% of base)
    2. Keyword modifier (e.g., "taller" → 130% of base)
    3. Automatic variation (using VariationEngine with config)
    
    Args:
        base_value: Base parameter value
        modifiers: User modifiers dictionary
        param_name: Parameter name ("height", "depth", "radius", "width")
        modifier_key: Modifier keyword ("taller", "deeper", "wider")
        variation_config: Configuration dict with variation settings
        variation_seed: Deterministic seed for variation
        is_int: Whether to return integer value
        
    Returns:
        Modified or varied parameter value
    """
    percent_key = f"{param_name}_percent"
    
    # Priority 1: Percentage modifier
    if modifiers.get(percent_key):
        value = base_value * (1.0 + modifiers[percent_key] / 100.0)
    # Priority 2: Keyword modifier
    elif modifiers.get(modifier_key):
        value = base_value * 1.3
    # Priority 3: Automatic variation
    else:
        variation_key = f"{param_name}_variation"
        min_key = f"{param_name}_min"
        max_key = f"{param_name}_max"
        
        if is_int:
            value = VariationEngine.apply_variation_int(
                int(base_value),
                variation_config.get(variation_key, 0.10),
                variation_seed,
                variation_config.get(min_key),
                variation_config.get(max_key)
            )
        else:
            value = VariationEngine.apply_variation(
                base_value,
                variation_config.get(variation_key, 0.10),
                variation_seed,
                variation_config.get(min_key),
                variation_config.get(max_key)
            )
    
    return int(value) if is_int else float(value)


def _generate_linear_feature_coords(cx: int, cy: int, length: int, seed: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Generate start/end coordinates for linear features with random orientation.
    
    Used by: canyon, ridge, ravine, pass, spur
    
    Args:
        cx, cy: Center coordinates
        length: Length of the linear feature
        seed: Deterministic seed for orientation
        
    Returns:
        (start, end) tuple of (x, y) coordinates, clamped to terrain bounds
    """
    rng = np.random.RandomState(seed)
    orientation = rng.uniform(0, 360)
    
    half_len = length // 2
    ang_rad = np.deg2rad(orientation)
    
    # Calculate start/end points
    start = (
        int(cx - half_len * np.cos(ang_rad)),
        int(cy - half_len * np.sin(ang_rad))
    )
    end = (
        int(cx + half_len * np.cos(ang_rad)),
        int(cy + half_len * np.sin(ang_rad))
    )
    
    # Clamp to terrain bounds
    start = (max(0, min(RES-1, start[0])), max(0, min(RES-1, start[1])))
    end = (max(0, min(RES-1, end[0])), max(0, min(RES-1, end[1])))
    
    return start, end


def _generate_bounding_box(cx: int, cy: int, radius: int) -> Tuple[int, int, int, int]:
    """
    Generate bounding box for area features.
    
    Used by: dunes, terraces
    
    Args:
        cx, cy: Center coordinates
        radius: Radius/half-size of the area
        
    Returns:
        (x0, y0, x1, y1) bounding box, clamped to terrain bounds
    """
    x0 = max(0, cx - radius)
    y0 = max(0, cy - radius)
    x1 = min(RES, cx + radius)
    y1 = min(RES, cy + radius)
    return (x0, y0, x1, y1)


# ============================================================================
# Feature Creation
# ============================================================================

# _create_feature() deleted - all feature creation now in FeatureRegistry
# _modify_feature() deleted - all feature modification now in FeatureRegistry
# Use FeatureRegistry.create_feature() and FeatureRegistry.modify_feature() directly

# Export functions for backward compatibility
def to_png_16bit_gray(h: np.ndarray, path: str):
    """Export heightmap as 16-bit grayscale PNG."""
    arr16 = (clamp01(h) * 65535.0).astype(np.uint16)
    Image.fromarray(arr16, mode="I;16").save(path)

def to_png_8bit_gray(h: np.ndarray, path: str):
    """Export heightmap as 8-bit grayscale PNG."""
    arr8 = (clamp01(h) * 255.0).astype(np.uint8)
    Image.fromarray(arr8, mode="L").save(path)

def to_png_rgba(splat: np.ndarray, path: str):
    """Export splatmap as RGBA PNG."""
    # Handle NaN/Inf values before casting
    splat = np.asarray(splat, dtype=np.float32)
    if np.any(~np.isfinite(splat)):
        splat = np.nan_to_num(splat, nan=0.0, posinf=1.0, neginf=0.0)
    arr8 = (clamp01(splat) * 255.0).astype(np.uint8)
    Image.fromarray(arr8, mode="RGBA").save(path)

# Alias for backward compatibility
make_splatmap = generate_splatmap

