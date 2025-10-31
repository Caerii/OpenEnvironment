"""Terrain generation orchestrator - Coordinates primitives, engine, and semantic layers."""
import numpy as np
from typing import Dict, Tuple, List
from PIL import Image

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
from .semantic.spatial_resolver import resolve_position, resolve_multiple_positions

# Import semantic
from .semantic.state_manager import FeatureState

# Import utilities (export functions stay here for backward compatibility)
from .utils import normalize01, clamp01

# Note: to_png functions are kept in terrain.py for backward compatibility
# They can be moved to engine/output.py later if desired

RES = 512

# Keep old regex parser for fallback
def parse_command(cmd: str) -> Dict:
    """
    Legacy regex parser - kept for fallback.
    
    Improved to extract counts more granularly - associates numbers with specific feature types.
    """
    import re
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
    for ftype in ["mountain", "hill", "valley", "dunes", "mesa", "plateau", "cliff", "canyon", "slope"]:
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
        for key in ["mountain", "hill", "valley", "dunes", "mesa", "plateau", "cliff", "canyon", "slope"]:
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
    import re
    
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
    import re
    poskey = None
    for k in ["top-left", "top-right", "bottom-left", "bottom-right", "top", "bottom", "left", "right", "center", "middle"]:
        if k in text:
            poskey = "center" if k == "middle" else k
            break
    return poskey


def _extract_coords(text: str) -> tuple:
    """Extract coordinate tuple from text."""
    import re
    m = re.search(r"\b(?:at\s*)?\(?(\d{1,3})\s*,\s*(\d{1,3})\)?", text)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
        x = max(0, min(RES-1, x))
        y = max(0, min(RES-1, y))
        return (x, y)
    return None


def _extract_modifiers(text: str) -> dict:
    """Extract modifier information from text."""
    import re
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

def apply_actions(cmd: str, state: Dict, base_biome_fn=None, direct_actions: List[Dict] = None) -> Tuple[np.ndarray, Dict, np.ndarray]:
    """
    Main orchestrator: Parse command, apply actions, generate terrain.
    
    Args:
        cmd: Natural language command string (empty string = rebuild from state only)
        state: Current terrain state dictionary
        base_biome_fn: Optional function to generate base biome (defaults to base_desert)
        direct_actions: Optional list of action dictionaries (for compositional calls)
        
    Returns:
        (heightmap, updated_state, splatmap)
    """
    seed = state.get("seed", 0)
    
    # Default to base_desert if no biome function specified
    if base_biome_fn is None:
        base_biome_fn = base_desert
    
    # If direct_actions provided, use them directly (compositional calls)
    if direct_actions is not None:
        actions = direct_actions
    # If empty command, just rebuild from state (no new actions)
    elif not cmd or not cmd.strip():
        actions = []
    else:
        # Parse command using MCP-enhanced semantic parser or fallback
        try:
            from .semantic.parser import SemanticParser
            parser = SemanticParser()
            # Pass scene state for context-aware parsing (MCP feature)
            parsed = parser.parse(cmd, scene_state=state)
        except Exception as e:
            print(f"Semantic parser unavailable ({e}), using regex fallback")
            parsed = parse_command(cmd)
        
        actions = parsed.get("actions", [])
    
    # Initialize state manager
    feature_state = FeatureState(state)
    
    # Process remove/modify actions first (they update state)
    remove_modify_actions = [a for a in actions if a.get("kind") in ("remove", "modify")]
    add_actions = [a for a in actions if a.get("kind") == "add"]
    
    # Execute remove/modify actions (they modify feature_state)
    for action_dict in remove_modify_actions:
        command = create_command_from_dict(action_dict)
        command.execute(None, feature_state, seed)  # Builder not needed for state-only operations
    
    # Use TerrainBuilder for single-pass construction
    builder = TerrainBuilder(base_biome_fn, seed)
    
    # Apply all existing features (including any modifications)
    for feat in feature_state.list_features():
        _apply_feature_to_builder(builder, feat, seed)
    
    # Execute add actions (they add features and apply them immediately)
    for action_dict in add_actions:
        command = create_command_from_dict(action_dict)
        command.execute(builder, feature_state, seed)
    
    # Finalize terrain
    h, dune_mask_total, cliff_mask_total = builder.finalize()
    
    # Generate splatmap
    splat = builder.build_splatmap()
    
    return h, feature_state.to_dict(), splat

# _reapply_feature is now replaced by _apply_feature_to_builder
# Kept for backward compatibility
def _reapply_feature(h: np.ndarray, feat: Dict, dune_mask: np.ndarray, seed: int):
    """Legacy reapply feature - now uses builder pattern."""
    _apply_feature_to_builder_legacy(h, feat, dune_mask, seed)


def _apply_feature_to_builder_legacy(h: np.ndarray, feat: Dict, dune_mask: np.ndarray, seed: int):
    """Legacy helper to apply feature to heightmap directly."""
    ftype = feat.get("type")
    
    if ftype in ("mountain", "hill"):
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 56 if ftype == "mountain" else 42)
        height = feat.get("height", 0.75 if ftype == "mountain" else 0.45)
        
        if ftype == "mountain":
            stamp = generate_mountain(cx, cy, radius, height)
        else:
            stamp = generate_hill(cx, cy, radius, height)
        
        stamp_primitive(h, stamp, BlendingMode.MAX)
    
    elif ftype == "mesa":
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 56)
        height = feat.get("height", 0.65)
        flatness = feat.get("flatness", 0.3)
        stamp = generate_mesa(cx, cy, radius, height, flatness)
        stamp_primitive(h, stamp, BlendingMode.MAX)
    
    elif ftype == "plateau":
        cx, cy = feat["x"], feat["y"]
        width = feat.get("width", 80)
        length = feat.get("length", 120)
        height = feat.get("height", 0.50)
        orientation = feat.get("orientation", 0.0)
        stamp = generate_plateau(cx, cy, width, length, height, orientation)
        stamp_primitive(h, stamp, BlendingMode.MAX)
    
    elif ftype == "valley":
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 64)
        depth = feat.get("depth", 0.55)  # Increased default depth
        stamp = generate_valley(cx, cy, radius, depth)
        stamp_primitive(h, stamp, BlendingMode.SUBTRACT)
    
    elif ftype == "canyon":
        start = (feat["x0"], feat["y0"])
        end = (feat["x1"], feat["y1"])
        width = feat.get("width", 12)
        depth = feat.get("depth", 0.60)
        falloff = feat.get("falloff", 0.5)
        stamp = generate_canyon(start, end, width, depth, falloff)
        stamp_primitive(h, stamp, BlendingMode.SUBTRACT)
    
    elif ftype == "cliff":
        cx, cy = feat["x"], feat["y"]
        length = feat.get("length", 80)
        height = feat.get("height", 0.55)
        orientation = feat.get("orientation", 0.0)
        steepness = feat.get("steepness", 0.9)
        stamp = generate_cliff(cx, cy, length, height, orientation, steepness)
        stamp_primitive(h, stamp, BlendingMode.MAX)
    
    elif ftype == "slope":
        if "start" in feat and "end" in feat:
            start = tuple(feat["start"])
            end = tuple(feat["end"])
            width = feat.get("width", 40)
            height = feat.get("height", 0.35)
            falloff = feat.get("falloff", 0.3)
            stamp = generate_slope(start, end, width, height, falloff)
        else:
            cx, cy = feat["x"], feat["y"]
            radius = feat.get("radius", 60)
            height = feat.get("height", 0.35)
            direction = feat.get("direction", 0.0)
            steepness = feat.get("steepness", 0.5)
            stamp = generate_slope_radial(cx, cy, radius, height, direction, steepness)
        stamp_primitive(h, stamp, BlendingMode.ADD)
    
    elif ftype == "dunes":
        box = (feat["x0"], feat["y0"], feat["x1"], feat["y1"])
        amp = feat.get("amp", 0.08)
        freq = feat.get("freq", 18.0)
        angle = feat.get("angle", 20.0)
        stamp = generate_dunes(box, amp, freq, angle, seed)
        stamp_primitive(h, stamp, BlendingMode.ADD)
        dune_mask[box[1]:box[3], box[0]:box[2]] = np.maximum(
            dune_mask[box[1]:box[3], box[0]:box[2]], 
            generate_dune_mask(box)[box[1]:box[3], box[0]:box[2]]
        )


def _apply_feature_to_builder(builder: TerrainBuilder, feat: Dict, seed: int):
    """Apply a feature dictionary to builder (used by new architecture)."""
    from .engine.commands import _apply_feature_to_builder as apply_to_builder
    apply_to_builder(builder, feat, seed)

# _execute_action is now replaced by ActionCommand pattern
# Kept for backward compatibility if needed
def _execute_action(action: Dict, h: np.ndarray, feature_state: FeatureState, 
                   dune_mask: np.ndarray, seed: int):
    """Legacy execute action - now uses command pattern."""
    from .engine.commands import create_command_from_dict
    from .engine.builder import TerrainBuilder
    
    builder = TerrainBuilder(lambda s: h, seed)  # Use existing heightmap as base
    builder.dune_mask = dune_mask
    command = create_command_from_dict(action)
    command.execute(builder, feature_state, seed)
    h[:] = builder.heightmap[:]
    dune_mask[:] = builder.dune_mask[:]

def _create_feature(ftype: str, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
    """
    Create a feature dictionary from parameters.
    
    Adds subtle, conservative variation when no explicit modifiers are given.
    Variation is bounded to prevent spikes and maintain smooth Gaussian falloff.
    """
    # Derive deterministic variation seed from position and global seed
    variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
    
    if ftype == "mountain":
        base_height = 0.75
        base_radius = 56
        
        # Apply modifiers if present
        if modifiers.get("height_percent"):
            height = base_height * (1.0 + modifiers["height_percent"] / 100.0)
        elif modifiers.get("taller"):
            height = base_height * 1.3
        else:
            # Apply subtle variation (only when no explicit modifier)
            cfg = VARIATION_CONFIG["mountain"]
            height = VariationEngine.apply_variation(
                base_height, cfg["height_variation"], variation_seed,
                cfg["height_min"], cfg["height_max"]
            )
        
        if modifiers.get("width_percent"):
            radius = int(base_radius * (1.0 + modifiers["width_percent"] / 100.0))
        elif modifiers.get("wider"):
            radius = int(base_radius * 1.3)
        else:
            # Apply subtle variation
            cfg = VARIATION_CONFIG["mountain"]
            radius = VariationEngine.apply_variation_int(
                base_radius, cfg["radius_variation"], variation_seed + 1,
                cfg["radius_min"], cfg["radius_max"]
            )
        
        return {"type": "mountain", "x": cx, "y": cy, "radius": radius, "height": height}
    
    elif ftype == "hill":
        base_height = 0.45
        base_radius = 42
        
        if modifiers.get("height_percent"):
            height = base_height * (1.0 + modifiers["height_percent"] / 100.0)
        elif modifiers.get("taller"):
            height = base_height * 1.3
        else:
            cfg = VARIATION_CONFIG["hill"]
            height = VariationEngine.apply_variation(
                base_height, cfg["height_variation"], variation_seed,
                cfg["height_min"], cfg["height_max"]
            )
        
        if modifiers.get("width_percent"):
            radius = int(base_radius * (1.0 + modifiers["width_percent"] / 100.0))
        elif modifiers.get("wider"):
            radius = int(base_radius * 1.3)
        else:
            cfg = VARIATION_CONFIG["hill"]
            radius = VariationEngine.apply_variation_int(
                base_radius, cfg["radius_variation"], variation_seed + 1,
                cfg["radius_min"], cfg["radius_max"]
            )
        
        return {"type": "hill", "x": cx, "y": cy, "radius": radius, "height": height}
    
    elif ftype == "valley":
        base_depth = 0.55
        base_radius = 64
        
        if modifiers.get("depth_percent"):
            depth = base_depth * (1.0 + modifiers["depth_percent"] / 100.0)
        elif modifiers.get("deeper"):
            depth = base_depth * 1.3
        else:
            cfg = VARIATION_CONFIG["valley"]
            depth = VariationEngine.apply_variation(
                base_depth, cfg["depth_variation"], variation_seed,
                cfg["depth_min"], cfg["depth_max"]
            )
        
        if modifiers.get("width_percent"):
            radius = int(base_radius * (1.0 + modifiers["width_percent"] / 100.0))
        elif modifiers.get("wider"):
            radius = int(base_radius * 1.3)
        else:
            cfg = VARIATION_CONFIG["valley"]
            radius = VariationEngine.apply_variation_int(
                base_radius, cfg["radius_variation"], variation_seed + 1,
                cfg["radius_min"], cfg["radius_max"]
            )
        
        return {"type": "valley", "x": cx, "y": cy, "radius": radius, "depth": depth}
    
    elif ftype == "dunes":
        cfg = VARIATION_CONFIG["dunes"]
        base_r = 96
        
        # Apply subtle variation to dune parameters
        amp = VariationEngine.apply_variation(0.08, cfg["amp_variation"], variation_seed)
        freq = VariationEngine.apply_variation(18.0, cfg["freq_variation"], variation_seed + 1)
        angle = VariationEngine.apply_variation(20.0, cfg["angle_variation"], variation_seed + 2)
        
        # Radius variation
        r = VariationEngine.apply_variation_int(
            base_r, cfg["radius_variation"], variation_seed + 3,
            cfg["radius_min"], cfg["radius_max"]
        )
        
        x0 = max(0, cx - r)
        y0 = max(0, cy - r)
        x1 = min(RES, cx + r)
        y1 = min(RES, cy + r)
        
        return {
            "type": "dunes",
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "amp": amp, "freq": freq, "angle": angle
        }
    
    elif ftype == "mesa":
        cfg = VARIATION_CONFIG["mountain"]  # Use mountain config as base
        base_height = 0.65
        base_radius = 56
        
        height = VariationEngine.apply_variation(
            base_height, cfg["height_variation"], variation_seed,
            cfg["height_min"] * 0.9, cfg["height_max"] * 0.95
        )
        radius = VariationEngine.apply_variation_int(
            base_radius, cfg["radius_variation"], variation_seed + 1,
            cfg["radius_min"], cfg["radius_max"]
        )
        
        return {"type": "mesa", "x": cx, "y": cy, "radius": radius, "height": height, "flatness": 0.3}
    
    elif ftype == "plateau":
        base_height = 0.50
        base_width = 80
        base_length = 120
        
        height = VariationEngine.apply_variation(base_height, 0.10, variation_seed, 0.35, 0.70)
        width = VariationEngine.apply_variation_int(base_width, 0.15, variation_seed + 1, 60, 120)
        length = VariationEngine.apply_variation_int(base_length, 0.15, variation_seed + 2, 80, 160)
        
        return {"type": "plateau", "x": cx, "y": cy, "width": width, "length": length,
                "height": height, "orientation": 0.0}
    
    elif ftype == "cliff":
        base_length = 80
        base_height = 0.55
        
        length = VariationEngine.apply_variation_int(base_length, 0.15, variation_seed, 50, 120)
        height = VariationEngine.apply_variation(base_height, 0.10, variation_seed + 1, 0.40, 0.75)
        
        return {"type": "cliff", "x": cx, "y": cy, "length": length, "height": height,
                "orientation": 0.0, "steepness": 0.9}
    
    elif ftype == "canyon":
        # Canyons need start/end points - use center as midpoint
        base_length = 100
        base_width = 12
        
        length = VariationEngine.apply_variation_int(base_length, 0.20, variation_seed, 60, 150)
        width = VariationEngine.apply_variation_int(base_width, 0.15, variation_seed + 1, 8, 18)
        
        # Generate orientation from seed
        import numpy as np
        rng = np.random.RandomState(variation_seed + 2)
        orientation = rng.uniform(0, 360)
        
        # Create start/end points
        half_len = length // 2
        ang_rad = np.deg2rad(orientation)
        start = (int(cx - half_len * np.cos(ang_rad)), int(cy - half_len * np.sin(ang_rad)))
        end = (int(cx + half_len * np.cos(ang_rad)), int(cy + half_len * np.sin(ang_rad)))
        
        # Clamp to bounds
        start = (max(0, min(RES-1, start[0])), max(0, min(RES-1, start[1])))
        end = (max(0, min(RES-1, end[0])), max(0, min(RES-1, end[1])))
        
        return {"type": "canyon", "x0": start[0], "y0": start[1], "x1": end[0], "y1": end[1],
                "width": width, "depth": 0.60, "falloff": 0.5}
    
    elif ftype == "slope":
        # Default to radial slope
        base_radius = 60
        base_height = 0.35
        
        radius = VariationEngine.apply_variation_int(base_radius, 0.15, variation_seed, 40, 90)
        height = VariationEngine.apply_variation(base_height, 0.10, variation_seed + 1, 0.25, 0.50)
        
        import numpy as np
        rng = np.random.RandomState(variation_seed + 2)
        direction = rng.uniform(0, 360)
        
        return {"type": "slope", "x": cx, "y": cy, "radius": radius, "height": height,
                "direction": direction, "steepness": 0.5}
    
    return None

def _modify_feature(feat: Dict, modifiers: Dict):
    """Modify an existing feature's parameters."""
    ftype = feat.get("type")
    
    if ftype in ("hill", "mountain"):
        if modifiers.get("height_percent"):
            feat["height"] = min(1.0, feat.get("height", 0.5) * (1.0 + modifiers["height_percent"] / 100.0))
        elif modifiers.get("taller"):
            feat["height"] = min(1.0, feat.get("height", 0.5) * 1.3)
        
        if modifiers.get("width_percent"):
            feat["radius"] = int(min(128, feat.get("radius", 48) * (1.0 + modifiers["width_percent"] / 100.0)))
        elif modifiers.get("wider"):
            feat["radius"] = int(min(128, feat.get("radius", 48) * 1.3))
    
    elif ftype == "valley":
        if modifiers.get("depth_percent"):
            feat["depth"] = min(1.0, feat.get("depth", 0.55) * (1.0 + modifiers["depth_percent"] / 100.0))
        elif modifiers.get("deeper"):
            feat["depth"] = min(1.0, feat.get("depth", 0.55) * 1.3)
        
        if modifiers.get("width_percent"):
            feat["radius"] = int(min(128, feat.get("radius", 64) * (1.0 + modifiers["width_percent"] / 100.0)))
        elif modifiers.get("wider"):
            feat["radius"] = int(min(128, feat.get("radius", 64) * 1.3))

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

