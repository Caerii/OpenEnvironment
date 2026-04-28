# Magic Numbers - Strategic Organization Plan

**Date:** October 31, 2025  
**Status:** Strategy Defined

---

## 📊 MAGIC NUMBER INVENTORY

### **Category 1: Global Constants (Need Centralization)**

#### **`RES = 512` - Terrain Resolution**
- **Found in:** 23 files (21 after deleting dead code)
- **Should be:** `engine/config.py` (already exists!)
- **Priority:** 🔴 **HIGH**

**Current Locations:**
```
✅ engine/config.py (line 5)              ← CENTRAL SOURCE
❌ terrain.py (line 32)                   ← Should import
❌ primitives/*.py (17 files)             ← Should import
❌ engine/stamping.py                     ← Should import
❌ engine/spatial.py                      ← Should import  
❌ semantic/spatial_resolver.py           ← Should import
```

**Fix:**
```python
# engine/config.py - Already there!
TERRAIN_RESOLUTION = 512
RES = TERRAIN_RESOLUTION  # Alias

# Everywhere else - CHANGE TO:
from ..engine.config import RES  # primitives
from .config import RES           # engine  
from .engine.config import RES    # root level
```

---

### **Category 2: Feature Defaults (Already Centralized)**

#### **Height/Depth/Radius Defaults**
- **Should be:** `engine/feature_registry.py` ✅ **ALREADY THERE!**
- **Status:** ✅ **PROPERLY ORGANIZED**

**Example:**
```python
# engine/feature_registry.py - Line 73
def get_defaults(self) -> Dict:
    return {"radius": 56, "height": 0.75, "use_noise": True}
```

**Also duplicated in:**
- `engine/config.py` - MountainConfig, HillConfig, etc. ✅ Also appropriate
- `terrain.py` - Uses `defaults.get()` with fallbacks ⚠️ Could be cleaner

**Assessment:** 🟢 **MOSTLY OK** - Registry is primary source

---

### **Category 3: Algorithm Constants (Keep As-Is)**

#### **Smoothing, Blending, Thresholds**
- **Location:** Inside specific functions
- **Reason:** Algorithm-specific parameters
- **Status:** ✅ **CORRECT - DON'T CHANGE**

**Examples:**
```python
# engine/splatmap.py - Line 47
rock_slope = smoothstep(0.30, 0.75, slope)  # Slope thresholds for rock

# primitives/ridge.py - Line 38
falloff = np.exp(-width_norm * falloff_factor)  # Geometric falloff

# engine/erosion.py
apply_edge_erosion(heightmap, erosion_strength=0.12, erosion_radius=2)
```

**Why these are FINE:**
- ✅ Algorithm-specific (not global constants)
- ✅ Documented in context
- ✅ Tuning parameters (expected to vary)
- ✅ Function default arguments (good practice)

---

### **Category 4: Region Calculations (Consider Centralizing)**

#### **`RES // 3` - Region Size**
- **Found in:** `engine/spatial.py`, several other files
- **Current:** Hardcoded calculation
- **Should be:** Configurable?

**Current Code:**
```python
# engine/spatial.py
def region_box(keyword: str) -> Tuple[int, int, int, int]:
    T = RES // 3  # ← Hardcoded 3x3 grid
    regions = {
        "top-left": (0, 0, T, T),
        ...
    }
```

**Proposed:**
```python
# engine/config.py
@dataclass
class SpatialConfig:
    grid_divisions: int = 3  # 3x3 grid
    
    @property
    def region_size(self) -> int:
        return TERRAIN_RESOLUTION // self.grid_divisions
```

**Priority:** 🟡 **MEDIUM** - Nice-to-have, not critical

---

### **Category 5: Hardcoded Coordinates (Appropriate)**

#### **Spatial Query Regions** 
```python
# semantic/parser.py - Lines 156, 158, 160
region_features = query_engine.find_within_region((0, 0, 256, 512))  # Left half
region_features = query_engine.find_within_region((256, 0, 512, 512))  # Right half
```

**Assessment:** ✅ **APPROPRIATE** - These are calculated values (RES/2)

**Could be improved:**
```python
# More explicit
left_half = (0, 0, RES//2, RES)
right_half = (RES//2, 0, RES, RES)
```

**Priority:** 🟢 **LOW** - Works fine

---

## 🎯 ACTION PLAN

### **Phase 1: Remove Dead Code (5 min)**
✅ **HIGH PRIORITY - DO IMMEDIATELY**

```bash
cd server
rm terrain_new.py terrain_old.py
```

**Benefit:**
- -622 lines of confusion
- Zero risk

---

### **Phase 2: Centralize RES (30 min)**
✅ **HIGH PRIORITY - DO SOON**

**Files to update:** 21 files

**Pattern:**
```python
# DELETE THIS LINE:
RES = 512

# ADD THIS LINE (adjust import path):
from ..engine.config import RES  # For primitives/
from .config import RES           # For engine/
from .engine.config import RES    # For root level files
```

**Files:**
1. `terrain.py`
2-18. All 17 primitive files
19. `engine/stamping.py`
20. `engine/spatial.py`
21. `semantic/spatial_resolver.py`

**Testing:**
```bash
# After changes, verify imports work
python -c "from server.terrain import apply_actions; print('OK')"
```

**Benefit:**
- Single source of truth
- Easy to change resolution
- Consistent across codebase

---

### **Phase 3: Clean Up Fallbacks (15 min)**
🟡 **MEDIUM PRIORITY - OPTIONAL**

**File:** `terrain.py` `_modify_feature()`

**Current:**
```python
feat["depth"] = min(1.0, feat.get("depth", 0.55) * ...)
                                         ^^^^^ Hardcoded fallback
```

**Better:**
```python
from .engine.feature_registry import FeatureRegistry
defaults = FeatureRegistry.get_defaults(feat["type"])
feat["depth"] = min(1.0, feat.get("depth", defaults["depth"]) * ...)
```

**Benefit:**
- Consistent with registry pattern
- No hardcoded values

---

## 📋 DECISION MATRIX

| Constant | Current State | Should Be | Priority | Effort |
|----------|---------------|-----------|----------|--------|
| `RES = 512` | ❌ 23 duplicates | ✅ Import from config | 🔴 HIGH | 30 min |
| Feature defaults | ✅ In registry | ✅ Use registry everywhere | 🟡 MEDIUM | 15 min |
| Algorithm params | ✅ In functions | ✅ Keep as-is | 🟢 NONE | 0 min |
| Region sizes | ⚠️ Calculated | 🟡 Could centralize | 🟢 LOW | 20 min |

---

## ✅ FINAL RECOMMENDATIONS

### **DO IMMEDIATELY:**
1. Delete `terrain_new.py` and `terrain_old.py` (5 min, zero risk)
2. Centralize `RES` constant (30 min, low risk)

### **DO SOON:**
3. Clean up `_modify_feature()` fallbacks (15 min, low risk)

### **OPTIONAL (Low Priority):**
4. Centralize region size calculations (20 min)
5. Organize docs into `docs/` folder (30 min)

### **DON'T DO:**
- ❌ Extract algorithm-specific constants (they're fine!)
- ❌ Centralize function default arguments (good practice)
- ❌ Extract every number (some are just values)

---

**Total Effort for Critical Fixes:** ~50 minutes  
**Risk Level:** 🟢 **LOW** - All changes are imports and deletions


