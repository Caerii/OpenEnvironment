# Root Cause Analysis: Deep Architectural Issues

## 🔴 Fundamental Architecture Disconnect

### **The Core Problem: Three Separate Worlds**

The system operates in **three disconnected layers**:

1. **Narrative Layer** (Aesthetic Intent)
   - Command → Archetype → Story → Feature Types
   - Generates: `Feature` objects with positions, parameters
   - **Output:** Typed features with semantic meaning

2. **Terrain Generation Layer** (Geometry)
   - Features → Heightmap Stamps → Heightmap
   - Features → Masks (dune_mask, cliff_mask) → Splatmap
   - **Output:** Heightmap + Splatmap (texture map)

3. **Quality Evaluation Layer** (Visual Assessment)
   - Heightmap + Splatmap → Metrics → Scores
   - **Output:** Quality scores, warnings

**The Critical Gap:** These layers don't communicate effectively!

---

## 🔴 Root Cause #1: Texture Generation is Indirect

### **How Texture Actually Works:**

```
Feature → Heightmap Stamp → Heightmap
Feature → Mask (if dunes/cliffs) → Splatmap
Heightmap → Slope Calculation → Texture Assignment
```

**The Problem:**
- Most features (mountains, valleys, plateaus) **don't generate texture masks**
- Texture is **derived from heightmap slope/height** after all features are applied
- Feature parameters (height, radius) affect heightmap, which affects texture **indirectly**
- Only `dunes` and `cliffs` have **direct** texture control via masks

**Why Refinement Fails:**
- Refinement adjusts positions → doesn't change heightmap significantly → doesn't change texture
- Refinement adds features → might help, but doesn't modify existing feature texture contribution
- **Need:** Direct parameter modification (radius, height) to affect texture distribution

**Evidence from Logs:**
```
Texture Score: 0.250-0.380 (consistently low)
Refinement: "Adjusted feature positions" (doesn't affect texture)
Result: No improvement
```

---

## 🔴 Root Cause #2: Context Rubric Uses Wrong Input

### **Current Flow:**
```
Command: "build a balanced landscape with hills and valleys"
↓
Narrative: Wind Architect (WRONG archetype)
↓
Command passed to rubric: "Wind Architect inviting layered organic" (constructed)
↓
Gemini analyzes: "dramatic_mountain" (misinterprets)
```

**The Problem:**
- Context rubric generation uses **command string**, not **archetype + goals**
- Command string is constructed from narrative_meta, which might be wrong
- Gemini has to **guess** context from text, not from structured data
- No validation that rubric matches archetype

**Why This Matters:**
- Wrong rubric → Wrong thresholds → Wrong evaluation → Wrong refinement targets

**Evidence:**
```
Command: "balanced landscape with hills and valleys"
Archetype: Wind Architect (should be Water's Legacy)
Context Rubric: dramatic_mountain (completely wrong!)
```

---

## 🔴 Root Cause #3: Archetype Matching is Keyword-Based

### **Current Logic:**
```python
# Simple keyword matching
if "dunes" in keywords: return Wind Architect
if "valley" in keywords: return Water's Legacy
# But "hills" might match Wind Architect first!
```

**The Problem:**
- No consideration of **feature type combinations**
- No weighting of keywords (valley > hills for Water's Legacy)
- No fallback to check if matched archetype makes sense

**Why This Matters:**
- Wrong archetype → Wrong feature types → Wrong narrative → Wrong composition

---

## 🔴 Root Cause #4: Refinement Operates on Wrong Level

### **Current Refinement:**
```
Warnings: ["Texture coverage low", "Extent narrow"]
↓
Refinement: Adjusts positions OR adds features
↓
Re-evaluate: Still low texture (positions didn't help)
```

**The Problem:**
- Refinement operates on **action level** (features)
- But texture issues need **parameter level** changes (radius, height)
- No tool to modify existing feature parameters
- No understanding of **which features** contribute to texture problems

**What's Missing:**
- **Texture-to-Feature Mapping:** Which features affect which texture regions?
- **Parameter Modification:** Change feature radius/height to affect texture
- **Feature Removal:** Remove features that hurt texture distribution

---

## 🔴 Root Cause #5: No Feedback Loop Between Layers

### **The Missing Connection:**

```
Quality Evaluation → Texture Issues → ??? → Feature Parameters
```

**Current State:**
- Quality evaluation identifies texture problems
- Refinement tries to fix with position changes
- **No mechanism** to translate texture issues → feature parameter changes

**What's Needed:**
1. **Texture Analysis Tool:** Analyze splatmap, identify texture gaps/overcoverage
2. **Feature Contribution Analysis:** Which features affect which texture regions?
3. **Parameter Suggestion:** Given texture issue, suggest feature parameter changes
4. **Iterative Refinement:** Try parameter changes, re-evaluate, learn

---

## 🔴 Root Cause #6: Quality Evaluation Doesn't Understand Narrative Context

### **Current Flow:**
```
Narrative: "Ancient Uplift, dramatic peaks"
↓
Features: Mountains with specific parameters
↓
Quality Evaluation: Uses generic or wrong rubric
↓
Warnings: Generic "texture coverage low"
```

**The Problem:**
- Quality evaluation doesn't know **what the narrative intended**
- Can't distinguish between "wrong texture" vs "wrong for this archetype"
- Context rubric generation happens **after** narrative, but uses wrong input

**What's Needed:**
- Pass **archetype + aesthetic goals** directly to rubric generation
- Don't rely on command string analysis
- Validate rubric matches archetype

---

## 🎯 Critical Fixes (In Priority Order)

### **1. Fix Context Rubric Generation (CRITICAL)**
**Problem:** Uses command string instead of archetype
**Fix:** Pass archetype + aesthetic_goals directly
**Impact:** Correct evaluation criteria applied

```python
# Current (WRONG):
context_rubric = evolution_service.generate_context_rubric(command, base_rubric)

# Should be:
narrative_meta = scene_state.get("_narrative_meta", {})
archetype = narrative_meta.get("archetype", "")
goals = narrative_meta.get("aesthetic_goals", [])
context_rubric = evolution_service.generate_context_rubric_from_archetype(
    archetype, goals, base_rubric
)
```

---

### **2. Add Texture-to-Feature Mapping (CRITICAL)**
**Problem:** Can't translate texture issues to feature changes
**Fix:** Analyze which features affect which texture regions
**Impact:** Refinement can target specific features

**New Tool:**
```python
def analyze_texture_feature_relationship(
    actions: List[Dict],
    heightmap: np.ndarray,
    splatmap: np.ndarray
) -> Dict[str, Any]:
    """
    Returns:
    {
        "feature_texture_contributions": {
            "action_0": {
                "grass_coverage": 0.15,
                "rock_coverage": 0.05,
                "sand_coverage": 0.0,
                "snow_coverage": 0.02,
                "affected_regions": [(x0, y0, x1, y1)]
            },
            ...
        },
        "texture_gaps": [
            {"region": (x, y, w, h), "needed_texture": "sand", "nearby_features": [0, 2]}
        ],
        "texture_overcoverage": [
            {"region": (x, y, w, h), "texture": "grass", "coverage": 0.85, "contributing_features": [1, 3]}
        ]
    }
    """
```

---

### **3. Add Feature Parameter Modification Tool (CRITICAL)**
**Problem:** Can't modify existing feature parameters
**Fix:** Tool to change height, radius, etc. based on texture needs
**Impact:** Direct texture control

**New Tool:**
```python
def modify_feature_parameters(
    scene_state: Dict[str, Any],
    action_id: int,
    parameter_changes: Dict[str, float],  # {"radius": +20, "height": +0.1}
    reason: str
) -> Dict[str, Any]:
    """
    Modify specific feature parameters to affect texture distribution.
    
    Example:
    - Increase mountain radius → More rock texture coverage
    - Increase dune radius → More sand texture coverage
    - Adjust height → Affects snow/grass distribution
    """
```

---

### **4. Fix Archetype Matching (HIGH PRIORITY)**
**Problem:** Keyword matching too simplistic
**Fix:** Check feature type combinations, weight keywords
**Impact:** Correct archetype → Correct features

```python
def match_archetype_from_keywords(keywords: List[str]) -> TerrainArchetype:
    # Check for feature type combinations
    if "valley" in keywords and ("hill" in keywords or "river" in keywords):
        return TERRAIN_ARCHETYPES["water_legacy"]  # Strong signal
    
    # Weight keywords by importance
    keyword_weights = {
        "valley": 3.0,  # Very strong signal for Water's Legacy
        "river": 2.5,
        "hills": 1.0,  # Weak signal
        "dunes": 3.0,  # Very strong for Wind Architect
    }
    
    # Score each archetype
    scores = {}
    for archetype_name, archetype in TERRAIN_ARCHETYPES.items():
        score = 0.0
        for keyword in keywords:
            weight = keyword_weights.get(keyword, 1.0)
            if keyword in archetype.primary_features:
                score += weight * 2.0
            elif keyword in archetype.secondary_features:
                score += weight * 1.0
        scores[archetype_name] = score
    
    return TERRAIN_ARCHETYPES[max(scores, key=scores.get)]
```

---

### **5. Reorder Refinement Warning Priority (HIGH PRIORITY)**
**Problem:** Texture warnings never trigger (extent matches first)
**Fix:** Check texture warnings FIRST
**Impact:** Texture issues actually get addressed

```python
# Current (WRONG):
elif "extent" in warning_lower:  # Matches first
    adjust_positions()
elif "texture" in warning_lower:  # Never reached
    add_features()

# Should be:
if "texture" in warning_lower or "coverage" in warning_lower:  # FIRST
    analyze_texture_distribution()
    modify_feature_parameters()
elif "extent" in warning_lower:
    adjust_positions()
```

---

### **6. Add Refinement Feedback Loop (MEDIUM PRIORITY)**
**Problem:** Refinement doesn't learn from failures
**Fix:** Track what works, try alternatives when it doesn't
**Impact:** Refinement improves over iterations

```python
def refine_with_feedback(
    actions: List[Dict],
    warnings: List[str],
    previous_refinements: List[Dict],  # What was tried before
    scene_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Refine with awareness of what was tried before.
    If position changes didn't work, try parameter changes.
    If adding features didn't work, try removing/modifying existing ones.
    """
```

---

## 🧠 Fundamental Insight

### **The Real Problem:**

The system has **three separate optimization loops** that don't communicate:

1. **Narrative Loop:** Optimize for aesthetic coherence
2. **Feature Generation Loop:** Optimize for spatial composition
3. **Quality Loop:** Optimize for texture/visual quality

**But they optimize different things:**
- Narrative → Feature types, positions
- Features → Heightmap geometry
- Quality → Texture maps

**The Missing Link:**
- **Texture maps depend on heightmap + masks**
- **Heightmap depends on feature parameters**
- **But refinement can't translate texture issues → parameter changes**

---

## 🎯 What Actually Makes Sense

### **Option A: Fix the Translation Layer (Recommended)**
1. Add texture-to-feature mapping
2. Add parameter modification tool
3. Fix context rubric to use archetype
4. Reorder refinement priority

**Pros:** Works with existing architecture
**Cons:** Still indirect (texture → parameters → texture)

---

### **Option B: Direct Texture Control (More Radical)**
1. Features generate texture masks directly (not just heightmaps)
2. Refinement modifies texture masks
3. Quality evaluates texture masks directly

**Pros:** Direct control, easier refinement
**Cons:** Requires architectural changes

---

### **Option C: Two-Stage Generation (Most Robust)**
1. **Stage 1:** Generate features for composition (current system)
2. **Stage 2:** Generate/adjust texture masks for texture quality
3. Refinement operates on both stages

**Pros:** Separates concerns, easier to optimize each
**Cons:** More complex, two-stage pipeline

---

## 📊 Evidence Summary

### **From Logs:**
1. **Texture scores consistently low** (0.25-0.38) → Indirect control problem
2. **Refinement makes same changes** → No learning, wrong level
3. **Context rubric mismatches** → Wrong input to generation
4. **Archetype mismatches** → Wrong features generated
5. **Quality plateaus** → No feedback loop

### **From Code:**
1. **No texture-to-feature mapping** → Can't translate issues
2. **No parameter modification tool** → Can't fix texture directly
3. **Context rubric uses command string** → Wrong input
4. **Refinement checks extent before texture** → Wrong priority
5. **Archetype matching is keyword-based** → Too simplistic

---

## 🚀 Recommended Action Plan

### **Phase 1: Critical Fixes (Do First)**
1. ✅ Fix context rubric to use archetype (not command string)
2. ✅ Reorder refinement warning priority (texture first)
3. ✅ Fix archetype matching (feature combinations)

### **Phase 2: Enable Texture Refinement (Do Next)**
4. ✅ Add texture-to-feature mapping tool
5. ✅ Add feature parameter modification tool
6. ✅ Update refinement to use parameter modification

### **Phase 3: Improve Feedback (Do Later)**
7. ✅ Add refinement feedback loop
8. ✅ Track refinement success/failure
9. ✅ Try alternative strategies when refinement fails

---

## 💡 Key Insight

**The fundamental issue is that texture quality is evaluated AFTER terrain generation, but refinement operates BEFORE terrain generation.**

We need a **bidirectional bridge**:
- **Forward:** Features → Terrain → Texture (current, works)
- **Backward:** Texture Issues → Feature Changes (missing, critical!)

The backward bridge requires:
1. Understanding which features affect which texture regions
2. Tools to modify feature parameters
3. Feedback loop to validate changes

