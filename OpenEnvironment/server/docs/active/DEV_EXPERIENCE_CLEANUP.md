# Developer Experience Cleanup

**Date:** November 11, 2025  
**Status:** 🔴 **IMPROVEMENTS NEEDED**

This document identifies code patterns and practices that make the codebase harder to understand, maintain, and extend. Focus is on **simplifying developer experience**, not removing planned features.

---

## 🔴 CRITICAL: Complex Import Patterns

### 1. Duplicated Importlib Pattern (7 files)

**Problem:** The same 10-line importlib workaround is duplicated across 7 files

**Files:**
1. `server/semantic/evaluation_v2.py` (lines 14-27)
2. `server/semantic/multi_agent/tools.py` (lines 15-30)
3. `server/semantic/narrative/generation.py` (lines 33-43)
4. `server/semantic/tools/narrative_tools.py` (lines 13-24)
5. `server/semantic/narrative/utils.py` (lines 10-21)
6. `server/semantic/tools/quality_tools.py` (lines 18-35)
7. `server/terrain.py` (lines 32-42)

**Impact:**
- **70+ lines of duplicated code**
- Hard to maintain (change in 7 places)
- Confusing for new developers
- Easy to make mistakes

**Solution:** Create helper in `server/semantic/evaluation/__init__.py`

**Action:** See `CLEANUP_REQUIRED.md` for implementation details

---

### 2. Complex Bootstrap Pattern in `generation.py`

**Location:** Lines 12-28

**Problem:** Nested try/except blocks for bootstrap import

**Current Code:**
```python
# Bootstrap import - handle both relative and absolute imports
try:
    from server.bootstrap import ensure_bootstrapped
    ensure_bootstrapped()
except ImportError:
    # Fallback: ensure server is in path
    import sys
    from pathlib import Path
    server_dir = Path(__file__).parent.parent.parent
    if str(server_dir) not in sys.path:
        sys.path.insert(0, str(server_dir))
    try:
        from server.bootstrap import ensure_bootstrapped
        ensure_bootstrapped()
    except ImportError:
        # If bootstrap doesn't exist, just ensure paths are set
        pass  # Continue without bootstrap
```

**Issues:**
- Nested try/except is hard to follow
- Silent failures (`pass`)
- Duplicated path manipulation logic
- Bootstrap should handle this, not each file

**Solution:** 
- Ensure `bootstrap.py` is always available
- Remove fallback logic from individual files
- Trust that bootstrap works (it's in `server/__init__.py`)

**Action:** Simplify to:
```python
from server.bootstrap import ensure_bootstrapped
ensure_bootstrapped()
```

---

### 3. Complex Import Fallback in `quality_tools.py`

**Location:** Lines 621-650

**Problem:** Triple-nested try/except for imports

**Current Code:**
```python
try:
    # Use bootstrap to ensure proper import environment
    import sys
    from pathlib import Path
    
    # Ensure server directory is in path
    server_dir = Path(__file__).parent.parent.parent
    server_dir_str = str(server_dir)
    if server_dir_str not in sys.path:
        sys.path.insert(0, server_dir_str)
    
    # Bootstrap the environment first
    try:
        from server.bootstrap import ensure_bootstrapped
        ensure_bootstrapped()
    except ImportError:
        # If bootstrap not available, try direct import
        pass
    
    # Now try to import - bootstrap should have set up the environment
    try:
        from server.terrain import apply_actions
        from server.orchestration import build_final_terrain
    except ImportError:
        # Fallback: import directly (when server dir is parent)
        parent_dir = server_dir.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        from server.terrain import apply_actions
        from server.orchestration import build_final_terrain
```

**Issues:**
- **30 lines** of import logic in a helper function
- Triple-nested try/except
- Manual path manipulation
- Should be handled at module level, not in function

**Solution:**
- Move imports to top of file
- Use bootstrap at module level
- Remove fallback logic

---

## 🟡 Inconsistent Error Handling

### 1. Silent Failures

**Problem:** Many `except Exception: pass` blocks hide errors

**Examples:**
- `server/semantic/narrative/generation.py` line 66: `except Exception as exc: pass`
- `server/semantic/tools/quality_tools.py` line 636: `except ImportError: pass`

**Impact:**
- Errors are swallowed
- Hard to debug
- Unclear failure modes

**Solution:**
- Log errors even if continuing
- Use specific exception types
- Document why errors are acceptable

**Example Fix:**
```python
except ImportError as e:
    logger.debug(f"Bootstrap not available: {e}, continuing with direct imports")
    # Continue without bootstrap
```

---

### 2. Inconsistent Error Messages

**Problem:** Error messages vary in detail and format

**Examples:**
- Some: `"Failed to render terrain preview"`
- Others: `"Error during apply_actions: {render_error}"`
- Some include context, others don't

**Solution:**
- Standardize error message format
- Always include context (function name, parameters)
- Use structured logging

---

## 🟡 Code Organization Issues

### 1. Long Functions

**Problem:** Some functions are very long (100+ lines)

**Examples:**
- `server/semantic/tools/quality_tools.py:refine_composition()` - 170+ lines
- `server/semantic/narrative/generation.py:generate_from_narrative()` - 200+ lines
- `server/parsing.py:_build_llm_prompt()` - 60+ lines

**Impact:**
- Hard to understand
- Hard to test
- Hard to modify

**Solution:**
- Break into smaller functions
- Extract helper functions
- Use composition

---

### 2. Deep Nesting

**Problem:** Some code has 4-5 levels of nesting

**Example:** `quality_tools.py:refine_composition()` has:
```python
if warnings:
    if texture_warnings:
        try:
            if analysis:
                if modifications:
                    # 5 levels deep!
```

**Solution:**
- Early returns
- Extract functions
- Use guard clauses

---

## 🟡 Type Hints Inconsistencies

### 1. Missing Type Hints

**Problem:** Some functions lack return type hints

**Examples:**
- `server/semantic/spatial_resolver.py:resolve_relative_position()` - no return type
- Many helper functions in `quality_tools.py`

**Impact:**
- Harder IDE autocomplete
- Less clear contracts
- Harder to catch bugs

**Solution:**
- Add return type hints to all functions
- Use `-> None` explicitly
- Use `Optional[...]` for nullable returns

---

### 2. Overuse of `Any` and `Dict[str, Any]`

**Problem:** Many functions use `Dict[str, Any]` instead of TypedDict

**Examples:**
- `scene_state: Dict[str, Any]` appears everywhere
- `actions: List[Dict[str, Any]]` instead of typed action dicts

**Impact:**
- No type checking
- Easy to make mistakes
- Hard to understand expected structure

**Solution:**
- Create TypedDict for common structures:
  - `SceneState`, `Action`, `FeatureDict`
- Use them consistently

**Example:**
```python
from typing import TypedDict

class SceneState(TypedDict, total=False):
    seed: int
    features: List[Dict[str, Any]]
    _narrative_meta: Dict[str, Any]
    # ... etc
```

---

## 🟡 Logging Inconsistencies

### 1. Inconsistent Log Levels

**Problem:** Similar events logged at different levels

**Examples:**
- Some info: `logger.info("Generating features...")`
- Others debug: `logger.debug("Created focal feature...")`
- Some warnings: `logger.warning("No generator found...")`

**Solution:**
- **INFO:** High-level operations (generation started, completed)
- **DEBUG:** Detailed steps (feature created, position calculated)
- **WARNING:** Recoverable issues (fallback used, missing optional data)
- **ERROR:** Failures (exceptions, invalid state)

---

### 2. Missing Context in Logs

**Problem:** Some log messages lack context

**Examples:**
- `"Failed to render"` - what failed? why?
- `"Error during apply_actions"` - which action? what state?

**Solution:**
- Always include relevant context
- Use structured logging
- Include IDs, counts, parameters

**Example:**
```python
logger.error(
    f"Failed to render terrain preview: {len(actions)} actions, "
    f"seed={scene_state.get('seed')}, error={e}"
)
```

---

## 🟡 Documentation Issues

### 1. Missing Docstrings

**Problem:** Some functions lack docstrings

**Examples:**
- Helper functions in `quality_tools.py`
- Internal functions in `generation.py`

**Solution:**
- Add docstrings to all public functions
- Include Args, Returns, Raises sections
- Use Google-style docstrings

---

### 2. Unclear Function Names

**Problem:** Some function names don't clearly indicate purpose

**Examples:**
- `_add_supporting_features()` - adds to what? modifies what?
- `_apply_quality_refinements()` - what does it return?
- `_merge_context_rubric()` - merges how?

**Solution:**
- Use verb-noun pattern
- Be specific about what's modified
- Include return type in name if helpful

---

## 🟡 Magic Numbers and Constants

### 1. Hardcoded Values

**Problem:** Some values are hardcoded instead of using config

**Examples:**
- `max_refinements=3` in multiple places
- `radius=150` for spatial queries
- `threshold=0.1` for texture differences

**Solution:**
- Move to `server/semantic/config.py`
- Use named constants
- Document why values were chosen

---

## 📋 Priority Actions

### High Priority (Immediate Impact):

1. ✅ **Refactor importlib pattern** - Create helper function (see CLEANUP_REQUIRED.md)
2. ✅ **Simplify bootstrap imports** - Remove nested try/except, trust bootstrap
3. ✅ **Add type hints** - Create TypedDict for SceneState, Action
4. ✅ **Standardize error messages** - Consistent format with context

### Medium Priority (Quality Improvements):

5. ⚠️ **Break up long functions** - Extract helpers from `refine_composition()`, `generate_from_narrative()`
6. ⚠️ **Reduce nesting** - Use early returns, guard clauses
7. ⚠️ **Improve logging** - Consistent levels, add context
8. ⚠️ **Add docstrings** - All public functions

### Low Priority (Polish):

9. ✅ **Move magic numbers to config** - Centralize constants
10. ✅ **Improve function names** - More descriptive names

---

## 🔧 Quick Wins (30 minutes)

### 1. Create TypedDict for Common Structures

**File:** `server/semantic/types.py` (new file)

```python
"""Type definitions for semantic layer."""

from typing import TypedDict, List, Dict, Any, Optional

class SceneState(TypedDict, total=False):
    """Standard scene state structure."""
    seed: int
    features: List[Dict[str, Any]]
    _narrative_meta: Optional[Dict[str, Any]]
    quality: Optional[Dict[str, Any]]
    # ... etc

class Action(TypedDict, total=False):
    """Standard action structure."""
    kind: str  # "add", "remove", "modify"
    type: str  # Feature type
    x: Optional[int]
    y: Optional[int]
    modifiers: Optional[Dict[str, Any]]
    # ... etc
```

Then update function signatures:
```python
def evaluate_terrain_quality(
    scene_state: SceneState,  # Instead of Dict[str, Any]
    actions: List[Action],   # Instead of List[Dict[str, Any]]
    ...
) -> Dict[str, Any]:
```

---

### 2. Simplify Bootstrap Imports

**Files:** `generation.py`, `quality_tools.py`

**Before:**
```python
try:
    from server.bootstrap import ensure_bootstrapped
    ensure_bootstrapped()
except ImportError:
    # ... 15 lines of fallback
```

**After:**
```python
from server.bootstrap import ensure_bootstrapped
ensure_bootstrapped()
```

**Rationale:** Bootstrap is always available (in `server/__init__.py`), fallback is unnecessary.

---

### 3. Standardize Error Logging

**Create helper:**
```python
# In server/semantic/utils.py (or similar)
def log_error_with_context(
    logger: logging.Logger,
    message: str,
    context: Dict[str, Any],
    exc: Optional[Exception] = None
):
    """Log error with structured context."""
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    full_message = f"{message} ({context_str})"
    if exc:
        logger.error(full_message, exc_info=exc)
    else:
        logger.error(full_message)
```

**Usage:**
```python
log_error_with_context(
    logger,
    "Failed to render terrain preview",
    {"actions_count": len(actions), "seed": scene_state.get("seed")},
    exc=render_error
)
```

---

## 📊 Impact Summary

**Developer Experience Improvements:**

1. **Reduced complexity:**
   - Remove 70+ lines of duplicated import code
   - Simplify 30+ lines of nested try/except
   - Clearer import patterns

2. **Better type safety:**
   - TypedDict for common structures
   - Better IDE autocomplete
   - Catch errors earlier

3. **Easier debugging:**
   - Consistent error messages
   - Better logging context
   - Clearer function names

4. **Easier maintenance:**
   - Smaller functions
   - Less nesting
   - Better documentation

---

## ✅ Verification

After improvements:
- [ ] Imports are simpler and consistent
- [ ] Type hints improve IDE experience
- [ ] Error messages are clear and helpful
- [ ] Logs provide useful debugging info
- [ ] Functions are easier to understand
- [ ] Code is easier to modify

---

*Last Updated: November 11, 2025*

