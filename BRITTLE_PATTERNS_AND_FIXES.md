# Brittle Patterns & Encapsulation Needs - Complete Analysis

## 🔴 Critical Brittle Patterns (User Identified)

### 1. **Keyword-Based Archetype Matching** ⚠️ **VERY BRITTLE**

**Location:** `server/semantic/narrative/archetypes.py:match_archetype_from_keywords()`

**Current Implementation:**
- Hard-coded keyword lists (374-389)
- Hard-coded keyword weights (324-348)
- Brittle string matching: `if "valley" in keywords_lower`
- No semantic understanding
- Doesn't handle synonyms ("ravine" ≠ "valley")
- Doesn't handle context ("mountain valley" vs "desert valley")

**Why It's Brittle:**
```python
# Current approach:
if "valley" in keywords_lower and "hill" in keywords_lower:
    return TERRAIN_ARCHETYPES["waters_legacy"]

# Problems:
# - "ravine" won't match "valley"
# - "rolling hills" might not match "hills"
# - "mountain valley" might match wrong archetype
```

**Better Approach:**
- Use LLM for semantic matching (we already have narrative pipeline!)
- The narrative pipeline could use LLM to understand command semantics
- Fallback to keyword matching only if LLM unavailable

**Encapsulation Needed:**
```python
# server/semantic/narrative/archetype_matcher.py
class ArchetypeMatcher:
    """Semantic archetype matching with keyword fallback."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self.keyword_matcher = KeywordArchetypeMatcher()  # Current implementation
    
    def match(self, command: str, keywords: List[str]) -> TerrainArchetype:
        """Match using LLM (preferred) or keywords (fallback)."""
        if self.llm_client:
            try:
                return self._match_with_llm(command)
            except Exception:
                pass
        return self.keyword_matcher.match(keywords)
```

---

### 2. **Hard-Coded Magic Numbers** ⚠️ **SCATTERED EVERYWHERE**

**Locations:**
- `server/semantic/tools/quality_tools.py`: Coverage thresholds, pixel distances, limits
- `server/semantic/narrative/generation.py`: Position bounds (32, 480), jitter values (-6, 6)
- Multiple files: Default positions (256), seed (42), quality threshold (0.8)

**Examples:**
```python
# quality_tools.py
coverage_thresholds = [0.15, 0.10, 0.05, 0.05]  # Magic numbers!
if len(coords[0]) > 10:  # Why 10?
if (x0 - 50 <= x <= x1 + 50):  # Why 50 pixels?
max_features_to_analyze = min(5, len(actions))  # Why 5?

# generation.py
pos.x = max(32, min(480, pos.x + delta))  # Why 32/480? (assumes 512x512)
delta = rng.randint(-6, 6)  # Why ±6?

# Multiple files
x = pos.get("x") or action.get("x", 256)  # Why 256? (center of 512x512)
seed = scene_state.get("seed", 42)  # Why 42?
quality_threshold = 0.8  # Why 0.8?
```

**Encapsulation Needed:**
```python
# server/semantic/config.py
class TerrainConfig:
    """Centralized configuration constants."""
    
    # Resolution (should import from engine.config)
    TERRAIN_RESOLUTION = 512
    TERRAIN_CENTER_X = TERRAIN_RESOLUTION // 2
    TERRAIN_CENTER_Y = TERRAIN_RESOLUTION // 2
    TERRAIN_BOUNDS_MIN = 32
    TERRAIN_BOUNDS_MAX = TERRAIN_RESOLUTION - 32
    
    # Texture Analysis
    TEXTURE_COVERAGE_THRESHOLDS = {
        "grass": 0.15,
        "rock": 0.10,
        "sand": 0.05,
        "snow": 0.05,
    }
    TEXTURE_DIFF_THRESHOLD = 0.05
    TEXTURE_GAP_MIN_PIXELS = 10
    MAX_FEATURES_TO_ANALYZE = 5
    NEARBY_FEATURE_RADIUS = 50
    
    # Parameter Modification
    PARAMETER_CHANGE_PERCENTAGES = {
        "sand": {"dunes": 0.2},  # 20% increase
        "rock": {"mountain": 0.15, "cliff": 0.15},
    }
    
    # Defaults
    DEFAULT_SEED = 42
    DEFAULT_QUALITY_THRESHOLD = 0.8
    DEFAULT_MAX_REFINEMENTS = 5
```

---

### 3. **Brittle Warning Text Matching** ⚠️ **BREAKS ON TEXT CHANGES**

**Location:** `server/semantic/tools/quality_tools.py:refine_composition()`

**Current Implementation:**
```python
texture_warnings = [w for w in quality_warnings if 
    "texture" in w.lower() or 
    ("coverage" in w.lower() and any(t in w.lower() for t in ["grass", "rock", "sand", "snow"]))]

if "feature count" in warning_lower or "add more" in warning_lower:
    ...
elif "diversity" in warning_lower or "contrasting" in warning_lower:
    ...
```

**Problems:**
- Breaks if warning text changes
- Doesn't handle variations ("texture coverage" vs "texture distribution")
- Hard to maintain
- No type safety

**Encapsulation Needed:**
```python
# server/semantic/evaluation/warning_types.py
from enum import Enum
from dataclasses import dataclass

class WarningCategory(Enum):
    TEXTURE_COVERAGE = "texture_coverage"
    TEXTURE_DISTRIBUTION = "texture_distribution"
    FEATURE_COUNT = "feature_count"
    DIVERSITY = "diversity"
    SPATIAL_EXTENT = "spatial_extent"
    HEIGHT_VARIATION = "height_variation"

@dataclass
class QualityWarning:
    category: WarningCategory
    message: str
    severity: float
    affected_texture: Optional[str] = None
    affected_features: Optional[List[int]] = None

# Update evaluate_quality_rubric() to return QualityWarning objects
```

---

### 4. **Brittle Feature Type Matching** ⚠️ **HARD-CODED STRINGS**

**Location:** Multiple files

**Current Implementation:**
```python
# quality_tools.py
if feat_type == "dunes":  # What about "dune" (singular)?
if feat_type in ["mountain", "cliff"]:  # Hard-coded list
has_dunes = any(a.get("type") == "dunes" for a in existing_actions)

# Multiple places
if channel_name == "sand" and feat_type == "dunes":
    ...
elif channel_name == "rock" and feat_type in ["mountain", "cliff"]:
    ...
```

**Problems:**
- String literals scattered everywhere
- No single source of truth
- Easy to typo ("dune" vs "dunes")
- Hard to add new feature types

**Encapsulation Needed:**
```python
# server/semantic/features/types.py
from typing import Set, Dict

# Canonical types (from FeatureRegistry)
ALL_FEATURE_TYPES = ["mountain", "valley", "dunes", "cliff", ...]

# Feature groups
ROCK_FEATURES: Set[str] = {"mountain", "cliff"}
SAND_FEATURES: Set[str] = {"dunes", "dune"}  # Handle both
GRASS_FEATURES: Set[str] = {"valley", "plateau"}
SNOW_FEATURES: Set[str] = {"mountain"}

# Texture contribution mapping
FEATURE_TEXTURE_MAP: Dict[str, Dict[str, float]] = {
    "mountain": {"rock": 0.4, "snow": 0.2},
    "dunes": {"sand": 0.6},
    "cliff": {"rock": 0.7},
}

def get_features_for_texture(texture: str) -> Set[str]:
    """Get features that contribute to a texture."""
    return {feat for feat, contribs in FEATURE_TEXTURE_MAP.items()
            if texture in contribs}

def is_rock_feature(feat_type: str) -> bool:
    """Check if feature contributes to rock texture."""
    return feat_type in ROCK_FEATURES
```

---

### 5. **Scattered State Initialization** ⚠️ **INCONSISTENT DEFAULTS**

**Location:** Multiple files

**Current Implementation:**
```python
# quality_tools.py
if "features" not in temp_state:
    temp_state["features"] = []
if "seed" not in temp_state:
    temp_state["seed"] = 42
if "next_id" not in temp_state:
    temp_state["next_id"] = 1

# multi_agent/tools.py
def _prepare_state(scene_state):
    return {
        "features": [],
        "seed": 42,
        "semantic_scene": {},
        "next_id": 1,
    }
```

**Problems:**
- Duplicated logic
- Inconsistent defaults
- Easy to miss required keys
- No validation

**Encapsulation Needed:**
```python
# server/semantic/state/initializer.py
class StateInitializer:
    """Centralized state initialization and validation."""
    
    REQUIRED_KEYS = ["features", "seed", "next_id"]
    DEFAULT_VALUES = {
        "features": [],
        "seed": 42,
        "next_id": 1,
        "semantic_scene": {},
        "base_biome_fn": None,
    }
    
    @staticmethod
    def initialize(scene_state: Optional[Dict] = None) -> Dict[str, Any]:
        """Initialize state with defaults."""
        state = StateInitializer.DEFAULT_VALUES.copy()
        if scene_state:
            state.update(scene_state)
        return state
    
    @staticmethod
    def validate(state: Dict[str, Any]) -> bool:
        """Validate state has required keys."""
        return all(key in state for key in StateInitializer.REQUIRED_KEYS)
```

---

### 6. **Hard-Coded Parameter Modification Values** ⚠️ **NO ADAPTATION**

**Location:** `server/semantic/tools/quality_tools.py:analyze_texture_feature_relationship()`

**Current Implementation:**
```python
if channel_name == "sand" and feat_type == "dunes":
    suggested_changes.append({
        "action_id": feat_id,
        "radius": +30,  # Fixed increment - doesn't scale!
        ...
    })
elif channel_name == "rock" and feat_type in ["mountain", "cliff"]:
    suggested_changes.append({
        "radius": +25,  # Different value - inconsistent!
        ...
    })
```

**Problems:**
- Fixed increments don't scale with feature size
- No consideration of current parameter values
- Different values for different features (inconsistent)
- Doesn't adapt to gap size

**Encapsulation Needed:**
```python
# server/semantic/tools/parameter_strategy.py
class ParameterModificationStrategy:
    """Calculate adaptive parameter modifications."""
    
    STRATEGIES = {
        "sand": {
            "dunes": {"radius_percent": 0.2, "min": 20, "max": 50}
        },
        "rock": {
            "mountain": {"radius_percent": 0.15, "min": 15, "max": 40},
            "cliff": {"radius_percent": 0.15, "min": 15, "max": 40}
        }
    }
    
    @staticmethod
    def calculate_modification(
        texture_gap: str,
        feature_type: str,
        current_radius: float,
        gap_size: float
    ) -> Dict[str, float]:
        """Calculate adaptive parameter change."""
        strategy = ParameterModificationStrategy.STRATEGIES.get(texture_gap, {}).get(feature_type)
        if not strategy:
            return {}
        
        # Percentage-based change
        percent_change = strategy["radius_percent"]
        change = current_radius * percent_change
        
        # Scale with gap size (larger gap = larger change)
        gap_factor = min(2.0, gap_size / 0.1)  # Scale up to 2x for large gaps
        change *= gap_factor
        
        # Clamp to min/max
        change = max(strategy["min"], min(strategy["max"], change))
        
        return {"radius": change}
```

---

### 7. **Import Path Manipulation Scattered** ⚠️ **DUPLICATED CODE**

**Location:** Multiple files

**Current Implementation:**
```python
# Repeated in many files:
import sys
from pathlib import Path
server_dir = Path(__file__).parent.parent.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))
```

**Problems:**
- Duplicated code
- Easy to get wrong paths
- Maintenance burden

**Encapsulation Needed:**
```python
# server/bootstrap.py (already exists, enhance it)
def ensure_bootstrapped():
    """Ensure server directory is in path."""
    import sys
    from pathlib import Path
    
    server_dir = Path(__file__).parent
    if str(server_dir) not in sys.path:
        sys.path.insert(0, str(server_dir))
    
    # Also ensure parent directory
    parent_dir = server_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

# Use everywhere:
from server.bootstrap import ensure_bootstrapped
ensure_bootstrapped()
```

---

### 8. **Broad Exception Handlers** ⚠️ **HIDES BUGS**

**Location:** Multiple files

**Current Implementation:**
```python
except Exception as e:  # Catches everything!
    logger.warning(f"Failed: {e}", exc_info=True)
    return default_value
```

**Problems:**
- Hides bugs (AttributeError, TypeError)
- Catches system errors (KeyboardInterrupt, MemoryError)
- Makes debugging hard

**Encapsulation Needed:**
```python
# server/semantic/exceptions.py
class TerrainGenerationError(Exception):
    """Base exception for terrain generation errors."""
    pass

class TextureAnalysisError(TerrainGenerationError):
    """Error during texture analysis."""
    pass

class ParameterModificationError(TerrainGenerationError):
    """Error during parameter modification."""
    pass

# Use specific exceptions:
try:
    ...
except (TextureAnalysisError, ParameterModificationError) as e:
    # Expected errors - handle gracefully
    logger.warning(f"Analysis failed: {e}")
except Exception as e:
    # Unexpected errors - let propagate
    raise
```

---

## 🟡 Medium Priority Issues

### 9. **Model Names Duplicated**

**Location:** `server/semantic/llm/factory.py`, `server/semantic/multi_agent/config.py`

**Fix:** Single source of truth in `llm/factory.py`

---

### 10. **Default Values Scattered**

**Location:** Multiple files

**Fix:** Centralize in `config.py`

---

## 📋 Implementation Plan

### **Phase 1: Critical Encapsulation (2-3 hours)**

1. ✅ Create `server/semantic/config.py` - All magic numbers
2. ✅ Create `server/semantic/state/initializer.py` - State initialization
3. ✅ Create `server/semantic/features/types.py` - Feature type constants
4. ✅ Create `server/semantic/evaluation/warning_types.py` - Structured warnings

### **Phase 2: Refactor Brittle Patterns (3-4 hours)**

5. ✅ Create `server/semantic/narrative/archetype_matcher.py` - LLM-based matching
6. ✅ Create `server/semantic/tools/parameter_strategy.py` - Adaptive modifications
7. ✅ Update all code to use new encapsulated components

### **Phase 3: Error Handling (1-2 hours)**

8. ✅ Create `server/semantic/exceptions.py` - Custom exceptions
9. ✅ Update error handling to use specific exceptions

---

## 🎯 Key Insight

**The keyword matching is brittle, but we already have LLM infrastructure!**

**Instead of improving keyword matching, we should:**
1. Use LLM for semantic archetype matching (leverage existing narrative pipeline)
2. Fallback to keywords only if LLM unavailable
3. This is much more robust and leverages existing infrastructure

**The narrative pipeline already uses LLM for story generation - we can use it for archetype matching too!**

