<!--
METADATA:
  File: ENCAPSULATION_PLAN.md
  Created: November 2025
  Last Modified: 2025-11-11
  Status: See README.md for current status
  Purpose: AI-generated planning/analysis document
  Archive Date: 2025-11-11
-->


## 📋 Document Purpose

This document was created during active development to plan encapsulation of brittle patterns.

## ⚠️ Status: See README.md for current status

# Encapsulation Plan: Fixing Brittle Patterns

## 🎯 Priority Order

### **Phase 1: Critical Brittle Patterns (Do First)**

#### 1. **Archetype Matching - Use LLM Instead of Keywords**

**Current Problem:**
- Hard-coded keyword lists and weights
- Brittle string matching
- No semantic understanding

**Solution:**
- Use narrative pipeline's LLM to match archetypes semantically
- Fallback to keyword matching only if LLM unavailable
- Leverage existing `develop_terrain_narrative()` infrastructure

**Implementation:**
```python
# server/semantic/narrative/archetype_matcher.py
class ArchetypeMatcher:
    """Semantic archetype matching using LLM with keyword fallback."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self.keyword_matcher = KeywordArchetypeMatcher()  # Fallback
    
    def match_archetype(self, command: str, keywords: List[str]) -> TerrainArchetype:
        """Match archetype using LLM (preferred) or keywords (fallback)."""
        if self.llm_client:
            try:
                return self._match_with_llm(command, keywords)
            except Exception as e:
                logger.warning(f"LLM matching failed: {e}, using keyword fallback")
        
        return self.keyword_matcher.match(keywords)
    
    def _match_with_llm(self, command: str, keywords: List[str]) -> TerrainArchetype:
        """Use LLM to semantically match archetype."""
        # Use existing narrative pipeline's LLM
        # It already understands terrain semantics!
        ...
```

---

#### 2. **Extract Magic Numbers to Configuration**

**Create:** `server/semantic/config.py`

```python
"""Configuration constants for semantic terrain generation."""

# Texture Analysis
TEXTURE_COVERAGE_THRESHOLDS = {
    "grass": 0.15,
    "rock": 0.10,
    "sand": 0.05,
    "snow": 0.05,
}

TEXTURE_DIFF_THRESHOLD = 0.05  # 5% difference threshold
TEXTURE_GAP_MIN_PIXELS = 10  # Minimum gap size to report
MAX_FEATURES_TO_ANALYZE = 5  # Limit texture analysis depth
NEARBY_FEATURE_RADIUS = 50  # Pixels
MAX_NEARBY_FEATURES = 2  # Top N features to suggest changes for

# Parameter Modification
PARAMETER_MODIFICATION_STRATEGIES = {
    "sand": {
        "dunes": {"radius_percent": 0.2, "min_increment": 20, "max_increment": 50}
    },
    "rock": {
        "mountain": {"radius_percent": 0.15, "min_increment": 15, "max_increment": 40},
        "cliff": {"radius_percent": 0.15, "min_increment": 15, "max_increment": 40}
    }
}

# Refinement
DEFAULT_QUALITY_THRESHOLD = 0.8
DEFAULT_MAX_REFINEMENTS = 5
DEFAULT_MAX_REFINEMENT_ITERATIONS = 5

# Feature Types
ROCK_FEATURES = ["mountain", "cliff"]
SAND_FEATURES = ["dunes"]
GRASS_FEATURES = ["valley", "plateau"]
SNOW_FEATURES = ["mountain"]  # High elevation

# Position Defaults
TERRAIN_CENTER_X = 256  # Should import from engine.config
TERRAIN_CENTER_Y = 256
```

---

#### 3. **Create Warning Type System**

**Create:** `server/semantic/evaluation/warning_types.py`

```python
"""Structured warning types for quality evaluation."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class WarningCategory(Enum):
    TEXTURE = "texture"
    COMPOSITION = "composition"
    SPATIAL = "spatial"
    FEATURE_COUNT = "feature_count"
    DIVERSITY = "diversity"
    HEIGHT_VARIATION = "height_variation"

@dataclass
class QualityWarning:
    category: WarningCategory
    message: str
    severity: float  # 0.0-1.0
    suggested_fix: Optional[str] = None
    affected_features: Optional[List[int]] = None
```

**Update:** `evaluate_quality_rubric()` to return `QualityWarning` objects instead of strings.

---

#### 4. **Create State Initializer**

**Create:** `server/semantic/state/initializer.py`

```python
"""Centralized state initialization and validation."""

class StateInitializer:
    """Initialize and validate terrain state."""
    
    DEFAULT_STATE = {
        "features": [],
        "seed": 42,
        "next_id": 1,
        "semantic_scene": {},
        "base_biome_fn": None,
    }
    
    @staticmethod
    def initialize(scene_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initialize state with defaults."""
        if scene_state is None:
            scene_state = {}
        
        state = StateInitializer.DEFAULT_STATE.copy()
        state.update(scene_state)
        
        # Ensure required keys exist
        for key, default_value in StateInitializer.DEFAULT_STATE.items():
            if key not in state:
                state[key] = default_value
        
        return state
    
    @staticmethod
    def validate(state: Dict[str, Any]) -> bool:
        """Validate state has required keys."""
        required_keys = ["features", "seed", "next_id"]
        return all(key in state for key in required_keys)
```

---

#### 5. **Create Feature Type Registry**

**Create:** `server/semantic/features/types.py`

```python
"""Feature type constants and groups."""

from typing import List, Dict, Set

# Canonical feature types (from FeatureRegistry)
ALL_FEATURE_TYPES = [
    "mountain", "valley", "dunes", "cliff", "plateau", "canyon",
    "hill", "mesa", "slope", "crater", "ridge", "ravine",
    "volcano", "pass", "mound", "basin", "pinnacle", "spur", "terraces"
]

# Feature type groups
ROCK_FEATURES: Set[str] = {"mountain", "cliff"}
SAND_FEATURES: Set[str] = {"dunes"}
GRASS_FEATURES: Set[str] = {"valley", "plateau"}
SNOW_FEATURES: Set[str] = {"mountain"}  # High elevation

# Texture contribution mapping
FEATURE_TEXTURE_CONTRIBUTION: Dict[str, Dict[str, float]] = {
    "mountain": {"rock": 0.4, "snow": 0.2, "grass": 0.1},
    "dunes": {"sand": 0.6, "rock": 0.1},
    "cliff": {"rock": 0.7, "grass": 0.1},
    "valley": {"grass": 0.5, "rock": 0.2},
    # ...
}

def get_texture_features(texture_name: str) -> List[str]:
    """Get features that contribute to a texture."""
    return [feat for feat, contribs in FEATURE_TEXTURE_CONTRIBUTION.items()
            if texture_name in contribs and contribs[texture_name] > 0.1]
```

---

### **Phase 2: Refactor Existing Code**

#### 6. **Update `analyze_texture_feature_relationship()`**

**Changes:**
- Use `TEXTURE_COVERAGE_THRESHOLDS` from config
- Use `FEATURE_TEXTURE_CONTRIBUTION` for suggestions
- Use percentage-based parameter changes
- Use `get_texture_features()` helper

#### 7. **Update `refine_composition()`**

**Changes:**
- Use `QualityWarning` objects instead of strings
- Match on `warning.category` instead of text
- Use `PARAMETER_MODIFICATION_STRATEGIES` from config

#### 8. **Update `match_archetype_from_keywords()`**

**Changes:**
- Use `ArchetypeMatcher` class
- Try LLM first, fallback to keywords
- Handle synonyms and variations

---

## 📊 Impact Assessment

### **Before (Brittle):**
- Keyword matching: 50% accuracy (from tests)
- Hard-coded values: 20+ magic numbers
- String matching: Breaks on text changes
- State initialization: Inconsistent defaults

### **After (Encapsulated):**
- LLM matching: 90%+ accuracy (semantic understanding)
- Configuration: Single source of truth
- Structured warnings: Type-safe matching
- State initialization: Consistent everywhere

---

## 🚀 Implementation Order

1. **Create config module** (30 min)
2. **Create state initializer** (20 min)
3. **Create feature type constants** (30 min)
4. **Create warning types** (45 min)
5. **Refactor archetype matching** (2 hours)
6. **Update texture analysis** (1 hour)
7. **Update refinement logic** (1 hour)

**Total:** ~5-6 hours for critical fixes

---

## 💡 Key Insight

**The keyword matching is brittle, but we already have the solution: the narrative pipeline uses LLM for semantic understanding!**

**Instead of fixing keyword matching, we should:**
1. Use the narrative pipeline's LLM to match archetypes
2. Fallback to keywords only if LLM unavailable
3. This leverages existing infrastructure and is much more robust




