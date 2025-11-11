# Implementation Roadmap - Geological Narrative System

## 🎯 **Vision Statement**

Build a **geological narrative AI** that takes a user's simple prompt and generates **beautiful, geologically coherent, emotionally resonant terrain** by:

1. Understanding the **emotional intent** and extracting a **geological story**
2. **Generating features** from narrative constraints (not random placement)
3. Using **only 6 core primitives** with perfect mastery
4. **Iterating** until geological coherence > 0.8
5. Taking **2-5 minutes** to produce the **highest quality** result

**User prompt:** "Create a beautiful desert canyon with ancient tranquility"
**Result:** A unique, believable, stunning terrain that tells a geological story

---

## 📦 **The 6 Core Primitives**

```python
1. Mountain   - Hero elevation, focal point, scale reference
2. Valley     - Hero depression, balance, paths
3. Dunes      - Texture provider, ONLY good sand source
4. Ridge      - Linear structure, skeleton, connections
5. Mound      - Detail layer, foreground interest
6. Canyon     - Linear drama, exploration channels
```

**Why these 6?**
- ✅ Cover all geological roles
- ✅ Activate all 4 splatmap channels (RGBA)
- ✅ Support all narrative archetypes
- ✅ Simple enough to master deeply
- ✅ Complex enough for infinite variation

---

## 🛠️ **Core Tools for ReAct Agent**

### **Tool 1: `develop_terrain_narrative`**
**Purpose:** Extract geological story from user intent

**Input:**
```python
user_intent: "beautiful desert canyon with ancient tranquility"
mood_keywords: ["beautiful", "ancient", "tranquility"]
desired_features: ["desert", "canyon"]
```

**Output:**
```python
TerrainNarrative(
    formation_story="Ancient river carved gently over millions of years...",
    primary_forces=["gentle_water_erosion", "wind_shaping"],
    time_scale="ancient",
    energy_level="moderate",
    mood_tags=["peaceful", "ancient", "timeless"],
    
    # What primitives are needed
    required_primitives=["canyon", "dunes"],  # Canyon + sand texture
    optional_primitives=["mountain", "ridge", "mound"],
    
    # Geological parameters
    erosion_energy="gentle",      # Ancient = weathered = smooth
    wind_direction=Vector(1, 0.3), # Consistent wind
    weathering_level=0.9,          # High = very smooth
    
    # Spatial constraints
    feature_relationships={
        "canyon": "primary_hero",
        "dunes": "required_in_canyon_floor",
        "mountain": "optional_backdrop"
    }
)
```

**LLM Reasoning:**
- "Desert" → Need sand → Dunes required (only source)
- "Canyon" → Primary feature
- "Ancient + tranquil" → Smooth, gentle, weathered forms
- Story: "Ancient river carved, dried up, wind filling with sand"

---

### **Tool 2: `generate_from_narrative`**
**Purpose:** Generate feature composition from narrative constraints

**Input:**
```python
narrative: TerrainNarrative (from tool 1)
scene_state: Dict (current terrain state)
```

**Output:**
```python
FeatureComposition(
    primary=[canyon],         # Hero features
    secondary=[mountain, ridge, dunes],  # Supporting
    details=[mound_1, mound_2, ...],     # Foreground
    
    # Geological sequence
    formation_sequence=[
        "1. Mountain formed from tectonic uplift",
        "2. River carved canyon from mountain",
        "3. Wind deposited dunes in canyon floor",
        "4. Erosion created mound debris"
    ],
    
    # Spatial relationships
    relationships={
        "canyon flows from mountain",
        "dunes fill canyon floor (wind shadow)",
        "ridge parallels canyon (erosion pattern)"
    },
    
    # Feature parameters (constrained by narrative)
    features={
        "canyon": {
            "start": (120, 450),
            "end": (380, 80),
            "width": 12,
            "depth": 0.7,
            "sinuosity": 1.3,  # Meandering
            "edge_smoothness": 0.9  # Ancient weathering
        },
        "dunes": {
            "area": wind_shadow_zone(canyon),
            "amplitude": 0.06,  # Subtle (peaceful)
            "frequency": 18,
            "angle": perpendicular(wind_direction)
        },
        "mountain": {
            "position": near(canyon.start, 80),
            "height": 0.75,
            "radius": 60,
            "steepness": 0.8,
            "weathering": 0.9  # Smooth
        },
        # ... ridge, mounds
    }
)
```

**LLM Reasoning:**
- Canyon: Primary, meandering, flows from mountain (water source)
- Mountain: Backdrop, water source story, scale reference
- Dunes: Required for sand, placed in wind shadow
- Ridge: Optional, reinforces canyon structure
- Mounds: Detail, erosion debris near canyon mouth

---

### **Tool 3: `evaluate_narrative_coherence`**
**Purpose:** Check if composition tells coherent story

**Input:**
```python
composition: FeatureComposition (from tool 2)
narrative: TerrainNarrative (from tool 1)
```

**Output:**
```python
CoherenceAnalysis(
    # 6 dimensions of quality
    geological_plausibility=0.95,  # Could form naturally?
    narrative_consistency=0.92,    # Supports story?
    scale_hierarchy=0.88,          # Clear size relationships?
    splatmap_coverage=1.0,         # All 4 channels used?
    visual_flow=0.85,              # Eye travels naturally?
    emotional_resonance=0.90,      # Evokes intended mood?
    
    overall_quality=0.92,  # Weighted average
    
    problems=[],  # List of issues if any
    
    design_notes=[
        "Canyon serves as primary hero",
        "All features support 'ancient river' narrative",
        "Smooth forms consistent with ancient weathering",
        "Dunes activate sand channel (required for desert)",
        "Mountain provides scale + water source story"
    ]
)
```

**Decision:** If overall_quality >= 0.8 → Generate! Else → Refine

---

### **Tool 4: `refine_narrative`**
**Purpose:** Fix problems and adjust narrative

**Input:**
```python
composition: FeatureComposition
coherence: CoherenceAnalysis (with problems)
narrative: TerrainNarrative
```

**Output:**
```python
TerrainNarrative (refined)
```

**Example Refinements:**
- "Canyon flows uphill" → Adjust gradient or change water story
- "Missing sand texture" → Add dunes (required)
- "No scale hierarchy" → Increase primary size, reduce detail size
- "Too chaotic" → Reduce feature count, simplify
- "Doesn't feel ancient" → Increase weathering_level

---

### **Tool 5: `calculate_spatial_constraints`**
**Purpose:** Calculate spatial relationships (wind shadow, flow paths, etc.)

**Examples:**
```python
# Wind shadow calculation
wind_shadow_zone(obstacle: Feature, wind_direction: Vector) -> Area
  → Returns zone where wind is blocked (dunes deposit here)

# Flow path calculation  
water_flow_path(terrain_gradient: ndarray) -> Path
  → Returns natural water flow lines (canyons follow this)

# Clustering zones
cluster_zone(center: Point, radius: float, clustering: float) -> List[Point]
  → Returns clustered positions (for mound fields)

# Parallel line calculation
parallel_line(feature: Linear, offset: float) -> (Point, Point)
  → Returns parallel line (for ridge along canyon)
```

---

### **Tool 6: `estimate_splatmap_coverage`**
**Purpose:** Preview which splatmap channels will be active

**Input:**
```python
composition: FeatureComposition
```

**Output:**
```python
{
    "R_grass": {
        "coverage": 0.40,  # 40% of terrain
        "sources": ["canyon floor", "valley", "mounds"]
    },
    "G_rock": {
        "coverage": 0.30,
        "sources": ["mountain", "canyon walls", "ridge sides"]
    },
    "B_sand": {
        "coverage": 0.20,
        "sources": ["dunes"]  # ONLY source!
    },
    "A_snow": {
        "coverage": 0.10,
        "sources": ["mountain peak"]
    }
}
```

**Quality check:** All 4 channels > 0? → Good variety!

---

## 🎭 **The ReAct Loop**

```python
# ============================================================
# ITERATION 1-2: UNDERSTAND
# ============================================================
narrative = develop_terrain_narrative(
    user_intent="beautiful desert canyon with ancient tranquility",
    mood_keywords=["beautiful", "ancient", "tranquility"],
    desired_features=["desert", "canyon"]
)

# LLM extracts:
# - Story: "Ancient river carved gently, dried up, wind filling"
# - Required: canyon, dunes
# - Style: smooth, weathered, peaceful

# ============================================================
# ITERATION 3-5: GENERATE
# ============================================================
composition = generate_from_narrative(
    narrative=narrative,
    scene_state=current_state
)

# LLM generates:
# - Canyon (primary hero)
# - Mountain (backdrop, water source)
# - Dunes (required for sand)
# - Ridge (structure)
# - Mounds (detail)

# ============================================================
# ITERATION 6-7: EVALUATE
# ============================================================
coherence = evaluate_narrative_coherence(
    composition=composition,
    narrative=narrative
)

# LLM checks:
# - Geological plausibility: 0.95 ✓
# - Narrative consistency: 0.92 ✓
# - Scale hierarchy: 0.88 ✓
# - Splatmap coverage: 1.0 ✓
# - Visual flow: 0.85 ✓
# - Emotional resonance: 0.90 ✓
# → Overall: 0.92 (excellent!)

if coherence.overall_quality >= 0.8:
    # SUCCESS! Convert to actions
    actions = composition.to_actions()
    
    return {
        "actions": actions,
        "success": True,
        "coherence_score": 0.92,
        "formation_story": narrative.formation_story,
        "design_notes": coherence.design_notes
    }
else:
    # ============================================================
    # ITERATION 8-9: REFINE
    # ============================================================
    refined_narrative = refine_narrative(
        composition=composition,
        coherence=coherence,
        narrative=narrative
    )
    
    # Regenerate with refined narrative
    composition = generate_from_narrative(refined_narrative)
    coherence = evaluate_narrative_coherence(composition, refined_narrative)
    # ... iterate until coherence >= 0.8

# ============================================================
# ITERATION 10: FINALIZE
# ============================================================
# Convert composition to terrain actions
# Return with design notes and coherence score
```

**Max iterations:** 10 (typical: 6-8)
**Time budget:** 2-5 minutes (justified for quality)

---

## 📅 **4-Week Implementation Plan**

### **Week 1: Narrative Framework** (Foundation)

**Days 1-2: Tool scaffolding**
- Create tool stubs for all 6 tools
- Define data structures (`TerrainNarrative`, `FeatureComposition`, `CoherenceAnalysis`)
- Set up tool registry for ReAct agent

**Days 3-4: Narrative archetypes**
- Define 5 terrain archetypes:
  - Water's Legacy (canyons, valleys, rivers)
  - Ancient Uplift (mountains, ridges)
  - Wind Architect (dunes, smooth forms)
  - Volcanic Birth (craters, radial patterns)
  - Depositional Plains (subtle, layered)

**Days 5-7: `develop_terrain_narrative` implementation**
- Extract mood keywords from user prompt
- Map mood → geological parameters
- Generate formation story
- Define required/optional primitives
- Test with 10+ example prompts

**Deliverable:** Working `develop_terrain_narrative` tool

---

### **Week 2: Generative Constraints** (Core Logic)

**Days 1-2: Spatial constraint system**
- Implement `calculate_spatial_constraints` tool
- Wind shadow calculation
- Flow path calculation (terrain gradient)
- Clustering algorithms
- Parallel line generation

**Days 3-5: `generate_from_narrative` implementation**
- Phase 1: Primary features (hero)
- Phase 2: Required features (narrative constraints)
- Phase 3: Optional features (enhancement)
- Phase 4: Detail features (foreground)
- Constraint satisfaction logic

**Days 6-7: Feature parameter generation**
- Narrative → primitive parameters mapping
- "Ancient" → high weathering, smooth forms
- "Dramatic" → high amplitude, steep slopes
- "Peaceful" → gentle curves, low variation

**Deliverable:** Working `generate_from_narrative` tool

---

### **Week 3: Coherence Evaluation** (Quality Control)

**Days 1-2: Geological plausibility checks**
- Water flows downhill check
- Deposition zone logic (wind shadow)
- Erosion pattern checks
- Scale relationship validation

**Days 3-4: Splatmap coverage analysis**
- Implement `estimate_splatmap_coverage` tool
- Check all 4 channels active
- Texture variety scoring

**Days 5-7: `evaluate_narrative_coherence` implementation**
- 6-dimensional quality scoring:
  - Geological plausibility
  - Narrative consistency
  - Scale hierarchy
  - Splatmap coverage
  - Visual flow
  - Emotional resonance
- Problem detection
- Design notes generation

**Deliverable:** Working `evaluate_narrative_coherence` tool

---

### **Week 4: Refinement & Integration** (Polish)

**Days 1-2: `refine_narrative` implementation**
- Problem → solution mapping
- Narrative adjustment strategies
- Iterative refinement logic

**Days 3-4: ReAct agent integration**
- Connect all tools to ReAct agent
- Implement iteration loop
- Add stopping conditions (coherence >= 0.8 OR max_iterations)

**Days 5-6: Testing & tuning**
- Test with 50+ diverse prompts:
  - "Beautiful desert canyon"
  - "Dramatic mountain vista"
  - "Peaceful valley"
  - "Ancient volcanic landscape"
  - "Mysterious dune sea"
- Tune quality thresholds
- Fix edge cases

**Day 7: Documentation & cleanup**
- Document all tools
- Clean up code
- Performance optimization

**Deliverable:** Production-ready geological narrative system

---

## 📊 **Success Metrics**

### **Quality Metrics:**
1. **Coherence score > 0.8** for 95%+ of generations
2. **All 4 splatmap channels** used meaningfully
3. **Clear scale hierarchy** in all terrains
4. **Geological plausibility** verified
5. **User mood match** > 0.8

### **Performance Metrics:**
1. **Completion time:** 2-5 minutes average
2. **Iteration count:** 6-8 average (max 10)
3. **Success rate:** > 95% (coherence achieved)

### **Variety Metrics:**
1. **No two terrains identical** (same prompt → different outputs)
2. **Primitive usage varies** (not always same patterns)
3. **Spatial layouts unique** (not grid-based)

---

## 🚀 **Phase 1 Quick Start (This Week)**

### **Immediate Tasks:**

1. **Create tool stubs** (1 hour)
   ```python
   # server/semantic/tools/narrative_tools.py
   def develop_terrain_narrative(...): pass
   def generate_from_narrative(...): pass
   def evaluate_narrative_coherence(...): pass
   def refine_narrative(...): pass
   def calculate_spatial_constraints(...): pass
   def estimate_splatmap_coverage(...): pass
   ```

2. **Define data structures** (2 hours)
   ```python
   # server/semantic/narrative_types.py
   @dataclass
   class TerrainNarrative: ...
   @dataclass
   class FeatureComposition: ...
   @dataclass
   class CoherenceAnalysis: ...
   ```

3. **Implement minimal `develop_terrain_narrative`** (4 hours)
   - Extract keywords from prompt
   - Simple mood → narrative mapping
   - Return basic TerrainNarrative

4. **Test with example prompts** (1 hour)
   - "Beautiful desert canyon"
   - "Dramatic mountain"
   - Verify narrative extraction

**Target:** End of day with working prototype of tool 1

---

## 💡 **Key Design Principles**

### **1. Constraint-Based Generation**
Don't randomly place features. Generate from geological constraints:
- Canyons follow water flow
- Dunes in wind shadows
- Ridges connect peaks
- Mounds near erosion sources

### **2. Narrative Coherence > Composition Rules**
"Does this tell a coherent story?" beats "Is this balanced?"

### **3. Iterate Until Beautiful**
Don't stop at first result. Iterate until coherence > 0.8.

### **4. Master 6, Not Mediocrize 25**
Deep mastery of 6 core primitives > shallow coverage of 25.

### **5. Geological Storytelling**
The system doesn't design terrain - it simulates geological processes.

---

## 🎯 **The End Goal**

**User types:** "Create a beautiful desert canyon with ancient tranquility"

**System delivers (in 2-5 minutes):**
- 🌍 Geologically coherent terrain (coherence: 0.92)
- 🎨 All 4 splatmap channels active (RGBA used)
- 📐 Clear scale hierarchy (mountain > canyon > dunes > mounds)
- 💚 Emotionally resonant ("ancient", "tranquil" feeling)
- ✨ Unique every time (same prompt → different beautiful results)

**Design notes:**
```
"Ancient river carved this canyon over millions of years from the mountain.
 River dried long ago, wind now slowly fills the canyon floor with sand.
 Smooth walls show patient weathering. Ridge reinforces canyon structure.
 Small mounds at canyon mouth tell story of ongoing erosion.
 
 Features used: Canyon (hero), Mountain (backdrop), Dunes (texture),
                Ridge (structure), Mounds (detail)
 
 Coherence: 0.92 (excellent)
 Splatmap: Grass 40%, Rock 30%, Sand 20%, Snow 10%"
```

**Beautiful. Believable. Unique.** ✨

---

*"Less is more. Master 6 primitives. Tell infinite stories."*

