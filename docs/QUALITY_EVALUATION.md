# Quality Evaluation System

The Semantic Terrain system includes comprehensive quality evaluation and refinement capabilities to ensure generated terrain meets aesthetic and technical standards.

---

## Overview

The quality evaluation system assesses terrain in multiple dimensions:

1. **Feature Metrics** - Composition and spatial arrangement
2. **Texture Metrics** - Visual quality and coverage
3. **Quality Rubric** - Combined scoring system
4. **Refinement** - Automatic improvement suggestions

---

## Feature Metrics

Feature metrics evaluate the composition and spatial arrangement of terrain features.

### Spacing
- **Distance Between Features** - Minimum and average distances
- **Distribution Pattern** - Clustering vs. uniform distribution
- **Overlap Detection** - Features that overlap too much

### Distribution
- **Spatial Balance** - Left/right, top/bottom balance
- **Feature Density** - Features per unit area
- **Clustering Analysis** - Natural vs. artificial clustering

### Hierarchy
- **Height Relationships** - Mountains taller than hills
- **Size Relationships** - Appropriate size differences
- **Focal Point Emphasis** - Clear focal features

### Balance
- **Visual Balance** - Weight distribution across terrain
- **Feature Type Balance** - Variety of feature types
- **Elevation Balance** - High vs. low features

---

## Texture Metrics

Texture metrics evaluate the visual quality of terrain textures.

### Coverage
- **Texture Coverage** - Percentage of terrain with textures
- **Gap Detection** - Areas without proper textures
- **Channel Distribution** - Balance of grass, rock, sand, snow

### Blending
- **Transition Smoothness** - How smoothly textures blend
- **Edge Quality** - Hard vs. soft texture edges
- **Gradient Analysis** - Texture gradient quality

### Contrast
- **Texture Variation** - Variety in texture patterns
- **Height-Texture Correlation** - Appropriate texture for height
- **Slope-Texture Correlation** - Appropriate texture for slope

---

## Quality Rubric

The quality rubric combines feature and texture metrics into overall scores.

### Composition Score
- **Feature Arrangement** - How well features are arranged
- **Spatial Relationships** - Natural feature relationships
- **Visual Balance** - Overall visual balance
- **Aesthetic Goals** - Achievement of stated goals

### Texture Score
- **Coverage Quality** - Texture coverage assessment
- **Blending Quality** - Texture blending assessment
- **Visual Appeal** - Overall texture appearance

### Overall Score
- **Combined Assessment** - Weighted combination of composition and texture
- **Quality Level** - Overall quality rating (0-10)
- **Recommendations** - Suggestions for improvement

---

## Refinement System

The refinement system automatically suggests improvements based on quality evaluation.

### Automatic Refinement

When quality issues are detected, the system can:

1. **Adjust Parameters** - Modify feature parameters (height, radius, etc.)
2. **Add Features** - Add features to fill gaps
3. **Reposition Features** - Move features for better spacing
4. **Modify Textures** - Adjust texture parameters

### Refinement Process

```
Quality Evaluation
    │
    ▼
Identify Issues
    │
    ▼
Generate Suggestions
    │
    ▼
Apply Refinements
    │
    ▼
Re-evaluate Quality
    │
    ▼
Iterate if Needed
```

### Refinement Examples

**Texture Coverage Issue:**
```
Problem: Low texture coverage (60%)
Solution: Add more features, adjust texture thresholds
Result: Improved coverage (85%)
```

**Spacing Issue:**
```
Problem: Features too close together
Solution: Reposition features, increase minimum distance
Result: Better spacing, natural distribution
```

**Balance Issue:**
```
Problem: All features on left side
Solution: Add features on right, redistribute
Result: Balanced distribution
```

---

## Quality Tools

The system provides tools for quality evaluation and refinement.

### Evaluation Tools

- **`evaluate_terrain_quality`** - Overall quality assessment
- **`analyze_texture_feature_relationship`** - Texture-feature analysis
- **`compute_feature_metrics`** - Feature composition metrics
- **`compute_texture_metrics`** - Texture quality metrics

### Refinement Tools

- **`refine_composition`** - Automatic composition refinement
- **`modify_feature_parameters`** - Parameter adjustment
- **`suggest_modification`** - Improvement suggestions

### Usage Examples

**Evaluate Quality:**
```python
quality = evaluate_terrain_quality(scene_state, actions)
# Returns: {composition_score, texture_score, overall_score, warnings}
```

**Refine Composition:**
```python
refined_actions, quality_info = refine_composition(
    scene_state, 
    actions,
    max_iterations=3
)
# Returns: Refined actions with improved quality scores
```

---

## Quality Thresholds

The system uses thresholds to identify quality issues.

### Feature Thresholds
- **Minimum Spacing** - 50 pixels between features
- **Maximum Density** - 10 features per 100x100 area
- **Balance Tolerance** - ±20% left/right balance

### Texture Thresholds
- **Minimum Coverage** - 80% texture coverage
- **Maximum Gap Size** - 100 pixels for texture gaps
- **Blending Smoothness** - Minimum 40px feathering

### Quality Levels
- **Excellent** (9-10) - No issues, high quality
- **Good** (7-8) - Minor issues, acceptable quality
- **Fair** (5-6) - Some issues, needs improvement
- **Poor** (0-4) - Major issues, significant problems

---

## Integration with Parsing Strategies

Quality evaluation integrates with parsing strategies:

### Narrative Pipeline
- Evaluates composition during generation
- Applies aesthetic goals
- Refines based on quality feedback

### ReAct Agent
- Uses quality tools during reasoning
- Iteratively improves based on evaluation
- Quality-aware action generation

### Multi-Agent Workflow
- Critic evaluates quality
- Integrator refines based on critique
- Judge provides final quality score

---

## Best Practices

### For Quality Evaluation
- Evaluate after action generation
- Check both feature and texture metrics
- Use quality scores to guide refinement

### For Refinement
- Iterate up to 3-5 times
- Focus on highest-impact improvements
- Balance quality vs. computation time

### For Quality Goals
- Set realistic quality thresholds
- Prioritize critical issues (coverage, spacing)
- Allow some variation for natural appearance

---

## Advanced Features

### Progressive Scoring
- **Progressive Range Scoring** - Scores improve as values approach ideal ranges
- **Threshold-Based Scoring** - Different scores for different thresholds
- **Weighted Metrics** - Customizable metric weights

### Context-Aware Evaluation
- **Scene Context** - Considers existing terrain
- **Aesthetic Goals** - Evaluates against stated goals
- **Archetype Matching** - Archetype-appropriate evaluation

### Visual Evaluation (Optional)
- **Gemini Vision** - Optional visual quality assessment
- **Image Analysis** - Analyzes rendered terrain images
- **Aesthetic Feedback** - Subjective quality feedback

---

See also:
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Parsing Strategies](PARSING_STRATEGIES.md) - How parsing integrates with quality
- [API Reference](API_REFERENCE.md) - Quality evaluation API endpoints

