# Generate Pathway Analysis

## Question
Is the generate pathway using the full narrative layer terrain generation and quality evaluation layer?

## Answer Summary

**Narrative Layer**: ✅ **YES** - Used as PRIMARY pathway  
**Quality Evaluation Layer**: ⚠️ **PARTIAL** - Feature metrics only, not full texture-based rubric

---

## Code Flow Trace

### Entry Point
```
TerrainController.generate()
  ↓
TerrainService.generate_terrain()
  ↓
apply_actions() in terrain.py
```

### Command Parsing (orchestration.py:41-118)

The `parse_command_to_actions()` function tries parsers in this order:

1. **Direct actions** (if provided) → returns immediately
2. **Empty command** → returns empty list
3. **Narrative Pipeline** (PRIMARY PATHWAY) ← **THIS IS USED**
   ```python
   try:
       actions, metadata = run_narrative_pipeline(command, state)
       # Sets state["_debug_last_parser"] = "narrative"
       return actions
   ```
4. **SemanticParser** (fallback if narrative fails)
5. **CommandParser** (regex fallback)

### Narrative Pipeline Flow (semantic/narrative/utils.py:24-65)

When `run_narrative_pipeline()` is called:

```python
def run_narrative_pipeline(command, scene_state):
    # Step 1: Develop terrain narrative
    narrative = develop_terrain_narrative(command, scene_state)
    
    # Step 2: Generate feature composition from narrative
    composition = generate_from_narrative(narrative, scene_state, seed=seed)
    
    # Step 3: Convert composition to actions
    actions = composition_to_actions(composition)
    
    # Step 4: Evaluate quality (BEFORE terrain generation)
    features = [composition.focal_point, ...supporting_features, ...accent_features]
    feature_dicts = features_to_dicts(features)
    metrics = compute_feature_metrics(feature_dicts)  # Feature metrics only
    quality = evaluate_aesthetic_quality(metrics)      # Basic quality score
    
    return actions, metadata
```

**Key Functions:**
- `develop_terrain_narrative()` - Creates TerrainNarrative with archetype, story, constraints
- `generate_from_narrative()` - Converts narrative → FeatureComposition (typed Features)
- `composition_to_actions()` - Converts FeatureComposition → action dicts

### Terrain Generation (terrain.py:231-351)

After actions are parsed, `apply_actions()` executes:

```python
def apply_actions(cmd, state, ...):
    # Step 1: Parse command to actions (uses narrative pipeline)
    actions = parse_command_to_actions(cmd, state, direct_actions)
    
    # Step 2-10: Execute actions, build terrain
    # ... (removes/modifies existing, adds new features)
    
    # Step 11: Finalize terrain
    h, dune_mask_total, cliff_mask_total = builder.finalize()
    splat = builder.build_splatmap()
    
    # Step 12: Post-generation quality evaluation (PARTIAL)
    if updated_state.get("features"):
        metrics = compute_feature_metrics(updated_state["features"])
        quality = evaluate_aesthetic_quality(metrics)  # Feature metrics only
        # Stores in state["_last_narrative_meta"]
```

### Quality Evaluation Analysis

#### ✅ What IS Used:

1. **Feature Metrics** (before terrain generation):
   - Called in `run_narrative_pipeline()` (utils.py:50-51)
   - Evaluates: feature_count, type_diversity, extent, height_stats, radius_stats

2. **Feature Metrics** (after terrain generation):
   - Called in `apply_actions()` (terrain.py:345-346)
   - Same metrics as above, but on final feature set

#### ❌ What is NOT Used:

1. **Texture Metrics** - NOT computed after terrain generation:
   - `compute_texture_metrics()` exists but never called in generate pathway
   - Would evaluate: texture coverage, entropy, rock/snow/sand correlations

2. **Full Quality Rubric** - NOT evaluated after terrain generation:
   - `evaluate_quality_rubric()` exists but never called in generate pathway
   - Would evaluate: composition + texture quality together
   - Used in multi-agent workflow (`score_scene_plan_visual`) but not in standard generate

3. **Texture-based Quality Checks**:
   - No evaluation of texture alignment (rock on slopes, snow on peaks, sand in valleys)
   - No coverage entropy checks
   - No texture-height correlation validation

---

## Comparison: Generate vs Multi-Agent Pathway

### Standard Generate Pathway
```
Command → Narrative Pipeline → Actions → Terrain Generation → Feature Metrics Only
```

### Multi-Agent Pathway (design_with_multi_agent)
```
Command → Multi-Agent Workflow → score_scene_plan_visual() → 
  → render_scene_preview() (generates heightmap/splatmap) →
  → compute_feature_metrics() + compute_texture_metrics(heightmap, splatmap) + 
  → evaluate_quality_rubric(feature_metrics, texture_metrics) ← FULL QUALITY EVALUATION
  → summarize_quality_rubric() + optional Gemini feedback
```

**Key Difference**: Multi-agent workflow actually renders the terrain first, then evaluates both feature AND texture metrics together.

---

## Findings

### ✅ Narrative Layer: FULLY USED
- The narrative layer IS the primary pathway for natural language commands
- Full pipeline: `develop_terrain_narrative()` → `generate_from_narrative()` → `composition_to_actions()`
- Creates rich geological narratives with archetypes, stories, constraints
- Generates typed Feature compositions with spatial reasoning

### ⚠️ Quality Evaluation Layer: PARTIALLY USED

**Used:**
- Feature-based metrics (count, diversity, extent, height variance)
- Basic aesthetic quality scoring
- Evaluated both BEFORE and AFTER terrain generation

**Missing:**
- Texture-based metrics (coverage, entropy, correlations)
- Full quality rubric evaluation (composition + textures together)
- Texture-height alignment validation
- Post-generation quality feedback loop

---

## Recommendations

To use the **full quality evaluation layer** in the generate pathway:

1. **Add texture metrics computation** after terrain generation:
   ```python
   # In apply_actions(), after splatmap is built:
   texture_metrics = compute_texture_metrics(h, splat)
   ```

2. **Add full quality rubric evaluation**:
   ```python
   # Combine feature + texture metrics:
   quality_rubric = evaluate_quality_rubric(metrics, texture_metrics)
   ```

3. **Store quality results** in state for potential refinement loops

4. **Consider quality-based refinement** if score is below threshold

---

## Code References

- **Narrative Pipeline**: `server/semantic/narrative/utils.py:24-65`
- **Command Parsing**: `server/orchestration.py:41-118`
- **Terrain Generation**: `server/terrain.py:231-351`
- **Quality Evaluation**: `server/semantic/evaluation.py`
- **Full Quality Example**: `server/semantic/multi_agent/tools.py:77-113` (score_scene_plan_visual)

