# Missing Components for Aesthetic Terrain Generation

## 🎯 Current State Analysis

Based on the ReAct logs and evaluation scores, here's what's working vs. what's missing:

### ✅ What Works:
1. **Narrative composer generates features** - Creates 5 features with proper types
2. **ReAct agent calls narrative tool** - Successfully uses `generate_narrative_composition`
3. **Quality rubric exists** - Comprehensive evaluation system with composition + texture metrics
4. **Splatmap generation** - Texture maps are generated from heightmaps
5. **Multi-agent workflow** - Separate workflow exists for iterative refinement

### ❌ Critical Gaps:

## 1. **NO ITERATIVE REFINEMENT LOOP** 🚨 CRITICAL

**Problem:** The ReAct agent generates actions **once** and stops. There's no feedback loop to improve quality.

**Current Flow:**
```
User Command → ReAct Agent → Narrative Tool → Actions → DONE
```

**What We Need:**
```
User Command → ReAct Agent → Generate Actions → Evaluate Quality → 
  → If quality < 0.8: Refine → Re-evaluate → Repeat until quality >= 0.8
```

**Missing Implementation:**
- No quality evaluation after action generation
- No refinement tools integrated into ReAct agent
- No iteration loop based on quality scores
- No stopping condition based on quality threshold

**Location:** `server/semantic/react_agent_v2.py` - `solve()` method stops after first successful generation

---

## 2. **QUALITY EVALUATION NOT INTEGRATED** 🚨 CRITICAL

**Problem:** Quality rubric exists (`evaluate_quality_rubric`) but is **never called** during ReAct execution.

**Current State:**
- Quality evaluation only happens in multi-agent workflow
- ReAct agent doesn't check if its output meets quality standards
- No feedback mechanism to guide improvements

**What We Need:**
```python
# After generating actions in ReAct agent:
actions = self._extract_actions_from_response(...)

# Evaluate quality
feature_metrics = compute_feature_metrics(actions)
texture_metrics = compute_texture_metrics(heightmap, splatmap)  # Need to render first!
quality_result = evaluate_quality_rubric(feature_metrics, texture_metrics)

if quality_result["overall_score"] < 0.8:
    # Refine based on warnings
    refinement_actions = self._refine_based_on_quality(actions, quality_result)
    actions = refinement_actions
```

**Missing:**
- Quality evaluation call in ReAct agent
- Rendering preview to get texture metrics
- Refinement logic based on quality warnings

---

## 3. **NO VISUAL FEEDBACK LOOP** 🚨 CRITICAL

**Problem:** The system doesn't render terrain and use visual output for critique/refinement.

**Current State:**
- Actions are generated without seeing the result
- No preview rendering during ReAct iterations
- No visual critique tools available to ReAct agent

**What We Need:**
```python
# Tool for ReAct agent:
def render_and_evaluate_terrain(
    actions: List[Dict],
    scene_state: Dict
) -> Dict:
    """
    Render terrain from actions and return:
    - Heightmap preview
    - Splatmap preview  
    - Quality metrics
    - Visual critique
    """
    # Apply actions to get heightmap/splatmap
    heightmap, splatmap = apply_actions(actions, scene_state)
    
    # Compute metrics
    feature_metrics = compute_feature_metrics(actions)
    texture_metrics = compute_texture_metrics(heightmap, splatmap)
    quality = evaluate_quality_rubric(feature_metrics, texture_metrics)
    
    # Optionally use Gemini for visual critique
    if gemini_available:
        visual_critique = critique_with_gemini(heightmap, splatmap, quality)
    
    return {
        "heightmap_preview": encode_preview(heightmap),
        "splatmap_preview": encode_preview(splatmap),
        "quality": quality,
        "visual_critique": visual_critique
    }
```

**Missing:**
- `render_and_evaluate_terrain` tool for ReAct agent
- Preview rendering capability
- Visual critique integration (Gemini multimodal)

---

## 4. **NARRATIVE COMPOSER DOESN'T ITERATE** ⚠️ IMPORTANT

**Problem:** `generate_narrative_composition` generates once and returns. No refinement based on quality.

**Current State:**
- Narrative composer generates features based on archetype
- No feedback loop to improve composition
- No quality-aware refinement

**What We Need:**
```python
def generate_narrative_composition_with_refinement(
    command: str,
    scene_state: Dict,
    max_iterations: int = 3,
    target_quality: float = 0.8
) -> Dict:
    """
    Generate narrative composition with iterative refinement.
    """
    iteration = 0
    best_actions = None
    best_score = 0.0
    
    while iteration < max_iterations:
        # Generate composition
        narrative = develop_terrain_narrative(command, scene_state)
        composition = plan_composition(narrative, constraints)
        actions = convert_composition_to_actions(composition)
        
        # Evaluate quality
        metrics = compute_feature_metrics(actions)
        quality = evaluate_aesthetic_quality(metrics)
        
        if quality["score"] >= target_quality:
            return {"actions": actions, "quality": quality}
        
        if quality["score"] > best_score:
            best_score = quality["score"]
            best_actions = actions
        
        # Refine based on warnings
        narrative = refine_narrative_composition(narrative, quality["warnings"])
        iteration += 1
    
    return {"actions": best_actions, "quality": {"score": best_score}}
```

**Missing:**
- Iterative refinement in narrative generation
- Quality-aware narrative refinement
- Integration with quality evaluation

---

## 5. **LOW QUALITY SCORES INDICATE MISSING FEATURES** ⚠️ IMPORTANT

**Current Scores:** `score=0.06 (comp=0.00, tex=0.12)`

**Analysis:**
- **Composition score = 0.00** → Features don't meet minimum requirements:
  - Need >= 4 features (currently generating 5, but may not be applied correctly)
  - Need >= 3 type diversity (may have duplicates)
  - Need >= 110 diagonal extent (features too close together)
  - Need >= 0.06 height std (not enough height variation)
  
- **Texture score = 0.12** → Texture metrics failing:
  - Coverage targets not met (grass/rock/sand/snow ranges)
  - Low entropy (texture distribution too concentrated)
  - Poor alignment (rock not on slopes, snow not on peaks, sand not in low areas)

**Root Causes:**
1. Features may not be applied to terrain correctly
2. Feature parameters (height, radius) may be too uniform
3. Splatmap generation may not be using feature-aware masks properly
4. No validation that features meet rubric requirements before returning

---

## 6. **MISSING REFINEMENT TOOLS FOR REACT AGENT** 🚨 CRITICAL

**Problem:** ReAct agent has no tools to refine based on quality feedback.

**Current Tools Available:**
- `generate_narrative_composition` - Generate initial composition
- `query_entities` - Query scene
- `calculate_position` - Spatial calculations
- `resolve_reference` - Reference resolution

**Missing Tools:**
- `evaluate_terrain_quality` - Evaluate current actions against rubric
- `refine_composition` - Refine actions based on quality warnings
- `render_preview` - Render and get visual feedback
- `adjust_feature_parameters` - Adjust heights/radii to meet requirements
- `add_supporting_features` - Add features to meet diversity/extent requirements

**What We Need:**
```python
# New tools for ReAct agent:

def evaluate_terrain_quality(
    actions: List[Dict],
    scene_state: Dict
) -> Dict:
    """Evaluate actions against quality rubric."""
    # Apply actions temporarily
    temp_state = copy.deepcopy(scene_state)
    apply_actions(actions, temp_state)
    
    # Render to get heightmap/splatmap
    heightmap, splatmap = build_final_terrain(temp_state)
    
    # Compute metrics
    feature_metrics = compute_feature_metrics(actions)
    texture_metrics = compute_texture_metrics(heightmap, splatmap)
    quality = evaluate_quality_rubric(feature_metrics, texture_metrics)
    
    return {
        "overall_score": quality["overall_score"],
        "composition_score": quality["categories"]["composition"]["score"],
        "texture_score": quality["categories"]["textures"]["score"],
        "warnings": quality["warnings"],
        "details": quality["categories"]
    }

def refine_composition(
    actions: List[Dict],
    quality_warnings: List[str],
    scene_state: Dict
) -> List[Dict]:
    """Refine actions based on quality warnings."""
    refined = actions.copy()
    
    for warning in quality_warnings:
        if "feature count" in warning.lower():
            # Add more features
            refined.extend(_generate_supporting_features(scene_state))
        elif "diversity" in warning.lower():
            # Add different feature types
            refined.extend(_add_diverse_features(scene_state))
        elif "extent" in warning.lower():
            # Spread features further apart
            refined = _adjust_positions_for_extent(refined)
        elif "height" in warning.lower():
            # Increase height variation
            refined = _adjust_heights_for_variation(refined)
    
    return refined
```

---

## 7. **NO INTEGRATION BETWEEN REACT AND MULTI-AGENT WORKFLOW** ⚠️ IMPORTANT

**Problem:** Two separate systems exist:
- ReAct agent (single-shot generation)
- Multi-agent workflow (iterative refinement with artist/critic/judge)

**What We Need:**
- Option 1: Integrate multi-agent workflow as a tool for ReAct agent
- Option 2: Use ReAct agent to generate initial actions, then pass to multi-agent for refinement
- Option 3: Make ReAct agent use multi-agent workflow internally when quality is low

**Recommended Approach:**
```python
# In ReAct agent solve():
actions = self._extract_actions_from_response(...)

# Evaluate quality
quality = evaluate_terrain_quality(actions, scene_state)

if quality["overall_score"] < 0.8:
    # Use multi-agent workflow for refinement
    from .multi_agent.workflow import run_multi_agent_terrain_design
    refined_result = run_multi_agent_terrain_design(
        command=user_command,
        initial_actions=actions,
        max_rounds=3
    )
    actions = refined_result["final_actions"]
```

---

## 8. **FEATURE PARAMETER TUNING MISSING** ⚠️ IMPORTANT

**Problem:** Feature parameters (height, radius, etc.) are generated but not tuned to meet quality requirements.

**Current State:**
- Narrative composer generates parameters based on archetype
- No validation that parameters create good composition
- No adjustment to meet rubric requirements

**What We Need:**
```python
def tune_feature_parameters(
    actions: List[Dict],
    target_metrics: Dict
) -> List[Dict]:
    """
    Adjust feature parameters to meet target metrics.
    
    Examples:
    - If height_std too low: Increase height variation
    - If extent too small: Increase radii or spread positions
    - If type_diversity too low: Ensure different types
    """
    tuned = []
    
    for action in actions:
        tuned_action = action.copy()
        
        # Adjust height for variation
        if target_metrics.get("height_std") < 0.06:
            tuned_action["modifiers"]["height"] = _adjust_for_variation(
                action["modifiers"]["height"],
                action["type"]
            )
        
        # Adjust radius for extent
        if target_metrics.get("extent_diagonal") < 110:
            tuned_action["modifiers"]["radius"] = _adjust_for_extent(
                action["modifiers"].get("radius", 50)
            )
        
        tuned.append(tuned_action)
    
    return tuned
```

---

## 9. **SPLATMAP GENERATION NOT USING FEATURE MASKS PROPERLY** ⚠️ IMPORTANT

**Problem:** Splatmap generation may not be receiving feature-aware masks (dune_mask, cliff_mask) correctly.

**Current State:**
- `generate_splatmap()` accepts `dune_mask` and `cliff_mask` parameters
- But these masks may not be generated/passed correctly from features
- Texture alignment metrics failing (rock not on slopes, etc.)

**What We Need:**
```python
# Ensure feature masks are generated and passed:
def build_final_terrain_with_masks(feature_state, base_biome_fn, seed: int):
    """Build terrain and ensure masks are generated."""
    builder = TerrainBuilder(base_biome_fn, seed)
    
    # Apply features and track masks
    dune_mask = np.zeros((512, 512), dtype=np.float32)
    cliff_mask = np.zeros((512, 512), dtype=np.float32)
    
    for feat in feature_state.list_features():
        stamp, masks = _apply_feature_to_builder(builder, feat, seed)
        
        if feat["type"] == "dunes":
            dune_mask = np.maximum(dune_mask, masks.get("dune_mask", 0))
        elif feat["type"] == "cliff":
            cliff_mask = np.maximum(cliff_mask, masks.get("cliff_mask", 0))
    
    heightmap = builder.get_heightmap()
    splatmap = generate_splatmap(heightmap, dune_mask, cliff_mask)
    
    return heightmap, splatmap, dune_mask, cliff_mask
```

---

## 10. **NO QUALITY-AWARE PROMPTING** ⚠️ IMPORTANT

**Problem:** ReAct agent prompts don't emphasize quality requirements or iterative improvement.

**What We Need:**
```python
# Enhanced system prompt:
"""
You are a terrain generation agent that creates BEAUTIFUL, HIGH-QUALITY terrain.

QUALITY REQUIREMENTS:
- Generate at least 4 features with 3+ different types
- Spread features across at least 110 units diagonal
- Create height variation (std >= 0.06)
- Ensure proper texture distribution (grass/rock/sand/snow)

WORKFLOW:
1. Generate initial composition using narrative tool
2. Evaluate quality using evaluate_terrain_quality tool
3. If quality < 0.8: Refine using refine_composition tool
4. Repeat until quality >= 0.8 or max iterations reached
"""
```

---

## 📋 Implementation Priority

### **Phase 1: Critical (Must Have)**
1. ✅ Add quality evaluation to ReAct agent after action generation
2. ✅ Add `evaluate_terrain_quality` tool for ReAct agent
3. ✅ Add `render_preview` tool to get heightmap/splatmap
4. ✅ Add iterative refinement loop in ReAct agent (quality < 0.8 → refine)

### **Phase 2: Important (Should Have)**
5. ✅ Add `refine_composition` tool based on quality warnings
6. ✅ Integrate multi-agent workflow as fallback for low quality
7. ✅ Add feature parameter tuning to meet rubric requirements
8. ✅ Ensure feature masks are passed to splatmap generation

### **Phase 3: Nice to Have**
9. ✅ Add Gemini visual critique integration
10. ✅ Add quality-aware prompting
11. ✅ Add narrative composer iterative refinement

---

## 🎯 Expected Outcome

After implementing these changes:

1. **Quality scores should improve from 0.06 → 0.80+**
2. **ReAct agent will iterate until quality threshold met**
3. **Features will meet composition requirements** (count, diversity, extent, height variation)
4. **Textures will align properly** (rock on slopes, snow on peaks, sand in low areas)
5. **System will produce aesthetically pleasing terrain consistently**

---

## 🔧 Next Steps

1. **Implement quality evaluation in ReAct agent**
2. **Add refinement tools**
3. **Add iterative loop with quality threshold**
4. **Test with quality tracking**
5. **Iterate until 80% quality consistently achieved**

