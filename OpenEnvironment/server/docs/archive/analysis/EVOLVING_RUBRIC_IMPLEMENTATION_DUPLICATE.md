# Evolving Rubric Implementation Plan

## 🎯 Core Concept

**Instead of static rubrics, use LLM-as-a-Judge to:**
1. **Discover** what makes terrain aesthetically pleasing
2. **Evolve** rubrics based on observed patterns
3. **Adapt** to different contexts and aesthetic goals
4. **Learn** continuously from what actually works

---

## 🏗️ Architecture

### **1. Rubric Evolution Service**

**File:** `server/semantic/rubric_evolution.py`

**Key Components:**
- `RubricEvolutionService` - Main service class
- `evolve_rubric_from_batch()` - Analyze terrains and evolve rubric
- `generate_context_rubric()` - Create context-specific rubrics
- `_identify_aesthetic_patterns()` - Use Gemini to find patterns

**Workflow:**
```
1. Collect batch of terrains with scores
2. Separate high-quality (0.8+) vs low-quality (<0.6)
3. Gemini analyzes visual patterns
4. Propose rubric improvements
5. Integrate improvements
6. Return evolved rubric
```

---

### **2. Integration Points**

#### **A. Quality Evaluation**
```python
# Before: Static rubric
rubric = DEFAULT_QUALITY_RUBRIC
score = evaluate_quality_rubric(metrics, texture_metrics, rubric)

# After: Context-aware evolved rubric
evolution_service = RubricEvolutionService(gemini_api_key)
context_rubric = evolution_service.generate_context_rubric(command, base_rubric)
score = evaluate_quality_rubric(metrics, texture_metrics, context_rubric)
```

#### **B. Multi-Agent Workflow**
```python
# Judge agent evolves rubrics periodically
if iteration % 10 == 0:  # Every 10 iterations
    evolved_rubric = evolution_service.evolve_rubric_from_batch(
        recent_terrains, current_rubric
    )
    update_rubric(evolved_rubric)
```

#### **C. Quality History Analysis**
```python
# Periodically evolve rubric from history
evolved = evolve_rubric_from_history(
    Path("logs/quality_history.jsonl"),
    current_rubric,
    min_samples=20
)
```

---

## 🔄 Evolution Loop

### **Phase 1: Pattern Discovery**

**Input:**
- Batch of terrains with scores
- Current rubric

**Process:**
1. Gemini analyzes high-quality terrains visually
2. Identifies common aesthetic patterns
3. Compares with low-quality terrains
4. Proposes missing criteria

**Output:**
- Observed patterns
- Missing criteria
- Threshold adjustments

### **Phase 2: Rubric Evolution**

**Input:**
- Patterns from Phase 1
- Current rubric

**Process:**
1. Add new criteria based on patterns
2. Adjust thresholds based on observations
3. Create context-specific adaptations
4. Validate improvements

**Output:**
- Evolved rubric
- Version metadata
- Confidence scores

### **Phase 3: Validation**

**Input:**
- Evolved rubric
- New terrain batch

**Process:**
1. Test evolved rubric on new terrains
2. Compare scores with old rubric
3. Measure improvement
4. Rollback if worse

**Output:**
- Validation results
- Decision: keep or rollback

---

## 📊 Example Evolution

### **Iteration 1: Baseline Rubric**
```python
{
  "composition": {
    "min_feature_count": 4,
    "min_type_diversity": 3,
    "min_extent_diagonal": 110.0,
    "min_height_std": 0.06
  }
}
```

**Results:** Scores 0.3-0.6

### **Iteration 2: Judge Analysis**

**Gemini observes:**
- High-quality terrains have better spatial balance
- Visual hierarchy is important (focal points)
- Feature clustering matters (not too tight, not too scattered)

**Proposed improvements:**
- Add `spatial_balance` criterion
- Add `height_hierarchy` criterion
- Add `feature_clustering` criterion
- Adjust thresholds to be context-aware

### **Iteration 3: Evolved Rubric**
```python
{
  "composition": {
    "min_feature_count": {"minimum": 4, "good": 6, "excellent": 8},
    "min_type_diversity": 3,
    "min_extent_diagonal": {"minimum": 100, "good": 130, "excellent": 160},
    "min_height_std": 0.06,
    "spatial_balance": {"minimum": 0.6, "good": 0.8, "excellent": 0.9},  # NEW
    "height_hierarchy": {"minimum": 0.5, "good": 0.7, "excellent": 0.9},  # NEW
    "feature_clustering": {"minimum": 0.5, "good": 0.7, "excellent": 0.85}  # NEW
  },
  "context_adaptations": {
    "dramatic": {
      "feature_count": {"minimum": 6, "good": 8, "excellent": 10},
      "height_std": {"minimum": 0.10, "good": 0.15, "excellent": 0.20}
    },
    "serene": {
      "feature_count": {"minimum": 2, "good": 4, "excellent": 6},
      "spatial_balance": {"minimum": 0.7, "good": 0.85, "excellent": 0.95}
    }
  }
}
```

**Results:** Scores 0.5-0.75 (improvement!)

---

## 🎨 Context-Aware Rubrics

### **Dramatic Mountain Scene**
```python
command = "create a dramatic mountain landscape with valleys and cliffs"

context_rubric = evolution_service.generate_context_rubric(command, base_rubric)

# Returns:
{
  "context_type": "dramatic_mountain",
  "thresholds": {
    "feature_count": {"minimum": 6, "good": 8, "excellent": 10},
    "height_std": {"minimum": 0.10, "good": 0.15, "excellent": 0.20},
    "spatial_balance": {"minimum": 0.6, "good": 0.8, "excellent": 0.9}
  },
  "priority_criteria": ["height_hierarchy", "spatial_balance", "feature_count"],
  "aesthetic_goals": ["drama", "contrast", "visual impact"]
}
```

### **Serene Desert Scene**
```python
command = "design a serene desert with rolling dunes"

context_rubric = evolution_service.generate_context_rubric(command, base_rubric)

# Returns:
{
  "context_type": "serene_desert",
  "thresholds": {
    "feature_count": {"minimum": 2, "good": 4, "excellent": 6},
    "height_std": {"minimum": 0.04, "good": 0.06, "excellent": 0.08},
    "spatial_balance": {"minimum": 0.7, "good": 0.85, "excellent": 0.95}
  },
  "priority_criteria": ["spatial_balance", "texture_coherence", "minimalism"],
  "aesthetic_goals": ["serenity", "harmony", "simplicity"]
}
```

---

## 🔬 Validation Strategy

### **1. A/B Testing**
```python
# Test evolved rubric vs old rubric
old_scores = [evaluate_with_rubric(t, old_rubric) for t in test_terrains]
new_scores = [evaluate_with_rubric(t, evolved_rubric) for t in test_terrains]

improvement = mean(new_scores) - mean(old_scores)
if improvement > 0.05:  # 5% improvement threshold
    adopt_rubric(evolved_rubric)
else:
    keep_rubric(old_rubric)
```

### **2. Pattern Confidence**
```python
# Track how often patterns appear
pattern_frequency = {
    "spatial_balance": 0.85,  # Appears in 85% of high-quality terrains
    "height_hierarchy": 0.72,  # Appears in 72% of high-quality terrains
}

# Only adopt high-confidence patterns
if pattern_frequency["spatial_balance"] > 0.8:
    add_criterion("spatial_balance")
```

### **3. Rubric Stability**
```python
# Track rubric changes over time
rubric_history = [
    {"version": 1, "criteria_count": 4},
    {"version": 2, "criteria_count": 7},
    {"version": 3, "criteria_count": 9},
]

# Avoid overfitting
if criteria_count > 15:
    logger.warning("Rubric becoming too complex, consider simplification")
```

---

## 📈 Expected Benefits

### **1. Adaptive Quality Assessment**
- Rubrics adapt to different contexts
- Better fit for different aesthetic goals
- More nuanced quality evaluation

### **2. Continuous Improvement**
- System learns what works
- Rubrics evolve with system capabilities
- Quality improves over time

### **3. Aesthetic Sophistication**
- Discovers new quality dimensions
- Identifies aesthetic patterns
- Proposes principled improvements

### **4. Context Awareness**
- Different thresholds for different scenes
- Priority criteria based on intent
- Better alignment with user goals

---

## 🚧 Implementation Challenges

### **1. Judge Consistency**
- Ensure judge provides consistent feedback
- Validate judge's suggestions
- Avoid judge biases

**Solution:** Multiple judge evaluations, consensus voting

### **2. Rubric Stability**
- Prevent overfitting
- Maintain generalizability
- Track evolution carefully

**Solution:** A/B testing, validation before adoption

### **3. Computational Cost**
- Visual analysis is expensive
- Batch processing needed
- Caching strategies

**Solution:** Batch evolution, cache patterns, periodic updates

### **4. Validation**
- How to validate judge's proposals?
- A/B testing infrastructure
- Pattern confidence tracking

**Solution:** Automated validation pipeline, rollback mechanism

---

## 🎯 Next Steps

1. **Implement RubricEvolutionService** ✅ (Done)
2. **Integrate into quality evaluation**
3. **Add rubric versioning system**
4. **Create validation pipeline**
5. **Test with real terrain batches**
6. **Monitor rubric evolution over time**

---

## 💭 Why This Matters

**Static rubrics assume we know what "good" means upfront.**

But aesthetic quality is:
- **Context-dependent**: What's good for dramatic isn't good for serene
- **Evolving**: Understanding improves as system improves
- **Pattern-based**: Real quality comes from patterns we haven't codified
- **Subjective**: Requires understanding, not just metrics

**LLM-as-a-Judge evolution enables:**
- True meta-learning: system learns how to learn better
- Adaptive quality assessment
- Continuous improvement
- Aesthetic sophistication

This is a powerful direction that could significantly improve the system's aesthetic capabilities!

