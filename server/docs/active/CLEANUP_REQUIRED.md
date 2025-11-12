# Codebase Cleanup Required

**Date:** November 11, 2025  
**Status:** 🔴 **ACTION REQUIRED**

This document identifies **truly dead code** that needs to be cleaned up or removed. Items planned for future use (like `evaluation_v2.py`, TODOs for planned features) are **NOT** included here.

---

## 🔴 CRITICAL: Deprecated Functions with Replacements

### 1. `_handle_spatial_query_DEPRECATED()` in `server/parsing.py`

**Location:** Lines 173-243

**Status:** ⚠️ **DEPRECATED** - Has replacement, should be removed

**Evidence:**
- Function is marked `_DEPRECATED` in name
- Replacement exists: `handle_spatial_query()` from `spatial_queries.py` (imported on line 9)
- Function is not called anywhere (grep shows 0 usages)

**Action:** 
- **Remove function entirely** - Replacement is available and working
- Function is 71 lines of dead code (173-243)

**Replacement:** `handle_spatial_query()` from `server/semantic/spatial_queries.py`

---

## 🟡 Commented Out Code Blocks

### 1. OLD IMPLEMENTATION in `server/parsing.py`

**Location:** Lines 39-45

**Code:**
```python
# OLD IMPLEMENTATION (kept for reference):
# api_key = os.environ.get("CEREBRAS_API_KEY")
# if not api_key:
#     raise ValueError("CEREBRAS_API_KEY not found in environment variables")
# self.client = Cerebras(api_key=api_key)
# self.model = "llama3.1-8b"
# self.tool_registry = get_tool_registry()
```

**Status:** ⚠️ **HISTORICAL REFERENCE** - Should be removed

**Reason:** 
- Old implementation before refactoring
- Git history preserves it
- No longer relevant

**Action:** Remove comment block

---

### 2. Commented Import in `server/terrain.py`

**Location:** Lines 44-45

**Code:**
```python
# DEAD IMPORT - SemanticParser is not used in this file (moved to orchestration.py)
# from .semantic.parser import SemanticParser
```

**Status:** ⚠️ **STALE COMMENT** - Should be removed

**Reason:**
- Import was removed, comment explains why
- Comment is no longer needed (Git history has context)
- Clutters code

**Action:** Remove both comment lines

---

## 🟡 Unused Imports

### 1. `Counter` in `server/semantic/evaluation_v2.py`

**Line 7:** `from collections import Counter`

**Status:** ❌ **UNUSED** - Not used anywhere in the file

**Note:** `evaluation_v2.py` is planned for future use, but this specific import is unused

**Action:** Remove unused import (keep file, just clean import)

---

## 🟡 Code Duplication: Importlib Pattern

### Problem: Duplicated importlib.util pattern across 7 files

**Files affected:**
1. `server/semantic/evaluation_v2.py` (lines 14-27) - *Planned for future use*
2. `server/semantic/multi_agent/tools.py` (lines 15-30)
3. `server/semantic/narrative/generation.py` (lines 33-43)
4. `server/semantic/tools/narrative_tools.py` (lines 13-24)
5. `server/semantic/narrative/utils.py` (lines 10-21)
6. `server/semantic/tools/quality_tools.py` (lines 18-35)
7. `server/terrain.py` (lines 32-42)

**Pattern (repeated 7 times):**
```python
# Import from evaluation.py module (not package)
import importlib.util
import sys
from pathlib import Path
evaluation_module_path = Path(__file__).parent / "evaluation.py"  # or parent / "evaluation.py"
spec = importlib.util.spec_from_file_location("semantic.evaluation_module", evaluation_module_path)
evaluation_module = importlib.util.module_from_spec(spec)
sys.modules["semantic.evaluation_module"] = evaluation_module
spec.loader.exec_module(evaluation_module)
# Use functions from evaluation_module
compute_feature_metrics = evaluation_module.compute_feature_metrics
# ... etc
```

**Why this exists:**
- `evaluation.py` is a module, `evaluation/` is a package
- Need to import from module, not package
- Workaround for Python import system limitation

**Action:**
- **Option A:** Create helper function in `server/semantic/evaluation/__init__.py` to export functions
- **Option B:** Keep as-is (it works, just verbose)
- **Option C:** Refactor `evaluation.py` to be part of package properly

**Recommendation:** Option A - Create helper to reduce duplication (can be done incrementally)

**Helper function example:**
```python
# In server/semantic/evaluation/__init__.py
import importlib.util
import sys
from pathlib import Path

def _load_evaluation_module():
    """Load evaluation.py module (not package)."""
    evaluation_module_path = Path(__file__).parent.parent / "evaluation.py"
    spec = importlib.util.spec_from_file_location("semantic.evaluation_module", evaluation_module_path)
    evaluation_module = importlib.util.module_from_spec(spec)
    sys.modules["semantic.evaluation_module"] = evaluation_module
    spec.loader.exec_module(evaluation_module)
    return evaluation_module

_evaluation_module = _load_evaluation_module()

# Export functions
compute_feature_metrics = _evaluation_module.compute_feature_metrics
compute_texture_metrics = _evaluation_module.compute_texture_metrics
evaluate_quality_rubric = _evaluation_module.evaluate_quality_rubric
# ... etc
```

Then files can just do:
```python
from ..evaluation import compute_feature_metrics, compute_texture_metrics
```

---

## ✅ NOT Included (Planned for Future Use)

These items are **NOT** cleanup targets because they're planned for future pipeline:

- ✅ **`evaluation_v2.py`** - Enhanced evaluation system planned for future use
- ✅ **TODOs in `generation.py`** - Background/foreground features planned
- ✅ **TODO in `spatial_resolver.py`** - Relative positioning planned feature
- ✅ **TODO in `narrative_tools.py`** - Iterative refinement planned
- ✅ **TODO in `narrative_dev.py`** - Topography inference planned

---

## 📋 Cleanup Priority

### High Priority (Do First - 5 minutes):
1. ✅ **Remove deprecated function** `_handle_spatial_query_DEPRECATED()` from `parsing.py` (71 lines: 173-243)
2. ✅ **Remove commented OLD IMPLEMENTATION** from `parsing.py` (lines 39-45)
3. ✅ **Remove DEAD IMPORT comment** from `terrain.py` (lines 44-45)
4. ✅ **Remove unused `Counter` import** from `evaluation_v2.py` (line 7)

### Medium Priority (Refactoring - 30 minutes):
5. ⚠️ **Refactor importlib pattern** - Create helper function in `evaluation/__init__.py` to reduce duplication

---

## 🔧 Recommended Actions

### Immediate Cleanup (5 minutes):

**1. Remove deprecated function from `parsing.py`:**
```python
# DELETE lines 173-243 (_handle_spatial_query_DEPRECATED function)
```

**2. Remove OLD IMPLEMENTATION comment from `parsing.py`:**
```python
# DELETE lines 39-45 (commented out old implementation)
```

**3. Remove DEAD IMPORT comment from `terrain.py`:**
```python
# DELETE lines 44-45 (commented import and explanation)
```

**4. Remove unused import from `evaluation_v2.py`:**
```python
# REMOVE line 7: from collections import Counter
```

### Refactoring (Optional - 30 minutes):

**5. Create helper for evaluation module import:**

Create `server/semantic/evaluation/__init__.py` helper:
```python
"""Evaluation module exports - handles evaluation.py vs evaluation/ package conflict."""

import importlib.util
import sys
from pathlib import Path

def _load_evaluation_module():
    """Load evaluation.py module (not package)."""
    evaluation_module_path = Path(__file__).parent.parent / "evaluation.py"
    spec = importlib.util.spec_from_file_location("semantic.evaluation_module", evaluation_module_path)
    evaluation_module = importlib.util.module_from_spec(spec)
    sys.modules["semantic.evaluation_module"] = evaluation_module
    spec.loader.exec_module(evaluation_module)
    return evaluation_module

_evaluation_module = _load_evaluation_module()

# Export commonly used functions
compute_feature_metrics = _evaluation_module.compute_feature_metrics
compute_texture_metrics = _evaluation_module.compute_texture_metrics
evaluate_quality_rubric = _evaluation_module.evaluate_quality_rubric
summarize_quality_rubric = _evaluation_module.summarize_quality_rubric
evaluate_aesthetic_quality = _evaluation_module.evaluate_aesthetic_quality
features_to_dicts = _evaluation_module.features_to_dicts
DEFAULT_QUALITY_RUBRIC = _evaluation_module.DEFAULT_QUALITY_RUBRIC
```

Then update files to use:
```python
from ..evaluation import compute_feature_metrics, compute_texture_metrics
```

---

## ✅ Verification

After cleanup, verify:
- [ ] No broken imports
- [ ] Tests still pass
- [ ] No functionality lost
- [ ] Code is cleaner and easier to understand
- [ ] Deprecated function removed
- [ ] Commented code removed
- [ ] Unused imports removed

---

## 📊 Impact Summary

**Lines to remove:**
- Deprecated function: 71 lines (173-243)
- Commented code: 7 lines (39-45)
- Comments: 2 lines (44-45)
- Unused import: 1 line (line 7)

**Total:** ~81 lines of dead code/comments

**Benefit:**
- Cleaner codebase
- Less confusion
- Easier maintenance
- Clearer intent

---

*Last Updated: November 11, 2025*
