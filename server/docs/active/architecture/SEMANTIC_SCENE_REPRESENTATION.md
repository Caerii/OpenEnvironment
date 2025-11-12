# Semantic Scene Representation: The Memory of Intent

> *"The terrain remembers not just what was built, but why it was built, and how its pieces relate to one another."*

## The Current State: Geometry Without Memory

When a user speaks to our terrain system, they speak in the language of intent and meaning. They say *"create a desert with rolling dunes"* and mean something more than coordinates and parameters. They envision a scene, a composition, a story told in landscape.

Our system, however, speaks only in geometry. It understands *where* things are, but not *what* they mean. It knows that a mountain exists at coordinates (128, 256) with a radius of 56, but it has forgotten—if it ever knew—that this mountain was *"the left mountain"* from the user's command, part of *"two mountains on the left"*, forming one wall of a conceptual *"mountain pass"*.

This is the fundamental limitation we address: **the gap between geometric representation and semantic understanding**.

---

## The Architecture of Understanding

### The Three-Tier Parser: A Cascade of Intelligence

The system processes natural language through a carefully orchestrated cascade, each tier bringing different capabilities:

**Parser Order (as of November 2025):**

1. **Narrative Pipeline** (PRIMARY) — The storyteller
   - Interprets aesthetic and narrative commands
   - Understands intent through geological storytelling
   - Transforms *"create a dramatic desert"* into a composition

2. **SemanticParser** (FALLBACK) — The reasoner
   - Employs LLM-powered reasoning with ReAct agent
   - Handles complex spatial relationships
   - Resolves ambiguous references through context

3. **CommandParser** (FINAL FALLBACK) — The pragmatist
   - Regex-based pattern matching
   - Always available, no external dependencies
   - Ensures the system never fails silently

This three-tier approach ensures that simple commands execute instantly, while complex aesthetic requests receive the full power of narrative understanding.

### The Current State Structure: Geometry Preserved

```json
{
  "features": [
    {"id": 1, "type": "mountain", "x": 128, "y": 256, "radius": 56, "height": 0.75},
    {"id": 2, "type": "valley", "x": 384, "y": 128, "radius": 64, "depth": 0.55}
  ],
  "seed": 0,
  "next_id": 3
}
```

This structure is precise, deterministic, and complete—for geometry. But it lacks the semantic layer that would allow the system to understand *relationships*, *intent*, and *composition*.

---

## The Four Gaps in Our Understanding

### Gap One: The Absence of Semantic Memory

The state stores geometric data with mathematical precision, but semantic meaning evaporates the moment features are created. The system knows:

- ✅ *"There's a mountain at (128, 256) with radius 56"*

But it cannot answer:

- ❌ *"Which mountain did the user mean when they said 'the left mountain'?"*
- ❌ *"What scene does this mountain belong to?"*
- ❌ *"How does this mountain relate to the valley nearby?"*

**Example:**
```python
User: "create a desert with rolling dunes"
System: Creates dunes [IDs 1,2,3], stores geometry
User: "make the dunes taller"
System: ❌ Which dunes? The system has forgotten the semantic connection.
```

### Gap Two: The Blindness to Spatial Relationships

Spatial relationships exist implicitly in the geometry, but they are not *explicitly represented*. The system cannot reason about:

- Proximity: *"near the mountains"*
- Betweenness: *"between the two peaks"*
- Grouping: *"the mountain range"*
- Composition: *"the valley entrance"*

**Example:**
```python
User: "add a valley between the two mountains"
Current system:
- Knows there are 2 mountains (IDs 4, 5)
- Cannot understand "between" as a spatial relationship
- Cannot calculate midpoint without explicit coordinates
- Cannot create the semantic link: valley BETWEEN mountains
```

### Gap Three: The Loss of Contextual Understanding

Each command exists in isolation. The system cannot connect:

- *"create a desert with dunes"* → *"make the dunes taller"*
- *"add two mountains on the left"* → *"add another mountain"* (where should it go?)
- *"create a mountain pass"* → *"widen the pass"* (which features compose it?)

**Example:**
```python
User sequence:
"create a desert with dunes"  → Creates dunes
"add two mountains on the left" → Creates mountains
"make the dunes taller" → ❌ Which dunes? System doesn't remember the semantic link.
```

### Gap Four: The Missing Compositional Memory

When a user creates *"a mountain pass with steep walls"*, the system generates five features: two mountains, a valley, and two cliffs. But it doesn't remember that these five features form a *conceptual whole*—a mountain pass.

**Example:**
```python
User: "create a mountain pass with steep walls"
System generates: [mountain1, mountain2, valley, cliff1, cliff2]
System stores: Five separate geometric features
System forgets: These form a conceptual "mountain pass"

User: "make the mountain pass wider"
System: ❌ What is "the mountain pass"? It's just five features now.
```

---

## The Vision: Semantic Scene Representation

### The Concept: A Scene Graph That Remembers

Imagine a data structure that preserves not just geometry, but *meaning*. A structure that remembers:

- **What** was created (the features)
- **Why** it was created (the user's intent)
- **How** pieces relate (spatial and semantic relationships)
- **When** it was created (temporal context)

This is the semantic scene graph—a memory layer that transforms the system from a geometric calculator into a *terrain storyteller*.

### The Structure: Entities, Relationships, and Constraints

```python
{
  "features": [...],  # Existing geometric data (unchanged)
  "semantic_scene": {
    "entities": {
      "desert_1": {
        "type": "scene",
        "label": "desert",
        "keywords": ["desert", "arid", "sandy"],
        "description": "desert with rolling dunes",
        "feature_refs": [1, 2, 3],  # Links to geometric features
        "created_at": "2024-01-15T10:30:00Z",
        "user_intent": "create a desert with rolling dunes"
      },
      "mountain_group_1": {
        "type": "group",
        "label": "two mountains on the left",
        "keywords": ["mountain", "left", "pair", "two"],
        "description": "two mountains positioned on the left side",
        "feature_refs": [4, 5],
        "spatial_constraint": "left",
        "composition": "group",
        "relationship": "siblings",
        "created_at": "2024-01-15T10:30:15Z",
        "user_intent": "two mountains on the left"
      },
      "mountain_pass_1": {
        "type": "composition",
        "label": "mountain pass",
        "keywords": ["pass", "entrance", "gap", "between"],
        "description": "valley passage between two mountains",
        "feature_refs": [4, 5, 6],  # mountains + valley
        "spatial_structure": {
          "layout": "linear",
          "components": {
            "walls": [4, 5],  # The mountains
            "passage": [6]    # The valley
          }
        },
        "emergent": true,  # Created implicitly by arrangement
        "created_at": "2024-01-15T10:31:00Z"
      }
    },
    "spatial_relationships": [
      {
        "type": "between",
        "entity": 6,  # valley
        "anchors": [4, 5],  # mountains
        "description": "valley is between the two mountains"
      },
      {
        "type": "part_of",
        "entity": "mountain_group_1",
        "parent": "mountain_pass_1",
        "description": "the mountain pair forms the walls of the pass"
      }
    ],
    "semantic_constraints": {
      "the_dunes": [1, 2, 3],  # When user says "the dunes", refers to these
      "the_mountains": [4, 5],  # When user says "the mountains"
      "the_left_side": {
        "region": "left",
        "entities": ["mountain_group_1"]
      }
    }
  }
}
```

This structure preserves the *story* of the terrain, not just its geometry.

---

## What This Enables: Six Transformations

### Transformation One: Contextual Reference Resolution

**Before:** The system cannot resolve *"the dunes"* without re-parsing the entire command history.

**After:** Direct semantic lookup transforms natural references into precise feature IDs.

**Example:**
```python
User: "create a desert with rolling dunes"
System: Creates dunes [IDs 1,2,3], tags as semantic_scene.entities.desert_1

User: "add two mountains on the left"
System: Creates mountains [IDs 4,5], tags as mountain_group_1

User: "make the dunes taller"
System: 
  1. Resolves "the dunes" → semantic_constraints["the_dunes"] → [1,2,3]
  2. Modifies features 1, 2, 3
  3. ✅ Natural reference resolved instantly
```

### Transformation Two: Spatial Reasoning

**Before:** The system cannot understand spatial relationships like *"between"*, *"near"*, or *"surrounding"*.

**After:** Spatial relationships are explicitly represented and can be reasoned about.

**Example:**
```python
User: "add a valley between the two mountains"

System reasoning:
1. Parse: wants valley, position="between", reference="two mountains"
2. Look up semantic_scene.entities.mountain_group_1
3. Get feature_refs [4, 5] (the two mountains)
4. Calculate midpoint between mountains[4] and mountains[5]
5. Place valley at midpoint
6. Create spatial_relationship: valley BETWEEN mountains
7. ✅ Spatial reasoning enabled
```

**What else becomes possible:**
- *"add hills surrounding the valley"* → Finds valley, places hills in circle
- *"create a path from the left mountain to the right mountain"* → Understands endpoints
- *"place a lake at the lowest point"* → Semantic search for lowest valley
- *"add cliffs along the northern edge"* → Understands directional context

### Transformation Three: Compositional Scene Memory

**Before:** Compositions like *"mountain pass"* exist only in the user's mind. The system sees five separate features.

**After:** Compositions are explicitly represented as semantic entities.

**Example:**
```python
User: "create a mountain pass with steep walls"

System generates:
- 2 mountains (walls)
- 1 valley (passage)
- 2 cliffs (steepness)

Semantic scene stores:
{
  "mountain_pass_1": {
    "type": "composition",
    "label": "mountain pass",
    "feature_refs": [1,2,3,4,5],
    "structure": {
      "walls": [1,2],
      "passage": [3],
      "details": [4,5]
    }
  }
}

User: "make the mountain pass wider"
System: 
  1. Understands "mountain pass" as composed entity
  2. Widens valley (passage)
  3. Increases distance between mountains (walls)
  4. Adjusts cliffs accordingly
  5. ✅ Compositional editing enabled
```

### Transformation Four: Intelligent Feature Placement

**Before:** *"add another mountain"* requires explicit coordinates or regions.

**After:** The system can infer placement based on existing scene composition.

**Example:**
```python
User: "add another mountain"

System reasoning:
1. Analyze semantic_scene
2. Find existing mountain_group_1 in "left" region
3. Infer user likely wants balance
4. Suggest placement on "right" side
5. Or cluster with existing mountains if that makes more sense

Prompt to LLM:
"Current scene has: desert with dunes (center), two mountains (left)
 User wants: add another mountain
 Spatial analysis: Left is occupied, right is empty
 Suggestion: Place on right for balance, or group with left for 'three peaks'"
```

### Transformation Five: Natural Modification

**Before:** *"make the desert more dramatic"* fails because the system doesn't know what *"the desert"* encompasses.

**After:** Semantic entities enable natural, context-aware modifications.

**Example:**
```python
User: "make the desert more dramatic"

System reasoning:
1. Look up semantic_scene.entities.desert_1
2. Get feature_refs [1,2,3] (the dunes)
3. Understand "dramatic" = increase amplitude/contrast
4. Modify all dune features:
   - Increase amplitude by 30%
   - Increase frequency for sharper peaks
   - Add variation
5. ✅ Natural modification enabled
```

### Transformation Six: Scene Understanding for Context

**Before:** The parser operates without scene context, making ambiguous references difficult.

**After:** The parser receives rich scene context, enabling intelligent interpretation.

**Example:**
```python
# Enhanced prompt to semantic parser:
f"""
Current Scene Context:
- desert_1: desert with rolling dunes (features [1,2,3] in center region)
- mountain_group_1: two mountains on the left (features [4,5] in left region)
- Spatial layout: left=mountains, center=dunes, right=empty

User command: "{user_input}"

Based on the scene context, parse this command intelligently:
- If referring to "the dunes/desert", use IDs [1,2,3]
- If referring to "the mountains", use IDs [4,5]
- If placing "another", consider existing spatial distribution
- If using relational terms (between, near, far from), reference existing entities
"""
```

**This enables context-aware parsing:**
- *"add a lake"* → LLM knows scene is desert, suggests placement in valley/low area
- *"add more mountains"* → LLM sees 2 exist on left, suggests right or grouping
- *"make it more forested"* → LLM knows current biome is desert, transitions appropriately

---

## Implementation Architecture

### Phase 1: Basic Semantic Tagging

The foundation is a simple but powerful abstraction: the semantic entity.

```python
class SemanticEntity:
    """Represents a semantic entity in the scene—a memory of intent."""
    
    def __init__(self, entity_id: str, entity_type: str, label: str):
        self.id = entity_id
        self.type = entity_type  # "scene", "group", "composition", "feature"
        self.label = label  # User's words, preserved
        self.keywords = []  # Extracted keywords for matching
        self.description = ""  # Natural language description
        self.feature_refs = []  # List of feature IDs (links to geometry)
        self.metadata = {}  # Additional semantic info
        self.created_at = time.time()
        self.user_intent = ""  # Original command, preserved

class SemanticSceneGraph:
    """Manages semantic representation of the terrain scene—the memory layer."""
    
    def __init__(self):
        self.entities = {}  # entity_id -> SemanticEntity
        self.relationships = []  # Spatial/semantic relationships
        self.constraints = {}  # Reference resolution ("the dunes" → IDs)
    
    def add_entity(self, entity: SemanticEntity):
        """Add a semantic entity to the scene, updating constraints."""
        self.entities[entity.id] = entity
        self._update_constraints(entity)
    
    def resolve_reference(self, text: str) -> List[int]:
        """
        Resolve natural language reference to feature IDs.
        
        This is the magic that makes "the dunes" work.
        
        Examples:
        - "the dunes" → [1, 2, 3]
        - "the mountains" → [4, 5]
        - "the desert" → [1, 2, 3] (via entity lookup)
        """
        text_lower = text.lower()
        
        # Check direct constraints first (fastest path)
        for key, value in self.constraints.items():
            if key in text_lower:
                if isinstance(value, list):
                    return value
                elif isinstance(value, dict) and "entities" in value:
                    return self._expand_entity_refs(value["entities"])
        
        # Check entity labels (semantic matching)
        for entity in self.entities.values():
            if entity.label.lower() in text_lower:
                return entity.feature_refs
            for keyword in entity.keywords:
                if keyword.lower() in text_lower:
                    return entity.feature_refs
        
        return []
    
    def find_spatial_context(self, reference: str) -> Dict:
        """
        Find spatial context for placement.
        
        Example: "between the mountains" → {type: "between", anchors: [4,5]}
        """
        relationships = [r for r in self.relationships 
                        if reference in r.get("description", "")]
        if relationships:
            return relationships[0]
        return {}
```

### Phase 2: Enhanced Semantic Parser

**Note:** This section describes a potential enhancement. The current implementation (as of November 2025) uses a three-tier parser system: Narrative Pipeline (PRIMARY) → SemanticParser (FALLBACK) → CommandParser (FINAL FALLBACK). See `CURRENT_ARCHITECTURE_STATUS.md` for current implementation details.

```python
class EnhancedSemanticParser(SemanticParser):
    """Semantic parser with scene context awareness."""
    
    def parse_with_context(self, command: str, scene_graph: SemanticSceneGraph) -> Dict:
        """Parse command with full scene context—the parser that remembers."""
        
        # Build context summary for LLM
        context = self._build_scene_context(scene_graph)
        
        # Enhanced system prompt
        system_prompt = f"""You are a terrain generation command parser with scene awareness.

Current Scene Context:
{context}

Parse the user command considering this context:
- Resolve references like "the dunes", "the mountains" to existing features
- Suggest intelligent placement based on existing spatial layout
- Understand compositional relationships
- Infer user intent from scene state

{self.base_system_prompt}"""

        # Parse with context
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            model=self.model,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return self._normalize_with_context(response, scene_graph)
    
    def _build_scene_context(self, scene_graph: SemanticSceneGraph) -> str:
        """Build textual scene context for LLM—the memory made readable."""
        lines = []
        
        for entity in scene_graph.entities.values():
            feature_count = len(entity.feature_refs)
            lines.append(
                f"- {entity.label} ({entity.type}): {entity.description}, "
                f"{feature_count} features, "
                f"created from: '{entity.user_intent}'"
            )
        
        # Add spatial summary
        spatial_summary = self._summarize_spatial_layout(scene_graph)
        lines.append(f"\nSpatial layout: {spatial_summary}")
        
        return "\n".join(lines)
```

### Phase 3: Action Execution with Semantic Tracking

```python
def apply_actions_with_semantics(cmd: str, state: Dict, base_biome_fn=None) -> Tuple:
    """
    Enhanced apply_actions that maintains semantic scene graph.
    
    This is where geometry and semantics meet—where features are created
    and their meaning is preserved.
    """
    # Load existing semantic scene
    scene_graph = SemanticSceneGraph()
    if "semantic_scene" in state:
        scene_graph.load(state["semantic_scene"])
    
    # Parse with context
    parser = EnhancedSemanticParser()
    parsed = parser.parse_with_context(cmd, scene_graph)
    
    actions = parsed.get("actions", [])
    feature_state = FeatureState(state)
    
    # Execute actions and track semantics
    for action in actions:
        # Execute the action (geometry)
        command = create_command_from_dict(action)
        feature_ids = command.execute(builder, feature_state, seed)
        
        # Create semantic entity for this action (meaning)
        entity = SemanticEntity(
            entity_id=f"{action['type']}_{uuid4()}",
            entity_type="group" if action.get("count", 1) > 1 else "feature",
            label=self._extract_label(cmd, action)
        )
        entity.feature_refs = feature_ids
        entity.keywords = self._extract_keywords(cmd, action)
        entity.description = self._generate_description(action)
        entity.user_intent = cmd
        
        scene_graph.add_entity(entity)
        
        # Track spatial relationships if inferrable
        if "position" in action and action["position"].get("region"):
            scene_graph.add_constraint(
                f"the {action['type']}{'s' if action.get('count', 1) > 1 else ''}",
                feature_ids
            )
    
    # Save semantic scene to state (persist the memory)
    state["semantic_scene"] = scene_graph.to_dict()
    
    return h, state, splat
```

---

## The Benefits: A System That Understands

### For Users: Natural Interaction

1. **Natural references**: *"make the dunes taller"* just works
2. **Spatial reasoning**: *"add a valley between the mountains"* understands relationships
3. **Scene modification**: *"make the desert more dramatic"* modifies the whole composition
4. **Compositional edits**: *"widen the mountain pass"* understands the composition
5. **Contextual placement**: *"add another mountain"* intelligently placed based on scene

### For the System: Intelligent Processing

1. **Better context**: LLM has full scene understanding, not just geometry
2. **Smarter parsing**: Can resolve ambiguous references through semantic lookup
3. **Spatial intelligence**: Understands relationships and proximity explicitly
4. **Memory**: Remembers user's conceptual organization, not just coordinates
5. **Emergent understanding**: Recognizes compositions (*"mountain pass"*) as semantic entities

### For Future Features: Extensibility

1. **Scene queries**: *"show me all mountains"* → semantic search
2. **Style transfer**: *"make it more alpine"* → understands scene type
3. **Procedural expansion**: *"add more like this"* → understands patterns
4. **Scene templates**: Save *"mountain pass"* as reusable composition
5. **Constraint preservation**: *"keep the symmetry"* during edits
6. **Natural undo**: *"remove the last mountain group"* → removes all related features

---

## Conclusion: From Geometry to Understanding

The semantic scene representation transforms the system from:

**Current:** *"Command → Geometric shapes → State"*

**Enhanced:** *"Intent → Semantic understanding → Contextual composition → Persistent scene memory"*

This enables **natural, intelligent, context-aware terrain editing** that understands not just *what* features exist, but *why* they were created and *how* they relate to each other.

The terrain remembers. The terrain understands. The terrain tells stories.
