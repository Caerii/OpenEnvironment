<!--
METADATA:
  File: BRITTLE_PATTERNS_ANALYSIS.md
  Created: November 2025
  Last Modified: 2025-11-11
  Status: PARTIALLY OUTDATED - Many patterns refactored, but analysis still relevant
  Purpose: Analysis of brittle code patterns and architectural issues
  Archive Date: 2025-11-11
-->

# Brittle Patterns & Encapsulation Needs

## 📋 Document Purpose

This document was created to **identify brittle code patterns** that needed refactoring. It analyzed hard-coded values, keyword matching, and other architectural issues.

## ✅ Current Status

**Many patterns have been refactored**, but the analysis remains useful for understanding design decisions:

- ✅ **Keyword-Based Archetype Matching** - IMPROVED (semantic matching added)
- ✅ **Magic Numbers** - FIXED (centralized in `server/semantic/config.py`)
- ✅ **Brittle String Matching** - FIXED (structured warnings implemented)
- ✅ **Inconsistent State** - FIXED (`StateInitializer` created)
- ⚠️ **Some patterns may still exist** - Check current codebase

## 📝 Historical Analysis

The patterns identified below have been addressed through the encapsulation work documented in `ENCAPSULATION_COMPLETE.md`.

## 🔴 Critical Brittle Patterns

### 1. **Keyword-Based Archetype Matching** (User Identified)

**Location:** `server/semantic/narrative/archetypes.py:match_archetype_from_keywords()`

**Problems:**
- Hard-coded keyword lists (374-389)
- Hard-coded keyword weights (324-348)
- Brittle string matching (`if "valley" in keywords_lower`)
- No semantic understanding - just keyword matching
- Doesn't handle synonyms, variations, or context

**Example:**
```python
keyword_weights = {
    "valley": 3.0,  # What if user says "ravine" or "gorge"?
    "hill": 1.0,    # What if user says "mound" or "knoll"?
    ...
}
```

**Impact:**
- Fails on synonyms ("ravine" ≠ "valley")
- Fails on variations ("rolling hills" vs "hills")
- Fails on context ("mountain valley" vs "desert valley")
- Requires manual updates for new keywords

**Fix Needed:**
- Use LLM for semantic matching (already have narrative pipeline!)
- Or create synonym dictionary
- Or use embedding-based similarity
- Encapsulate in `ArchetypeMatcher` class

---

### 2. **Hard-Coded Texture Thresholds**

**Location:** `server/semantic/tools/quality_tools.py:analyze_texture_feature_relationship()`

**Problems:**
```python
coverage_thresholds = [0.15, 0.10, 0.05, 0.05]  # Magic numbers!
if len(coords[0]) > 10:  # Why 10?
if (x0 - 50 <= x <= x1 + 50):  # Why 50 pixels?
```

**Impact:**
- No way to tune thresholds
- Thresholds don't adapt to context
- Hard to understand why these values

**Fix Needed:**
- Move to configuration
- Make context-aware (different thresholds for different archetypes)
- Document rationale

---

### 3. **Hard-Coded Parameter Modification Values**

**Location:** `server/semantic/tools/quality_tools.py:analyze_texture_feature_relationship()`

**Problems:**
```python
if channel_name == "sand" and feat_type == "dunes":
    suggested_changes.append({
        "action_id": feat_id,
        "radius": +30,  # Why 30? Should be based on current radius!
        ...
    })
elif channel_name == "rock" and feat_type in ["mountain", "cliff"]:
    suggested_changes.append({
        "radius": +25,  # Why 25? Different from sand?
        ...
    })
```

**Impact:**
- Fixed increments don't scale with feature size
- No consideration of current parameter values
- Different values for different features (inconsistent)

**Fix Needed:**
- Calculate percentage-based changes (e.g., +20% of current radius)
- Use LLM to suggest optimal changes
- Make adaptive based on gap size

---

### 4. **Brittle Warning Text Matching**

**Location:** `server/semantic/tools/quality_tools.py:refine_composition()`

**Problems:**
```python
texture_warnings = [w for w in quality_warnings if 
    "texture" in w.lower() or 
    ("coverage" in w.lower() and any(t in w.lower() for t in ["grass", "rock", "sand", "snow"]))]

if "feature count" in warning_lower or "add more" in warning_lower:
    ...
elif "diversity" in warning_lower or "contrasting" in warning_lower:
    ...
```

**Impact:**
- Breaks if warning text changes
- Doesn't handle variations ("texture coverage" vs "texture distribution")
- Hard to maintain

**Fix Needed:**
- Use structured warning types (enum or constants)
- Return warning categories from evaluation
- Match on category, not text

---

### 5. **Brittle Feature Type Matching**

**Location:** Multiple places

**Problems:**
```python
if feat_type == "dunes":  # What about "dune" (singular)?
if feat_type in ["mountain", "cliff"]:  # Hard-coded list
has_dunes = any(a.get("type") == "dunes" for a in existing_actions)
```

**Impact:**
- Doesn't handle type variations
- Hard-coded lists scattered everywhere
- No single source of truth for feature types

**Fix Needed:**
- Use FeatureRegistry for canonical types
- Create feature type groups (e.g., ROCK_FEATURES = ["mountain", "cliff"])
- Use constants, not string literals

---

### 6. **Scattered State Initialization**

**Location:** Multiple files

**Problems:**
```python
# In quality_tools.py:
if "features" not in temp_state:
    temp_state["features"] = []
if "seed" not in temp_state:
    temp_state["seed"] = 42
if "next_id" not in temp_state:
    temp_state["next_id"] = 1

# In multi_agent/tools.py:
def _prepare_state(scene_state):
    return {
        "features": [],
        "seed": 42,
        "semantic_scene": {},
        "next_id": 1,
    }
```

**Impact:**
- Duplicated initialization logic
- Inconsistent defaults
- Easy to miss required keys

**Fix Needed:**
- Create `StateInitializer` class
- Single source of truth for default state
- Validation method

---

### 7. **Import Path Manipulation Scattered**

**Location:** Multiple files

**Problems:**
```python
# Repeated in many files:
import sys
from pathlib import Path
server_dir = Path(__file__).parent.parent.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))
```

**Impact:**
- Duplicated code
- Easy to get wrong paths
- Maintenance burden

**Fix Needed:**
- Centralize in bootstrap module
- Use proper package structure
- Or use relative imports consistently

---

### 8. **Broad Exception Handlers**

**Location:** Multiple files

**Problems:**
```python
except Exception as e:  # Catches everything!
    logger.warning(f"Failed: {e}", exc_info=True)
    return default_value
```

**Impact:**
- Hides bugs (AttributeError, TypeError)
- Catches system errors (KeyboardInterrupt, MemoryError)
- Makes debugging hard

**Fix Needed:**
- Catch specific exceptions
- Let unexpected errors propagate
- Document expected exceptions

---

### 9. **Magic Numbers in Texture Analysis**

**Location:** `server/semantic/tools/quality_tools.py`

**Problems:**
```python
max_features_to_analyze = min(5, len(actions))  # Why 5?
mask = np.any(np.abs(texture_diff) > 0.05, axis=2)  # Why 0.05?
if len(coords[0]) > 10:  # Why 10?
for feat_id in nearby_features[:2]:  # Why top 2?
```

**Impact:**
- No way to tune analysis depth
- Thresholds may not work for all cases
- Hard to understand trade-offs

**Fix Needed:**
- Move to configuration
- Make adaptive based on scene complexity
- Document rationale

---

### 10. **Hard-Coded Position Defaults**

**Location:** Multiple files

**Problems:**
```python
x = pos.get("x") or action.get("x", 256)  # Why 256? (center of 512x512)
y = pos.get("y") or action.get("y", 256)
```

**Impact:**
- Assumes 512x512 resolution
- Breaks if resolution changes
- Should use TERRAIN_RESOLUTION / 2

**Fix Needed:**
- Import TERRAIN_RESOLUTION from config
- Calculate center dynamically

---

## 🟡 Medium Priority Issues

### 11. **Model Names Duplicated**

**Location:** `server/semantic/llm/factory.py`, `server/semantic/multi_agent/config.py`

**Problems:**
- Model names defined in multiple places
- Easy to get out of sync
- No validation that model exists

**Fix Needed:**
- Single source of truth
- Model registry/validation

---

### 12. **Default Values Scattered**

**Location:** Multiple files

**Problems:**
```python
seed=42  # Appears everywhere
max_refinements=5  # Hard-coded in multiple places
quality_threshold=0.8  # Hard-coded
```

**Fix Needed:**
- Configuration file
- Environment variables with defaults
- Centralized constants

---

### 13. **Feature Type Lists Duplicated**

**Location:** Multiple files

**Problems:**
- Feature type lists repeated: `["mountain", "valley", "dunes", ...]`
- No single source of truth
- Easy to miss types

**Fix Needed:**
- Use FeatureRegistry.get_all_types()
- Create feature type groups/constants

---

## 🟢 Low Priority (But Should Fix)

### 14. **String Formatting Inconsistencies**

**Location:** Multiple files

**Problems:**
- Mix of f-strings, .format(), % formatting
- Inconsistent error message formats

**Fix Needed:**
- Standardize on f-strings
- Create error message formatter

---

### 15. **Logging Levels Inconsistent**

**Location:** Multiple files

**Problems:**
- Mix of logger.info(), logger.warning(), logger.error()
- Some errors logged as warnings
- Some info logged as errors

**Fix Needed:**
- Define logging standards
- Use appropriate levels consistently

---

## 📋 Recommended Encapsulation Strategy

### **Phase 1: Critical Brittle Patterns**

1. **Create `ArchetypeMatcher` Class**
   - Encapsulate keyword matching logic
   - Support LLM-based semantic matching
   - Handle synonyms and variations

2. **Create `TextureAnalysisConfig` Class**
   - Centralize thresholds
   - Make context-aware
   - Document rationale

3. **Create `ParameterModificationStrategy` Class**
   - Calculate adaptive parameter changes
   - Use percentage-based increments
   - Consider current values

4. **Create `WarningClassifier` Class**
   - Use structured warning types
   - Match on categories, not text
   - Return typed warnings

5. **Create `StateInitializer` Class**
   - Single source of truth for state defaults
   - Validation methods
   - Consistent initialization

### **Phase 2: Configuration & Constants**

6. **Create `TerrainConfig` Module**
   - All magic numbers
   - Feature type constants
   - Default values
   - Thresholds

7. **Create `FeatureTypeRegistry`**
   - Canonical feature types
   - Type groups (ROCK_FEATURES, etc.)
   - Type validation

8. **Create `ModelRegistry`**
   - Model names and capabilities
   - Validation
   - Single source of truth

### **Phase 3: Error Handling**

9. **Create Custom Exception Classes**
   - `TerrainGenerationError`
   - `TextureAnalysisError`
   - `ParameterModificationError`
   - Specific exceptions for each domain

10. **Standardize Error Handling**
    - Catch specific exceptions
    - Proper error propagation
    - Consistent error messages

---

## 🎯 Immediate Actions

### **High Impact, Low Effort:**

1. ✅ **Extract Magic Numbers to Constants**
   - Create `server/semantic/config.py`
   - Move all thresholds, defaults, limits

2. ✅ **Create Feature Type Constants**
   - `ROCK_FEATURES = ["mountain", "cliff"]`
   - `SAND_FEATURES = ["dunes"]`
   - Use throughout codebase

3. ✅ **Create Warning Type Enum**
   - Replace string matching with enum
   - Return structured warnings

4. ✅ **Centralize State Initialization**
   - Create `StateInitializer` class
   - Use everywhere

### **High Impact, Medium Effort:**

5. ✅ **Refactor Archetype Matching**
   - Use LLM for semantic matching (already have narrative pipeline!)
   - Fallback to keyword matching
   - Handle synonyms

6. ✅ **Make Parameter Modifications Adaptive**
   - Calculate percentage-based changes
   - Consider current values
   - Use LLM to suggest optimal changes

---

## 💡 Key Insight

**The keyword matching is brittle because it's trying to solve a semantic problem with syntactic matching.**

**Better approach:**
- Use the narrative pipeline's LLM to match archetypes semantically
- Fallback to keyword matching only if LLM unavailable
- This leverages existing infrastructure!




