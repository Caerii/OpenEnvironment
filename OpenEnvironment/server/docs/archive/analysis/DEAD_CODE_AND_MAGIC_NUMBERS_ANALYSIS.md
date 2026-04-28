# Dead Code & Magic Numbers - Comprehensive Analysis

**Date:** October 31, 2025  
**Status:** Action Plan Ready

---

## 🔴 PART 1: DEAD CODE FILES

### **`terrain_new.py` (311 lines) - UNUSED**

**Status:** ❌ **DELETE**

**Evidence:**
- No imports found in any file (`grep` shows zero matches)
- Appears to be a legacy/intermediate version during refactoring
- Contains old 4-feature system (mountain, hill, valley, dunes only)
- Has outdated implementations that don't match current system

**Content Analysis:**
- **Duplicate of:** Older version of current `terrain.py`
- **Missing features:** Only has 4 primitives vs current 19
- **Outdated logic:** Uses `stamp_gaussian()` instead of registry
- **Different API:** Has different function signatures

**Risk of Deletion:** 🟢 **ZERO RISK** - Not referenced anywhere

---

### **`terrain_old.py` (311 lines) - UNUSED**

**Status:** ❌ **DELETE**

**Evidence:**
- No imports found in any file
- Even older version than `terrain_new.py`
- Contains `seed+17` hack on line 56 (bad practice)
- Uses `random.Random` instead of `np.random.RandomState` (non-deterministic)

**Content Analysis:**
- **Duplicate of:** Very old terrain.py before major refactorings
- **Contains bugs:** Non-deterministic randomness, seed+17 hack
- **Outdated:** Uses direct stamping instead of command pattern

**Risk of Deletion:** 🟢 **ZERO RISK** - Not referenced anywhere

---

### **Action:** Delete Both Files

```bash
# Safe to delete - no dependencies
rm server/terrain_new.py
rm server/terrain_old.py
```

**Benefit:**
- Removes 622 lines of confusing, outdated code
- Eliminates risk of editing wrong file
- Clears up project structure

---

## 🔴 PART 2: MAGIC NUMBER - `RES = 512`

### **Current State: Duplicated 23 Times**

**Files Containing `RES = 512`:**

1. ✅ `engine/config.py` (line 5) - **CENTRAL SOURCE**
2. ❌ `terrain.py` (line 32)
3. ❌ `terrain_new.py` (line 27) - DELETE FILE
4. ❌ `terrain_old.py` (line 11) - DELETE FILE
5. ❌ `primitives/base.py` (line 6)
6. ❌ `primitives/mountains.py` (line 6)
7. ❌ `primitives/valleys.py` (line 7)
8. ❌ `primitives/dunes.py` (line 7)
9. ❌ `primitives/cliffs.py` (line 6)
10. ❌ `primitives/slopes.py` (line 6)
11. ❌ `primitives/crater.py` (line 6)
12. ❌ `primitives/ridge.py` (line 7)
13. ❌ `primitives/ravine.py` (line 7)
14. ❌ `primitives/volcano.py` (line 6)
15. ❌ `primitives/passes.py` (line 7)
16. ❌ `primitives/mound.py` (line 6)
17. ❌ `primitives/basin.py` (line 6)
18. ❌ `primitives/pinnacle.py` (line 6)
19. ❌ `primitives/spur.py` (line 7)
20. ❌ `primitives/terraces.py` (line 7)
21. ❌ `engine/stamping.py` (line 7)
22. ❌ `engine/spatial.py` (line 5)
23. ❌ `semantic/spatial_resolver.py` (line 5)

**After deleting terrain_new.py and terrain_old.py: 21 duplicates remain**

---

### **Proper Organization:**

```python
# ✅ SINGLE SOURCE OF TRUTH: engine/config.py
TERRAIN_RESOLUTION = 512  # or just RES

# ❌ EVERYWHERE ELSE: Import it
from ..engine.config import TERRAIN_RESOLUTION as RES
# or
from server.engine.config import TERRAIN_RESOLUTION as RES
```

---

### **Why This Matters:**

**Current Problem:**
```python
# File 1: primitives/mountains.py
RES = 512
stamp = np.zeros((RES, RES))

# File 2: primitives/valleys.py  
RES = 512
stamp = np.zeros((RES, RES))

# ... 21 more files ...
```

**If you want to change resolution to 1024:**
- ❌ Must edit 21 files
- ❌ Risk of missing one (inconsistency)
- ❌ Git diff is huge
- ❌ Merge conflicts likely

**After Fix:**
```python
# engine/config.py
TERRAIN_RESOLUTION = 1024  # ONE CHANGE

# All files automatically use new value
from ..engine.config import TERRAIN_RESOLUTION as RES
```

---

### **Implementation Plan:**

#### **Step 1:** Verify `engine/config.py` exports it
```python
# engine/config.py
TERRAIN_RESOLUTION = 512  # ← Already exists!
RES = TERRAIN_RESOLUTION  # Alias for backward compatibility
```

#### **Step 2:** Update all primitive files (17 files)
```python
# OLD:
RES = 512

# NEW:
from ..engine.config import RES
```

#### **Step 3:** Update engine files (2 files)
```python
# OLD:
RES = 512

# NEW:
from .config import RES
```

#### **Step 4:** Update terrain.py
```python
# OLD:
RES = 512

# NEW:
from .engine.config import RES
```

#### **Step 5:** Update semantic/spatial_resolver.py
```python
# OLD:
RES = 512

# NEW:
from ..engine.config import RES
```

---

## 🟡 PART 3: MAGIC NUMBERS - Feature Defaults

### **Current State: Scattered Everywhere**

**Default Values Duplicated Across Files:**

| Constant | Value | Files | Purpose |
|----------|-------|-------|---------|
| Mountain height | `0.75` | 15+ files | Default peak height |
| Hill height | `0.45` | 12+ files | Default peak height |
| Valley depth | `0.55` | 10+ files | Default depth |
| Mesa height | `0.65` | 5+ files | Default height |
| Cliff height | `0.55` | 4+ files | Default height |
| Volcano height | `0.80` | 4+ files | Default height |
| Mountain radius | `56` | 10+ files | Default radius |
| Hill radius | `42` | 8+ files | Default radius |
| Valley radius | `64` | 8+ files | Default radius |
| Dune amp | `0.08` | 6+ files | Wave amplitude |
| Dune freq | `18.0` | 6+ files | Wave frequency |
| Smoothing sigma | `0.8` | 4+ files | Gaussian smoothing |

---

### **Where These Numbers Appear:**

1. **`engine/config.py`** - ✅ Proper place (already exists!)
   - `MountainConfig.default_height = 0.75`
   - `HillConfig.default_height = 0.45`
   - `ValleyConfig.default_depth = 0.55`
   - `DuneConfig.default_amp = 0.08`

2. **`engine/feature_registry.py`** - ✅ Also appropriate
   - `get_defaults()` returns `{"height": 0.75, "radius": 56}`
   - **Good:** These are generator-specific defaults

3. **`terrain.py` (_create_feature)** - ⚠️ Partially fixed
   - Still has some hardcoded values as fallbacks
   - Uses `defaults.get("height", 0.75)` - good pattern

4. **`terrain.py` (_modify_feature)** - ❌ Duplicated
   - Lines 916, 918, 938, 940, 970, 972, etc.
   - Hardcoded `0.55`, `0.80`, etc. as fallbacks

5. **Various primitives** - ✅ Reasonable
   - Primitives have their own default parameters
   - These are **function arguments**, not global constants

---

### **Assessment: Actually Not That Bad**

**Why These Duplicates Are OK:**

1. **Config System Exists** - `engine/config.py` already has proper structure
2. **Registry Has Defaults** - `FeatureRegistry.get_defaults()` works
3. **Fallback Pattern** - `defaults.get("height", 0.75)` is defensive programming

**The "magic numbers" in primitives are actually:**
- Function default parameters (good!)
- Not global constants (would be bad)

**Example:**
```python
# This is GOOD:
def generate_mountain(cx: int, cy: int, radius: int = 56, height: float = 0.75):
    # Function has sensible defaults
    
# This is BAD:
MOUNTAIN_RADIUS = 56  # Global constant duplicated everywhere
```

---

### **What Actually Needs Fixing:**

#### ✅ **Keep As-Is:**
- `engine/config.py` - Already correct
- `engine/feature_registry.py` - Already correct
- Primitive function defaults - These are fine

#### ❌ **Fix These:**
- `terrain.py` (_modify_feature) - Use registry instead of hardcoded fallbacks
- Region size calculation `RES//3` - Should be configurable

---

## 🎯 PART 4: PRIORITIZED ACTION PLAN

### **Phase 1: Delete Dead Code (5 minutes)**

```bash
cd server
rm terrain_new.py terrain_old.py
git add -u
git commit -m "refactor: remove dead code files (terrain_new.py, terrain_old.py)"
```

**Impact:** ✅ Immediate cleanup, zero risk

---

### **Phase 2: Centralize RES Constant (30 minutes)**

**Files to update (21 total):**

```python
# 1. terrain.py
- RES = 512
+ from .engine.config import RES

# 2-18. All primitive files (17 files)
- RES = 512
+ from ..engine.config import RES

# 19. engine/stamping.py
- RES = 512
+ from .config import RES

# 20. engine/spatial.py
- RES = 512
+ from .config import RES

# 21. semantic/spatial_resolver.py
- RES = 512
+ from ..engine.config import RES
```

**Script to help:**
```bash
# Find all files that need updating
grep -r "^RES = 512" server/ --exclude-dir=__pycache__

# After manual updates, test:
python -m pytest server/test_*.py
```

**Impact:** ✅ Single source of truth, easier to change resolution

---

### **Phase 3: Remove Magic Number Fallbacks (15 minutes)**

**Only one file needs updating:** `terrain.py` (_modify_feature)

```python
# OLD: Line 916, etc.
feat["depth"] = min(1.0, feat.get("depth", 0.55) * ...)

# NEW:
defaults = FeatureRegistry.get_defaults(feat["type"])
feat["depth"] = min(1.0, feat.get("depth", defaults["depth"]) * ...)
```

**Impact:** ✅ Consistent with registry pattern

---

### **Phase 4: Configuration for Region Sizes (Optional, 20 minutes)**

```python
# engine/config.py - Add:
@dataclass
class SpatialConfig:
    """Configuration for spatial positioning."""
    region_divisions: int = 3  # 3x3 grid
    
    @property
    def region_size(self) -> int:
        """Size of one region in a 3x3 grid."""
        return TERRAIN_RESOLUTION // self.region_divisions
```

**Impact:** 🟡 Nice-to-have, not critical

---

## 📊 SUMMARY

### **Dead Code:**
- ❌ **DELETE:** `terrain_new.py` (311 lines, unused)
- ❌ **DELETE:** `terrain_old.py` (311 lines, unused)
- **Total removal:** 622 lines of confusing code

### **RES = 512:**
- ✅ **Already centralized** in `engine/config.py`
- ❌ **Duplicated** in 21 files (after deleting dead code)
- 🔧 **Fix:** Import from config instead of redefining

### **Other Magic Numbers:**
- ✅ **Actually OK!** Most are function defaults or already in config
- 🔧 **Minor fix:** Use registry in `_modify_feature()` instead of hardcoded fallbacks

---

## ⏱️ TIME ESTIMATE

- **Phase 1 (Delete dead code):** 5 minutes
- **Phase 2 (Centralize RES):** 30 minutes
- **Phase 3 (Fix fallbacks):** 15 minutes
- **Phase 4 (Config region sizes):** 20 minutes (optional)

**Total:** ~50 minutes for critical fixes  
**Total with optional:** ~70 minutes

---

## ✅ RECOMMENDED IMMEDIATE ACTIONS

1. **Delete dead code files** (zero risk, immediate benefit)
2. **Centralize RES constant** (low risk, high benefit)
3. **Fix fallback pattern** (low risk, consistency improvement)

**DON'T NEED TO DO:**
- ❌ Change primitive function defaults (they're fine!)
- ❌ Refactor config system (it's already good!)
- ❌ Extract every number (some are just function defaults)

---

**The main issue is not "too many magic numbers" - it's "duplicated constants".**  
**Once RES is centralized, the system is actually quite clean!**


