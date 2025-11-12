# Narrative Generation System - Geological Storytelling with 6 Core Primitives

## 🎯 **The Complete Vision**

User says: **"Create a beautiful desert canyon with ancient tranquility"**

System generates: **A geologically coherent, aesthetically stunning terrain that tells a story.**

---

## 🌍 **The 6 Core Primitives**

```python
CORE_PRIMITIVES = {
    "mountain": {  # Hero elevation
        "role": "focal_point",
        "splatmap": ["rock", "snow"],
        "scale": "large"
    },
    "valley": {  # Hero depression
        "role": "balance",
        "splatmap": ["grass", "sand"],
        "scale": "large"
    },
    "dunes": {  # Texture provider
        "role": "surface_texture",
        "splatmap": ["sand"],  # ONLY source of good sand
        "scale": "medium"
    },
    "ridge": {  # Linear structure
        "role": "skeleton",
        "splatmap": ["rock", "grass"],
        "scale": "medium"
    },
    "mound": {  # Detail layer
        "role": "foreground_detail",
        "splatmap": ["grass"],
        "scale": "small"
    },
    "canyon": {  # Linear drama
        "role": "exploration",
        "splatmap": ["grass", "rock"],
        "scale": "medium"
    }
}
```

---

## 🧠 **The AI's Reasoning Tools**

### Tool 1: `develop_terrain_narrative`

```python
def develop_terrain_narrative(
    user_intent: str,
    mood_keywords: List[str],
    desired_features: List[str]
) -> TerrainNarrative:
    """
    Extract geological story from user intent.
    
    This is the FOUNDATION - everything else flows from this.
    
    Example:
        Input: "beautiful desert canyon with ancient tranquility"
        
        Extraction:
        - Biome: desert (→ need sand texture → dunes required)
        - Feature: canyon (→ primary feature)
        - Mood: ancient, tranquil (→ smooth, weathered, gentle)
        
        Geological Story:
        "Ancient river carved gently over millions of years.
         River dried up long ago, wind slowly filling canyon with sand.
         Smooth walls show patient weathering.
         Quiet, timeless, peaceful."
        
        Formation Forces:
        - Primary: gentle_water_erosion (ancient = smooth)
        - Secondary: wind_deposition (desert = dunes)
        - Time scale: ancient (= high weathering, smooth forms)
        
        Returns:
        TerrainNarrative(
            formation_story="...",
            primary_forces=["gentle_water_erosion", "wind_shaping"],
            time_scale="ancient",
            energy_level="moderate",
            mood_tags=["peaceful", "ancient", "timeless"],
            
            # Constraints that guide all generation
            required_primitives=["canyon", "dunes"],  # Canyon + sand texture
            optional_primitives=["mountain", "ridge", "mound"],
            forbidden_primitives=[],  # None forbidden
            
            # Geological parameters
            erosion_energy="gentle",  # Ancient = weathered = smooth
            wind_direction=Vector(1.0, 0.3),  # Consistent NE wind
            water_history="dried_long_ago",
            weathering_level=0.9,  # High = very smooth
            
            # Spatial constraints
            feature_relationships={
                "canyon": "primary_hero",
                "mountain": "optional_backdrop",
                "dunes": "required_in_canyon_floor",
                "ridge": "optional_canyon_wall",
                "mound": "optional_debris"
            }
        )
    """
    pass
```

**Key Insight:** The narrative defines **what CAN exist** (geological plausibility) and **what MUST exist** (fulfill user intent).

---

### Tool 2: `generate_from_narrative`

```python
def generate_from_narrative(
    narrative: TerrainNarrative,
    scene_state: Dict
) -> FeatureComposition:
    """
    Generate feature composition that satisfies narrative constraints.
    
    This is GENERATIVE, not placing predefined features.
    Uses ONLY the 6 core primitives.
    
    Example (continued from above):
    
    Phase 1: PRIMARY FEATURES (hero elements)
    ==========================================
    
    Rule: "Canyon is primary feature"
    → Generate main canyon
    
    Canyon(
        # Position: Center-weighted but natural
        start=(120, 450),
        end=(380, 80),
        
        # Parameters from narrative
        width=12,  # Narrow = focused erosion
        depth=0.7,  # Deep = long carving time
        
        # Ancient = smooth, gentle curves
        sinuosity=1.3,  # Meandering (not straight)
        edge_smoothness=0.9,  # Very smooth (weathered)
        
        # Geological constraint: Flows downhill
        follows_terrain_gradient=True
    )
    
    Phase 2: REQUIRED FEATURES (narrative constraints)
    ===================================================
    
    Rule: "Desert biome requires sand texture"
    Constraint: "Only dunes provide good sand"
    → Must add dunes
    
    Rule: "Wind deposits sand in wind shadows"
    Constraint: "Canyon creates wind shadow"
    → Dunes go in canyon floor/lee side
    
    Dunes(
        # Spatial constraint: In canyon wind shadow
        area=calculate_wind_shadow_zone(
            obstacle=canyon,
            wind_direction=narrative.wind_direction
        ),
        
        # Parameters from narrative
        amplitude=0.06,  # Subtle (peaceful, not dramatic)
        frequency=18,    # Medium wavelength
        angle=perpendicular(narrative.wind_direction),
        
        # Ancient = partially filled
        fill_level=0.4  # 40% filled canyon floor
    )
    
    Phase 3: OPTIONAL FEATURES (enhance story)
    ===========================================
    
    Rule: "Canyon needs scale reference"
    Optional: "Mountain provides scale + suggests water source"
    → Add mountain at canyon "head"
    
    Mountain(
        # Spatial: At canyon origin (water source story)
        position=near_point(canyon.start, radius=80),
        
        # Parameters for "backdrop" role
        height=0.75,      # Prominent but not dominant
        radius=60,        # Large enough for scale
        steepness=0.8,    # Moderate (ancient = weathered)
        
        # Ancient = smooth
        noise_detail=0.3,  # Low detail = smooth
        weathering=0.9     # High weathering
    )
    
    Rule: "Ridges can reinforce canyon structure"
    Optional: "Ridge parallel to canyon creates wall"
    → Add ridge along one canyon side
    
    Ridge(
        # Spatial: Parallel to canyon, offset
        start=parallel_line(canyon, offset=100)[0],
        end=parallel_line(canyon, offset=100)[1],
        
        # Parameters for "supporting" role
        height=0.4,   # Medium (supports canyon, not hero)
        width=20,     # Moderate
        steepness=0.7,  # Gentle (ancient)
        
        # Connect to mountain
        connects_to=[mountain]
    )
    
    Phase 4: DETAIL FEATURES (foreground interest)
    ===============================================
    
    Rule: "Mounds add foreground detail"
    Optional: "Erosion debris from canyon/ridge"
    → Scatter mounds near canyon mouth
    
    Mounds(
        # Spatial: Clustered near canyon mouth (debris field)
        count=5,
        positions=cluster_near(
            center=canyon.end,
            radius=60,
            clustering=0.7  # Moderate clustering
        ),
        
        # Parameters for "detail" role
        height_range=(0.12, 0.18),  # Small (detail scale)
        radius_range=(20, 30),      # Varied sizes
        
        # Story: Erosion debris
        noise_detail=0.5,  # Medium detail
        irregular=True     # Not perfect (natural)
    )
    
    RESULT
    ======
    FeatureComposition(
        primary=[canyon],
        secondary=[mountain, ridge, dunes],
        details=[mound_1, mound_2, mound_3, mound_4, mound_5],
        
        # Geological coherence
        formation_sequence=[
            "1. Tectonic uplift created mountain",
            "2. River carved canyon from mountain",
            "3. Canyon walls became ridges (resistant rock)",
            "4. River dried, wind deposited dunes",
            "5. Ongoing erosion creates mound debris"
        ],
        
        # Spatial relationships
        relationships={
            "canyon flows from mountain",
            "ridge parallels canyon",
            "dunes fill canyon floor",
            "mounds cluster at canyon mouth"
        },
        
        # Composition metrics
        scale_hierarchy=[mountain, canyon, ridge, dunes, mounds],
        focal_point=canyon,
        supporting_features=[mountain, ridge],
        texture_layer=dunes,
        detail_layer=mounds
    )
    """
    pass
```

**Key Insight:** Features emerge from **spatial constraints** and **geological relationships**, not random placement.

---

### Tool 3: `evaluate_narrative_coherence`

```python
def evaluate_narrative_coherence(
    composition: FeatureComposition,
    narrative: TerrainNarrative
) -> CoherenceAnalysis:
    """
    Evaluate if generated composition tells a coherent story.
    
    This is the REAL aesthetic evaluation.
    
    Checks:
    
    1. GEOLOGICAL PLAUSIBILITY
    ===========================
    
    ✓ Does canyon flow downhill? (water must flow)
    ✓ Do ridges align with canyon? (erosion pattern)
    ✓ Are dunes in wind shadow? (deposition logic)
    ✓ Are mounds near erosion source? (debris origin)
    ✓ Is mountain at canyon head? (water source)
    
    Score: 0.95 (highly plausible)
    
    2. NARRATIVE CONSISTENCY
    =========================
    
    ✓ All features support "ancient river" story
    ✓ Smooth forms consistent with "ancient" (weathered)
    ✓ Dunes consistent with "desert" biome
    ✓ Gentle curves consistent with "tranquil" mood
    ✓ No contradictions
    
    Score: 0.92 (very consistent)
    
    3. SCALE HIERARCHY
    ===================
    
    ✓ Clear primary feature (canyon)
    ✓ Clear secondary features (mountain, ridge, dunes)
    ✓ Clear detail layer (mounds)
    ✓ Size relationships realistic
    
    Scale sequence: Mountain (0.75) > Canyon (0.7) > Ridge (0.4) > Dunes (0.06) > Mounds (0.15)
    
    Score: 0.88 (good hierarchy)
    
    4. SPLATMAP COVERAGE
    =====================
    
    ✓ Sand channel active (dunes)
    ✓ Grass channel active (canyon floor, valley, mounds)
    ✓ Rock channel active (canyon walls, mountain, ridge)
    ✓ Snow channel active (mountain peak)
    
    All 4 channels used meaningfully!
    
    Score: 1.0 (perfect coverage)
    
    5. VISUAL FLOW
    ===============
    
    Eye path:
    1. Enter at mountain (focal point)
    2. Follow canyon down (natural flow)
    3. Ridge guides eye along canyon
    4. Discover dunes in canyon floor (detail)
    5. Exit at mound cluster (foreground)
    
    ✓ Natural eye movement
    ✓ Multiple points of interest
    ✓ Clear beginning, middle, end
    
    Score: 0.85 (good flow)
    
    6. EMOTIONAL RESONANCE
    =======================
    
    Target mood: "ancient tranquility"
    
    ✓ Smooth forms evoke "ancient" (weathered)
    ✓ Gentle curves evoke "tranquil" (not jagged)
    ✓ Balanced composition evokes "peaceful"
    ✓ Muted height variation evokes "calm"
    
    Mood match: 0.90 (strong resonance)
    
    OVERALL QUALITY
    ===============
    Weighted average: 0.92 (excellent)
    
    VERDICT: ✓ COHERENT - Ready to generate!
    
    If score < 0.8, would suggest refinements and regenerate.
    """
    
    return CoherenceAnalysis(
        geological_plausibility=0.95,
        narrative_consistency=0.92,
        scale_hierarchy=0.88,
        splatmap_coverage=1.0,
        visual_flow=0.85,
        emotional_resonance=0.90,
        overall_quality=0.92,
        
        problems=[],  # None found!
        
        design_notes=[
            "Canyon serves as primary hero feature",
            "Mountain provides scale reference and water source story",
            "Ridge reinforces canyon structure",
            "Dunes activate sand channel (required for desert feel)",
            "Mounds add foreground detail and erosion story",
            "All features support 'ancient river' geological narrative",
            "Smooth forms consistent with ancient weathering",
            "Gentle curves support tranquil mood"
        ]
    )
```

**Key Insight:** Good composition emerges from geological coherence, not from applying design rules.

---

### Tool 4: `refine_narrative` (if coherence < 0.8)

```python
def refine_narrative(
    composition: FeatureComposition,
    coherence: CoherenceAnalysis,
    narrative: TerrainNarrative
) -> TerrainNarrative:
    """
    Adjust narrative based on what's not working.
    
    Example problems and fixes:
    
    Problem: "Canyon flows uphill" (geological_plausibility = 0.4)
    Fix: Adjust water_history to "underground piping" OR adjust terrain gradient
    
    Problem: "No sand texture" (splatmap_coverage = 0.6, missing B channel)
    Fix: Add dunes (only source of good sand)
    
    Problem: "All same size" (scale_hierarchy = 0.5)
    Fix: Increase primary feature size, decrease detail feature size
    
    Problem: "Too busy, chaotic" (visual_flow = 0.5)
    Fix: Reduce feature count, simplify composition
    
    Problem: "Doesn't feel ancient" (emotional_resonance = 0.6)
    Fix: Increase weathering_level → smoother forms
    
    Returns: Refined narrative → regenerate composition
    """
    pass
```

---

## 🎭 **The Complete ReAct Loop**

```python
# User input
user_prompt = "Create a beautiful desert canyon with ancient tranquility"

# ============================================================
# ITERATION 1-2: UNDERSTAND (Develop Narrative)
# ============================================================

narrative = develop_terrain_narrative(
    user_intent=user_prompt,
    mood_keywords=["beautiful", "ancient", "tranquility"],
    desired_features=["desert", "canyon"]
)

# LLM reasoning:
# "Desert → Need sand texture → Dunes required
#  Canyon → Primary feature
#  Ancient + tranquil → Smooth, gentle, weathered
#  
#  Story: Ancient river carved canyon, dried up,
#         wind filling with sand, very peaceful
#  
#  Required primitives: canyon, dunes
#  Optional: mountain (scale), ridge (structure), mound (detail)"

# ============================================================
# ITERATION 3-5: GENERATE (Create Composition)
# ============================================================

composition = generate_from_narrative(
    narrative=narrative,
    scene_state=current_state
)

# LLM reasoning:
# "Canyon: Primary hero, meandering, smooth walls
#  Mountain: At canyon head (water source), moderate height
#  Ridge: Parallel to canyon (reinforces structure)
#  Dunes: In canyon floor (wind shadow), subtle amplitude
#  Mounds: Near canyon mouth (erosion debris), clustered
#  
#  All features follow geological constraints:
#  - Canyon flows downhill
#  - Dunes in wind shadow
#  - Ridge parallel to canyon
#  - Mounds near erosion source"

# ============================================================
# ITERATION 6-7: EVALUATE (Check Coherence)
# ============================================================

coherence = evaluate_narrative_coherence(
    composition=composition,
    narrative=narrative
)

# LLM reasoning:
# "Geological plausibility: ✓ High (0.95)
#  Narrative consistency: ✓ High (0.92)
#  Scale hierarchy: ✓ Good (0.88)
#  Splatmap coverage: ✓ Perfect (1.0)
#  Visual flow: ✓ Good (0.85)
#  Emotional resonance: ✓ Strong (0.90)
#  
#  Overall: 0.92 (excellent)
#  
#  No problems detected. Ready to generate!"

if coherence.overall_quality >= 0.8:
    # SUCCESS! Convert to actions
    actions = composition.to_actions()
    
    return {
        "actions": actions,
        "success": True,
        "formation_story": narrative.formation_story,
        "coherence_score": coherence.overall_quality,
        "design_notes": coherence.design_notes,
        
        "primitives_used": {
            "canyon": 1,
            "mountain": 1,
            "ridge": 1,
            "dunes": 1,
            "mound": 5
        },
        
        "splatmap_preview": {
            "R_grass": "Canyon floor, valley, mounds (40%)",
            "G_rock": "Canyon walls, mountain, ridge sides (30%)",
            "B_sand": "Dunes in canyon floor (20%)",
            "A_snow": "Mountain peak (10%)"
        }
    }

else:
    # ITERATION 8-9: REFINE (Adjust and Retry)
    refined_narrative = refine_narrative(
        composition=composition,
        coherence=coherence,
        narrative=narrative
    )
    
    # Regenerate with refined narrative...
```

---

## 💎 **Why This Works**

### **1. Constrained Primitives = Clear Roles**

With only 6 primitives, each has a **clear geological role**:

```python
"Need sand?" → Dunes (only option)
"Need focal point?" → Mountain or canyon
"Need structure?" → Ridge
"Need detail?" → Mound
"Need balance?" → Valley
```

No analysis paralysis. Clear decisions.

### **2. Geological Coherence = Beauty**

If the story makes sense, it looks beautiful:

```python
✓ Canyon flows from mountain (water source)
✓ Dunes in canyon floor (wind shadow)
✓ Ridge parallel to canyon (erosion pattern)
✓ Mounds at canyon mouth (debris field)

= Looks natural because it IS natural
```

### **3. Splatmap Coverage = Visual Richness**

All 4 channels activated:

```python
Canyon + Valley + Mound → Grass (R)
Mountain + Ridge walls → Rock (G)
Dunes → Sand (B) ← ONLY source!
Mountain peak → Snow (A)

= Rich, varied textures
```

### **4. Scale Hierarchy = Awe**

Clear size relationships:

```python
Mountain (0.75) > Canyon (0.7) > Ridge (0.4) > Mound (0.15) > Dunes (0.06)

Big → Medium → Small = Natural scale progression
```

### **5. Narrative Iteration = Quality**

Don't stop until coherence > 0.8:

```python
Iteration 1-2: Develop story
Iteration 3-5: Generate features
Iteration 6-7: Evaluate coherence
if coherence < 0.8:
    Iteration 8-9: Refine and regenerate
    
Keep iterating until beautiful!
```

---

## 🚀 **Implementation Plan**

### **Week 1: Core Tools**

1. `develop_terrain_narrative` - Extract story from user intent
2. Narrative archetype library (Water's Legacy, Ancient Uplift, Wind Architect, etc.)
3. Mood → parameter mapping ("ancient" → high weathering, smooth forms)

### **Week 2: Generative Constraints**

1. `generate_from_narrative` - Constraint-based feature generation
2. Spatial constraint system (wind shadow, flow paths, etc.)
3. Geological relationship rules (canyon from mountain, dunes in shadow, etc.)

### **Week 3: Coherence Evaluation**

1. `evaluate_narrative_coherence` - Multi-dimensional quality scoring
2. Plausibility checks (flows downhill, correct deposition zones, etc.)
3. Splatmap coverage analysis
4. Visual flow calculation

### **Week 4: Refinement & Polish**

1. `refine_narrative` - Problem detection and correction
2. Full iteration loop testing
3. Quality tuning (target: 0.8+ coherence)
4. Edge cases and failure modes

---

## 📊 **Success Criteria**

A successful generation achieves:

1. **Coherence > 0.8** across all dimensions
2. **All 4 splatmap channels** used meaningfully
3. **Clear scale hierarchy** (3+ levels)
4. **Geological plausibility** (story makes sense)
5. **Emotional resonance** (matches user mood)
6. **Unique every time** (no formulaic patterns)

---

## 🎯 **The Deep Answer (Final)**

**The system doesn't "place features" - it simulates geological storytelling.**

1. **Understand** the user's emotional intent
2. **Develop** a geological narrative that evokes that emotion
3. **Generate** features from narrative constraints (not random placement)
4. **Evaluate** geological coherence (not composition rules)
5. **Refine** the narrative until coherence emerges
6. **Result**: Beautiful, believable, unique terrain

**6 primitives × Infinite narratives × Constraint-based generation = Endless beauty** ✨

---

*"Beauty emerges when you simulate nature correctly, using the smallest set of tools that can tell any story."*

