import re
import json
import random
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image
from noise import pnoise2
from scipy.ndimage import gaussian_filter
from .utils import normalize01, clamp01, smooth_mask, sobel_slope, percentiles

RES = 512

def base_desert(seed=0) -> np.ndarray:
    # low, mostly flat, slight dune-friendly base
    rng = random.Random(seed)
    h = np.zeros((RES, RES), dtype=np.float32)
    # tiny low-frequency wobble so it's not dead flat
    for y in range(RES):
        for x in range(RES):
            h[y, x] = 0.03 * pnoise2(x/512.0, y/512.0, octaves=2, repeatx=1024, repeaty=1024, base=seed)
    h = normalize01(h) * 0.15  # keep it low
    return h

def stamp_gaussian(h: np.ndarray, cx: int, cy: int, radius: int, peak: float, mode: str = "max"):
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    sigma = max(1.0, radius / 2.0)
    stamp = peak * np.exp(-(dx*dx + dy*dy) / (2.0 * sigma * sigma))
    if mode == "max":   # mountains/hills
        np.maximum(h, stamp, out=h)
    elif mode == "min": # valleys (negative stamp)
        h[:] = np.minimum(h, 1.0 - stamp)
    else: # weighted blend
        h[:] = 0.5*h + 0.5*stamp

def add_valley(h: np.ndarray, cx: int, cy: int, radius: int, depth: float):
    # valley: subtract a gaussian and smooth
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    sigma = max(1.0, radius / 2.0)
    carve = depth * np.exp(-(dx*dx + dy*dy) / (2.0 * sigma * sigma))
    h[:] = clamp01(h - carve)
    # local soften
    h[:] = gaussian_filter(h, sigma=0.6)

def add_dunes(h: np.ndarray, region: Tuple[int,int,int,int], amp=0.08, freq=18.0, angle_deg=20.0, seed=0):
    x0, y0, x1, y1 = region
    ang = np.deg2rad(angle_deg)
    cs, sn = np.cos(ang), np.sin(ang)
    for y in range(y0, y1):
        for x in range(x0, x1):
            xr = (x*cs + y*sn) / freq
            yr = (-x*sn + y*cs) / freq
            n = pnoise2(xr, yr, octaves=2, repeatx=4096, repeaty=4096, base=seed+17)
            h[y, x] = clamp01(h[y, x] + amp * (0.5*n + 0.5))

def region_box(keyword: str) -> Tuple[int,int,int,int]:
    # 3x3 grid slicing; crude but effective
    T = RES//3
    m = {
        "top-left":      (0, 0, T, T),
        "top":           (T, 0, 2*T, T),
        "top-right":     (2*T, 0, RES, T),
        "left":          (0, T, T, 2*T),
        "center":        (T, T, 2*T, 2*T),
        "right":         (2*T, T, RES, 2*T),
        "bottom-left":   (0, 2*T, T, RES),
        "bottom":        (T, 2*T, 2*T, RES),
        "bottom-right":  (2*T, 2*T, RES, RES),
    }
    return m.get(keyword, (T, T, 2*T, 2*T))

def random_point_in(box):
    x0, y0, x1, y1 = box
    return (random.randint(x0, x1-1), random.randint(y0, y1-1))

def parse_command(cmd: str) -> Dict:
    cmd = cmd.lower()
    # defaults
    res = {"actions": []}
    # count
    count = 1
    m = re.search(r"(one|two|three|four|five|six|seven|eight|nine|ten|\d+)", cmd)
    words = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
    if m:
        c = m.group(1)
        count = words.get(c, None) or int(c)

    # feature type
    ftype = None
    for key in ["mountain","hill","valley","dunes"]:
        if key in cmd:
            ftype = key
            break

    # position
    poskey = None
    for k in ["top-left","top-right","bottom-left","bottom-right","top","bottom","left","right","center","middle"]:
        if k in cmd:
            poskey = "center" if k == "middle" else k
            break

    # precise coordinates
    coord = None
    m = re.search(r"\b(?:at\s*)?\(?(\d{1,3})\s*,\s*(\d{1,3})\)?", cmd)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
        x = max(0, min(RES-1, x))
        y = max(0, min(RES-1, y))
        coord = (x, y)

    # modifiers
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

def make_splatmap(h: np.ndarray, dune_mask: np.ndarray) -> np.ndarray:
    slope = sobel_slope(h)
    h90, h97 = percentiles(h, 90, 97)

    rock = np.clip((slope - 0.35) / (0.8 - 0.35 + 1e-6), 0, 1)
    snow = np.clip((h - h90) / (max(1e-6, h97 - h90)), 0, 1)
    flat_low = ((0.2 - slope) / 0.2).clip(0,1) * ((0.35 - h) / 0.35).clip(0,1)
    sand = np.clip(0.8*dune_mask + flat_low, 0, 1)

    grass = np.clip(1.0 - np.maximum(np.maximum(rock, snow), sand), 0, 1)

    # stack RGBA
    splat = np.stack([grass, rock, sand, snow], axis=-1)  # (H,W,4)
    # normalize per pixel
    s = splat.sum(axis=-1, keepdims=True) + 1e-6
    splat /= s
    return splat.astype(np.float32)

def to_png_16bit_gray(h: np.ndarray, path: str):
    arr16 = (clamp01(h) * 65535.0).astype(np.uint16)
    Image.fromarray(arr16, mode="I;16").save(path)

def to_png_8bit_gray(h: np.ndarray, path: str):
    arr8 = (clamp01(h) * 255.0).astype(np.uint8)
    Image.fromarray(arr8, mode="L").save(path)

def to_png_rgba(splat: np.ndarray, path: str):
    arr8 = (clamp01(splat) * 255.0).astype(np.uint8)
    Image.fromarray(arr8, mode="RGBA").save(path)

def apply_actions(cmd: str, state: Dict) -> Tuple[np.ndarray, Dict, np.ndarray]:
    # Try semantic parser first, fallback to regex
    try:
        from .semantic.parser import SemanticParser
        parser = SemanticParser()
        parsed = parser.parse(cmd)
    except Exception as e:
        print(f"Semantic parser unavailable ({e}), using regex fallback")
        parsed = parse_command(cmd)
    
    actions = parsed.get("actions", [])
    seed = state.get("seed", 0)

    # rebuild from state every time for determinism
    if not state.get("features"):
        h = base_desert(seed)
        state["features"] = []
    else:
        h = np.zeros((RES, RES), dtype=np.float32)
        # base biome: desert baseline again
        h[:] = base_desert(seed)

    dune_mask_total = np.zeros_like(h)

    # reapply existing features
    for f in state["features"]:
        t = f["type"]
        if t in ("mountain","hill"):
            stamp_gaussian(h, f["x"], f["y"], f["radius"], f["height"], "max")
        elif t == "valley":
            add_valley(h, f["x"], f["y"], f["radius"], f["depth"])
        elif t == "dunes":
            box = (f["x0"], f["y0"], f["x1"], f["y1"])
            add_dunes(h, box, amp=f["amp"], freq=f["freq"], angle_deg=f["angle"], seed=seed)
            # mark dune area for splat
            x0,y0,x1,y1 = box
            dune_mask_total[y0:y1, x0:x1] = np.maximum(dune_mask_total[y0:y1, x0:x1], 1.0)

    # execute actions (process all actions from semantic parser)
    for action in actions:
        kind = action.get("kind", "add")
        ftype = action.get("type") or action.get("ftype") or "hill"
        
        # Handle new structured format from semantic parser
        count = action.get("count", 1)
        poskey = action.get("poskey") or (action.get("position", {}).get("region") if isinstance(action.get("position"), dict) else None)
        coord = action.get("coord") or (tuple(action.get("position", {}).get("coords")) if isinstance(action.get("position"), dict) and action.get("position", {}).get("coords") else None)
        modifiers = action.get("modifiers", {})

        if kind == "add":
            n = max(1, count)
            if coord:
                centers = [coord]
            else:
                box = region_box(poskey or "center")
                centers = [random_point_in(box) for _ in range(n)]

            for i, (cx, cy) in enumerate(centers):
                if ftype == "mountain":
                    height = 0.75
                    if modifiers.get("height_percent"):
                        height *= (1.0 + modifiers["height_percent"] / 100.0)
                    elif modifiers.get("taller"):
                        height *= 1.3
                    feat = {"type":"mountain","x":cx,"y":cy,"radius":56,"height":min(1.0, height)}
                    stamp_gaussian(h, cx, cy, feat["radius"], feat["height"], "max")
                elif ftype == "hill":
                    height = 0.45
                    if modifiers.get("height_percent"):
                        height *= (1.0 + modifiers["height_percent"] / 100.0)
                    elif modifiers.get("taller"):
                        height *= 1.3
                    feat = {"type":"hill","x":cx,"y":cy,"radius":42,"height":min(1.0, height)}
                    stamp_gaussian(h, cx, cy, feat["radius"], feat["height"], "max")
                elif ftype == "valley":
                    depth = 0.35
                    if modifiers.get("depth_percent"):
                        depth *= (1.0 + modifiers["depth_percent"] / 100.0)
                    elif modifiers.get("deeper"):
                        depth *= 1.3
                    feat = {"type":"valley","x":cx,"y":cy,"radius":64,"depth":min(1.0, depth)}
                    add_valley(h, cx, cy, feat["radius"], feat["depth"])
                elif ftype == "dunes":
                    # make a region box around center
                    r = 96
                    x0 = max(0, cx - r); y0 = max(0, cy - r)
                    x1 = min(RES, cx + r); y1 = min(RES, cy + r)
                    feat = {"type":"dunes","x0":x0,"y0":y0,"x1":x1,"y1":y1,"amp":0.08,"freq":18.0,"angle":20.0}
                    add_dunes(h, (x0,y0,x1,y1), amp=feat["amp"], freq=feat["freq"], angle_deg=feat["angle"], seed=seed)
                    dune_mask_total[y0:y1, x0:x1] = np.maximum(dune_mask_total[y0:y1, x0:x1], 1.0)
                else:
                    continue
                state["features"].append(feat)

        elif kind == "remove":
            # Remove: find most recent matching feature
            idx = None
            for i in range(len(state["features"])-1, -1, -1):
                if ftype is None or state["features"][i]["type"] == ftype:
                    idx = i; break
            if idx is not None:
                del state["features"][idx]

        elif kind == "modify":
            # Modify: find most recent matching feature and update
            idx = None
            for i in range(len(state["features"])-1, -1, -1):
                if ftype is None or state["features"][i]["type"] == ftype:
                    idx = i; break
            if idx is not None:
                f = state["features"][idx]
                if f["type"] in ("hill","mountain"):
                    if modifiers.get("height_percent"):
                        f["height"] = min(1.0, f.get("height",0.5) * (1.0 + modifiers["height_percent"] / 100.0))
                    elif modifiers.get("taller"):
                        f["height"] = min(1.0, f.get("height",0.5)*1.3)
                    if modifiers.get("width_percent"):
                        f["radius"] = int(min(128, f.get("radius",48) * (1.0 + modifiers["width_percent"] / 100.0)))
                    elif modifiers.get("wider"):
                        f["radius"] = int(min(128, f.get("radius",48)*1.3))
                if f["type"] == "valley":
                    if modifiers.get("depth_percent"):
                        f["depth"] = min(1.0, f.get("depth",0.3) * (1.0 + modifiers["depth_percent"] / 100.0))
                    elif modifiers.get("deeper"):
                        f["depth"] = min(1.0, f.get("depth",0.3)*1.3)

    # rebuild once after actions to reflect current state
    h = base_desert(seed)
    dune_mask_total[:] = 0
    for f in state["features"]:
        t = f["type"]
        if t in ("mountain","hill"):
            stamp_gaussian(h, f["x"], f["y"], f["radius"], f["height"], "max")
        elif t == "valley":
            add_valley(h, f["x"], f["y"], f["radius"], f["depth"])
        elif t == "dunes":
            box = (f["x0"], f["y0"], f["x1"], f["y1"])
            add_dunes(h, box, amp=f["amp"], freq=f["freq"], angle_deg=f["angle"], seed=seed)
            x0,y0,x1,y1 = box
            dune_mask_total[y0:y1, x0:x1] = 1.0

    h = gaussian_filter(h, sigma=0.8)  # cheap seam softener
    h = normalize01(h)
    splat = make_splatmap(h, dune_mask_total)
    return h, state, splat

