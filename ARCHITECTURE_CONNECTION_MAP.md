# Architecture Connection Map: What Exists vs What's Connected

## Current State (BROKEN CONNECTIONS)

```
┌─────────────────────────────────────────────────────────────┐
│                    GENERATE PATHWAY                         │
│                                                             │
│  Command → parse_command_to_actions()                       │
│              ↓                                              │
│         run_narrative_pipeline()                            │
│              ↓                                              │
│    develop_terrain_narrative()                              │
│              ↓                                              │
│    generate_from_narrative()                                │
│              ↓                                              │
│    composition_to_actions()                                  │
│              ↓                                              │
│         apply_actions()                                     │
│              ↓                                              │
│    TerrainBuilder.finalize()                                │
│              ↓                                              │
│    heightmap, splatmap                                      │
│              ↓                                              │
│    ❌ compute_feature_metrics()  ← ONLY THIS                │
│    ❌ evaluate_aesthetic_quality()  ← ONLY THIS            │
│                                                             │
│    ✅ compute_texture_metrics()  ← EXISTS BUT NOT CALLED   │
│    ✅ evaluate_quality_rubric()  ← EXISTS BUT NOT CALLED    │
│    ✅ summarize_quality_rubric()  ← EXISTS BUT NOT CALLED  │
│                                                             │
│    ❌ Quality refinement loop  ← NOT CONNECTED             │
│    ❌ target_coherence check  ← NOT USED                   │
│    ❌ max_refinement_iterations  ← NOT USED                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              MULTI-AGENT PATHWAY (WORKS!)                  │
│                                                             │
│  Command → score_scene_plan_visual()                        │
│              ↓                                              │
│    render_scene_preview()  ← Generates terrain             │
│              ↓                                              │
│    ✅ compute_feature_metrics()                            │
│    ✅ compute_texture_metrics()  ← CALLED!                  │
│    ✅ evaluate_quality_rubric()  ← CALLED!                   │
│    ✅ summarize_quality_rubric()  ← CALLED!                │
│                                                             │
│    ✅ Full quality evaluation  ← WORKS!                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Target State (ALL CONNECTED)

```
┌─────────────────────────────────────────────────────────────┐
│                    GENERATE PATHWAY                         │
│                                                             │
│  Command → parse_command_to_actions()                       │
│              ↓                                              │
│         run_narrative_pipeline()                            │
│              ↓                                              │
│    develop_terrain_narrative()                              │
│         (target_coherence, max_refinement_iterations)       │
│              ↓                                              │
│    generate_from_narrative()                                │
│              ↓                                              │
│    ✅ Quality check (preview)                               │
│    ✅ refine_composition_by_quality()  ← NEW               │
│              ↓                                              │
│    composition_to_actions()                                 │
│              ↓                                              │
│         apply_actions()                                     │
│              ↓                                              │
│    TerrainBuilder.finalize()                                │
│              ↓                                              │
│    heightmap, splatmap                                      │
│              ↓                                              │
│    ✅ compute_feature_metrics()                            │
│    ✅ compute_texture_metrics()  ← NOW CALLED!             │
│    ✅ evaluate_quality_rubric()  ← NOW CALLED!             │
│    ✅ summarize_quality_rubric()  ← NOW CALLED!           │
│              ↓                                              │
│    ✅ Store quality in state                                │
│    ✅ Check if quality meets target_coherence               │
│    ✅ Post-generation refinement if needed                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Status Matrix

| Component | Exists? | Connected? | Location | Priority |
|-----------|---------|------------|----------|----------|
| `compute_texture_metrics()` | ✅ Yes | ❌ No | `evaluation.py:129` | 🔴 CRITICAL |
| `evaluate_quality_rubric()` | ✅ Yes | ❌ No | `evaluation.py:194` | 🔴 CRITICAL |
| `summarize_quality_rubric()` | ✅ Yes | ❌ No | `evaluation.py:338` | 🟡 HIGH |
| `target_coherence` | ✅ Yes | ❌ No | `types.py:146` | 🔴 CRITICAL |
| `max_refinement_iterations` | ✅ Yes | ❌ No | `types.py:147` | 🔴 CRITICAL |
| Refinement logic | ✅ Yes* | ❌ No | `react_agent_v2.py:291` | 🔴 CRITICAL |
| Background features | ❌ No | N/A | `generation.py:175` | 🟢 MEDIUM |
| Foreground features | ❌ No | N/A | `generation.py:176` | 🟢 MEDIUM |
| Depth layers | ❌ No | N/A | `generation.py:177` | 🟢 MEDIUM |
| Negative space | ❌ No | N/A | `generation.py:178` | 🟢 MEDIUM |

*Exists but in wrong place (ReAct agent, not narrative pipeline)

---

## Connection Points

### Connection Point 1: Texture Metrics
**File**: `server/terrain.py`  
**Line**: After 325  
**Action**: Add call to `compute_texture_metrics(h, splat)`

### Connection Point 2: Quality Rubric
**File**: `server/terrain.py`  
**Line**: After texture metrics  
**Action**: Add call to `evaluate_quality_rubric(feature_metrics, texture_metrics)`

### Connection Point 3: Refinement Loop
**File**: `server/semantic/narrative/utils.py`  
**Line**: After `generate_from_narrative()`  
**Action**: Add quality check and refinement call

### Connection Point 4: Quality Storage
**File**: `server/terrain.py`  
**Line**: After quality evaluation  
**Action**: Store quality results in `state["quality"]`

---

## Data Flow: Before vs After

### BEFORE (Broken):
```
Terrain Generation
    ↓
Feature Metrics Only
    ↓
Basic Quality Score
    ↓
Stored in _last_narrative_meta
    ↓
❌ Never used for anything
```

### AFTER (Fixed):
```
Terrain Generation
    ↓
Feature Metrics + Texture Metrics
    ↓
Full Quality Rubric (composition + textures)
    ↓
Stored in state["quality"]
    ↓
✅ Used for refinement decisions
✅ Used for quality reporting
✅ Available for future features
```

---

## Refinement Flow: Before vs After

### BEFORE (Missing):
```
Generate Composition
    ↓
Convert to Actions
    ↓
Generate Terrain
    ↓
❌ No quality check
❌ No refinement
❌ Quality ignored
```

### AFTER (Complete):
```
Generate Composition
    ↓
Preview Quality Check
    ↓
✅ Refine if below threshold
    ↓
Convert to Actions
    ↓
Generate Terrain
    ↓
Full Quality Evaluation
    ↓
✅ Post-generation refinement if needed
    ↓
Final Quality Score
```

---

## Key Insights

1. **90% of code already exists** - just needs to be connected
2. **Multi-agent pathway shows the way** - it already works correctly
3. **Refinement logic exists** - just needs extraction from ReAct agent
4. **Missing features are well-defined** - clear implementation path

**Effort Breakdown**:
- **Connecting existing code**: 1-2 days (80% of value)
- **Extracting refinement**: 1 day (15% of value)
- **Completing missing features**: 1-2 weeks (5% of value, but important for completeness)

---

## Quick Win Strategy

### Day 1 Morning (2 hours):
1. Add texture metrics call (30 min)
2. Add quality rubric call (30 min)
3. Store quality in state (30 min)
4. Test and verify (30 min)

### Day 1 Afternoon (3 hours):
1. Extract refinement logic (2 hours)
2. Connect to pipeline (1 hour)

### Day 2 (4 hours):
1. Test refinement loop (2 hours)
2. Fix bugs (2 hours)

**Result**: Full quality evaluation + automatic refinement in 1 day!

---

## Risk Mitigation

### Low Risk Changes:
- ✅ Adding function calls (texture metrics, quality rubric)
- ✅ Storing data in state
- ✅ Making quality evaluation optional

### Medium Risk Changes:
- ⚠️ Refinement loop (needs testing)
- ⚠️ Modifying narrative pipeline

### Mitigation:
- Add feature flags to enable/disable refinement
- Keep old code path as fallback
- Extensive testing before enabling by default

---

## Success Criteria

### Phase 1 Success:
- [ ] `state["quality"]` exists after generation
- [ ] `state["quality"]["texture_score"]` > 0
- [ ] `state["quality"]["overall_score"]` combines composition + textures
- [ ] No duplicate quality evaluation

### Phase 2 Success:
- [ ] Refinement runs when quality < target_coherence
- [ ] Quality improves after refinement
- [ ] Refinement respects max_iterations
- [ ] Refinement can be disabled

### Overall Success:
- [ ] Generate pathway matches multi-agent pathway quality evaluation
- [ ] Quality scores are actionable (used for refinement)
- [ ] System is more robust and produces better terrain

