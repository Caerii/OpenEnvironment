# Critical Action Plan: What Actually Makes Sense

## 🎯 The Core Insight

**The fundamental problem:** We're trying to optimize texture quality by adjusting features, but texture is **derived from heightmap**, not directly from features. This creates an **indirect optimization problem** that's hard to solve.

**The solution:** We need a **bidirectional bridge**:
- **Forward:** Features → Terrain → Texture ✅ (works)
- **Backward:** Texture Issues → Feature Changes ❌ (missing, critical!)

---

## 🔴 Phase 1: Critical Fixes (Do First - 2-3 hours)

### **Fix #1: Context Rubric Uses Archetype (NOT Command String)**

**Why Critical:**
- Wrong rubric → Wrong evaluation → Wrong refinement targets
- Currently: Gemini misinterprets command strings
- Should: Use structured archetype + goals data

**Implementation:**
```python
# In quality_tools.py, evaluate_terrain_quality()
# BEFORE calling generate_context_rubric:

narrative_meta = scene_state.get("_narrative_meta", {})
if narrative_meta:
    archetype = narrative_meta.get("archetype", "")
    goals = narrative_meta.get("aesthetic_goals", [])
    
    # Pass structured data, not command string
    context_rubric = evolution_service.generate_context_rubric_from_archetype(
        archetype=archetype,
        aesthetic_goals=goals,
        base_rubric=DEFAULT_QUALITY_RUBRIC
    )
else:
    # Fallback to command string only if no narrative
    context_rubric = evolution_service.generate_context_rubric(command, base_rubric)
```

**Impact:** Correct evaluation criteria applied → Better refinement targets

---

### **Fix #2: Reorder Refinement Warning Priority**

**Why Critical:**
- Texture warnings never trigger (extent matches first)
- Texture is the bottleneck (0.25-0.38 scores)
- Must check texture FIRST

**Implementation:**
```python
# In quality_tools.py, refine_composition()
# Reorder the warning checks:

for warning in quality_warnings[:max_refinements]:
    warning_lower = warning.lower()
    
    # CRITICAL: Check texture FIRST (most important)
    if "texture" in warning_lower or "coverage" in warning_lower:
        # Analyze texture distribution
        texture_analysis = analyze_texture_distribution(...)
        # Modify feature parameters based on texture needs
        refined_actions = modify_features_for_texture(refined_actions, texture_analysis)
        changes_made.append("Adjusted feature parameters for texture distribution")
    
    # Then check other issues
    elif "extent" in warning_lower or "spread" in warning_lower:
        refined_actions = _adjust_positions_for_extent(refined_actions)
        changes_made.append("Adjusted feature positions to increase spatial spread")
    
    # ... rest of checks
```

**Impact:** Texture issues actually get addressed → Quality improves

---

### **Fix #3: Fix Archetype Matching (Feature Combinations)**

**Why Critical:**
- "hills and valleys" → Wind Architect (wrong)
- Should be Water's Legacy
- Wrong archetype → Wrong features → Wrong narrative

**Implementation:**
```python
# In archetypes.py, match_archetype_from_keywords()

def match_archetype_from_keywords(keywords: List[str]) -> TerrainArchetype:
    # FIRST: Check for strong feature type combinations
    keywords_lower = [k.lower() for k in keywords]
    
    # Strong combinations (override individual keywords)
    if "valley" in keywords_lower and ("hill" in keywords_lower or "river" in keywords_lower):
        return TERRAIN_ARCHETYPES["waters_legacy"]
    
    if "dune" in keywords_lower and "desert" in keywords_lower:
        return TERRAIN_ARCHETYPES["wind_architect"]
    
    if "mountain" in keywords_lower and ("peak" in keywords_lower or "dramatic" in keywords_lower):
        return TERRAIN_ARCHETYPES["ancient_uplift"]
    
    # THEN: Score individual keywords (weighted)
    keyword_weights = {
        "valley": 3.0,  # Very strong for Water's Legacy
        "river": 2.5,
        "dune": 3.0,   # Very strong for Wind Architect
        "desert": 2.5,
        "mountain": 2.0,
        "hill": 1.0,   # Weak signal (could be multiple archetypes)
    }
    
    scores = {name: 0.0 for name in TERRAIN_ARCHETYPES.keys()}
    
    for keyword in keywords_lower:
        weight = keyword_weights.get(keyword, 1.0)
        
        # Check primary features (higher weight)
        for archetype_name, archetype in TERRAIN_ARCHETYPES.items():
            if keyword in [f.lower() for f in archetype.primary_features]:
                scores[archetype_name] += weight * 2.0
            elif keyword in [f.lower() for f in archetype.secondary_features]:
                scores[archetype_name] += weight * 1.0
    
    best_archetype = max(scores, key=scores.get)
    return TERRAIN_ARCHETYPES[best_archetype]
```

**Impact:** Correct archetype → Correct features → Better composition

---

## 🟡 Phase 2: Enable Texture Refinement (Do Next - 4-6 hours)

### **Tool #1: Texture-to-Feature Mapping**

**Why Critical:**
- Need to know which features affect which texture regions
- Without this, can't target specific features for modification

**Implementation:**
```python
def analyze_texture_feature_relationship(
    actions: List[Dict[str, Any]],
    scene_state: Dict[str, Any],
    render_preview: bool = True
) -> Dict[str, Any]:
    """
    Analyze which features contribute to which texture regions.
    
    Strategy:
    1. Render terrain with each feature individually
    2. Compare texture maps (with vs without each feature)
    3. Identify feature contributions to each texture channel
    
    Returns:
    {
        "feature_contributions": {
            "action_0": {
                "grass_coverage": 0.15,
                "rock_coverage": 0.05,
                "sand_coverage": 0.0,
                "snow_coverage": 0.02,
                "affected_region": (x0, y0, x1, y1)
            },
            ...
        },
        "texture_gaps": [
            {
                "region": (x, y, w, h),
                "needed_texture": "sand",
                "nearby_features": [0, 2],
                "suggested_changes": [
                    {"action_id": 0, "change": "increase_radius", "value": +30}
                ]
            }
        ]
    }
    """
    # Render full terrain
    heightmap_full, splatmap_full = _render_terrain_preview(actions, scene_state)
    
    feature_contributions = {}
    
    # For each feature, render without it and compare
    for i, action in enumerate(actions):
        actions_without = actions[:i] + actions[i+1:]
        heightmap_partial, splatmap_partial = _render_terrain_preview(actions_without, scene_state)
        
        # Calculate difference
        texture_diff = splatmap_full - splatmap_partial
        
        # Extract contribution per channel
        contributions = {
            "grass_coverage": float(texture_diff[:, :, 0].mean()),
            "rock_coverage": float(texture_diff[:, :, 1].mean()),
            "sand_coverage": float(texture_diff[:, :, 2].mean()),
            "snow_coverage": float(texture_diff[:, :, 3].mean()),
        }
        
        # Find affected region (where difference is significant)
        mask = np.any(np.abs(texture_diff) > 0.1, axis=2)
        if np.any(mask):
            coords = np.where(mask)
            x0, y0 = int(coords[1].min()), int(coords[0].min())
            x1, y1 = int(coords[1].max()), int(coords[0].max())
            contributions["affected_region"] = (x0, y0, x1, y1)
        
        feature_contributions[f"action_{i}"] = contributions
    
    # Analyze texture gaps
    texture_gaps = _identify_texture_gaps(splatmap_full, feature_contributions)
    
    return {
        "feature_contributions": feature_contributions,
        "texture_gaps": texture_gaps,
    }
```

**Impact:** Understand feature→texture relationship → Targeted refinement

---

### **Tool #2: Modify Feature Parameters**

**Why Critical:**
- Can't fix texture without modifying feature parameters
- Position changes don't affect texture significantly
- Need direct parameter control

**Implementation:**
```python
def modify_feature_parameters(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    modifications: List[Dict[str, Any]]  # [{"action_id": 0, "radius": +30, "height": +0.1}]
) -> Dict[str, Any]:
    """
    Modify specific feature parameters to affect texture distribution.
    
    Args:
        modifications: List of parameter changes
            [{"action_id": 0, "radius": +30, "height": +0.1, "reason": "Increase rock coverage"}]
    
    Returns:
        {
            "refined_actions": List[Dict],
            "changes_made": List[str],
            "expected_texture_impact": Dict[str, float]
        }
    """
    refined_actions = copy.deepcopy(actions)
    changes_made = []
    
    for mod in modifications:
        action_id = mod.get("action_id")
        if action_id >= len(refined_actions):
            continue
        
        action = refined_actions[action_id]
        modifiers = action.setdefault("modifiers", {})
        
        # Apply parameter changes
        if "radius" in mod:
            current_radius = modifiers.get("radius", 50)
            modifiers["radius"] = max(20, min(200, current_radius + mod["radius"]))
            changes_made.append(f"Action {action_id}: radius {current_radius} → {modifiers['radius']}")
        
        if "height" in mod:
            current_height = modifiers.get("height", 0.5)
            modifiers["height"] = max(0.1, min(1.5, current_height + mod["height"]))
            changes_made.append(f"Action {action_id}: height {current_height:.2f} → {modifiers['height']:.2f}")
        
        # ... other parameters
    
    return {
        "refined_actions": refined_actions,
        "changes_made": changes_made,
    }
```

**Impact:** Direct texture control → Effective refinement

---

### **Update Refinement to Use New Tools**

**Implementation:**
```python
# In refine_composition(), when texture warning detected:

if "texture" in warning_lower or "coverage" in warning_lower:
    # Step 1: Analyze texture-feature relationship
    texture_analysis = analyze_texture_feature_relationship(
        refined_actions, scene_state, render_preview=True
    )
    
    # Step 2: Identify needed modifications
    modifications = []
    for gap in texture_analysis.get("texture_gaps", []):
        needed_texture = gap["needed_texture"]
        nearby_features = gap["nearby_features"]
        
        # Find features that can provide this texture
        for action_id in nearby_features:
            action = refined_actions[action_id]
            feature_type = action.get("type")
            
            # Map texture needs to parameter changes
            if needed_texture == "sand" and feature_type == "dunes":
                modifications.append({
                    "action_id": action_id,
                    "radius": +30,  # Increase dune size → more sand
                    "reason": f"Increase {needed_texture} coverage"
                })
            elif needed_texture == "rock" and feature_type in ["mountain", "cliff"]:
                modifications.append({
                    "action_id": action_id,
                    "radius": +25,  # Increase size → more rock
                    "height": +0.1,  # Increase height → more rock on slopes
                    "reason": f"Increase {needed_texture} coverage"
                })
    
    # Step 3: Apply modifications
    if modifications:
        mod_result = modify_feature_parameters(refined_actions, scene_state, modifications)
        refined_actions = mod_result["refined_actions"]
        changes_made.extend(mod_result["changes_made"])
```

**Impact:** Texture issues actually fixed → Quality improves significantly

---

## 🟢 Phase 3: Improve Feedback (Do Later - 2-3 hours)

### **Add Refinement Feedback Loop**

Track what works, try alternatives when it doesn't.

---

## 📊 Expected Impact

### **After Phase 1:**
- ✅ Correct archetype matching → Right features generated
- ✅ Correct context rubrics → Right evaluation criteria
- ✅ Texture warnings prioritized → Texture issues addressed

**Expected:** Quality scores improve from 0.5-0.7 → 0.6-0.75

### **After Phase 2:**
- ✅ Texture-to-feature mapping → Understand relationships
- ✅ Parameter modification → Direct texture control
- ✅ Targeted refinement → Effective improvements

**Expected:** Quality scores improve from 0.6-0.75 → 0.75-0.85

---

## 🎯 What Makes Sense vs What Doesn't

### **✅ Makes Sense:**
1. **Fix context rubric** - Uses wrong input, easy fix, high impact
2. **Reorder refinement priority** - Texture is bottleneck, must check first
3. **Fix archetype matching** - Wrong features = wrong everything
4. **Add texture-to-feature mapping** - Need to understand relationships
5. **Add parameter modification** - Need direct control

### **❌ Doesn't Make Sense:**
1. **Regenerating entire composition** - Too expensive, loses narrative coherence
2. **Adding more features** - Already have enough, need to modify existing ones
3. **Complex multi-agent loops** - Current system works, just needs better tools
4. **Redesigning texture generation** - Works fine, just need better refinement

---

## 🚀 Recommended Order

1. **Fix #1-3** (Phase 1) - 2-3 hours, high impact, low risk
2. **Tool #1-2** (Phase 2) - 4-6 hours, critical for texture refinement
3. **Update refinement** - 2 hours, integrates new tools
4. **Test and iterate** - Continuous

**Total:** ~8-11 hours for critical fixes + texture refinement capability

---

## 💡 Key Insight

**The system architecture is sound, but the refinement layer is operating at the wrong level.**

- **Current:** Refinement operates on **feature level** (positions, add/remove)
- **Needed:** Refinement operates on **parameter level** (radius, height, etc.)

**The fix:** Add tools to bridge texture issues → parameter changes.

This is **much simpler** than redesigning the entire system, and addresses the root cause directly.

