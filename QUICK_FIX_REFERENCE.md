# Quick Fix Reference: Exact Code Changes

## Phase 1: Hook Up Quality Evaluation (30 minutes)

### Fix 1: Add Texture Metrics to `apply_actions()`

**File**: `server/terrain.py`  
**Location**: After line 325 (after `splat = builder.build_splatmap()`)

**Add this code**:
```python
# After line 325:
splat = builder.build_splatmap()

# ADD THESE IMPORTS at top of file (around line 40):
from .semantic.evaluation import compute_texture_metrics, evaluate_quality_rubric, summarize_quality_rubric

# ADD THIS CODE after splatmap generation:
# Compute comprehensive quality metrics
if updated_state.get("features"):
    # Feature metrics (already computed, but ensure we have them)
    feature_metrics = compute_feature_metrics(updated_state["features"])
    
    # Texture metrics (NEW - this was missing!)
    texture_metrics = compute_texture_metrics(h, splat)
    
    # Full quality rubric (NEW - combines feature + texture)
    quality_rubric = evaluate_quality_rubric(feature_metrics, texture_metrics)
    
    # Store comprehensive quality results
    meta = updated_state.setdefault("_last_narrative_meta", {})
    meta["metrics"] = feature_metrics
    meta["texture_metrics"] = texture_metrics  # NEW
    meta["quality_rubric"] = quality_rubric    # NEW
    meta["quality"] = {
        "overall_score": quality_rubric["overall_score"],
        "composition_score": quality_rubric["categories"]["composition"]["score"],
        "texture_score": quality_rubric["categories"]["textures"]["score"],
        "warnings": quality_rubric["warnings"]
    }
    
    # Also store at top level for easy access
    updated_state["quality"] = {
        "overall_score": quality_rubric["overall_score"],
        "composition": quality_rubric["categories"]["composition"],
        "textures": quality_rubric["categories"]["textures"],
        "warnings": quality_rubric["warnings"],
        "timestamp": time.time()
    }
```

**Before** (line 344-349):
```python
if updated_state.get("features"):
    metrics = compute_feature_metrics(updated_state["features"])
    quality = evaluate_aesthetic_quality(metrics)
    meta = updated_state.setdefault("_last_narrative_meta", {})
    meta.setdefault("metrics", metrics)
    meta.setdefault("quality", quality)
```

**After** (replace with above code):
```python
# Full quality evaluation with texture metrics
if updated_state.get("features"):
    feature_metrics = compute_feature_metrics(updated_state["features"])
    texture_metrics = compute_texture_metrics(h, splat)  # NEW!
    quality_rubric = evaluate_quality_rubric(feature_metrics, texture_metrics)  # NEW!
    
    # Store comprehensive results
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
    
    updated_state["quality"] = {
        "overall_score": quality_rubric["overall_score"],
        "composition": quality_rubric["categories"]["composition"],
        "textures": quality_rubric["categories"]["textures"],
        "warnings": quality_rubric["warnings"],
        "timestamp": time.time()
    }
```

---

### Fix 2: Remove Duplicate Quality Evaluation

**File**: `server/semantic/narrative/utils.py`  
**Location**: Lines 49-51 (in `run_narrative_pipeline()`)

**Option A: Make it optional** (Recommended):
```python
def run_narrative_pipeline(
    command: str,
    scene_state: Dict[str, Any] | None,
    evaluate_quality_preview: bool = False  # NEW parameter
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # ... existing code ...
    
    actions = composition_to_actions(composition)
    if not actions:
        return [], {}
    
    # Only evaluate quality if requested (will be evaluated after terrain generation anyway)
    if evaluate_quality_preview:
        features = []
        if composition.focal_point:
            features.append(composition.focal_point)
        features.extend(composition.supporting_features)
        features.extend(composition.accent_features)
        
        feature_dicts = features_to_dicts(features)
        metrics = compute_feature_metrics(feature_dicts)
        quality = evaluate_aesthetic_quality(metrics)
        
        metadata["metrics"] = metrics
        metadata["quality"] = quality
    else:
        # Skip quality evaluation - will be done after terrain generation with texture metrics
        metadata["metrics"] = None
        metadata["quality"] = None
    
    return actions, metadata
```

**Option B: Remove it entirely** (Simpler):
```python
# Remove lines 43-51, replace with:
metadata: Dict[str, Any] = {
    "archetype": narrative.archetype.name,
    "aesthetic_goals": [goal.value for goal in narrative.aesthetic_goals],
    "mood": narrative.mood,
    "story": narrative.story,
    "focal_type": narrative.hero_feature_type,
    "supporting_types": narrative.supporting_feature_types,
    "accent_types": narrative.accent_feature_types,
    # Quality will be evaluated after terrain generation with texture metrics
}
```

**Recommendation**: Use Option B (simpler, avoids duplication)

---

## Phase 2: Add Quality-Based Refinement (3-5 hours)

### Fix 3: Create Refinement Module

**New File**: `server/semantic/narrative/refinement.py`

**Create this file**:
```python
"""Quality-based composition refinement."""
import logging
from typing import Dict, List, Tuple, Any
import random

from .types import FeatureComposition, TerrainNarrative
from .generation import generate_from_narrative, _ensure_feature_instance
from .converters import composition_to_actions
from ..evaluation import (
    compute_feature_metrics,
    evaluate_aesthetic_quality,
    features_to_dicts
)
from ...engine.feature_registry import FeatureRegistry

logger = logging.getLogger(__name__)


def refine_composition_by_quality(
    composition: FeatureComposition,
    narrative: TerrainNarrative,
    scene_state: Dict,
    initial_quality: Dict[str, Any],
    seed: int
) -> Tuple[FeatureComposition, Dict[str, Any]]:
    """
    Refine composition based on quality warnings.
    
    Returns:
        Tuple of (refined_composition, refinement_info)
    """
    target_score = narrative.target_coherence
    max_iterations = narrative.max_refinement_iterations
    current_score = initial_quality.get("overall_score", 0.0)
    
    refinement_info = {
        "initial_score": current_score,
        "final_score": current_score,
        "iterations": 0,
        "changes": []
    }
    
    # If already meets target, no refinement needed
    if current_score >= target_score:
        logger.info(f"Quality already meets target: {current_score:.3f} >= {target_score}")
        return composition, refinement_info
    
    warnings = initial_quality.get("warnings", [])
    if not warnings:
        logger.info("No quality warnings to address")
        return composition, refinement_info
    
    current_composition = composition
    rng = random.Random(seed)
    
    logger.info(f"Refining composition: {current_score:.3f} < {target_score}, {len(warnings)} warnings")
    
    for iteration in range(max_iterations):
        if not warnings:
            break
        
        # Apply refinements based on warnings
        refined = _apply_quality_refinements(
            current_composition,
            warnings,
            narrative,
            rng,
            seed + iteration
        )
        
        # Re-evaluate quality (feature metrics only - texture requires terrain generation)
        features = _extract_features_from_composition(refined)
        feature_dicts = features_to_dicts(features)
        metrics = compute_feature_metrics(feature_dicts)
        quality = evaluate_aesthetic_quality(metrics)
        
        new_score = quality.get("score", 0.0)
        new_warnings = quality.get("warnings", [])
        
        logger.info(f"Refinement iteration {iteration + 1}: score {new_score:.3f}")
        
        # Check if we've improved
        if new_score >= target_score:
            refinement_info["final_score"] = new_score
            refinement_info["iterations"] = iteration + 1
            refinement_info["changes"].append(f"Reached target score: {new_score:.3f}")
            logger.info(f"Quality threshold reached: {new_score:.3f} >= {target_score}")
            return refined, refinement_info
        
        # If quality decreased significantly, stop
        if new_score < current_score * 0.9:
            logger.warning(f"Quality decreased: {new_score:.3f} < {current_score * 0.9:.3f}, stopping")
            break
        
        # Continue refining
        current_composition = refined
        current_score = new_score
        warnings = new_warnings
        refinement_info["iterations"] = iteration + 1
    
    refinement_info["final_score"] = current_score
    return current_composition, refinement_info


def _extract_features_from_composition(composition: FeatureComposition) -> List:
    """Extract all features from composition."""
    features = []
    if composition.focal_point:
        features.append(composition.focal_point)
    features.extend(composition.supporting_features)
    features.extend(composition.accent_features)
    features.extend(composition.background_features)
    features.extend(composition.foreground_features)
    return features


def _apply_quality_refinements(
    composition: FeatureComposition,
    warnings: List[str],
    narrative: TerrainNarrative,
    rng: random.Random,
    seed: int
) -> FeatureComposition:
    """Apply specific refinements based on quality warnings."""
    from .generation import _generate_supporting_features, _generate_accent_features
    
    refined = composition
    changes = []
    
    # Parse warnings and apply fixes
    warning_lower = [w.lower() for w in warnings]
    
    # "Low feature count" → add more supporting features
    if any("feature count" in w or "sparse" in w for w in warning_lower):
        if len(refined.supporting_features) < 4:
            logger.debug("Adding supporting features for low feature count")
            new_supporting = _generate_supporting_features(
                narrative,
                {"supporting": narrative.supporting_feature_types},
                refined.focal_point,
                rng,
                seed + 1000
            )
            refined.supporting_features.extend(new_supporting)
            changes.append(f"Added {len(new_supporting)} supporting features")
    
    # "Feature diversity low" → add different feature types
    if any("diversity" in w or "contrast" in w for w in warning_lower):
        existing_types = {refined.focal_point.type if refined.focal_point else None}
        existing_types.update(f.type for f in refined.supporting_features)
        existing_types.update(f.type for f in refined.accent_features)
        existing_types.discard(None)
        
        # Find a type we don't have
        all_types = set(narrative.supporting_feature_types + narrative.accent_feature_types)
        missing_types = all_types - existing_types
        
        if missing_types:
            new_type = rng.choice(list(missing_types))
            logger.debug(f"Adding {new_type} for diversity")
            # Add as accent feature
            from .generation import _spawn_feature_near
            new_feature = _spawn_feature_near(
                new_type,
                refined.focal_point,
                narrative,
                rng,
                seed + 2000,
                distance_range=(120, 180),
                random_position=True
            )
            if new_feature:
                refined.accent_features.append(new_feature)
                changes.append(f"Added {new_type} for diversity")
    
    # "Spatial spread limited" → spread features further apart
    if any("spread" in w or "coverage" in w or "cramped" in w for w in warning_lower):
        # Move supporting features further from focal
        if refined.focal_point and refined.supporting_features:
            focal_pos = refined.focal_point.position
            for feat in refined.supporting_features:
                # Increase distance from focal
                dx = feat.position.x - focal_pos.x
                dy = feat.position.y - focal_pos.y
                distance = (dx*dx + dy*dy)**0.5
                if distance < 100:
                    # Move further away
                    scale = 1.5
                    feat.position.x = int(focal_pos.x + dx * scale)
                    feat.position.y = int(focal_pos.y + dy * scale)
                    # Clamp to bounds
                    feat.position.x = max(50, min(462, feat.position.x))
                    feat.position.y = max(50, min(462, feat.position.y))
            changes.append("Spread features further apart")
    
    # "Height variation minimal" → vary heights more
    if any("height" in w and "variation" in w for w in warning_lower):
        # Increase height variance in supporting features
        for feat in refined.supporting_features:
            if feat.parameters.height is not None:
                # Vary heights more
                feat.parameters.height = rng.uniform(0.3, 0.9)
            elif feat.parameters.depth is not None:
                feat.parameters.depth = rng.uniform(0.2, 0.6)
        changes.append("Increased height variation")
    
    return refined
```

---

### Fix 4: Connect Refinement to Pipeline

**File**: `server/semantic/narrative/utils.py`  
**Location**: After line 38 (after `composition = generate_from_narrative(...)`)

**Add this code**:
```python
composition = generate_from_narrative(narrative, scene_state, seed=seed)

# NEW: Quality-based refinement
from .refinement import refine_composition_by_quality

# Evaluate initial quality
features = []
if composition.focal_point:
    features.append(composition.focal_point)
features.extend(composition.supporting_features)
features.extend(composition.accent_features)

feature_dicts = features_to_dicts(features)
metrics = compute_feature_metrics(feature_dicts)
quality = evaluate_aesthetic_quality(metrics)

# Refine if below threshold
if quality.get("score", 0.0) < narrative.target_coherence:
    logger.info(f"Quality below threshold ({quality.get('score', 0.0):.3f} < {narrative.target_coherence}), refining...")
    composition, refinement_info = refine_composition_by_quality(
        composition, narrative, scene_state, quality, seed
    )
    metadata["refinement"] = refinement_info
    metadata["initial_quality"] = quality.get("score", 0.0)
    metadata["final_quality"] = refinement_info.get("final_score", quality.get("score", 0.0))
else:
    metadata["refinement"] = None

actions = composition_to_actions(composition)
```

---

## Testing Checklist

### Phase 1 Testing:
- [ ] Generate terrain with command
- [ ] Check `state["quality"]` exists
- [ ] Verify `quality["overall_score"]` is a number
- [ ] Verify `quality["composition"]` and `quality["textures"]` exist
- [ ] Verify `quality["warnings"]` is a list
- [ ] Check texture metrics computed correctly
- [ ] Verify no duplicate quality evaluation in logs

### Phase 2 Testing:
- [ ] Generate terrain with low-quality command
- [ ] Verify refinement runs when quality below threshold
- [ ] Check refinement_info in metadata
- [ ] Verify quality improves after refinement
- [ ] Test with quality already above threshold (should skip refinement)
- [ ] Test max_iterations respected
- [ ] Test that refinement can be disabled

---

## Quick Verification Commands

### Check if texture metrics are computed:
```python
# In Python shell or test:
from server.terrain import apply_actions
state = {"features": [], "seed": 42}
h, state, splat = apply_actions("create dramatic mountains", state)
assert "quality" in state
assert "texture_metrics" in state.get("_last_narrative_meta", {})
assert state["quality"]["overall_score"] > 0
```

### Check if refinement runs:
```python
# Generate with command that produces low quality
h, state, splat = apply_actions("add mountain", state)  # Low feature count
meta = state.get("_last_narrative_meta", {})
if meta.get("refinement"):
    print(f"Refinement ran: {meta['refinement']['iterations']} iterations")
    print(f"Quality improved: {meta['initial_quality']} -> {meta['final_quality']}")
```

---

## Rollback Plan

If something breaks:

1. **Phase 1 Rollback**: Comment out texture metrics code, revert to old quality evaluation
2. **Phase 2 Rollback**: Set `enable_refinement=False` or comment out refinement code

All changes are additive (except removing duplicate evaluation), so easy to disable.

