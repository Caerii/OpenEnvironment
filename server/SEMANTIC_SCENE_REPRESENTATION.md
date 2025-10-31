# Semantic Scene Representation - Deep Analysis

## Current System Architecture

### How Natural Language Understanding Works Now

#### 1. **Command Flow**
```
User Input → SemanticParser → Actions List → Execute → State Update
```

#### 2. **Current Parsing System**

**Two-Stage Parsing:**
```python
# Stage 1: LLM-based semantic parser (Cerebras Qwen-3-235B)
parser.parse("create a desert with rolling dunes and two mountains on the left")

# Output: Structured actions
{
  "actions": [
    {"kind": "add", "type": "dunes", "count": 1, "position": {"region": "center"}},
    {"kind": "add", "type": "mountain", "count": 2, "position": {"region": "left"}}
  ]
}

# Stage 2: Action execution
- Create feature dictionaries (with x, y, radius, height, etc.)
- Add to state.features[] list
- Apply to terrain heightmap
```

**Current State Structure:**
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

### Current Limitations

#### ❌ **Problem 1: No Semantic Memory**
The state stores **geometric data** but not **semantic meaning**:
- ✅ Knows: "There's a mountain at (128, 256) with radius 56"
- ❌ Doesn't know: "This is the 'left mountain' the user mentioned"
- ❌ Doesn't know: "This mountain is part of a 'desert scene'"
- ❌ Doesn't know: "These two mountains create a 'valley entrance'"

#### ❌ **Problem 2: No Spatial Relationships**
```python
# User says: "add a valley between the two mountains"
# Current system:
- Knows there are 2 mountains
- Doesn't know their spatial relationship
- Can't understand "between"
- Can't reason about proximity, adjacency, or grouping
```

#### ❌ **Problem 3: No Contextual Understanding**
```python
# User sequence:
"create a desert with dunes"  → Creates dunes
"add two mountains on the left" → Creates mountains
"make the dunes taller" → Which dunes? System doesn't remember "the dunes from the desert command"
```

#### ❌ **Problem 4: No Scene Composition Memory**
```python
# User creates: "a mountain pass with steep walls"
# System stores: [mountain1, mountain2, valley, cliff1, cliff2]
# But doesn't remember: "These 5 features form a conceptual 'mountain pass'"
```

---

## Proposed: Semantic Scene Representation

### Concept: Scene Graph with Semantic Labels

```python
{
  "features": [...],  # Existing geometric data
  "semantic_scene": {
    "entities": {
      "desert_1": {
        "type": "scene",
        "label": "desert",
        "keywords": ["desert", "arid", "sandy"],
        "description": "desert with rolling dunes",
        "feature_refs": [1, 2, 3],  # IDs of dunes features
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

---

## What This Enables

### 1. **Contextual Reference Resolution** 🎯

**Scenario:**
```python
User: "create a desert with rolling dunes"
System: Creates dunes [IDs 1,2,3], tags as semantic_scene.entities.desert_1

User: "add two mountains on the left"
System: Creates mountains [IDs 4,5], tags as mountain_group_1, links to "left"

User: "make the dunes taller"
System: Resolves "the dunes" → looks up semantic_constraints["the_dunes"] → [1,2,3]
        Modifies features 1, 2, 3
```

**Current System:** ❌ Can't resolve "the dunes" without re-parsing entire history

**With Semantic Scene:** ✅ Direct lookup in semantic memory

### 2. **Spatial Reasoning** 🗺️

**Scenario:**
```python
User: "add a valley between the two mountains"

System reasoning:
1. Parse: wants valley, position="between", reference="two mountains"
2. Look up semantic_scene.entities.mountain_group_1
3. Get feature_refs [4, 5]
4. Calculate midpoint between mountains[4] and mountains[5]
5. Place valley at midpoint
6. Create spatial_relationship: valley BETWEEN mountains
```

**What else becomes possible:**
- "add hills surrounding the valley" → finds valley, places hills in circle
- "create a path from the left mountain to the right mountain"
- "place a lake at the lowest point" → semantic search for lowest valley
- "add cliffs along the northern edge" → understands "northern" in scene context

### 3. **Compositional Scene Memory** 🏗️

**Scenario:**
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
System: Understands "mountain pass" as composed entity
        - Widens valley (passage)
        - Increases distance between mountains (walls)
        - Adjusts cliffs accordingly
```

**Without semantic memory:** ❌ Would need to modify each piece individually

**With semantic memory:** ✅ Understands the composition, modifies coherently

### 4. **Intelligent Feature Placement** 🧠

**Scenario:**
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

### 5. **Natural Modification** ✨

**Without Semantic Scene:**
```python
User: "make the desert more dramatic"
System: ❌ Doesn't know what "the desert" encompasses
```

**With Semantic Scene:**
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
```

### 6. **Scene Understanding for Context** 🎨

**With semantic scene, the LLM can be prompted with:**

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
- "add a lake" → LLM knows scene is desert, suggests placement in valley/low area
- "add more mountains" → LLM sees 2 exist on left, suggests right or grouping
- "make it more forested" → LLM knows current biome is desert, transitions appropriately

---

## Implementation Architecture

### Phase 1: Basic Semantic Tagging

```python
class SemanticEntity:
    """Represents a semantic entity in the scene."""
    def __init__(self, entity_id: str, entity_type: str, label: str):
        self.id = entity_id
        self.type = entity_type  # "scene", "group", "composition", "feature"
        self.label = label  # User's words
        self.keywords = []  # Extracted keywords for matching
        self.description = ""  # Natural language description
        self.feature_refs = []  # List of feature IDs
        self.metadata = {}  # Additional semantic info
        self.created_at = time.time()
        self.user_intent = ""  # Original command

class SemanticSceneGraph:
    """Manages semantic representation of the terrain scene."""
    def __init__(self):
        self.entities = {}  # entity_id -> SemanticEntity
        self.relationships = []  # Spatial/semantic relationships
        self.constraints = {}  # Reference resolution ("the dunes" → IDs)
    
    def add_entity(self, entity: SemanticEntity):
        """Add a semantic entity to the scene."""
        self.entities[entity.id] = entity
        self._update_constraints(entity)
    
    def resolve_reference(self, text: str) -> List[int]:
        """
        Resolve natural language reference to feature IDs.
        
        Examples:
        - "the dunes" → [1, 2, 3]
        - "the mountains" → [4, 5]
        - "the desert" → [1, 2, 3]
        """
        text_lower = text.lower()
        
        # Check direct constraints
        for key, value in self.constraints.items():
            if key in text_lower:
                if isinstance(value, list):
                    return value
                elif isinstance(value, dict) and "entities" in value:
                    # Resolve entity references
                    return self._expand_entity_refs(value["entities"])
        
        # Check entity labels
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
        relationships = [r for r in self.relationships if reference in r.get("description", "")]
        if relationships:
            return relationships[0]
        return {}
```

### Phase 2: Enhanced Semantic Parser

```python
class EnhancedSemanticParser(SemanticParser):
    """Semantic parser with scene context awareness."""
    
    def parse_with_context(self, command: str, scene_graph: SemanticSceneGraph) -> Dict:
        """Parse command with full scene context."""
        
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
        """Build textual scene context for LLM."""
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
        # Execute the action
        command = create_command_from_dict(action)
        feature_ids = command.execute(builder, feature_state, seed)
        
        # Create semantic entity for this action
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
    
    # Save semantic scene to state
    state["semantic_scene"] = scene_graph.to_dict()
    
    return h, state, splat
```

---

## Benefits Summary

### For Users 🎯

1. **Natural references**: "make the dunes taller" just works
2. **Spatial reasoning**: "add a valley between the mountains"
3. **Scene modification**: "make the desert more dramatic"
4. **Compositional edits**: "widen the mountain pass"
5. **Contextual placement**: "add another mountain" → intelligently placed

### For System 🧠

1. **Better context**: LLM has full scene understanding
2. **Smarter parsing**: Can resolve ambiguous references
3. **Spatial intelligence**: Understands relationships and proximity
4. **Memory**: Remembers user's conceptual organization
5. **Emergent understanding**: Recognizes compositions ("mountain pass")

### For Future Features 🚀

1. **Scene queries**: "show me all mountains"
2. **Style transfer**: "make it more alpine" → understands scene type
3. **Procedural expansion**: "add more like this" → understands patterns
4. **Scene templates**: Save "mountain pass" as reusable composition
5. **Constraint preservation**: "keep the symmetry" during edits
6. **Natural undo**: "remove the last mountain group" → removes all related

---

## Conclusion

The semantic scene representation transforms the system from:

**Current:** "Command → Geometric shapes → State"

**Enhanced:** "Intent → Semantic understanding → Contextual composition → Persistent scene memory"

This enables **natural, intelligent, context-aware terrain editing** that understands not just *what* features exist, but *why* they were created and *how* they relate to each other.

