# Optimal Architecture - The Right Way

## 🎯 **Core Principle: Single Source of Truth**

**One type system, used everywhere. No adapters, no parallel systems, no confusion.**

---

## 📐 **Architectural Analysis**

### **What We Need (Requirements):**

1. **Type Safety** - Catch errors at dev time, not runtime
2. **Clean Domain Model** - Features are domain objects, not dicts
3. **Serialization Boundary** - JSON I/O only at edges (API, file system)
4. **No Duplication** - One Position type, one Feature type, one State type
5. **Backward Compatibility** - Existing terrain_state.json files must load
6. **Performance** - No unnecessary conversions between types

### **What EXISTS (3 Competing Systems):**

#### **System A: `domain/models.py` (Dataclass, Typed, UNUSED)**
```python
@dataclass
class Position:
    """Flexible position (x/y OR region OR relative)"""
    x: Optional[int] = None
    y: Optional[int] = None
    region: Optional[str] = None
    relative_to: Optional[str] = None

@dataclass
class Feature:
    """Typed feature (flat structure)"""
    id: int
    type: str
    position: Position
    parameters: FeatureParameters
    
    def to_dict(self) -> Dict[str, Any]:
        # Flatten for JSON
```

**Pros:**
✅ Already exists, well-designed
✅ Dataclass = simple, pythonic
✅ Flexible Position (absolute/region/relative)
✅ Has to_dict/from_dict for I/O

**Cons:**
❌ Not actually used anywhere in codebase
❌ Flat structure (parameters in separate dataclass)
❌ No polymorphism (all features use same FeatureParameters)

---

#### **System B: My Sketch (`features/base.py`, OOP, NEW)**
```python
class Feature(ABC):
    """OOP feature with methods"""
    def __init__(self, identity, geometry, appearance):
        ...
    
    @abstractmethod
    def get_stamp(self, seed: int) -> np.ndarray:
        pass
    
    @abstractmethod
    def get_blending_mode(self) -> BlendingMode:
        pass

class Mountain(Feature):
    """Concrete mountain with MountainParams"""
    def get_stamp(self, seed):
        return generate_mountain(...)
```

**Pros:**
✅ OOP = polymorphism, encapsulation
✅ Type-specific parameters (MountainParams, ValleyParams)
✅ Methods on objects (get_stamp, get_blending_mode)
✅ Strong separation of concerns (identity/geometry/appearance)

**Cons:**
❌ Duplicates domain/models.py
❌ More complex (ABC, inheritance)
❌ Not integrated with existing code
❌ My Position type conflicts with domain/models.Position

---

#### **System C: Legacy (`FeatureState`, Dict-based, ACTIVELY USED)**
```python
class FeatureState:
    """Dict-based state manager"""
    def add_feature(self, feature: Dict) -> int:
        ...
    
    def list_features(self) -> List[Dict]:
        return self.state["features"]
```

**Pros:**
✅ Actually used in terrain.py
✅ Simple (just dicts)
✅ Works with existing FeatureRegistry

**Cons:**
❌ No type safety
❌ Runtime errors (KeyError, wrong types)
❌ Hard to refactor
❌ No IDE autocomplete

---

## ✨ **The OPTIMAL Solution: Hybrid Approach**

### **Core Insight:**

**Use dataclasses for DATA, use OOP for BEHAVIOR.**

```
Domain Models (Data)          Engine (Behavior)
     ↓                              ↓
Feature (dataclass)    →    FeatureRenderer (OOP)
     ↓                              ↓
  to_dict() for I/O         get_stamp() methods
```

### **Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                  Layer 1: Core Types                         │
│  (Immutable primitives - shared utilities)                   │
├─────────────────────────────────────────────────────────────┤
│  server/core/                                                │
│    geometry.py:                                              │
│      - GridPosition(x, y)       [immutable, validated]       │
│      - Region(x_min, x_max, ...) [immutable, validated]      │
│      - Circle(center, radius)    [immutable, validated]      │
│                                                              │
│  Purpose: Shared spatial types for calculations             │
│  Used by: Narrative tools, spatial queries, constraints     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 2: Domain Models (Data)                   │
│  (What features ARE - dataclasses)                           │
├─────────────────────────────────────────────────────────────┤
│  server/domain/models.py:                                    │
│                                                              │
│    @dataclass                                                │
│    class Position:                                           │
│        """Flexible position spec (x/y OR region OR relative)│
│        x: Optional[int]                                      │
│        y: Optional[int]                                      │
│        region: Optional[str]  # "center", "left", etc.      │
│        relative_to: Optional[str]                            │
│                                                              │
│    @dataclass                                                │
│    class FeatureData:                                        │
│        """Base data for all features"""                      │
│        id: int                                               │
│        type: str  # "mountain", "valley", etc.              │
│        position: Position                                    │
│        base_params: Dict[str, Any]  # Flexible params       │
│        metadata: Dict[str, Any]                              │
│                                                              │
│        def to_dict(self) -> Dict[str, Any]:                 │
│            """Serialize for JSON (I/O boundary)"""           │
│                                                              │
│        @classmethod                                          │
│        def from_dict(cls, data: Dict) -> 'FeatureData':     │
│            """Deserialize from JSON (I/O boundary)"""        │
│                                                              │
│    @dataclass                                                │
│    class TerrainState:                                       │
│        """Complete terrain state"""                          │
│        features: List[FeatureData]                           │
│        seed: int                                             │
│        biome: str                                            │
│        next_id: int                                          │
│        semantic_scene: Optional[Dict]                        │
│                                                              │
│  Purpose: Domain data structures (WHAT, not HOW)            │
│  Serialization: Only at I/O boundaries (JSON files, API)    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           Layer 3: Feature Renderers (Behavior)              │
│  (How features are RENDERED - OOP)                           │
├─────────────────────────────────────────────────────────────┤
│  server/engine/renderers.py:                                 │
│                                                              │
│    class FeatureRenderer(ABC):                               │
│        """Knows HOW to render a feature type"""              │
│        @abstractmethod                                       │
│        def render(self, feature: FeatureData, seed: int)     │
│                 -> Tuple[np.ndarray, BlendingMode]:          │
│            pass                                              │
│                                                              │
│    class MountainRenderer(FeatureRenderer):                  │
│        def render(self, feature: FeatureData, seed: int):    │
│            # Extract mountain-specific params                │
│            radius = feature.base_params.get('radius', 56)    │
│            steepness = feature.base_params.get('steepness')  │
│            height = feature.base_params.get('height', 0.75)  │
│                                                              │
│            # Generate stamp using primitive function         │
│            from ..primitives.mountains import generate_mtn   │
│            stamp = generate_mountain(                        │
│                cx=feature.position.x,                        │
│                cy=feature.position.y,                        │
│                radius=radius,                                │
│                height=height,                                │
│                steepness=steepness,                          │
│                seed=seed                                     │
│            )                                                 │
│            return stamp, BlendingMode.MAX                    │
│                                                              │
│    class RendererRegistry:                                   │
│        """Maps feature types → renderers"""                  │
│        _renderers = {                                        │
│            "mountain": MountainRenderer(),                   │
│            "valley": ValleyRenderer(),                       │
│            # ...                                             │
│        }                                                     │
│                                                              │
│        @classmethod                                          │
│        def render(cls, feature: FeatureData, seed: int):     │
│            renderer = cls._renderers[feature.type]           │
│            return renderer.render(feature, seed)             │
│                                                              │
│  Purpose: Encapsulate rendering logic (HOW to make stamps)  │
│  Replaces: FeatureRegistry (similar pattern, cleaner API)   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 4: State Management                       │
│  (Managing collections of features)                          │
├─────────────────────────────────────────────────────────────┤
│  Use: domain/models.TerrainState directly                    │
│                                                              │
│  terrain_state = TerrainState.from_dict(json_data)          │
│  terrain_state.features  # List[FeatureData]                │
│  terrain_state.add_feature(feature_data)                     │
│  terrain_state.to_dict()  # For JSON serialization          │
│                                                              │
│  NO separate FeatureState class needed!                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Key Design Decisions**

### **Decision 1: Dataclass for Data, Not OOP**

**Why:**
- Features are primarily DATA (id, type, position, params)
- Don't need polymorphic behavior on the data itself
- Simpler serialization (dataclass → dict → JSON)
- Better for state management (immutable, hashable)

**Implementation:**
```python
@dataclass
class FeatureData:
    """Pure data - no behavior"""
    id: int
    type: str
    position: Position
    base_params: Dict[str, Any]  # Flexible, not pre-defined
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### **Decision 2: OOP for Rendering, Not Data**

**Why:**
- Rendering logic IS polymorphic (mountains ≠ valleys)
- Encapsulates primitive function calls
- Easy to add new feature types (just add renderer)
- Separates WHAT (data) from HOW (rendering)

**Implementation:**
```python
class MountainRenderer(FeatureRenderer):
    def render(self, feature: FeatureData, seed: int):
        # Extract params, call primitive, return stamp
        ...
```

### **Decision 3: Single Position Type (domain/models.py)**

**Why:**
- `domain/models.Position` is more flexible (absolute/region/relative)
- Already exists and is well-designed
- Parsers output this format
- Spatial resolvers work with this format

**My `core/geometry.GridPosition` is DIFFERENT:**
- Used for calculations AFTER position is resolved
- Immutable, validated, simple (x, y only)
- Used internally by spatial queries, constraints

**Coexistence:**
```python
# domain/models.Position: Specification (what user wants)
pos_spec = Position(region="center")

# Resolved to core/geometry.GridPosition: Concrete location
from core.geometry import GridPosition
grid_pos = GridPosition(256, 256)
```

### **Decision 4: Parameters as Dict, Not Typed**

**Why:**
- Different features have different parameters
- Don't want 6+ separate dataclasses (MountainParams, ValleyParams, etc.)
- Flexible for narrative-generated features
- Validation happens at rendering time

**Implementation:**
```python
# Mountain feature:
feature = FeatureData(
    id=1,
    type="mountain",
    position=Position(x=256, y=256),
    base_params={
        "radius": 56,
        "steepness": 1.2,
        "height": 0.75,
        "use_noise": True
    }
)

# Valley feature (different params, same structure):
feature = FeatureData(
    id=2,
    type="valley",
    position=Position(x=100, y=100),
    base_params={
        "radius": 80,
        "depth": 0.6,
        "flatness": 0.5
    }
)
```

---

## 🔧 **Migration Path**

### **Phase 1: Refine domain/models.py (Current Week)**

1. **Rename `Feature` → `FeatureData`** (clarify it's data, not behavior)
2. **Simplify `FeatureParameters` → `base_params: Dict`** (more flexible)
3. **Keep Position as-is** (it's already perfect)
4. **Keep TerrainState as-is** (it's already perfect)

```python
# server/domain/models.py (REFINED)

@dataclass
class FeatureData:
    """
    Feature data (WHAT a feature is, not HOW it renders).
    
    This is the single source of truth for feature state.
    Use this everywhere except at rendering time.
    """
    id: int
    type: str  # "mountain", "valley", "dunes", "cliff", "plateau", "canyon"
    position: Position
    base_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON (I/O boundary only)."""
        result = {
            "id": self.id,
            "type": self.type,
            **asdict(self.position),  # Flatten position
            **self.base_params,  # Flatten params
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureData':
        """Deserialize from JSON (I/O boundary only)."""
        # Extract known position fields
        position = Position(
            x=data.get("x"),
            y=data.get("y"),
            region=data.get("region"),
            relative_to=data.get("relative_to"),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0)
        )
        
        # Everything else goes in base_params
        known_keys = {"id", "type", "x", "y", "region", "relative_to", 
                     "offset_x", "offset_y", "metadata"}
        base_params = {k: v for k, v in data.items() if k not in known_keys}
        
        return cls(
            id=data["id"],
            type=data["type"],
            position=position,
            base_params=base_params,
            metadata=data.get("metadata", {})
        )
```

### **Phase 2: Create RendererRegistry (Week 2)**

Replace `FeatureRegistry` with cleaner `RendererRegistry`:

```python
# server/engine/renderers.py (NEW)

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np
from ..domain.models import FeatureData
from .stamping import BlendingMode

class FeatureRenderer(ABC):
    """Renders a feature type to heightmap stamp."""
    
    @abstractmethod
    def render(self, feature: FeatureData, seed: int) -> Tuple[np.ndarray, BlendingMode]:
        """
        Render feature to stamp + blending mode.
        
        Args:
            feature: Feature data (typed)
            seed: Random seed
            
        Returns:
            (512x512 heightmap stamp, blending mode)
        """
        pass

class MountainRenderer(FeatureRenderer):
    def render(self, feature: FeatureData, seed: int):
        from ..primitives.mountains import generate_mountain
        
        stamp = generate_mountain(
            cx=feature.position.x or 256,
            cy=feature.position.y or 256,
            radius=feature.base_params.get("radius", 56),
            height=feature.base_params.get("height", 0.75),
            steepness=feature.base_params.get("steepness", 1.0),
            use_noise=feature.base_params.get("use_noise", True),
            seed=seed
        )
        return stamp, BlendingMode.MAX

# ... Similar for Valley, Dunes, etc.

class RendererRegistry:
    """Central registry of feature renderers."""
    
    _renderers: Dict[str, FeatureRenderer] = {}
    
    @classmethod
    def register(cls, feature_type: str, renderer: FeatureRenderer):
        cls._renderers[feature_type] = renderer
    
    @classmethod
    def render(cls, feature: FeatureData, seed: int) -> Tuple[np.ndarray, BlendingMode]:
        """Render a feature using its registered renderer."""
        renderer = cls._renderers.get(feature.type)
        if not renderer:
            raise ValueError(f"No renderer for feature type: {feature.type}")
        return renderer.render(feature, seed)

# Auto-register core renderers
RendererRegistry.register("mountain", MountainRenderer())
RendererRegistry.register("valley", ValleyRenderer())
# ...
```

### **Phase 3: Update terrain.py to Use TerrainState (Week 2)**

```python
# server/terrain.py (UPDATED)

from .domain.models import TerrainState, FeatureData

def apply_actions(cmd: str, state: Dict, ...) -> Tuple[np.ndarray, Dict, np.ndarray]:
    # ... (steps 1-2: scene graph, parse) ...
    
    # Step 3: Load TYPED state
    terrain_state = TerrainState.from_dict(state)
    
    # ... (steps 4-7: removals) ...
    
    # Step 8: Build terrain with TYPED features
    builder = TerrainBuilder(base_biome_fn, seed)
    for feature in terrain_state.features:  # List[FeatureData]
        apply_feature_to_builder(builder, feature, seed)
    
    # ... (steps 9-10: add actions) ...
    
    # Step 11: Serialize typed → dict for JSON
    updated_state = terrain_state.to_dict()
    return h, updated_state, splat

def apply_feature_to_builder(builder: TerrainBuilder, feature: FeatureData, seed: int):
    """Apply TYPED feature to builder."""
    from .engine.renderers import RendererRegistry
    
    # Render using registry (clean, typed API)
    stamp, mode = RendererRegistry.render(feature, seed)
    
    # Apply
    builder.apply_feature(stamp, mode.value, feature_type=feature.type)
```

---

## ✅ **Benefits of This Architecture**

1. **Type Safety**: `FeatureData` is typed, used everywhere
2. **No Adapters**: No dict ↔ typed conversions except at I/O
3. **Clean Separation**: Data (FeatureData) vs Behavior (Renderer)
4. **Backward Compatible**: `to_dict()` / `from_dict()` for JSON
5. **Flexible Params**: Dict-based params, not 6+ typed dataclasses
6. **Easy to Extend**: Add renderer, register, done
7. **Single Source of Truth**: One Feature type, used everywhere

---

## 🎯 **Summary**

**What to BUILD:**
- ✅ Use `domain/models.py` (refine FeatureData, TerrainState)
- ✅ Create `engine/renderers.py` (RendererRegistry, clean API)
- ✅ Keep `core/geometry.py` (GridPosition for calculations)
- ✅ Migrate terrain.py to use TerrainState

**What to DISCARD:**
- ❌ My `features/base.py` (OOP Feature ABC)
- ❌ My `features/mountain.py` (Mountain class)
- ❌ My `features/adapters.py` (not needed)
- ❌ `semantic/state_manager.py` (FeatureState, dict-based)

**Ready to implement this the RIGHT way?**

