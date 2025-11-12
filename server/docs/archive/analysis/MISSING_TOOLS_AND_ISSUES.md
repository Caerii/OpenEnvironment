# Missing Tools and Critical Issues Analysis

## 🔴 Critical Issues Identified

### **1. Context Rubric Mismatch**
**Problem:** 
- Command: `"build a balanced landscape with hills and valleys"`
- Matched Archetype: `Wind Architect` ❌ (should be `Water's Legacy`)
- Context Rubric Used: `dramatic_mountain` ❌ (completely wrong!)

**Root Cause:**
- Context rubric selection is based on keyword matching, not archetype or command intent
- Archetype matching is incorrectly selecting `Wind Architect` for hills/valleys

**Impact:**
- Quality evaluation uses wrong rubric thresholds
- Refinement targets wrong criteria
- Scores don't reflect actual terrain quality

---

### **2. Refinement Not Addressing Texture Issues**
**Problem:**
- Texture scores consistently low: 0.250-0.380 (target: 0.6+)
- Refinement only adjusts positions, not texture distribution
- Texture warnings trigger `_add_features_for_texture_balance()` but it's not effective

**Root Cause:**
- `refine_composition` logic checks warnings sequentially with `elif` chains
- "extent/spread" warnings match before "texture" warnings
- Texture refinement adds features but doesn't modify existing feature parameters

**Impact:**
- Quality plateaus at 0.5-0.7 despite refinement attempts
- Texture issues persist across iterations

---

### **3. Archetype Matching Failure**
**Problem:**
- `"hills and valleys"` → `Wind Architect` (wrong)
- Should match `Water's Legacy` archetype

**Root Cause:**
- Keyword matching in `match_archetype_from_keywords()` is too simplistic
- "hills" might match "dunes" keywords, "valleys" not weighted strongly enough

**Impact:**
- Wrong feature types generated (dunes instead of valleys)
- Wrong narrative context applied
- Wrong aesthetic goals inferred

---

### **4. ReAct Agent Failing to Extract Actions**
**Problem:**
- When narrative tool isn't called, agent tries to extract actions from text
- Multiple failures: `"No actions found in response (tried 4 strategies)"`

**Root Cause:**
- Agent finishes reasoning but doesn't call tools
- Action extraction regex/parsing fails
- No fallback to force narrative tool usage

**Impact:**
- Wasted iterations (3-4 iterations before finally calling narrative tool)
- Inconsistent behavior

---

## 🛠️ Missing Tools Needed

### **1. `modify_feature_parameters` Tool**
**Purpose:** Directly modify feature height, scale, radius based on specific warnings

**Why Needed:**
- Current refinement only adjusts positions or adds features
- Can't modify existing feature parameters to improve texture/height variation
- Texture issues often require adjusting feature sizes, not just positions

**Signature:**
```python
def modify_feature_parameters(
    scene_state: Dict[str, Any],
    feature_ids: List[int],
    parameter_changes: Dict[str, float],  # {"height": +0.1, "radius": +20}
    reason: str  # "Increase height variation" or "Improve texture coverage"
) -> Dict[str, Any]
```

---

### **2. `analyze_texture_distribution` Tool**
**Purpose:** Analyze rendered texture maps and suggest specific improvements

**Why Needed:**
- Current texture analysis is generic
- Need to identify which areas need which textures
- Need to suggest specific feature modifications or additions

**Signature:**
```python
def analyze_texture_distribution(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    render_preview: bool = True
) -> Dict[str, Any]:
    """
    Returns:
    {
        "texture_gaps": [{"region": [x, y, w, h], "needed_texture": "sand", "reason": "..."}],
        "texture_overcoverage": [{"region": [...], "texture": "grass", "coverage": 0.85}],
        "suggested_modifications": [
            {"action_id": 1, "change": "increase_radius", "value": 20, "reason": "..."}
        ],
        "suggested_additions": [
            {"type": "dunes", "position": [x, y], "reason": "Add sand texture in gap"}
        ]
    }
    """
```

---

### **3. `regenerate_composition_with_constraints` Tool**
**Purpose:** Regenerate narrative composition with specific constraints/improvements

**Why Needed:**
- When initial generation fails quality threshold
- When refinement isn't working, need to regenerate with different parameters
- Can specify: feature types, count, positions, archetype overrides

**Signature:**
```python
def regenerate_composition_with_constraints(
    scene_state: Dict[str, Any],
    command: str,
    constraints: Dict[str, Any],  # {"archetype": "Water's Legacy", "min_features": 6}
    previous_actions: List[Dict[str, Any]]  # For reference
) -> Dict[str, Any]
```

---

### **4. `analyze_refinement_failure` Tool**
**Purpose:** Analyze why refinement isn't improving quality and suggest alternatives

**Why Needed:**
- Current refinement makes changes but quality doesn't improve
- Need to understand why (wrong changes? insufficient changes? evaluation issue?)
- Suggest alternative strategies

**Signature:**
```python
def analyze_refinement_failure(
    scene_state: Dict[str, Any],
    original_actions: List[Dict[str, Any]],
    refined_actions: List[Dict[str, Any]],
    original_score: float,
    refined_score: float,
    warnings: List[str]
) -> Dict[str, Any]:
    """
    Returns:
    {
        "failure_reason": "positional_changes_dont_affect_texture",
        "root_cause": "Texture score low but refinement only adjusted positions",
        "suggested_strategy": "modify_feature_parameters",
        "specific_changes": [
            {"action_id": 2, "parameter": "radius", "change": +30, "reason": "..."}
        ]
    }
    """
```

---

### **5. `fix_context_rubric_mismatch` Tool**
**Purpose:** Detect and fix context rubric mismatches

**Why Needed:**
- Context rubric selection is broken (using "dramatic_mountain" for "balanced landscape")
- Need to verify rubric matches command/archetype
- Need to regenerate correct rubric if mismatch detected

**Signature:**
```python
def fix_context_rubric_mismatch(
    command: str,
    archetype: str,
    current_rubric_context: str,
    scene_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Returns:
    {
        "mismatch_detected": True,
        "expected_context": "balanced_landscape",
        "corrected_rubric": {...},
        "reason": "Command 'hills and valleys' should use Water's Legacy, not Wind Architect"
    }
    """
```

---

### **6. `force_narrative_tool_usage` Tool**
**Purpose:** Force narrative tool usage when ReAct agent fails to extract actions

**Why Needed:**
- Agent sometimes finishes reasoning without calling tools
- Need fallback to ensure narrative tool is always used for aesthetic commands
- Prevents wasted iterations

**Signature:**
```python
def force_narrative_tool_usage(
    scene_state: Dict[str, Any],
    command: str,
    reason: str  # "ReAct agent failed to extract actions"
) -> Dict[str, Any]
```

---

## 🔧 Code Fixes Needed

### **1. Fix Context Rubric Selection**
**File:** `server/semantic/tools/quality_tools.py`

**Issue:** Context rubric selection uses keyword matching instead of archetype

**Fix:**
```python
# Current (WRONG):
context_type = "dramatic_mountain" if "dramatic" in command.lower() else "serene_desert"

# Should be:
narrative_meta = scene_state.get("_narrative_meta", {})
archetype = narrative_meta.get("archetype", "")
aesthetic_goals = narrative_meta.get("aesthetic_goals", [])

# Map archetype + goals to context type
context_type = _map_archetype_to_context(archetype, aesthetic_goals, command)
```

---

### **2. Fix Refinement Warning Priority**
**File:** `server/semantic/tools/quality_tools.py`

**Issue:** `elif` chain means texture warnings never trigger if extent warnings exist

**Fix:**
```python
# Current (WRONG):
elif "extent" in warning_lower or "spread" in warning_lower:
    # This matches first, texture never checked
    
# Should be:
# Check texture warnings FIRST (most critical)
if "texture" in warning_lower or "coverage" in warning_lower:
    # Handle texture
elif "extent" in warning_lower or "spread" in warning_lower:
    # Handle extent
```

---

### **3. Fix Archetype Matching**
**File:** `server/semantic/narrative/archetypes.py`

**Issue:** `match_archetype_from_keywords()` incorrectly matches "hills and valleys"

**Fix:**
- Increase weight for "valley" keyword
- Add "hills" as secondary feature for Water's Legacy
- Check for feature type combinations (hills + valleys = Water's Legacy)

---

### **4. Add Refinement Feedback Loop**
**File:** `server/semantic/react_agent_v2.py`

**Issue:** Refinement doesn't learn from failures

**Fix:**
- Track refinement attempts and results
- If quality doesn't improve after 2-3 refinements, try alternative strategy
- Use `analyze_refinement_failure` tool to understand why

---

## 📊 Metrics to Track

1. **Context Rubric Match Rate:** % of times correct rubric is used
2. **Refinement Success Rate:** % of refinements that improve quality
3. **Texture Score Improvement:** Average texture score improvement per refinement
4. **Archetype Match Accuracy:** % of correct archetype matches
5. **Tool Call Efficiency:** Average iterations before successful tool call

---

## 🎯 Priority Actions

### **Immediate (Critical):**
1. ✅ Fix context rubric selection to use archetype, not keywords
2. ✅ Fix refinement warning priority (texture first)
3. ✅ Fix archetype matching for "hills and valleys"

### **High Priority:**
4. Implement `modify_feature_parameters` tool
5. Implement `analyze_texture_distribution` tool
6. Add refinement feedback loop

### **Medium Priority:**
7. Implement `analyze_refinement_failure` tool
8. Implement `regenerate_composition_with_constraints` tool
9. Add `force_narrative_tool_usage` fallback

---

## 🔍 Evidence from Logs

### **Context Mismatch:**
```
Command: "build a balanced landscape with hills and valleys"
Archetype: Wind Architect (WRONG)
Context Rubric: dramatic_mountain (WRONG)
Expected: Water's Legacy, balanced_landscape
```

### **Refinement Plateau:**
```
Iteration 1: 0.560 → Refinement → 0.690
Iteration 2: 0.690 → Refinement → 0.690 (no improvement)
Iteration 3: 0.690 → Refinement → 0.620 (worse!)
Iteration 4: 0.620 → Refinement → 0.690
Iteration 5: 0.690 → Refinement → 0.690 (plateau)
```

### **Texture Scores:**
```
All iterations: texture=0.250-0.380 (target: 0.6+)
Composition: 1.000 (perfect)
Overall: 0.5-0.7 (limited by texture)
```

---

## 💡 Key Insights

1. **Refinement is making wrong changes** - Position adjustments don't fix texture issues
2. **Context rubrics are mismatched** - Wrong evaluation criteria applied
3. **Archetype matching is broken** - Wrong features generated
4. **No feedback loop** - Refinement doesn't learn from failures
5. **Missing granular tools** - Can't modify specific feature parameters

