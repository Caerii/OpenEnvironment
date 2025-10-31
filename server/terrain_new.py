"""Terrain generation orchestrator - Coordinates primitives, engine, and semantic layers."""
import numpy as np
from typing import Dict, Tuple
from PIL import Image

# Import primitives
from .primitives.base import base_desert
from .primitives.mountains import generate_mountain, generate_hill, generate_mesa, generate_plateau
from .primitives.valleys import generate_valley, generate_canyon
from .primitives.dunes import generate_dunes, generate_dune_mask

# Import engine
from .engine.stamping import stamp_primitive, BlendingMode, apply_smoothing
from .engine.splatmap import generate_splatmap
from .engine.spatial import region_box, random_point_in, resolve_multiple_positions

# Import semantic
from .semantic.state_manager import FeatureState
from .semantic.spatial_resolver import resolve_position

# Import utilities (export functions stay here for backward compatibility)
from .utils import normalize01, clamp01

# Note: to_png functions are kept in terrain.py for backward compatibility
# They can be moved to engine/output.py later if desired

RES = 512

# Keep old regex parser for fallback
def parse_command(cmd: str) -> Dict:
    """Legacy regex parser - kept for fallback."""
    import re
    cmd = cmd.lower()
    res = {"actions": []}
    count = 1
    m = re.search(r"(one|two|three|four|five|six|seven|eight|nine|ten|\d+)", cmd)
    words = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
    if m:
        c = m.group(1)
        count = words.get(c, None) or int(c)
    
    ftype = None
    for key in ["mountain","hill","valley","dunes"]:
        if key in cmd:
            ftype = key
            break
    
    poskey = None
    for k in ["top-left","top-right","bottom-left","bottom-right","top","bottom","left","right","center","middle"]:
        if k in cmd:
            poskey = "center" if k == "middle" else k
            break
    
    coord = None
    m = re.search(r"\b(?:at\s*)?\(?(\d{1,3})\s*,\s*(\d{1,3})\)?", cmd)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
        x = max(0, min(RES-1, x))
        y = max(0, min(RES-1, y))
        coord = (x, y)
    
    taller = re.search(r"(taller|\+?(\d+)% taller|\+?(\d+)% height)", cmd)
    deeper = re.search(r"(deeper|\+?(\d+)% deeper)", cmd)
    wider  = re.search(r"(wider|\+?(\d+)% wider|radius\s*(\d+))", cmd)
    
    res["actions"].append({
        "kind": "add" if "add" in cmd or "create" in cmd or "make" in cmd else
                 "remove" if "remove" in cmd or "delete" in cmd else
                 "modify" if "modify" in cmd else "add",
        "type": ftype,
        "count": count,
        "poskey": poskey,
        "coord": coord,
        "modifiers": {
            "taller": bool(taller),
            "deeper": bool(deeper),
            "wider":  bool(wider),
        }
    })
    return res

def apply_actions(cmd: str, state: Dict) -> Tuple[np.ndarray, Dict, np.ndarray]:
    """
    Main orchestrator: Parse command, apply actions, generate terrain.
    
    Args:
        cmd: Natural language command string
        state: Current terrain state dictionary
        
    Returns:
        (heightmap, updated_state, splatmap)
    """
    # Parse command using semantic parser or fallback
    try:
        from .semantic.parser import SemanticParser
        parser = SemanticParser()
        parsed = parser.parse(cmd)
    except Exception as e:
        print(f"Semantic parser unavailable ({e}), using regex fallback")
        parsed = parse_command(cmd)
    
    actions = parsed.get("actions", [])
    seed = state.get("seed", 0)
    
    # Initialize state manager
    feature_state = FeatureState(state)
    
    # Rebuild base terrain
    h = base_desert(seed)
    dune_mask_total = np.zeros_like(h)
    
    # Reapply existing features
    for feat in feature_state.list_features():
        _reapply_feature(h, feat, dune_mask_total, seed)
    
    # Execute new actions
    for action in actions:
        _execute_action(action, h, feature_state, dune_mask_total, seed)
    
    # Rebuild final terrain from updated state
    h = base_desert(seed)
    dune_mask_total = np.zeros_like(h)
    for feat in feature_state.list_features():
        _reapply_feature(h, feat, dune_mask_total, seed)
    
    # Post-processing
    apply_smoothing(h, sigma=0.8)
    h = normalize01(h)
    
    # Generate splatmap
    splat = generate_splatmap(h, dune_mask_total)
    
    return h, feature_state.to_dict(), splat

def _reapply_feature(h: np.ndarray, feat: Dict, dune_mask: np.ndarray, seed: int):
    """Reapply a stored feature to terrain."""
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
    
    elif ftype == "valley":
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 64)
        depth = feat.get("depth", 0.35)
        stamp = generate_valley(cx, cy, radius, depth)
        stamp_primitive(h, stamp, BlendingMode.SUBTRACT)
    
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

def _execute_action(action: Dict, h: np.ndarray, feature_state: FeatureState, 
                   dune_mask: np.ndarray, seed: int):
    """Execute a single action from parsed command."""
    kind = action.get("kind", "add")
    ftype = action.get("type") or "hill"
    count = action.get("count", 1)
    position = action.get("position", {})
    modifiers = action.get("modifiers", {})
    
    existing_features = feature_state.list_features()
    
    if kind == "add":
        # Resolve positions
        if count > 1:
            positions = resolve_multiple_positions(position, count, existing_features)
        else:
            pos = resolve_position(position, existing_features)
            positions = [pos]
        
        # Create features
        for cx, cy in positions:
            feat = _create_feature(ftype, cx, cy, modifiers, seed)
            if feat:
                feature_state.add_feature(feat)
    
    elif kind == "remove":
        ordinal = action.get("ordinal")  # e.g., "second mountain" → ordinal=2
        feature_state.remove_feature(
            feature_type=ftype if ftype else None,
            ordinal=ordinal
        )
    
    elif kind == "modify":
        ordinal = action.get("ordinal")
        feat = feature_state.find_feature(
            feature_type=ftype if ftype else None,
            ordinal=ordinal
        )
        if feat:
            _modify_feature(feat, modifiers)

def _create_feature(ftype: str, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
    """Create a feature dictionary from parameters."""
    if ftype == "mountain":
        height = 0.75
        if modifiers.get("height_percent"):
            height *= (1.0 + modifiers["height_percent"] / 100.0)
        elif modifiers.get("taller"):
            height *= 1.3
        radius = 56
        if modifiers.get("width_percent"):
            radius = int(radius * (1.0 + modifiers["width_percent"] / 100.0))
        elif modifiers.get("wider"):
            radius = int(radius * 1.3)
        return {"type": "mountain", "x": cx, "y": cy, "radius": radius, "height": min(1.0, height)}
    
    elif ftype == "hill":
        height = 0.45
        if modifiers.get("height_percent"):
            height *= (1.0 + modifiers["height_percent"] / 100.0)
        elif modifiers.get("taller"):
            height *= 1.3
        radius = 42
        if modifiers.get("width_percent"):
            radius = int(radius * (1.0 + modifiers["width_percent"] / 100.0))
        elif modifiers.get("wider"):
            radius = int(radius * 1.3)
        return {"type": "hill", "x": cx, "y": cy, "radius": radius, "height": min(1.0, height)}
    
    elif ftype == "valley":
        depth = 0.35
        if modifiers.get("depth_percent"):
            depth *= (1.0 + modifiers["depth_percent"] / 100.0)
        elif modifiers.get("deeper"):
            depth *= 1.3
        radius = 64
        if modifiers.get("width_percent"):
            radius = int(radius * (1.0 + modifiers["width_percent"] / 100.0))
        elif modifiers.get("wider"):
            radius = int(radius * 1.3)
        return {"type": "valley", "x": cx, "y": cy, "radius": radius, "depth": min(1.0, depth)}
    
    elif ftype == "dunes":
        r = 96
        x0 = max(0, cx - r)
        y0 = max(0, cy - r)
        x1 = min(RES, cx + r)
        y1 = min(RES, cy + r)
        return {
            "type": "dunes",
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "amp": 0.08, "freq": 18.0, "angle": 20.0
        }
    
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
            feat["depth"] = min(1.0, feat.get("depth", 0.3) * (1.0 + modifiers["depth_percent"] / 100.0))
        elif modifiers.get("deeper"):
            feat["depth"] = min(1.0, feat.get("depth", 0.3) * 1.3)
        
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
    arr8 = (clamp01(splat) * 255.0).astype(np.uint8)
    Image.fromarray(arr8, mode="RGBA").save(path)

# Alias for backward compatibility
make_splatmap = generate_splatmap

