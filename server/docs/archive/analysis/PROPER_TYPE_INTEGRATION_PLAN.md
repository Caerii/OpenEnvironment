# Proper Type Integration Plan - Understanding What EXISTS

## ⚠️ **CRITICAL REALIZATION: We Have DUPLICATE Type Systems!**

### **What I Found:**

#### **System 1: NEW (What I Just Built) ✨**
```
server/core/geometry.py         ← Position, Region, Circle (NEW, immutable)
server/features/base.py          ← Feature ABC (NEW, OOP)
server/features/mountain.py      ← Mountain class (NEW)
server/features/adapters.py      ← Adapters (NEW)
```

#### **System 2: EXISTING (domain/models.py) 📦**
```python
# server/domain/models.py (ALREADY EXISTS!)

@dataclass
class Position:
    """Position specification - x/y OR region OR relative_to"""
    x: Optional[int] = None
    y: Optional[int] = None
    region: Optional[str] = None
    relative_to: Optional[str] = None
    offset_x: int = 0
    offset_y: int = 0

@dataclass  
class FeatureParameters:
    """Feature parameters (height, radius, etc.)"""
    height: float = 0.5
    radius: int = 50
    steepness: float = 1.0
    # ... etc

@dataclass
class Feature:
    """Typed feature (dataclass, not OOP)"""
    id: int
    type: str
    position: Position
    parameters: FeatureParameters
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        # Flatten to dict for backward compat

@dataclass
class TerrainState:
    """Complete state manager with typed features"""
    features: List[Feature]  # ← TYPED!
    seed: int = 0
    next_id: int = 1
    semantic_scene: Optional[Dict] = None
    
    def add_feature(self, feature: Feature) -> int:
        ...
    def remove_feature(self, feature_id: int) -> bool:
        ...
```

#### **System 3: LEGACY (FeatureState in semantic/state_manager.py) 🏚️**
```python
# server/semantic/state_manager.py (DICT-BASED, OLD)

class FeatureState:
    """Dict-based state manager (LEGACY)"""
    def __init__(self, state: Optional[Dict] = None):
        self.state = state or {"features": [], "seed": 0, "next_id": 1}
    
    def add_feature(self, feature: Dict) -> int:
        # Works with DICTS
        ...
    
    def list_features(self) -> List[Dict]:
        # Returns DICTS
        return self.state["features"].copy()
```

---

## 🤦 **The Problem: THREE Competing Systems!**

### **Conflicts:**

1. **`core/geometry.Position` (NEW)** vs **`domain/models.Position` (EXISTING)**
   - NEW: Immutable, simple (x, y), validated
   - EXISTING: Flexible (absolute OR region OR relative), dataclass
   
2. **`features/base.Feature` (NEW OOP ABC)** vs **`domain/models.Feature` (EXISTING dataclass)**
   - NEW: OOP hierarchy, get_stamp() methods, BlendingMode enum
   - EXISTING: Dataclass, flat structure, to_dict() for compatibility
   
3. **`domain/models.TerrainState` (TYPED)** vs **`semantic/state_manager.FeatureState` (DICTS)**
   - TerrainState: Uses typed Feature dataclasses
   - FeatureState: Uses Dict[str, Any]

### **Current Usage:**

```python
# terrain.py line 272:
feature_state = FeatureState(state)  # ← Uses DICT-BASED FeatureState!

# orchestration.py line 289:
for feat in feature_state.list_features():  # ← Returns List[Dict]
    _apply_feature_to_builder(builder, feat, seed)  # ← Expects Dict
```

**BUT... `domain/models.py` has been sitting there UNUSED with proper types!**

---

## ✅ **The CORRECT Path Forward**

### **Option A: Use Existing domain/models.py (RECOMMENDED)**

**Rationale:**
- `domain/models.py` ALREADY has typed Feature + TerrainState
- It's designed for gradual migration (has `to_dict()` / `from_dict()`)
- It's dataclass-based (simpler than OOP hierarchy)
- It's ALREADY IN THE CODEBASE (respect existing work!)

**Changes Needed:**

1. **Migrate from `FeatureState` (dict) → `TerrainState` (typed)**
   ```python
   # REPLACE in terrain.py:
   # OLD:
   feature_state = FeatureState(state)  # Dict-based
   
   # NEW:
   terrain_state = TerrainState.from_dict(state)  # Typed!
   ```

2. **Update `_apply_feature_to_builder` to accept Feature dataclass**
   ```python
   # engine/commands.py
   def _apply_feature_to_builder(builder: TerrainBuilder, feat: Feature, seed: int):
       """
       Apply typed Feature to builder.
       
       Args:
           feat: Typed Feature dataclass (from domain/models.py)
       """
       from ..engine.feature_registry import FeatureRegistry
       
       # Convert to dict for legacy FeatureRegistry
       feat_dict = feat.to_dict()  # ← domain/models.Feature has this!
       
       # Generate stamp
       stamp = FeatureRegistry.generate_stamp(feat.type, feat_dict, seed)
       mode = FeatureRegistry.get_blending_mode(feat.type)
       
       # Apply
       builder.apply_feature(stamp, mode, feature_type=feat.type, feature_params=feat_dict)
   ```

3. **Bridge: Extend FeatureRegistry to accept typed Features**
   ```python
   # engine/feature_registry.py
   class FeatureRegistry:
       @classmethod
       def generate_stamp_typed(cls, feature: 'Feature', seed: int) -> np.ndarray:
           """
           Generate stamp from typed Feature (domain/models.Feature).
           
           This is the NEW API. Old dict-based API stays for compatibility.
           """
           from ..domain.models import Feature
           
           # Convert to dict and use existing generator
           feat_dict = feature.to_dict()
           return cls.generate_stamp(feature.type, feat_dict, seed)
   ```

4. **DISCARD my new OOP Feature classes** (sorry for the confusion!)
   - They duplicate existing work in `domain/models.py`
   - The dataclass approach in domain/models is simpler and already integrated
   - My `core/geometry.py` can stay as utilities, but not for features

---

### **Option B: Enhance My New OOP System (NOT RECOMMENDED)**

**Why NOT:**
- Duplicates existing `domain/models.py`
- More complex (ABC, inheritance, methods)
- Ignores existing codebase conventions
- More refactoring needed

---

## 🎯 **CORRECT Integration Steps (Using Existing Types)**

### **Phase 1: Switch from FeatureState → TerrainState (Week 1)**

```python
# FILE: terrain.py

def apply_actions(...) -> Tuple[np.ndarray, Dict, np.ndarray]:
    # ... (steps 1-2: parse) ...
    
    # Step 3: Initialize TYPED state manager
    from .domain.models import TerrainState
    terrain_state = TerrainState.from_dict(state)  # ← Load typed features!
    
    # ... (steps 4-7: removals) ...
    
    # Step 8: Build terrain with TYPED features
    builder = TerrainBuilder(base_biome_fn, seed)
    for feature in terrain_state.features:  # ← List[Feature], not List[Dict]!
        _apply_feature_to_builder_typed(builder, feature, seed)
    
    # ... (rest) ...
    
    # Step 11: Save as dict for JSON
    updated_state = terrain_state.to_dict()  # ← Serialize typed → dict
    return h, updated_state, splat
```

### **Phase 2: Update Feature Application (Week 1)**

```python
# FILE: engine/commands.py

def _apply_feature_to_builder_typed(
    builder: TerrainBuilder,
    feature: 'Feature',  # domain/models.Feature
    seed: int
):
    """
    Apply TYPED feature to builder.
    
    This is the NEW primary path. Old dict-based helper stays for compatibility.
    """
    from ..domain.models import Feature
    from ..engine.feature_registry import FeatureRegistry
    
    # Convert to dict for FeatureRegistry (still uses dicts internally)
    feat_dict = feature.to_dict()
    
    # Generate stamp (existing FeatureRegistry code)
    stamp = FeatureRegistry.generate_stamp(feature.type, feat_dict, seed)
    mode = FeatureRegistry.get_blending_mode(feature.type)
    
    # Apply
    builder.apply_feature(stamp, mode, feature_type=feature.type, feature_params=feat_dict)
```

### **Phase 3: Update ActionCommands to Work with Typed State (Week 2)**

```python
# FILE: engine/commands.py

class AddFeatureCommand(ActionCommand):
    def execute(self, builder, state, seed):
        """state is now TerrainState (typed), not FeatureState (dict)!"""
        from ..domain.models import Feature, FeatureParameters, Position as DomainPosition
        
        # Create TYPED feature
        params = FeatureParameters(
            height=self.action.get("height", 0.5),
            radius=self.action.get("radius", 50),
            steepness=self.action.get("steepness", 1.0)
        )
        
        pos = DomainPosition(
            x=self.action.get("x"),
            y=self.action.get("y")
        )
        
        feature = Feature(
            id=0,  # Will be assigned by TerrainState.add_feature()
            type=self.action.get("type", "mountain"),
            position=pos,
            parameters=params
        )
        
        # Add to typed state
        feature_id = state.add_feature(feature)
        
        # Apply to builder
        if builder:
            _apply_feature_to_builder_typed(builder, feature, seed)
        
        return [feature_id]
```

### **Phase 4: Update Narrative Tools to Generate Typed Features (Week 2-3)**

```python
# FILE: semantic/narrative/composition.py

from ...domain.models import Feature, FeatureParameters, Position as DomainPosition

def generate_features_from_narrative(narrative: TerrainNarrative) -> List[Feature]:
    """Generate TYPED features from narrative."""
    features = []
    
    for spec in narrative.composition.features:
        params = FeatureParameters(
            height=spec.height,
            radius=spec.radius,
            steepness=spec.steepness
        )
        
        pos = DomainPosition(x=spec.x, y=spec.y)
        
        feature = Feature(
            id=0,  # Will be assigned
            type=spec.feature_type.value,
            position=pos,
            parameters=params,
            metadata={"role": spec.role, "narrative_id": narrative.id}
        )
        
        features.append(feature)
    
    return features
```

---

## 📊 **Migration Checklist**

### **✅ What to KEEP:**
- [x] `domain/models.py` (Feature, FeatureParameters, Position, TerrainState)
- [x] `core/geometry.py` (Position, Region, Circle) - Rename to avoid conflict, use as utilities
- [x] Existing `FeatureRegistry` (works with dicts)
- [x] Existing `TerrainBuilder` (works with stamps)

### **❌ What to DISCARD:**
- [ ] `features/base.py` (Feature ABC) - duplicates domain/models.Feature
- [ ] `features/mountain.py` (Mountain class) - use domain/models.Feature instead
- [ ] `features/adapters.py` - not needed, domain/models already has to_dict/from_dict

### **🔄 What to CHANGE:**
- [ ] `terrain.py`: Use `TerrainState.from_dict()` instead of `FeatureState()`
- [ ] `orchestration.py`: Update to work with `List[Feature]` instead of `List[Dict]`
- [ ] `engine/commands.py`: Create `_apply_feature_to_builder_typed()` 
- [ ] `engine/commands.py`: Update ActionCommand classes to create typed Features
- [ ] Rename `core/geometry.Position` → `core/geometry.GridPosition` to avoid conflict

---

## 🎯 **Immediate Action**

**STOP building the OOP Feature system. START using domain/models.py properly!**

### **Next Steps:**

1. **Rename core/geometry types** to avoid conflicts:
   - `Position` → `GridPosition`
   - Keep `Region`, `Circle` as spatial utilities

2. **Create bridge function** `_apply_feature_to_builder_typed()` in engine/commands.py

3. **Update terrain.py** to use `TerrainState` instead of `FeatureState`

4. **Test migration** with existing terrain generation

5. **Gradually update** ActionCommands to create typed Features

**This respects the existing codebase and builds on what's there, not replacing it!**

