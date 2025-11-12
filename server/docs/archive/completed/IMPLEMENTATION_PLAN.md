# Comprehensive Implementation Plan - Balanced Approach

## Overview
This plan addresses **all critical areas** in a balanced way: production bugs, architectural improvements, and aesthetic enhancements. Optimized for single-user local development.

---

## Phase 1: Critical Production Fixes (Week 1)

### 1.1 Fix Race Conditions & State Management
**Files:** `server/main.py`, `server/semantic/state_manager.py`

**Tasks:**
- Add file locking for state.json (cross-platform: use `fcntl` on Unix, `msvcrt` on Windows, or simple lock file)
- Implement atomic writes (write to temp file, then rename)
- Add state validation on load (handle corrupted state gracefully)
- Add state backup before modifications

**Key Changes:**
```python
# Atomic state operations
def atomic_read_state() -> Dict:
    with open(STATE_PATH, "r") as f:
        # Use file locking (cross-platform solution)
        if sys.platform != 'win32':
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        return json.load(f)

def atomic_write_state(state: Dict):
    temp_path = STATE_PATH + ".tmp"
    with open(temp_path, "w") as f:
        if sys.platform != 'win32':
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(state, f, indent=2)
    os.replace(temp_path, STATE_PATH)  # Atomic rename
```

### 1.2 Fix Non-Deterministic Randomness
**Files:** `server/engine/spatial.py`, `server/primitives/dunes.py`, `server/terrain.py`

**Tasks:**
- Replace Python `random` module with NumPy's `RandomState`
- Use deterministic seed derivation (hash of feature ID + global seed)
- Remove magic number hacks (like `seed+17`)

**Key Changes:**
```python
# spatial.py - Use seeded NumPy RNG
import numpy as np

def random_point_in(box: Tuple[int, int, int, int], seed: int = 0) -> Tuple[int, int]:
    rng = np.random.RandomState(seed)
    x0, y0, x1, y1 = box
    return (rng.randint(x0, x1), rng.randint(y0, y1))

# dunes.py - Remove seed+17 hack
n = pnoise2(xr, yr, octaves=2, repeatx=4096, repeaty=4096, base=seed)
```

### 1.3 Add Comprehensive Error Handling
**Files:** `server/main.py`

**Tasks:**
- Wrap all endpoints in try/except
- Return proper HTTP status codes (400, 500, etc.)
- Add structured error responses
- Log errors with context

**Key Changes:**
```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.post("/api/generate")
def generate(cmd: Command):
    try:
        # Validate input
        if not cmd.text or not cmd.text.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        # Read state with error handling
        try:
            state = atomic_read_state()
        except FileNotFoundError:
            state = {"features": [], "seed": 0}
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted state file: {e}")
            state = {"features": [], "seed": 0}  # Reset on corruption
        
        # Generate terrain
        try:
            h, state, splat = apply_actions(cmd.text, state)
        except Exception as e:
            logger.error("Terrain generation failed", exc_info=e)
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        
        # Save state atomically
        atomic_write_state(state)
        
        # Save outputs
        tag = generate_unique_tag()
        urls = save_outputs(h, splat, tag)
        
        return {"ok": True, "state": state, "assets": urls}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 1.4 Add Input Validation
**Files:** `server/main.py`

**Tasks:**
- Enhance Command model with Pydantic validators
- Add length limits (max 1000 chars)
- Content validation (not empty, not just whitespace)

**Key Changes:**
```python
from pydantic import Field, validator

class Command(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    
    @validator('text')
    def validate_text(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Command cannot be empty or whitespace")
        return v
```

### 1.5 Fix Normalization Edge Cases
**Files:** `server/utils.py`

**Tasks:**
- Handle NaN/Inf values
- Handle empty arrays
- Better handling of flat terrain

**Key Changes:**
```python
def normalize01(h: np.ndarray) -> np.ndarray:
    if h.size == 0:
        return h
    
    if np.any(np.isnan(h)) or np.any(np.isinf(h)):
        raise ValueError("Heightmap contains NaN or Inf values")
    
    h_min = h.min()
    h_max = h.max()
    
    if h_max == h_min:
        return np.zeros_like(h)  # Flat terrain → all zeros
    
    return (h - h_min) / (h_max - h_min)
```

### 1.6 Add File Cleanup
**Files:** `server/main.py`

**Tasks:**
- Keep only last N asset files (e.g., last 20)
- Cleanup old files on startup
- Use UUIDs instead of timestamps for uniqueness

**Key Changes:**
```python
import uuid
import glob

def cleanup_old_assets(max_files: int = 20):
    """Keep only the most recent N asset files."""
    pattern = os.path.join(OUT_DIR, "height_*_*.png")
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    
    for file in files[max_files:]:
        try:
            os.remove(file)
        except Exception as e:
            logger.warning(f"Failed to delete {file}: {e}")

def generate_unique_tag() -> str:
    return str(uuid.uuid4())

# Call on startup
cleanup_old_assets()
```

---

## Phase 2: Architectural Foundation (Week 2)

### 2.1 Create Feature Base Class
**Files:** NEW `server/features/__init__.py`, NEW `server/features/base.py`

**Tasks:**
- Create abstract Feature base class
- Define interface (generate_stamp, get_blending_mode, serialize, etc.)
- Add parameter validation

**Key Structure:**
```python
# features/base.py
from abc import ABC, abstractmethod
from typing import Dict, Tuple
import numpy as np

class Feature(ABC):
    def __init__(self, feature_id: int, x: int, y: int):
        self.id = feature_id
        self.x = self._validate_coord(x)
        self.y = self._validate_coord(y)
    
    def _validate_coord(self, coord: int) -> int:
        if not (0 <= coord < 512):
            raise ValueError(f"Coordinate {coord} out of bounds [0, 512)")
        return coord
    
    @abstractmethod
    def generate_stamp(self, terrain: np.ndarray, seed: int) -> np.ndarray:
        """Generate heightmap stamp for this feature."""
        pass
    
    @abstractmethod
    def get_blending_mode(self) -> str:
        """Get blending mode for this feature."""
        pass
    
    @abstractmethod
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get bounding box (x0, y0, x1, y1)."""
        pass
    
    def serialize(self) -> Dict:
        """Serialize to dict for storage."""
        return {"id": self.id, "type": self.get_type(), "x": self.x, "y": self.y}
    
    @abstractmethod
    def get_type(self) -> str:
        """Get feature type string."""
        pass
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict) -> 'Feature':
        """Deserialize from dict."""
        pass
```

### 2.2 Create Concrete Feature Classes
**Files:** NEW `server/features/mountain.py`, `server/features/hill.py`, `server/features/valley.py`, `server/features/dunes.py`

**Tasks:**
- Migrate each feature type to a class
- Move creation logic from terrain.py into classes
- Add validation

**Key Structure:**
```python
# features/mountain.py
from .base import Feature
from ..primitives.mountains import generate_mountain
from ..engine.stamping import BlendingMode

class MountainFeature(Feature):
    def __init__(self, feature_id: int, x: int, y: int, radius: int = 56, 
                 height: float = 0.75, steepness: float = 1.0):
        super().__init__(feature_id, x, y)
        self.radius = self._validate_radius(radius)
        self.height = self._validate_height(height)
        self.steepness = steepness
    
    def _validate_radius(self, radius: int) -> int:
        if not (1 <= radius <= 128):
            raise ValueError(f"Radius {radius} out of bounds [1, 128]")
        return radius
    
    def _validate_height(self, height: float) -> float:
        if not (0.0 <= height <= 1.0):
            raise ValueError(f"Height {height} out of bounds [0.0, 1.0]")
        return height
    
    def generate_stamp(self, terrain: np.ndarray, seed: int) -> np.ndarray:
        return generate_mountain(self.x, self.y, self.radius, self.height, self.steepness)
    
    def get_blending_mode(self) -> str:
        return BlendingMode.MAX
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        return (max(0, self.x - self.radius), max(0, self.y - self.radius),
                min(512, self.x + self.radius), min(512, self.y + self.radius))
    
    def get_type(self) -> str:
        return "mountain"
    
    @classmethod
    def deserialize(cls, data: Dict) -> 'MountainFeature':
        return cls(
            feature_id=data["id"],
            x=data["x"],
            y=data["y"],
            radius=data.get("radius", 56),
            height=data.get("height", 0.75),
            steepness=data.get("steepness", 1.0)
        )
```

### 2.3 Create Feature Registry
**Files:** NEW `server/features/registry.py`

**Tasks:**
- Central registry for feature types
- Plugin system for adding features
- Factory method for feature creation

**Key Structure:**
```python
# features/registry.py
from typing import Dict, Type
from .base import Feature

class FeatureRegistry:
    _types: Dict[str, Type[Feature]] = {}
    
    @classmethod
    def register(cls, ftype: str, feature_class: Type[Feature]):
        cls._types[ftype] = feature_class
    
    @classmethod
    def create(cls, ftype: str, params: Dict) -> Feature:
        if ftype not in cls._types:
            raise ValueError(f"Unknown feature type: {ftype}")
        return cls._types[ftype].from_params(params)
    
    @classmethod
    def deserialize(cls, data: Dict) -> Feature:
        ftype = data.get("type")
        if ftype not in cls._types:
            raise ValueError(f"Unknown feature type: {ftype}")
        return cls._types[ftype].deserialize(data)
```

### 2.4 Create Configuration System
**Files:** NEW `server/config.py`

**Tasks:**
- Central configuration for all defaults
- Feature-specific configs
- Environment variable support

**Key Structure:**
```python
# config.py
from dataclasses import dataclass, field
import os

@dataclass
class MountainConfig:
    default_height: float = 0.75
    default_radius: int = 56
    default_steepness: float = 1.0
    height_variation: float = 0.15  # ±15%
    radius_variation: float = 0.15
    min_height: float = 0.3
    max_height: float = 1.0
    min_radius: int = 32
    max_radius: int = 128

@dataclass
class TerrainConfig:
    resolution: int = 512
    default_seed: int = 0
    smoothing_sigma: float = 0.8
    mountains: MountainConfig = field(default_factory=MountainConfig)
    hills: HillConfig = field(default_factory=HillConfig)
    valleys: ValleyConfig = field(default_factory=ValleyConfig)
    dunes: DuneConfig = field(default_factory=DuneConfig)
    
    @classmethod
    def load(cls):
        """Load config, can be extended with environment variables."""
        return cls()

# Global config instance
_config = None

def get_config() -> TerrainConfig:
    global _config
    if _config is None:
        _config = TerrainConfig.load()
    return _config
```

### 2.5 Refactor terrain.py - Remove Double Rebuild
**Files:** `server/terrain.py`

**Tasks:**
- Remove duplicate rebuild (lines 118-124 and 130-134)
- Use FeatureRegistry instead of if/elif chains
- Single rebuild path

**Key Changes:**
```python
def apply_actions(cmd: str, state: Dict, base_biome_fn=None) -> Tuple[np.ndarray, Dict, np.ndarray]:
    seed = state.get("seed", 0)
    
    if base_biome_fn is None:
        base_biome_fn = base_desert
    
    # Parse command
    if not cmd or not cmd.strip():
        actions = []
    else:
        try:
            from .semantic.parser import SemanticParser
            parser = SemanticParser()
            parsed = parser.parse(cmd)
        except Exception as e:
            logger.warning(f"Semantic parser failed: {e}, using regex fallback")
            parsed = parse_command(cmd)
        actions = parsed.get("actions", [])
    
    # Initialize state manager
    feature_state = FeatureState(state)
    
    # SINGLE rebuild path (removed duplicate!)
    h = base_biome_fn(seed)
    dune_mask_total = np.zeros_like(h)
    
    # Reapply existing features
    for feat_data in feature_state.list_features():
        feat = FeatureRegistry.deserialize(feat_data)
        stamp = feat.generate_stamp(h, seed)
        mode = feat.get_blending_mode()
        stamp_primitive(h, stamp, mode)
        
        # Handle dune mask if needed
        if feat.get_type() == "dunes":
            bounds = feat.get_bounds()
            dune_mask_total[bounds[1]:bounds[3], bounds[0]:bounds[2]] = 1.0
    
    # Execute new actions
    for action in actions:
        _execute_action(action, h, feature_state, dune_mask_total, seed)
    
    # Post-processing
    apply_smoothing(h, sigma=0.8)
    h = normalize01(h)
    
    # Generate splatmap
    splat = generate_splatmap(h, dune_mask_total)
    
    return h, feature_state.to_dict(), splat
```

---

## Phase 3: Architectural Migration (Week 3)

### 3.1 Refactor _create_feature to Use Registry
**Files:** `server/terrain.py`

**Tasks:**
- Replace if/elif chains with FeatureRegistry.create()
- Use config for defaults
- Apply variation

**Key Changes:**
```python
def _create_feature(ftype: str, cx: int, cy: int, modifiers: Dict, seed: int, feature_id: int) -> Feature:
    """Create a feature using registry."""
    config = get_config()
    
    # Get default parameters from config
    if ftype == "mountain":
        base_height = config.mountains.default_height
        base_radius = config.mountains.default_radius
        # Apply modifiers
        if modifiers.get("height_percent"):
            base_height *= (1.0 + modifiers["height_percent"] / 100.0)
        elif modifiers.get("taller"):
            base_height *= 1.3
        
        # Apply variation (deterministic)
        variation_seed = hash(f"{feature_id}_{seed}") % (2**31)
        height = VariationEngine.apply_variation(
            base_height, config.mountains.height_variation, variation_seed
        )
        radius = VariationEngine.apply_variation_int(
            base_radius, config.mountains.radius_variation, variation_seed
        )
        
        return MountainFeature(feature_id, cx, cy, radius, height)
    
    # Similar for other types...
```

### 3.2 Refactor _reapply_feature to Use Registry
**Files:** `server/terrain.py`

**Tasks:**
- Replace if/elif chains with FeatureRegistry.deserialize()
- Use Feature.generate_stamp() method

**Key Changes:**
```python
def _reapply_feature(h: np.ndarray, feat_data: Dict, dune_mask: np.ndarray, seed: int):
    """Reapply a stored feature to terrain."""
    feat = FeatureRegistry.deserialize(feat_data)
    stamp = feat.generate_stamp(h, seed)
    mode = feat.get_blending_mode()
    stamp_primitive(h, stamp, mode)
    
    # Handle dune mask if needed
    if feat.get_type() == "dunes":
        bounds = feat.get_bounds()
        dune_mask[bounds[1]:bounds[3], bounds[0]:bounds[2]] = np.maximum(
            dune_mask[bounds[1]:bounds[3], bounds[0]:bounds[2]],
            generate_dune_mask(bounds)[bounds[1]:bounds[3], bounds[0]:bounds[2]]
        )
```

### 3.3 Update State Manager
**Files:** `server/semantic/state_manager.py`

**Tasks:**
- Support both dicts (backward compatibility) and Feature objects
- Migration function for old state files

**Key Changes:**
```python
def add_feature(self, feature: Union[Dict, Feature]) -> int:
    """Add a feature (dict or Feature object)."""
    if isinstance(feature, dict):
        # Legacy dict format
        feature_id = self.state["next_id"]
        feature["id"] = feature_id
        self.state["features"].append(feature)
    else:
        # Feature object
        feature_id = self.state["next_id"]
        feature.id = feature_id
        self.state["features"].append(feature.serialize())
    
    self.state["next_id"] += 1
    return feature_id
```

---

## Phase 4: Aesthetic Improvements (Week 4)

### 4.1 Add Variation System
**Files:** NEW `server/engine/variation.py`

**Tasks:**
- Deterministic variation engine
- Apply ±15% randomness to feature dimensions
- Seed-based for reproducibility

**Key Structure:**
```python
# engine/variation.py
import numpy as np

class VariationEngine:
    @staticmethod
    def apply_variation(base_value: float, variation: float, seed: int) -> float:
        """Apply ±variation% to base value deterministically."""
        rng = np.random.RandomState(seed)
        multiplier = 1.0 + rng.uniform(-variation, variation)
        return base_value * multiplier
    
    @staticmethod
    def apply_variation_int(base_value: int, variation: float, seed: int) -> int:
        """Apply variation to integer values."""
        varied = VariationEngine.apply_variation(float(base_value), variation, seed)
        return int(round(varied))
```

### 4.2 Apply Variation to Feature Creation
**Files:** `server/features/mountain.py`, `server/features/hill.py`, etc.

**Tasks:**
- Integrate variation into feature constructors
- Use config for variation percentages

**Key Changes:**
```python
# In MountainFeature creation
from ..engine.variation import VariationEngine
from ..config import get_config

config = get_config()
variation_seed = hash(f"{feature_id}_{seed}") % (2**31)

height = VariationEngine.apply_variation(
    config.mountains.default_height,
    config.mountains.height_variation,
    variation_seed
)

radius = VariationEngine.apply_variation_int(
    config.mountains.default_radius,
    config.mountains.radius_variation,
    variation_seed
)
```

### 4.3 Improve Spatial Distribution
**Files:** `server/engine/spatial.py`, `server/semantic/spatial_resolver.py`

**Tasks:**
- Implement Poisson disk sampling for scattered distribution
- Add minimum spacing enforcement

**Key Changes:**
```python
# spatial.py
def poisson_disk_sample(bounds: Tuple[int, int, int, int], count: int, 
                       min_distance: float, seed: int) -> List[Tuple[int, int]]:
    """Generate naturally distributed points."""
    x0, y0, x1, y1 = bounds
    rng = np.random.RandomState(seed)
    
    points = []
    attempts = 0
    max_attempts = count * 30
    
    while len(points) < count and attempts < max_attempts:
        x = rng.randint(x0, x1)
        y = rng.randint(y0, y1)
        
        # Check minimum distance
        valid = True
        for px, py in points:
            dist = np.sqrt((x - px)**2 + (y - py)**2)
            if dist < min_distance:
                valid = False
                break
        
        if valid:
            points.append((x, y))
        
        attempts += 1
    
    return points[:count]
```

### 4.4 Update Splatmap Edge Cases
**Files:** `server/engine/splatmap.py`

**Tasks:**
- Better handling of flat terrain
- Validate splatmap output

**Key Changes:**
```python
def generate_splatmap(heightmap: np.ndarray, dune_mask: np.ndarray = None) -> np.ndarray:
    # ... existing code ...
    
    # Snow: Handle flat terrain
    if h97 - h90 < 1e-6:
        snow = np.zeros_like(heightmap)
    else:
        snow = np.clip((heightmap - h90) / (h97 - h90), 0, 1)
    
    # ... rest of code ...
    
    # Validate output
    assert np.all(splat >= 0), "Splatmap contains negative values"
    assert np.all(splat <= 1), "Splatmap contains values > 1"
    
    return splat.astype(np.float32)
```

---

## Phase 5: Infrastructure & Polish (Week 5)

### 5.1 Add Logging System
**Files:** NEW `server/logging_config.py`, update `server/main.py`

**Tasks:**
- Structured logging setup
- Replace print() with logger calls

**Key Changes:**
```python
# logging_config.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('terrain.log')
        ]
    )
```

### 5.2 Update Frontend Error Display
**Files:** `web/src/App.tsx`

**Tasks:**
- Show error messages to user
- Add retry logic

**Key Changes:**
```typescript
const [error, setError] = useState<string | null>(null)

async function send(kind: 'gen' | 'mod') {
  setIsLoading(true)
  setError(null)
  try {
    const fn = kind === 'gen' ? postCommand : modifyCommand
    const res = await fn(input)
    setAssets(res.assets)
    setStateJson(res.state)
  } catch (err: any) {
    const errorMsg = err.response?.data?.detail || err.message || 'Unknown error'
    setError(errorMsg)
    console.error('Generation failed:', err)
  } finally {
    setIsLoading(false)
  }
}

// In JSX:
{error && (
  <div style={{
    color: '#ff6b6b',
    padding: '8px',
    background: '#2a1a1a',
    borderRadius: '4px',
    fontSize: '12px'
  }}>
    Error: {error}
  </div>
)}
```

### 5.3 Register Features
**Files:** NEW `server/features/__init__.py`

**Tasks:**
- Import all feature classes
- Register them with FeatureRegistry

**Key Changes:**
```python
# features/__init__.py
from .registry import FeatureRegistry
from .mountain import MountainFeature
from .hill import HillFeature
from .valley import ValleyFeature
from .dunes import DunesFeature

# Register all features
FeatureRegistry.register("mountain", MountainFeature)
FeatureRegistry.register("hill", HillFeature)
FeatureRegistry.register("valley", ValleyFeature)
FeatureRegistry.register("dunes", DunesFeature)
```

---

## Implementation Checklist

### Week 1: Critical Fixes
- [ ] Add atomic state operations (file locking)
- [ ] Fix non-deterministic randomness (NumPy RNG)
- [ ] Add error handling to all endpoints
- [ ] Add input validation (Pydantic)
- [ ] Fix normalization edge cases
- [ ] Add file cleanup (UUIDs, retention policy)

### Week 2: Architecture Foundation
- [ ] Create Feature base class
- [ ] Create MountainFeature class
- [ ] Create HillFeature class
- [ ] Create ValleyFeature class
- [ ] Create DunesFeature class
- [ ] Create FeatureRegistry
- [ ] Create Configuration system
- [ ] Remove double rebuild from terrain.py

### Week 3: Architecture Migration
- [ ] Refactor _create_feature to use registry
- [ ] Refactor _reapply_feature to use registry
- [ ] Update state_manager for backward compatibility
- [ ] Test with old state files
- [ ] Update semantic parser schema

### Week 4: Aesthetic Improvements
- [ ] Create VariationEngine
- [ ] Apply variation to feature creation
- [ ] Implement Poisson disk sampling
- [ ] Update splatmap edge cases
- [ ] Test aesthetic improvements

### Week 5: Polish & Testing
- [ ] Add logging system
- [ ] Update frontend error display
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update documentation

---

## Testing Strategy

### Unit Tests
- Test each Feature class independently
- Test VariationEngine
- Test normalization edge cases
- Test error handling

### Integration Tests
- Test full terrain generation pipeline
- Test backward compatibility with old state files
- Test error recovery

### Visual Tests
- Compare generated terrains before/after changes
- Verify aesthetic improvements

---

## Backward Compatibility

- Old state files (without IDs) should still work
- Feature dict format maintained during migration
- Gradual migration: support both dicts and Feature objects
- State migration function for old formats

---

## Success Criteria

- ✅ No race conditions (file locking works)
- ✅ Deterministic generation (same seed = same result)
- ✅ All endpoints have error handling
- ✅ Features can be added without modifying core code
- ✅ Natural variation in feature sizes (±15%)
- ✅ Smooth blending with no hard edges
- ✅ Files cleaned up automatically
- ✅ Errors displayed to user
- ✅ Comprehensive logging
- ✅ No double rebuild (single path)

---

This plan provides a **balanced, comprehensive approach** that addresses production bugs, architectural improvements, and aesthetic enhancements systematically over 5 weeks.

