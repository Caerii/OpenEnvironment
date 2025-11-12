# Semantic Context Requirements - Systematic Analysis

## 🎯 Core Question

**What information does the LLM need to maintain semantic identity and structural understanding of the scene?**

---

## 📊 Current State Analysis

### What We're Sending Now (After "Fix"):
```
=== SCENE ENTITIES ===
  'the mountains' → IDs [1, 3, 5] (mountains, peaks, summit)
  'the dunes' → IDs [2, 4, 6] (sand, desert, dune)
Entity types: {'feature': 8, 'group': 2}
```

### What We Lost:
- ❌ **Spatial relationships** (near, between, north of, etc.)
- ❌ **Feature locations** (where are these features?)
- ❌ **Feature attributes** (height, size, shape)
- ❌ **User intent history** (why was this created?)
- ❌ **Temporal ordering** (what was created when?)
- ❌ **Hierarchical structure** (/World/Features/Mountain_Group)
- ❌ **Tool parameter guidance** (how to use each feature type)

---

## 🎭 The Semantic Identity Problem

### Scenario 1: Spatial Reference
**User:** "Add a valley between the mountains"

**LLM needs:**
1. ✅ Entity labels ("the mountains")
2. ✅ Feature IDs ([1, 3, 5])
3. ❌ **Spatial positions** of features 1, 3, 5 (WHERE are they?)
4. ❌ **How to calculate "between"** two points

**Current capability:** Can identify mountains, but not calculate spatial position

---

### Scenario 2: Contextual Modification
**User:** "Make the tall mountains even taller"

**LLM needs:**
1. ✅ Entity labels ("the mountains")
2. ❌ **Which mountains are tall?** (need height attribute)
3. ❌ **Current height values** to know what "taller" means
4. ❌ **Parameter ranges** for height modification

**Current capability:** Can identify all mountains, but not filter by attribute

---

### Scenario 3: Historical Context
**User:** "Remove the terrain I just added"

**LLM needs:**
1. ❌ **Temporal ordering** (which features are newest?)
2. ❌ **User intent tracking** (what was the last user command?)
3. ❌ **Creation timestamps**

**Current capability:** No way to determine "just added"

---

### Scenario 4: Compositional Understanding
**User:** "Add hills around the existing mountains"

**LLM needs:**
1. ✅ Entity labels ("mountains")
2. ✅ Feature IDs
3. ❌ **Spatial positions** (where to place "around"?)
4. ❌ **Bounding regions** (how big is the mountain cluster?)
5. ❌ **Density calculation** (how many hills = "around"?)

**Current capability:** Limited - can identify target but not calculate placement

---

## 🧩 MCP Tool Design: What Tools Should Exist?

### Current Problem:
We're treating the LLM like a simple parser, but it should be an **intelligent scene understanding agent** with access to **semantic tools**.

### MCP Tool Categories Needed:

---

## 1️⃣ **Scene Query Tools** (Read Operations)

### A. `query_entities`
**Purpose:** Find entities matching criteria
```python
@tool(category=ToolCategory.QUERY)
def query_entities(
    label: Optional[str] = None,
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    created_after: Optional[float] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Query scene entities by various criteria.
    
    Returns:
        List of matching entities with full metadata
    """
```

**Example:** "Find all mountains created in the last minute"

---

### B. `get_feature_details`
**Purpose:** Get complete information about specific features
```python
@tool(category=ToolCategory.QUERY)
def get_feature_details(
    feature_ids: List[int]
) -> List[Dict]:
    """
    Get detailed information about specific features.
    
    Returns:
        - type (mountain, valley, etc.)
        - position (x, y)
        - attributes (height, radius, etc.)
        - creation_time
        - parent_entity
    """
```

**Example:** "What are the attributes of features [1, 3, 5]?"

---

### C. `get_spatial_relationships`
**Purpose:** Calculate spatial relationships between features
```python
@tool(category=ToolCategory.QUERY)
def get_spatial_relationships(
    reference_ids: List[int],
    relationship_type: str = "near"  # near, between, north_of, etc.
) -> Dict:
    """
    Calculate spatial relationships relative to reference features.
    
    Returns:
        - centroid position
        - bounding box
        - nearby_positions (for "around")
        - between_position (for "between")
        - directional_positions (for "north of")
    """
```

**Example:** "Calculate position between mountains [1, 3]"

---

### D. `query_scene_summary`
**Purpose:** Get high-level scene understanding
```python
@tool(category=ToolCategory.QUERY)
def query_scene_summary() -> Dict:
    """
    Get overall scene composition and statistics.
    
    Returns:
        - total_features: count
        - feature_type_distribution: {mountain: 5, valley: 3}
        - spatial_density_map: regions with high/low feature density
        - recent_changes: last 5 operations
        - dominant_biome: inferred from feature types
    """
```

**Example:** "What's the overall composition of the terrain?"

---

## 2️⃣ **Spatial Calculation Tools**

### A. `calculate_position`
**Purpose:** Calculate coordinates for spatial commands
```python
@tool(category=ToolCategory.SPATIAL)
def calculate_position(
    reference_ids: Optional[List[int]] = None,
    relationship: str = "near",  # near, between, around, north_of
    region: Optional[str] = None,  # "center", "left", "top-right"
    offset: Optional[Tuple[int, int]] = None
) -> Tuple[int, int]:
    """
    Calculate target position based on spatial reasoning.
    
    Handles:
        - "near the mountains" → position close to mountain centroid
        - "between X and Y" → midpoint calculation
        - "north of X" → position shifted north
        - "around X" → positions in circular pattern
    """
```

**Example:** "Where should I place a valley near features [1, 3]?"

---

### B. `calculate_region_positions`
**Purpose:** Generate multiple positions for "around", "scattered", etc.
```python
@tool(category=ToolCategory.SPATIAL)
def calculate_region_positions(
    count: int,
    reference_ids: Optional[List[int]] = None,
    pattern: str = "scattered",  # scattered, circular, line, grid
    radius: int = 100
) -> List[Tuple[int, int]]:
    """
    Generate multiple positions based on spatial pattern.
    
    Patterns:
        - scattered: random positions in region
        - circular: positions around reference point
        - line: positions along a line
        - grid: evenly spaced grid
    """
```

**Example:** "Where should I place 5 hills around the mountains?"

---

## 3️⃣ **Reference Resolution Tools**

### A. `resolve_reference`
**Purpose:** Convert natural language to feature IDs
```python
@tool(category=ToolCategory.RESOLUTION)
def resolve_reference(
    reference: str,
    filter_type: Optional[str] = None,
    filter_attribute: Optional[Dict] = None
) -> List[int]:
    """
    Resolve natural language reference to feature IDs.
    
    Supports:
        - Labels: "the mountains" → entity lookup
        - Ordinals: "last mountain" → temporal ordering
        - Attributes: "tall mountains" → attribute filtering
        - Spatial: "mountains on the left" → spatial filtering
    """
```

**Example:** "Which features are 'the tall mountains'?"

---

### B. `resolve_temporal_reference`
**Purpose:** Resolve time-based references
```python
@tool(category=ToolCategory.RESOLUTION)
def resolve_temporal_reference(
    temporal_phrase: str  # "just added", "recent", "oldest"
) -> List[int]:
    """
    Resolve temporal references to feature IDs.
    
    Handles:
        - "just added" / "recently added" → last 1-5 features
        - "oldest" / "first" → earliest created
        - "last 3 mountains" → last N of type
    """
```

**Example:** "Which features were 'just added'?"

---

## 4️⃣ **Parameter Inference Tools**

### A. `infer_feature_parameters`
**Purpose:** Suggest appropriate parameters based on context
```python
@tool(category=ToolCategory.INFERENCE)
def infer_feature_parameters(
    feature_type: str,
    user_modifiers: List[str],  # ["tall", "wide", "steep"]
    existing_features: List[Dict],  # For relative sizing
    position: Tuple[int, int]
) -> Dict:
    """
    Infer appropriate parameters for new feature.
    
    Considers:
        - User modifiers: "tall" → height: 0.9
        - Existing features: match or contrast sizes
        - Position: adjust for edge cases
        - Defaults: sensible parameter ranges
    """
```

**Example:** "What parameters should I use for a 'tall steep mountain'?"

---

### B. `suggest_modification`
**Purpose:** Calculate modification values
```python
@tool(category=ToolCategory.INFERENCE)
def suggest_modification(
    feature_ids: List[int],
    modification_type: str,  # "taller", "wider", "deeper"
    intensity: str = "moderate"  # "slightly", "moderate", "much"
) -> Dict:
    """
    Suggest parameter changes for modifications.
    
    Returns:
        - current_values: existing parameters
        - suggested_values: modified parameters
        - change_percent: % change applied
    """
```

**Example:** "How should I modify features [1, 3] to make them 'much taller'?"

---

## 5️⃣ **Validation & Safety Tools**

### A. `validate_action`
**Purpose:** Check if action is semantically valid
```python
@tool(category=ToolCategory.VALIDATION)
def validate_action(
    action: Dict
) -> Dict:
    """
    Validate if proposed action makes semantic sense.
    
    Checks:
        - Position bounds (0-511)
        - Parameter ranges
        - Feature compatibility
        - Collision detection
        - Resource limits
    
    Returns:
        - valid: bool
        - issues: List[str] (warnings/errors)
        - suggestions: List[str] (how to fix)
    """
```

**Example:** "Is it valid to add a mountain at position (600, 300)?" → No, out of bounds

---

## 6️⃣ **Composition Tools**

### A. `suggest_composition`
**Purpose:** Help with multi-feature compositions
```python
@tool(category=ToolCategory.COMPOSITION)
def suggest_composition(
    intent: str,  # "dramatic landscape", "rolling hills", "mountain range"
    available_space: Optional[Dict] = None
) -> List[Dict]:
    """
    Suggest multi-feature composition based on high-level intent.
    
    Returns:
        List of suggested features with:
            - type
            - position
            - parameters
            - relationships
    """
```

**Example:** "How should I create a 'dramatic mountain range'?"

---

## 📐 Systematic Prompt Architecture

### Tier 1: Essential Context (Always Include)
**Budget: ~400 tokens**

```
=== SCENE IDENTITY ===
Entities (most recent 10):
  'the mountains' → [1,3,5] at center (mountain, 3 features, tall)
  'the dunes' → [2,4,6] at left (dunes, 3 features, rolling)
  
Recent actions (last 3):
  1. Added mountains at center
  2. Added dunes at left
  3. Modified mountains to be taller
```

**Purpose:** Minimal scene awareness for reference resolution

---

### Tier 2: Spatial Context (Include for spatial commands)
**Budget: ~600 tokens**

```
=== SPATIAL LAYOUT ===
Region density:
  center: high (6 features)
  left: medium (3 features)
  right: low (1 feature)
  
Feature positions (centroids):
  Mountains [1,3,5]: (256, 256) - center
  Dunes [2,4,6]: (128, 256) - left
```

**Purpose:** Spatial reasoning for "near", "between", "around" commands

---

### Tier 3: Attribute Context (Include for attribute-based queries)
**Budget: ~800 tokens**

```
=== FEATURE ATTRIBUTES ===
Mountains [1,3,5]:
  height: 0.8-0.9 (tall)
  radius: 50-60 (medium)
  
Dunes [2,4,6]:
  amplitude: 0.08 (gentle)
  frequency: 20 (rolling)
```

**Purpose:** Filtering and modification based on attributes

---

### Tier 4: Tool Registry (Always include, but compact)
**Budget: ~200 tokens**

```
=== AVAILABLE TOOLS ===
Scene Queries:
  - query_entities: find entities by criteria
  - get_feature_details: get feature attributes
  - get_spatial_relationships: calculate positions
  
Spatial Calculation:
  - calculate_position: resolve spatial references
  - calculate_region_positions: multi-position patterns
  
Features: mountain, valley, dunes, mesa, plateau...
```

**Purpose:** Tool discovery and invocation

---

## 🎯 Adaptive Context Strategy

### Smart Context Selection

```python
def build_context(command: str, scene_state: Dict) -> str:
    """Build context based on command type analysis."""
    
    # Analyze command to determine what context is needed
    command_type = analyze_command_intent(command)
    
    context_tiers = []
    
    # Tier 1: Always include
    context_tiers.append(build_essential_context(scene_state))
    
    # Tier 2: Include for spatial commands
    if command_type.is_spatial:
        context_tiers.append(build_spatial_context(scene_state))
    
    # Tier 3: Include for attribute queries
    if command_type.needs_attributes:
        context_tiers.append(build_attribute_context(scene_state))
    
    # Tier 4: Always include tool registry
    context_tiers.append(build_tool_registry())
    
    # Check token budget
    total_tokens = sum(estimate_tokens(tier) for tier in context_tiers)
    
    if total_tokens > 6000:  # Leave headroom
        # Prioritize: Essential > Tools > Spatial > Attributes
        context_tiers = optimize_context_budget(context_tiers, max_tokens=6000)
    
    return "\n\n".join(context_tiers)
```

---

## 🔄 Tool Call Flow

### Current Flow (Parser Only):
```
User: "Add valley between mountains"
  ↓
Parser → LLM → JSON
  {kind: "add", type: "valley", position: {region: "center"}}
  ↓
Execute action (guesses position)
```

**Problem:** LLM has no access to actual mountain positions!

---

### Proposed Flow (MCP Tools):
```
User: "Add valley between mountains"
  ↓
Parser → LLM receives context + tool list
  ↓
LLM: "I need to know where mountains are"
  ↓
Tool call: resolve_reference("the mountains") → [1, 3, 5]
  ↓
Tool call: get_feature_details([1, 3, 5]) 
  → [{x: 100, y: 200}, {x: 300, y: 250}, {x: 200, y: 300}]
  ↓
Tool call: calculate_position(
    reference_ids=[1, 3, 5],
    relationship="between"
) → (200, 250)
  ↓
LLM: Generates final action
  {kind: "add", type: "valley", position: {coords: [200, 250]}}
  ↓
Execute action with precise position!
```

**Benefit:** LLM has real-time access to scene data via tools!

---

## 💡 Key Insights

### 1. **Tool-First Architecture**
Instead of "put everything in the prompt", give the LLM **tools to query what it needs**.

**Advantages:**
- ✅ Token-efficient (query on demand)
- ✅ Always up-to-date (reads live state)
- ✅ Compositional (chain multiple tools)
- ✅ Debuggable (see tool calls in logs)

---

### 2. **Layered Context Strategy**
Different commands need different context levels:

| Command Type | Context Needed | Example |
|--------------|----------------|---------|
| **Simple Add** | Tier 1 (Essential) | "add a mountain" |
| **Reference** | Tier 1 + Tools | "remove the mountains" |
| **Spatial** | Tier 1 + Tier 2 + Tools | "add valley between mountains" |
| **Attribute** | Tier 1 + Tier 3 + Tools | "make tall mountains taller" |

---

### 3. **Semantic Identity = Structure + Relationships + History**

**Current:** Just labels and IDs  
**Needed:**
- ✅ Labels & IDs (reference resolution)
- ✅ Positions & bounds (spatial reasoning)
- ✅ Attributes (filtering & modification)
- ✅ Relationships (between, near, north of)
- ✅ Temporal data (recent, oldest, last)
- ✅ User intent (why was this created?)

---

## 🎯 Recommended Implementation Priority

### Phase 1: Essential Query Tools (Week 1)
1. `query_entities` - Find entities by criteria
2. `get_feature_details` - Get feature attributes
3. `resolve_reference` - Better reference resolution

**Impact:** Enables attribute-based queries and modifications

---

### Phase 2: Spatial Tools (Week 2)
4. `get_spatial_relationships` - Calculate positions
5. `calculate_position` - Resolve spatial references
6. `calculate_region_positions` - Multi-position patterns

**Impact:** Enables "between", "around", "near" commands

---

### Phase 3: Advanced Tools (Week 3)
7. `resolve_temporal_reference` - Time-based queries
8. `infer_feature_parameters` - Smart parameter suggestion
9. `validate_action` - Safety checks

**Impact:** Smarter, safer terrain generation

---

### Phase 4: Composition Tools (Week 4)
10. `suggest_composition` - Multi-feature patterns
11. `suggest_modification` - Intelligent edits
12. Adaptive context system

**Impact:** Natural language → complex terrains

---

## 📊 Token Budget Allocation (Revised)

```
Base instructions:           ~500 tokens
Essential context (Tier 1):  ~400 tokens
Spatial context (Tier 2):    ~600 tokens (conditional)
Attribute context (Tier 3):  ~800 tokens (conditional)
Tool registry:               ~200 tokens
User command:                ~200 tokens
Tool responses:              ~1000 tokens (dynamic)
──────────────────────────────────────────────
MAX TOTAL:                   ~3700 tokens
──────────────────────────────────────────────
Remaining headroom:          ~4500 tokens ✅
```

**Strategy:** Start with minimal context, let LLM request more via tools!

---

## ✅ Conclusion

### The Problem with Current Approach:
❌ **Static context dump** - trying to anticipate everything LLM might need  
❌ **Context explosion** - more features = more tokens  
❌ **No semantic reasoning** - LLM can't calculate spatial relationships  

### The Solution:
✅ **Tool-based architecture** - LLM queries what it needs  
✅ **Adaptive context** - include only what's relevant to command  
✅ **Semantic tools** - enable real spatial/temporal reasoning  

### Next Steps:
1. Implement Phase 1 tools (query_entities, get_feature_details, resolve_reference)
2. Update system prompt to include tool descriptions
3. Enable tool calling in parser
4. Test with complex spatial commands
5. Iterate based on results

**Expected outcome:** Richer semantic understanding with LESS token usage! 🎉

