# Evolving Rubric System - LLM-as-a-Judge Meta-Learning

## 🎯 Core Insight

**Current Problem:**
- Static rubrics with fixed thresholds (e.g., "4+ features", "3+ types")
- Can't adapt to different aesthetic styles or contexts
- No learning from what actually works
- Rubrics become outdated as system improves

**Proposed Solution:**
- Use LLM-as-a-Judge to **evolve rubrics over time**
- Judge analyzes terrains and proposes rubric improvements
- Rubrics adapt to different contexts and aesthetic goals
- System learns what actually makes terrain aesthetically pleasing

---

## 🧠 Deep Analysis: Why Static Rubrics Fail

### **1. Context Blindness**

**Static:** "4+ features minimum"
**Problem:** 
- A dramatic mountain scene might need 8+ features
- A serene desert might need only 2-3 features
- Same threshold doesn't fit all contexts

**Evolving:** Judge analyzes command context and suggests appropriate thresholds

### **2. Aesthetic Blindness**

**Static:** "3+ feature types minimum"
**Problem:**
- Doesn't consider which types work well together
- Doesn't understand visual harmony
- Ignores aesthetic principles (contrast, rhythm, unity)

**Evolving:** Judge identifies aesthetic patterns and proposes type combinations

### **3. Threshold Rigidity**

**Static:** "Extent diagonal >= 110"
**Problem:**
- Too strict for some scenes (cramped)
- Too loose for others (sparse)
- Doesn't adapt to feature count or scene goals

**Evolving:** Judge suggests dynamic thresholds based on scene characteristics

### **4. Missing Dimensions**

**Static:** Only checks feature_count, type_diversity, extent, height_std
**Problem:**
- Missing spatial balance, visual hierarchy, coherence
- Can't identify new quality dimensions
- Rubrics become outdated

**Evolving:** Judge discovers new quality dimensions from analyzing terrains

---

## 🚀 Proposed Architecture

### **Phase 1: Rubric Evolution Loop**

```
1. Generate terrain with current rubric
2. Judge evaluates terrain visually
3. Judge identifies what makes it good/bad
4. Judge proposes rubric improvements
5. Validate and integrate improvements
6. Update rubric for next iteration
```

### **Phase 2: Context-Aware Rubrics**

```
1. Analyze command intent (dramatic, serene, etc.)
2. Judge suggests context-specific thresholds
3. Apply adaptive rubric for this context
4. Learn from results
```

### **Phase 3: Aesthetic Pattern Learning**

```
1. Judge analyzes batch of high-quality terrains
2. Identifies common aesthetic patterns
3. Proposes new rubric criteria based on patterns
4. Validates patterns with new terrains
```

---

## 💡 Implementation Strategy

### **1. Rubric Evolution Agent**

**Role:** Analyzes terrains and evolves rubrics

**Prompt:**
```
You are a rubric evolution specialist. Analyze the following terrains and their quality scores:

[Show batch of terrains with scores]

Based on your analysis:
1. What makes high-scoring terrains (0.8+) aesthetically pleasing?
2. What patterns do you observe in composition, texture, spatial relationships?
3. What rubric criteria are missing or too rigid?
4. Propose specific rubric improvements with thresholds.

Return structured JSON:
{
  "observed_patterns": [...],
  "missing_criteria": [...],
  "threshold_adjustments": {...},
  "new_criteria": [...],
  "aesthetic_principles": [...]
}
```

### **2. Context-Aware Rubric Generator**

**Role:** Generates context-specific rubrics

**Prompt:**
```
Command: "{command}"
Current rubric: {current_rubric}

Based on the command intent, suggest:
1. Appropriate thresholds for this context
2. Priority criteria (what matters most for this scene type)
3. Aesthetic goals (dramatic, serene, balanced, etc.)

Return adaptive rubric for this context.
```

### **3. Aesthetic Pattern Discovery**

**Role:** Discovers new quality dimensions

**Prompt:**
```
Analyze these high-quality terrains (score 0.8+):
[Show terrains]

What aesthetic principles do they follow?
What spatial relationships create visual harmony?
What texture patterns enhance realism?

Propose new rubric criteria based on these patterns.
```

---

## 🔧 Technical Implementation

### **1. Rubric Evolution Service**

```python
class RubricEvolutionService:
    """Evolves quality rubrics using LLM-as-a-Judge."""
    
    def evolve_rubric(
        self,
        terrain_batch: List[Dict],
        current_rubric: Dict,
        gemini_client: GeminiClient
    ) -> Dict:
        """
        Analyze terrains and evolve rubric.
        
        Args:
            terrain_batch: List of terrains with scores
            current_rubric: Current rubric to evolve
            gemini_client: Gemini client for visual analysis
        
        Returns:
            Evolved rubric with improvements
        """
        # 1. Visual analysis of terrains
        visual_analysis = self._analyze_terrain_batch(
            terrain_batch, gemini_client
        )
        
        # 2. Pattern identification
        patterns = self._identify_patterns(visual_analysis)
        
        # 3. Rubric proposal
        improvements = self._propose_rubric_improvements(
            patterns, current_rubric
        )
        
        # 4. Validate and integrate
        evolved_rubric = self._integrate_improvements(
            current_rubric, improvements
        )
        
        return evolved_rubric
```

### **2. Context-Aware Rubric Generator**

```python
def generate_context_rubric(
    command: str,
    base_rubric: Dict,
    gemini_client: GeminiClient
) -> Dict:
    """
    Generate context-specific rubric based on command intent.
    
    Args:
        command: User command (e.g., "dramatic mountain landscape")
        base_rubric: Base rubric to adapt
        gemini_client: For understanding command intent
    
    Returns:
        Context-adapted rubric
    """
    # Analyze command intent
    intent = gemini_client.analyze_intent(command)
    
    # Generate adaptive thresholds
    adaptive_rubric = adapt_rubric_to_intent(
        base_rubric, intent
    )
    
    return adaptive_rubric
```

### **3. Aesthetic Pattern Learning**

```python
def discover_aesthetic_patterns(
    high_quality_terrains: List[Dict],
    gemini_client: GeminiClient
) -> Dict:
    """
    Discover aesthetic patterns from high-quality terrains.
    
    Args:
        high_quality_terrains: Terrains with score 0.8+
        gemini_client: For visual pattern analysis
    
    Returns:
        Discovered patterns and proposed criteria
    """
    # Visual analysis
    analyses = [
        gemini_client.analyze_aesthetics(terrain)
        for terrain in high_quality_terrains
    ]
    
    # Pattern extraction
    patterns = extract_common_patterns(analyses)
    
    # Propose new criteria
    new_criteria = propose_criteria_from_patterns(patterns)
    
    return {
        "patterns": patterns,
        "new_criteria": new_criteria,
        "confidence": calculate_confidence(patterns)
    }
```

---

## 📊 Rubric Evolution Workflow

### **Iteration 1: Baseline**
```
Current Rubric:
- feature_count >= 4
- type_diversity >= 3
- extent_diagonal >= 110
- height_std >= 0.06

Generate 10 terrains → Scores: 0.3-0.6
```

### **Iteration 2: Judge Analysis**
```
Judge analyzes terrains:
- High-scoring terrains have better spatial balance
- Missing: visual hierarchy check
- Thresholds too rigid for different contexts

Proposed Improvements:
- Add spatial_balance metric
- Add height_hierarchy check
- Make thresholds context-aware
```

### **Iteration 3: Evolved Rubric**
```
Evolved Rubric:
- feature_count: context-dependent (4-8)
- type_diversity >= 3
- extent_diagonal: context-dependent (100-150)
- height_std >= 0.06
- spatial_balance >= 0.7 (NEW)
- height_hierarchy >= 0.6 (NEW)

Generate 10 terrains → Scores: 0.5-0.75
```

### **Iteration 4: Further Evolution**
```
Judge identifies:
- Texture alignment patterns
- Feature clustering optimal ranges
- Aesthetic coherence principles

Further improvements...
```

---

## 🎨 Context-Aware Rubric Examples

### **Dramatic Mountain Scene**
```python
{
    "context": "dramatic_mountain",
    "feature_count": {"minimum": 6, "good": 8, "excellent": 10},
    "height_std": {"minimum": 0.10, "good": 0.15, "excellent": 0.20},
    "spatial_balance": {"minimum": 0.6, "good": 0.8, "excellent": 0.9},
    "priority": ["height_hierarchy", "spatial_balance", "feature_count"]
}
```

### **Serene Desert Scene**
```python
{
    "context": "serene_desert",
    "feature_count": {"minimum": 2, "good": 4, "excellent": 6},
    "height_std": {"minimum": 0.04, "good": 0.06, "excellent": 0.08},
    "spatial_balance": {"minimum": 0.7, "good": 0.85, "excellent": 0.95},
    "priority": ["spatial_balance", "texture_coherence", "minimalism"]
}
```

---

## 🔬 Validation Strategy

### **1. A/B Testing**
- Compare old vs evolved rubric on same commands
- Measure quality improvement
- Track rubric effectiveness

### **2. Pattern Confidence**
- Track how often proposed patterns appear
- Validate patterns with new terrains
- Remove low-confidence patterns

### **3. Rubric Stability**
- Avoid overfitting to specific terrains
- Maintain generalizability
- Track rubric evolution over time

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

### **2. Rubric Stability**
- Prevent overfitting
- Maintain generalizability
- Track evolution carefully

### **3. Computational Cost**
- Visual analysis is expensive
- Batch processing needed
- Caching strategies

### **4. Validation**
- How to validate judge's proposals?
- A/B testing infrastructure
- Pattern confidence tracking

---

## 🎯 Implementation Phases

### **Phase 1: Foundation** (Week 1)
- Rubric evolution service structure
- Basic judge analysis prompts
- Rubric versioning system

### **Phase 2: Pattern Discovery** (Week 2)
- Aesthetic pattern extraction
- New criteria proposal
- Pattern validation

### **Phase 3: Context Adaptation** (Week 3)
- Context-aware rubric generation
- Intent analysis
- Adaptive thresholds

### **Phase 4: Continuous Evolution** (Week 4+)
- Automated evolution loop
- Rubric history tracking
- Performance monitoring

---

## 💭 Deep Thoughts

### **Why This Matters**

Static rubrics assume we know what "good" means upfront. But aesthetic quality is:
- **Context-dependent**: What's good for a dramatic scene isn't good for a serene one
- **Evolving**: As the system improves, our understanding of quality improves
- **Pattern-based**: Real quality comes from patterns we haven't codified yet
- **Subjective**: Aesthetic judgment requires understanding, not just metrics

### **The Meta-Learning Opportunity**

Instead of just using LLM-as-a-Judge to evaluate, we can use it to:
- **Discover** what makes terrain aesthetically pleasing
- **Evolve** our understanding of quality
- **Adapt** to different contexts and goals
- **Learn** from what actually works

This is true meta-learning: the system learns how to learn better quality assessment.

---

## 🔗 Integration Points

### **1. Quality Evaluation**
- Use evolved rubrics for evaluation
- Context-aware rubric selection
- Adaptive threshold application

### **2. Refinement System**
- Refinement guided by evolved rubrics
- Context-specific refinement strategies
- Pattern-based improvements

### **3. Multi-Agent Workflow**
- Judge agent evolves rubrics
- Artist agent uses evolved rubrics
- Critic agent validates rubric improvements

---

## 📝 Next Steps

1. **Design Rubric Evolution API**
   - Input: terrain batch, current rubric
   - Output: evolved rubric, confidence scores

2. **Create Judge Analysis Prompts**
   - Pattern identification
   - Criteria proposal
   - Threshold suggestions

3. **Build Rubric Versioning System**
   - Track rubric evolution
   - A/B test different versions
   - Rollback if needed

4. **Implement Context Analysis**
   - Command intent extraction
   - Context classification
   - Adaptive rubric generation

This is a powerful direction that could significantly improve the system's aesthetic capabilities!

