# Narrative-ReAct Deep Integration Plan

## Current State Analysis

### **Problem: Narrative and ReAct Are Loosely Coupled**

**Current Flow:**
1. ReAct agent can optionally call `generate_narrative_composition` tool
2. Narrative generates features independently
3. ReAct treats narrative as just another tool, not a constraint system
4. Narrative constraints (archetype, aesthetic goals, geological process) are lost after generation

**Issues:**
- ❌ Narrative constraints don't inform spatial tool decisions
- ❌ Quality evaluation doesn't consider narrative context deeply
- ❌ Refinement loops don't maintain narrative coherence
- ❌ Spatial patterns from archetype aren't enforced
- ❌ Texture preferences from narrative aren't considered

---

## Deep Integration Strategy

### **1. Narrative as Constraint System**

**Concept:** Narrative should provide constraints that guide ALL ReAct decisions, not just initial generation.

**Implementation:**
- Extract narrative early (before ReAct loop)
- Pass narrative constraints to all tools
- Use narrative to inform spatial decisions, quality evaluation, refinement

**Key Constraints to Extract:**
- **Spatial Patterns:** Archetype clustering tendency, directional alignment
- **Feature Preferences:** Primary/secondary/accent feature types
- **Texture Preferences:** Preferred texture distributions from archetype
- **Composition Rules:** Focal point bias, depth layers, negative space
- **Aesthetic Goals:** Height/radius modifiers, noise preferences
- **Geological Constraints:** Process-based feature relationships

---

### **2. Constraint-Aware Tools**

**Spatial Tools Should Respect Narrative:**
- `calculate_position` → Use archetype spatial patterns
- `calculate_region_positions` → Apply clustering tendency
- `query_features` → Filter by narrative feature preferences

**Quality Tools Should Use Narrative:**
- `evaluate_terrain_quality` → Use narrative context for rubric
- `refine_composition` → Maintain narrative coherence
- Context rubrics should use narrative archetype

---

### **3. Narrative State Management**

**Store Narrative in Scene State:**
```python
scene_state["_narrative"] = {
    "archetype": "Ancient Uplift",
    "aesthetic_goals": ["dramatic", "monumental"],
    "spatial_patterns": {
        "clustering_tendency": 0.7,
        "directional_alignment": 45.0,
    },
    "feature_preferences": {
        "primary": ["mountain"],
        "secondary": ["valley", "cliff"],
        "accent": ["plateau"],
    },
    "texture_preferences": {
        "grass": 0.2,
        "rock": 0.5,
        "sand": 0.1,
        "snow": 0.2,
    },
    "composition_rules": {
        "focal_bias": (0.618, 0.382),
        "depth_layers": 3,
        "negative_space": 0.3,
    },
}
```

---

### **4. Constraint Propagation**

**Flow:**
1. **Extract Narrative** → Develop narrative from command
2. **Store Constraints** → Save to scene state
3. **ReAct Reasoning** → Use constraints in all decisions
4. **Quality Evaluation** → Check against narrative constraints
5. **Refinement** → Maintain narrative coherence

---

## Implementation Plan

### **Phase 1: Extract and Store Narrative**

**File: `server/semantic/react_agent_v2.py`**

```python
def solve(self, user_command: str, scene_state: Dict[str, Any], ...):
    # Extract narrative EARLY
    narrative = self._extract_narrative(user_command, scene_state)
    
    # Store narrative constraints in scene state
    if narrative:
        scene_state["_narrative"] = self._narrative_to_constraints(narrative)
        scene_state["_narrative_meta"] = {
            "archetype": narrative.archetype.name,
            "story": narrative.story,
            "aesthetic_goals": [g.value for g in narrative.aesthetic_goals],
        }
    
    # Continue with ReAct loop...
```

---

### **Phase 2: Constraint-Aware Spatial Tools**

**File: `server/semantic/tools/spatial_tools.py`**

```python
def calculate_position(
    scene_state: Dict[str, Any],
    feature_type: str,
    region: Optional[str] = None,
    ...
) -> Dict[str, Any]:
    # Get narrative constraints
    narrative = scene_state.get("_narrative", {})
    
    # Apply archetype spatial patterns
    if narrative:
        clustering = narrative.get("spatial_patterns", {}).get("clustering_tendency", 0.5)
        alignment = narrative.get("spatial_patterns", {}).get("directional_alignment")
        
        # Use clustering to determine spacing
        # Use alignment for directional patterns
        ...
```

---

### **Phase 3: Narrative-Aware Quality Evaluation**

**File: `server/semantic/tools/quality_tools.py`**

```python
def evaluate_terrain_quality(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    ...
) -> Dict[str, Any]:
    # Get narrative context
    narrative_meta = scene_state.get("_narrative_meta", {})
    narrative_constraints = scene_state.get("_narrative", {})
    
    # Use narrative for context rubric
    command = narrative_meta.get("archetype", "") + " " + " ".join(
        narrative_meta.get("aesthetic_goals", [])
    )
    
    # Check against narrative constraints
    # - Feature preferences
    # - Texture preferences
    # - Spatial patterns
    ...
```

---

### **Phase 4: Narrative-Coherent Refinement**

**File: `server/semantic/tools/quality_tools.py`**

```python
def refine_composition(
    scene_state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    feedback: str,
    ...
) -> Dict[str, Any]:
    # Get narrative constraints
    narrative = scene_state.get("_narrative", {})
    
    # Refine while maintaining narrative coherence
    # - Don't violate archetype constraints
    # - Maintain aesthetic goals
    # - Preserve spatial patterns
    ...
```

---

## Quality Improvements

### **1. Better Spatial Coherence**

**Before:** Features placed randomly or by simple rules
**After:** Features respect archetype spatial patterns
- Wind Architect → Features aligned with wind direction
- Ancient Uplift → Features clustered in uplift zones
- Water's Legacy → Features follow water flow patterns

---

### **2. Consistent Texture Distribution**

**Before:** Textures applied generically
**After:** Textures match narrative preferences
- Desert archetype → High sand, low grass
- Mountain archetype → High rock, snow at peaks
- Valley archetype → Balanced grass/rock

---

### **3. Aesthetic Goal Enforcement**

**Before:** Aesthetic goals only affect initial generation
**After:** Aesthetic goals guide all decisions
- "Dramatic" → Higher height variation, steeper slopes
- "Serene" → Gentler transitions, smoother forms
- "Rugged" → More noise, sharper features

---

### **4. Narrative Coherence in Refinement**

**Before:** Refinement can break narrative coherence
**After:** Refinement maintains narrative constraints
- Won't add features that violate archetype
- Won't change textures that break narrative
- Maintains spatial patterns during refinement

---

## Implementation Steps

### **Step 1: Extract Narrative Early** ✅
- Modify `ReActAgentV2.solve()` to extract narrative before loop
- Store narrative constraints in scene state

### **Step 2: Constraint Extraction** ✅
- Create `_narrative_to_constraints()` helper
- Extract spatial patterns, feature preferences, texture preferences

### **Step 3: Update Spatial Tools** ⏳
- Modify `calculate_position` to use narrative constraints
- Apply clustering tendency and directional alignment

### **Step 4: Update Quality Tools** ⏳
- Use narrative context in quality evaluation
- Check against narrative constraints

### **Step 5: Update Refinement** ⏳
- Maintain narrative coherence during refinement
- Don't violate archetype constraints

### **Step 6: Testing** ⏳
- Test with various commands
- Verify constraints are respected
- Check quality improvements

---

## Expected Outcomes

### **Quality Improvements:**
- ✅ Better spatial coherence (features follow archetype patterns)
- ✅ Consistent texture distribution (matches narrative preferences)
- ✅ Aesthetic goal enforcement (goals guide all decisions)
- ✅ Narrative coherence (refinement maintains constraints)

### **User Experience:**
- ✅ More predictable results (narrative constraints guide generation)
- ✅ Better quality (constraints ensure coherence)
- ✅ Faster refinement (constraints prevent bad changes)

---

## Next Steps

1. **Implement narrative extraction in ReAct**
2. **Create constraint extraction helper**
3. **Update spatial tools to use constraints**
4. **Update quality tools to check constraints**
5. **Test and iterate**

