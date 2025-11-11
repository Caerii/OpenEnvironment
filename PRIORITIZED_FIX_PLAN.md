# Prioritized Fix Plan: Connecting Existing Components

## Executive Summary

**Key Finding**: Most quality evaluation infrastructure **already exists** and is **fully implemented**. The problem is simply that it's **not hooked up** to the generate pathway. This makes fixes **much easier** than implementing from scratch.

**Strategy**: 
1. **Phase 1 (Quick Wins)**: Hook up existing quality evaluation (1-2 days)
2. **Phase 2 (Medium Effort)**: Add quality-based refinement loop (3-5 days)
3. **Phase 3 (New Features)**: Complete missing composition features (1-2 weeks)

---

## Phase 1: Quick Wins - Hook Up Existing Quality Evaluation 🔴 HIGH PRIORITY

### 1.1 Add Texture Metrics to Generate Pathway
**Status**: ✅ Function exists and works  
**Effort**: 30 minutes  
**Impact**: 🔴 CRITICAL - Enables full quality evaluation

**What Exists**:
- `compute_texture_metrics(heightmap, splatmap)` - Complete implementation
- Returns: coverage, entropy, correlations (rock/slope, snow/height, sand/low)

**What's Missing**: Just needs to be called after terrain generation

**Fix Location**: `server/terrain.py:apply_actions()` after line 325

**Implementation**:
```python
# After terrain generation (line 325):
h, dune_mask_total, cliff_mask_total = builder.finalize()
splat = builder.build_splatmap()

# ADD THIS:
from .semantic.evaluation import compute_texture_metrics, evaluate_quality_rubric

# Compute texture metrics
texture_metrics = compute_texture_metrics(h, splat)

# Combine with feature metrics for full quality rubric
if updated_state.get("features"):
    feature_metrics = compute_feature_metrics(updated_state["features"])
    quality_rubric = evaluate_quality_rubric(feature_metrics, texture_metrics)
    
    # Store comprehensive quality results
    meta = updated_state.setdefault("_last_narrative_meta", {})
    meta["metrics"] = feature_metrics
    meta["texture_metrics"] = texture_metrics
    meta["quality_rubric"] = quality_rubric
    meta["quality"] = {
        "overall_score": quality_rubric["overall_score"],
        "composition_score": quality_rubric["categories"]["composition"]["score"],
        "texture_score": quality_rubric["categories"]["textures"]["score"],
        "warnings": quality_rubric["warnings"]
    }
```

**Testing**: 
- Verify texture metrics computed correctly
- Verify quality rubric includes both composition and texture scores
- Check that warnings are generated for quality issues

---

### 1.2 Remove Duplicate Quality Evaluation
**Status**: ⚠️ Redundant computation  
**Effort**: 15 minutes  
**Impact**: 🟡 MEDIUM - Performance improvement

**Problem**: Quality evaluated twice:
1. In `run_narrative_pipeline()` (before terrain generation)
2. In `apply_actions()` (after terrain generation)

**Fix**: 
- Keep evaluation in `apply_actions()` (has texture metrics)
- Remove from `run_narrative_pipeline()` OR make it optional
- Pass quality from narrative pipeline to avoid recomputation

**Implementation**:
```python
# In run_narrative_pipeline() - make quality evaluation optional:
def run_narrative_pipeline(
    command: str,
    scene_state: Dict[str, Any] | None,
    evaluate_quality: bool = False  # NEW: optional
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # ... existing code ...
    
    if evaluate_quality:
        feature_dicts = features_to_dicts(features)
        metrics = compute_feature_metrics(feature_dicts)
        quality = evaluate_aesthetic_quality(metrics)
        metadata["metrics"] = metrics
        metadata["quality"] = quality
    # Otherwise skip - will be evaluated after terrain generation
```

**Testing**: Verify no duplicate computation, quality still available

---

### 1.3 Store Quality Results in State
**Status**: ⚠️ Partially done  
**Effort**: 15 minutes  
**Impact**: 🟡 MEDIUM - Enables quality-based decisions

**Current**: Quality stored in `_last_narrative_meta` but not easily accessible

**Fix**: Make quality results part of standard state structure

**Implementation**:
```python
# In apply_actions(), after quality evaluation:
updated_state["quality"] = {
    "overall_score": quality_rubric["overall_score"],
    "composition": quality_rubric["categories"]["composition"],
    "textures": quality_rubric["categories"]["textures"],
    "warnings": quality_rubric["warnings"],
    "timestamp": time.time()
}
```

**Testing**: Verify quality accessible via `state["quality"]`

---

## Phase 2: Medium Effort - Quality-Based Refinement Loop 🟡 MEDIUM PRIORITY

### 2.1 Extract Refinement Logic from ReAct Agent
**Status**: ✅ Logic exists in `react_agent_v2._evaluate_and_refine()`  
**Effort**: 2-3 hours  
**Impact**: 🔴 HIGH - Enables automatic quality improvement

**What Exists**:
- Complete refinement loop in `react_agent_v2.py:291-400`
- Evaluates quality, checks threshold, refines based on warnings
- Has retry logic and quality decrease detection

**What's Missing**: 
- Not connected to standard generate pathway
- Depends on tool executor (multi-agent specific)
- Needs to work with narrative pipeline directly

**Fix**: Create standalone refinement function

**Implementation**:
```python
# New file: server/semantic/narrative/refinement.py

def refine_composition_by_quality(
    composition: FeatureComposition,
    narrative: TerrainNarrative,
    scene_state: Dict,
    initial_quality: Dict[str, Any],
    seed: int
) -> Tuple[FeatureComposition, Dict[str, Any]]:
    """
    Refine composition based on quality warnings.
    
    Args:
        composition: Initial composition
        narrative: Terrain narrative with quality targets
        scene_state: Current scene state
        initial_quality: Quality evaluation results
        seed: Random seed
        
    Returns:
        Tuple of (refined_composition, refinement_info)
    """
    from .generation import generate_from_narrative
    from .converters import composition_to_actions
    from ..evaluation import compute_feature_metrics, evaluate_aesthetic_quality
    
    target_score = narrative.target_coherence
    max_iterations = narrative.max_refinement_iterations
    current_score = initial_quality.get("overall_score", 0.0)
    
    refinement_info = {
        "initial_score": current_score,
        "iterations": 0,
        "changes": []
    }
    
    if current_score >= target_score:
        return composition, refinement_info
    
    warnings = initial_quality.get("warnings", [])
    current_composition = composition
    
    for iteration in range(max_iterations):
        if not warnings:
            break
            
        # Apply refinements based on warnings
        refined = _apply_quality_refinements(
            current_composition,
            warnings,
            narrative,
            seed + iteration
        )
        
        # Re-evaluate quality
        actions = composition_to_actions(refined)
        features = _extract_features_from_composition(refined)
        feature_dicts = features_to_dicts(features)
        metrics = compute_feature_metrics(feature_dicts)
        quality = evaluate_aesthetic_quality(metrics)
        
        new_score = quality.get("score", 0.0)
        
        if new_score >= target_score:
            refinement_info["final_score"] = new_score
            refinement_info["iterations"] = iteration + 1
            return refined, refinement_info
        
        if new_score < current_score * 0.9:  # Quality decreased
            break  # Revert to previous
        
        current_composition = refined
        current_score = new_score
        warnings = quality.get("warnings", [])
        refinement_info["iterations"] = iteration + 1
    
    refinement_info["final_score"] = current_score
    return current_composition, refinement_info


def _apply_quality_refinements(
    composition: FeatureComposition,
    warnings: List[str],
    narrative: TerrainNarrative,
    seed: int
) -> FeatureComposition:
    """Apply specific refinements based on quality warnings."""
    # Parse warnings and apply fixes
    # Examples:
    # - "Low feature count" → add more supporting features
    # - "Feature diversity low" → add different feature types
    # - "Spatial spread limited" → spread features further apart
    # - "Height variation minimal" → vary heights more
    # ... (implementation details)
```

**Integration Point**: `server/terrain.py:apply_actions()` or `server/semantic/narrative/utils.py:run_narrative_pipeline()`

**Testing**:
- Test refinement loop with low-quality compositions
- Verify quality improves after refinement
- Test that it respects max_iterations
- Test that it stops when threshold reached

---

### 2.2 Connect Refinement to Generate Pathway
**Status**: ⚠️ Not connected  
**Effort**: 1-2 hours  
**Impact**: 🔴 HIGH - Makes refinement automatic

**Fix Location**: `server/semantic/narrative/utils.py:run_narrative_pipeline()`

**Implementation**:
```python
def run_narrative_pipeline(
    command: str,
    scene_state: Dict[str, Any] | None,
    enable_refinement: bool = True  # NEW: enable/disable refinement
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # ... existing narrative development ...
    
    composition = generate_from_narrative(narrative, scene_state, seed=seed)
    
    # Evaluate initial quality
    features = _extract_features_from_composition(composition)
    feature_dicts = features_to_dicts(features)
    metrics = compute_feature_metrics(feature_dicts)
    quality = evaluate_aesthetic_quality(metrics)
    
    # Refine if enabled and below threshold
    if enable_refinement and quality.get("score", 0.0) < narrative.target_coherence:
        from .refinement import refine_composition_by_quality
        composition, refinement_info = refine_composition_by_quality(
            composition, narrative, scene_state, quality, seed
        )
        metadata["refinement"] = refinement_info
    
    actions = composition_to_actions(composition)
    # ... rest of function ...
```

**Testing**: 
- Verify refinement runs when quality below threshold
- Verify refinement can be disabled
- Test with various quality scores

---

### 2.3 Add Quality Threshold Configuration
**Status**: ⚠️ Hardcoded  
**Effort**: 30 minutes  
**Impact**: 🟡 MEDIUM - Makes system configurable

**Current**: `target_coherence=0.8` hardcoded in `narrative_dev.py:344`

**Fix**: Make configurable via environment variable or config file

**Implementation**:
```python
# In narrative_dev.py:
import os
DEFAULT_TARGET_COHERENCE = float(os.environ.get("TERRAIN_TARGET_COHERENCE", "0.8"))
DEFAULT_MAX_REFINEMENT_ITERATIONS = int(os.environ.get("TERRAIN_MAX_REFINEMENT_ITERATIONS", "5"))

# Use in develop_terrain_narrative():
target_coherence = DEFAULT_TARGET_COHERENCE
max_refinement_iterations = DEFAULT_MAX_REFINEMENT_ITERATIONS
```

**Testing**: Verify environment variables work, defaults used if not set

---

## Phase 3: Complete Missing Features 🟢 LOW PRIORITY (But Important)

### 3.1 Implement Background Features
**Status**: 🔴 TODO stub  
**Effort**: 4-6 hours  
**Impact**: 🟡 MEDIUM - Completes composition

**Current**: `background_features=[]` in `generation.py:175`

**Implementation Plan**:
```python
def _generate_background_features(
    narrative: TerrainNarrative,
    focal_point: Feature,
    supporting_features: List[Feature],
    rng: random.Random,
    seed: int
) -> List[Feature]:
    """
    Generate background features (distant, atmospheric).
    
    Background features:
    - Further from focal point (distance > 200)
    - Lower height/depth (subtle)
    - More spread out
    - Atmospheric (clouds, distant mountains, horizon elements)
    """
    background_features = []
    
    # Determine background types from archetype
    background_types = _get_background_types(narrative.archetype)
    
    # Generate 2-4 background features
    n_background = rng.randint(2, 4)
    
    for i in range(n_background):
        bg_type = rng.choice(background_types)
        
        # Place far from focal point
        distance = rng.uniform(200, 300)
        angle = rng.uniform(0, 360)
        x = int(focal_point.position.x + distance * _cos_deg(angle))
        y = int(focal_point.position.y + distance * _sin_deg(angle))
        
        # Clamp to terrain bounds
        x = max(50, min(462, x))
        y = max(50, min(462, y))
        
        # Generate with subtle parameters
        generator = FeatureRegistry._generators.get(bg_type)
        if generator:
            modifiers = _extract_modifiers_from_narrative(narrative, "background")
            modifiers["height"] = modifiers.get("height", 0.3) * 0.6  # Reduce height
            modifiers["radius"] = modifiers.get("radius", 50) * 0.8   # Reduce radius
            
            feature = generator.create_feature(x, y, modifiers, seed + 1000 + i)
            feature = _ensure_feature_instance(feature)
            if feature:
                background_features.append(feature)
    
    return background_features
```

**Integration**: Add to `generate_from_narrative()` after accent features

**Testing**: Verify background features placed correctly, don't interfere with focal

---

### 3.2 Implement Foreground Features
**Status**: 🔴 TODO stub  
**Effort**: 4-6 hours  
**Impact**: 🟡 MEDIUM - Completes composition

**Similar to background but closer to camera/viewer**

**Implementation Plan**:
```python
def _generate_foreground_features(
    narrative: TerrainNarrative,
    focal_point: Feature,
    rng: random.Random,
    seed: int
) -> List[Feature]:
    """
    Generate foreground features (close, detailed).
    
    Foreground features:
    - Close to focal point (distance < 100)
    - Small, detailed
    - Add visual interest and depth
    - Examples: small rocks, vegetation, terrain details
    """
    # Similar structure to background but different placement logic
    # ... (implementation)
```

**Integration**: Add to `generate_from_narrative()` after accent features

---

### 3.3 Implement Depth Layering
**Status**: 🔴 TODO stub  
**Effort**: 6-8 hours  
**Impact**: 🟡 MEDIUM - Promised feature

**Current**: `depth_layers=[]` but `depth_layers_needed` calculated in narrative

**Implementation Plan**:
```python
def _generate_depth_layers(
    composition: FeatureComposition,
    narrative: TerrainNarrative,
    rng: random.Random
) -> List[Dict[str, Any]]:
    """
    Organize features into depth layers for visual hierarchy.
    
    Returns:
        List of depth layer dicts: [{"z_order": 1, "feature_ids": [...]}, ...]
    """
    depth_layers = []
    num_layers = narrative.depth_layers_needed
    
    # Categorize features by distance from focal point
    all_features = []
    if composition.focal_point:
        all_features.append(("focal", composition.focal_point))
    all_features.extend([("supporting", f) for f in composition.supporting_features])
    all_features.extend([("accent", f) for f in composition.accent_features])
    
    # Sort by distance from focal
    if composition.focal_point:
        focal_pos = composition.focal_point.position
        all_features.sort(key=lambda x: _distance(
            x[1].position.x, x[1].position.y,
            focal_pos.x, focal_pos.y
        ))
    
    # Assign to layers
    features_per_layer = len(all_features) // num_layers
    for layer_idx in range(num_layers):
        start_idx = layer_idx * features_per_layer
        end_idx = start_idx + features_per_layer if layer_idx < num_layers - 1 else len(all_features)
        
        layer_features = all_features[start_idx:end_idx]
        feature_ids = [f[1].id for f in layer_features if hasattr(f[1], 'id')]
        
        depth_layers.append({
            "z_order": layer_idx + 1,
            "feature_ids": feature_ids,
            "feature_types": [f[0] for f in layer_features]
        })
    
    return depth_layers
```

**Integration**: Add to `generate_from_narrative()` after composition creation

---

### 3.4 Implement Negative Space
**Status**: 🔴 TODO stub  
**Effort**: 4-6 hours  
**Impact**: 🟡 MEDIUM - Important for aesthetics

**Current**: `negative_space_importance` calculated but not used

**Implementation Plan**:
```python
def _generate_negative_space_zones(
    composition: FeatureComposition,
    narrative: TerrainNarrative,
    rng: random.Random
) -> List[Tuple[int, int, int, int]]:
    """
    Identify negative space zones (empty areas for visual breathing room).
    
    Returns:
        List of (x_min, x_max, y_min, y_max) tuples
    """
    importance = narrative.negative_space_importance
    
    if importance < 0.3:
        return []  # Low importance, skip
    
    # Find empty areas (no features)
    all_features = []
    if composition.focal_point:
        all_features.append(composition.focal_point)
    all_features.extend(composition.supporting_features)
    all_features.extend(composition.accent_features)
    
    # Calculate feature coverage
    feature_coverage = _calculate_feature_coverage(all_features)
    
    # Find largest empty rectangles
    negative_zones = _find_empty_zones(feature_coverage, importance)
    
    return negative_zones
```

**Integration**: Add to `generate_from_narrative()` after composition creation

---

## Phase 4: Code Quality Improvements 🟢 LOW PRIORITY

### 4.1 Fix Import Hell
**Status**: ⚠️ Complex import chains  
**Effort**: 2-3 hours  
**Impact**: 🟡 MEDIUM - Maintainability

**Fix**: Consolidate imports, use proper package structure

### 4.2 Fix Type Conversion Functions
**Status**: ⚠️ Duplicate functions  
**Effort**: 1-2 hours  
**Impact**: 🟡 MEDIUM - Consistency

**Fix**: Consolidate `_ensure_feature()` and `_ensure_feature_instance()`

### 4.3 Remove Dynamic Module Loading
**Status**: ⚠️ Bypasses import system  
**Effort**: 2-3 hours  
**Impact**: 🟡 MEDIUM - Testability

**Fix**: Use normal imports, handle missing modules gracefully

---

## Priority Ranking Summary

### 🔴 CRITICAL (Do First - 1-2 days)
1. **Hook up texture metrics** (30 min) - Enables full quality evaluation
2. **Add quality-based refinement loop** (3-5 hours) - Automatic quality improvement
3. **Connect refinement to generate pathway** (1-2 hours) - Makes refinement work

### 🟡 HIGH PRIORITY (Do Next - 3-5 days)
4. **Remove duplicate quality evaluation** (15 min) - Performance
5. **Store quality results properly** (15 min) - Enables quality-based decisions
6. **Add quality threshold configuration** (30 min) - Configurability

### 🟢 MEDIUM PRIORITY (Do Later - 1-2 weeks)
7. **Implement background features** (4-6 hours) - Completes composition
8. **Implement foreground features** (4-6 hours) - Completes composition
9. **Implement depth layering** (6-8 hours) - Promised feature
10. **Implement negative space** (4-6 hours) - Important for aesthetics

### ⚪ LOW PRIORITY (Technical Debt - When Time Permits)
11. Fix import hell
12. Fix type conversion functions
13. Remove dynamic module loading

---

## Implementation Strategy

### Week 1: Quick Wins
- **Day 1**: Hook up texture metrics + remove duplicate evaluation
- **Day 2**: Add refinement loop + connect to pathway
- **Day 3**: Testing and bug fixes

### Week 2: Complete Features
- **Days 4-5**: Background and foreground features
- **Days 6-7**: Depth layering and negative space

### Week 3: Polish
- **Days 8-9**: Code quality improvements
- **Day 10**: Documentation and testing

---

## Success Metrics

### Phase 1 Success:
- ✅ Texture metrics computed for all generations
- ✅ Full quality rubric evaluated (composition + textures)
- ✅ Quality scores stored in state
- ✅ No duplicate quality evaluation

### Phase 2 Success:
- ✅ Refinement loop runs when quality below threshold
- ✅ Quality improves after refinement iterations
- ✅ Respects max_iterations and target_coherence
- ✅ Refinement can be enabled/disabled

### Phase 3 Success:
- ✅ Background features generated and placed correctly
- ✅ Foreground features generated and placed correctly
- ✅ Depth layers assigned to features
- ✅ Negative space zones identified

---

## Risk Assessment

### Low Risk (Safe to Do):
- Hooking up texture metrics (just adding function calls)
- Removing duplicate evaluation (performance improvement)
- Storing quality results (data structure changes)

### Medium Risk (Needs Testing):
- Refinement loop (complex logic, needs thorough testing)
- Background/foreground features (new generation logic)

### High Risk (Needs Careful Design):
- Depth layering (affects visual output)
- Negative space (may conflict with feature placement)

---

## Dependencies

### Phase 1 Dependencies:
- None - all functions exist

### Phase 2 Dependencies:
- Phase 1 complete (needs quality evaluation working)

### Phase 3 Dependencies:
- Phase 1 complete (needs quality evaluation for testing)
- Can be done in parallel with Phase 2

---

## Notes

1. **Most work is connecting existing pieces** - not implementing new features
2. **Quality evaluation is 90% done** - just needs to be called
3. **Refinement logic exists** - just needs extraction and integration
4. **Missing features are well-defined** - clear implementation path

**Estimated Total Effort**: 
- Phase 1: 1-2 days
- Phase 2: 3-5 days  
- Phase 3: 1-2 weeks
- **Total: 2-3 weeks** for complete implementation

