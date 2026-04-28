# OpenEnvironment System - Engineering Explanation

## Overview

**OpenEnvironment** is a real-time terrain generation system that converts natural language commands (e.g., "add two mountains on the left") into procedural 3D terrain with heightmaps and splatmaps. The system uses an LLM-powered parser, a semantic scene graph for reference resolution, and a deterministic terrain engine.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  - React Three Fiber 3D viewer                              │
│  - Command input UI                                          │
│  - Real-time terrain visualization                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              API Layer (FastAPI - main.py)                  │
│  - POST /api/generate - Process natural language commands   │
│  - POST /api/modify - Modify terrain                       │
│  - GET /api/state - Get current terrain state              │
│  - POST /api/reset - Reset to flat terrain                  │
│  - Atomic state management (file locking)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Orchestrator Layer (terrain.py)                    │
│  - apply_actions() - Main entry point                       │
│  - Coordinates parsing, state management, generation        │
│  - Scene graph integration                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  Semantic Layer  │    │  Engine Layer     │
│  - Parser (LLM)  │    │  - Builder        │
│  - Scene Graph   │    │  - Stamping       │
│  - State Mgr     │    │  - Splatmap       │
│  - Ref Resolver  │    │  - Spatial        │
└─────────┬────────┘    └─────────┬────────┘
          │                      │
          │                      ▼
          │              ┌──────────────────┐
          │              │  Primitives      │
          │              │  - Mountains     │
          │              │  - Valleys       │
          │              │  - Dunes         │
          │              │  - Cliffs        │
          │              └──────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Output Files                               │
│  - heightmap_*.png (16-bit & 8-bit)                         │
│  - splatmap_*.png (RGBA texture blending)                    │
│  - terrain_state.json (persistent state)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Command to Output

### Step 1: Command Parsing (`orchestration.py`)

**Input:** Natural language string
```
"create a desert with rolling dunes and two mountains on the left"
```

**Process (Three-Tier Parser System):**
1. **Narrative Pipeline** (Primary): Handles aesthetic/narrative commands via `run_narrative_pipeline()`
2. **SemanticParser** (Fallback): Uses LLM (Together/Cerebras) with ReAct agent for complex spatial reasoning
3. **CommandParser** (Final Fallback): Regex-based parser for simple commands
   - System prompt includes:
     - Available tool registry (MCP-style)
     - Current scene graph state (for reference resolution)
     - Parsing rules and examples
   - Output format:
     ```json
     {
       "actions": [
         {
           "kind": "add",
           "type": "dunes",
           "count": 1,
           "position": {"region": "center"},
           "modifiers": {}
         },
         {
           "kind": "add",
           "type": "mountain",
           "count": 2,
           "position": {"region": "left"},
           "modifiers": {}
         }
       ]
     }
     ```

2. **Fallback Parser** (Regex): If LLM fails, uses regex-based parsing

**Key Features:**
- Extracts exact counts ("two mountains" → count: 2)
- Resolves spatial references ("on the left" → region: "left")
- Supports compositional commands (multiple features in one command)
- Can resolve references using scene graph context

---

### Step 2: Reference Resolution (`semantic/scene/reference_resolver.py`)

**When:** Commands contain references like "the dunes" or "last mountain"

**Process:**
1. **Entity Label Match**: Find semantic entity by label ("the dunes" → Entity → Feature IDs)
2. **Ordinal Resolution**: "first", "last", "second" → resolve by creation order
3. **Keyword Match**: Match entity keywords
4. **Type Match**: Fallback - all features of that type

**Example:**
```
User: "make the mountains taller"
Scene Graph: Entity "two mountains" → Feature IDs [4, 5]
Resolution: Modify features 4 and 5
```

---

### Step 3: Action Execution (`engine/commands.py`)

**Input:** Parsed action dictionaries

**Process:**
1. **Create Command Objects**: Convert dicts to `ActionCommand` objects
   - `AddCommand`: Adds new features
   - `RemoveCommand`: Removes features
   - `ModifyCommand`: Modifies existing features

2. **Execute Commands**: Each command updates `FeatureState` and applies changes to `TerrainBuilder`

**Example:**
```python
# AddCommand.execute()
for i in range(action.count):
    feature_id = feature_state.add_feature({
        "type": action.type,
        "x": resolved_x,
        "y": resolved_y,
        ...
    })
    # Apply stamp to terrain immediately
    builder.apply_feature(stamp, blending_mode)
```

---

### Step 4: Terrain Building (`engine/builder.py`)

**TerrainBuilder Pattern:**
- **Single-pass generation**: No double rebuild
- **Incremental application**: Features applied as they're created
- **Mask management**: Tracks dune masks and cliff masks separately

**Process:**
1. **Initialize**: Create base biome (desert, flat, etc.)
2. **Apply Features**: Each feature generates a "stamp" (heightmap snippet)
3. **Blending**: Stamps blended using modes:
   - `MAX`: Mountains (preserve highest)
   - `ADD`: Hills (additive)
   - `MIN`: Valleys (preserve lowest)
4. **Post-processing**:
   - Adaptive smoothing (preserves edges)
   - Edge erosion (natural weathering)
   - Normalization (0-1 range)

**Example:**
```python
builder = TerrainBuilder(base_desert, seed=0)
# Apply mountain stamp
stamp = generate_mountain(x, y, radius, height)
builder.apply_feature(stamp, BlendingMode.MAX)
# Finalize
heightmap, dune_mask, cliff_mask = builder.finalize()
```

---

### Step 5: Splatmap Generation (`engine/splatmap.py`)

**Purpose:** Generate RGBA texture blending map for Unity terrain

**Process:**
1. **Height-based segmentation**:
   - Grass: Low elevations (0-60%)
   - Sand: Medium elevations (60-80%)
   - Rock: High elevations (80-97%)
   - Snow: Very high elevations (97-100%)

2. **Feature-based masks**:
   - Dunes: Force sand texture
   - Cliffs: Force rock texture

3. **Smooth blending**: Feather transitions between zones

**Output:** 4-channel RGBA image (512×512)

---

### Step 6: Scene Graph Integration (`semantic/scene/integration.py`)

**Purpose:** Create semantic entities for reference resolution

**Process:**
1. **Extract Labels**: From command ("two mountains" → "two mountains")
2. **Extract Keywords**: Feature type, descriptors
3. **Create Entity**: Links label to feature IDs
4. **Store in Scene Graph**: Persistent in state

**Example:**
```python
# After adding 2 mountains with IDs [4, 5]
entity = SemanticEntity(
    label="two mountains",
    keywords=["mountain", "mountains"],
    feature_refs=[4, 5],
    user_intent="add two mountains on the left"
)
scene_graph.add_entity(entity)
```

---

### Step 7: State Persistence (`engine/state_lock.py`)

**Process:**
1. **Atomic Read**: File locking prevents race conditions
2. **Update State**: Merge new features into state
3. **Atomic Write**: Write to temp file, then rename (atomic operation)

**State Format:**
```json
{
  "features": [
    {"id": 1, "type": "dunes", "x": 256, "y": 256, ...},
    {"id": 2, "type": "mountain", "x": 128, "y": 256, ...}
  ],
  "seed": 0,
  "semantic_scene": {
    "version": 1,
    "root": {...}  // Scene graph structure
  }
}
```

---

## Key Components Deep Dive

### 1. Semantic Scene Graph (`semantic/scene/graph.py`)

**Purpose:** USD-inspired hierarchical structure for semantic understanding

**Structure:**
```
/World
  /Features          # Geometric features
    /Mountain_Group
      /feature_1
      /feature_2
  /Semantics         # Semantic entities
    /entity_1        # "two mountains" → [1, 2]
```

**Key Operations:**
- `add_feature()`: Add geometric feature
- `add_entity()`: Add semantic entity
- `find_feature_by_id()`: Query by ID
- `query()`: USD-style path queries

**Benefits:**
- Enables reference resolution ("the dunes")
- Maintains semantic labels and descriptions
- Supports complex queries

---

### 2. Terrain Primitives (`primitives/`)

**Purpose:** Pure functions that generate heightmap stamps

**Examples:**
- `generate_mountain()`: Gaussian-based mountain stamp
- `generate_valley()`: Inverted Gaussian valley
- `generate_dunes()`: Perlin noise dunes
- `generate_cliff()`: Vertical cliff faces

**Signature:**
```python
def generate_mountain(x: int, y: int, radius: int, height: float, steepness: float = 1.0) -> np.ndarray:
    """Generate 512×512 heightmap stamp for mountain."""
    # Returns 512×512 array (only stamp region is non-zero)
```

**Deterministic:** Same parameters = same output (uses seeded NumPy RNG)

---

### 3. Spatial Resolution (`semantic/spatial_resolver.py`)

**Purpose:** Resolve spatial references ("left", "center", "between the mountains")

**Process:**
1. **Region Box**: Convert region strings to bounding boxes
   ```python
   "left" → (0, 0, 256, 512)  # Left half of terrain
   ```

2. **Poisson Disk Sampling**: Natural distribution (not grid-based)

3. **Context-Aware**: Uses scene graph to resolve "between X and Y"

---

### 4. State Management (`semantic/state_manager.py`)

**FeatureState Class:**
- Manages feature list
- Handles add/remove/modify operations
- Generates unique feature IDs
- Serialization/deserialization

**Key Methods:**
- `add_feature()`: Add new feature
- `remove_feature()`: Remove by ID
- `modify_feature()`: Update feature parameters
- `list_features()`: Get all features

---

## Extension Points

### Adding a New Feature Type

**1. Create Primitive Function** (`primitives/new_feature.py`):
```python
def generate_new_feature(x: int, y: int, radius: int, height: float) -> np.ndarray:
    """Generate heightmap stamp."""
    # ... implementation
    return stamp
```

**2. Register in Parser** (`semantic/parser.py`):
- Add to feature type list in system prompt
- Add to regex fallback parser

**3. Update Tool Registry** (`semantic/tool_registry.py`):
- Add tool definition for MCP context

**4. Update Commands** (`engine/commands.py`):
- Add handling in `_create_feature()` if needed

**No changes needed to:**
- Core orchestrator (`terrain.py`)
- Builder pattern (`engine/builder.py`)
- API layer (`main.py`)

---

### Adding a New Biome

**1. Create Base Function** (`primitives/base.py`):
```python
def base_new_biome(seed: int) -> np.ndarray:
    """Generate 512×512 base terrain."""
    # ... implementation
    return heightmap
```

**2. Use in API** (`main.py`):
```python
h, state, splat = apply_actions(cmd.text, state, base_biome_fn=base_new_biome)
```

---

## State Management Details

### File Locking (`engine/state_lock.py`)

**Cross-Platform:**
- Windows: Uses `msvcrt` module
- Unix: Uses `fcntl` module

**Atomic Operations:**
1. Write to temp file (`state.json.tmp`)
2. Lock file
3. Write data
4. Rename temp → final (atomic on most filesystems)

**Prevents:**
- Race conditions (multiple requests modifying state)
- Corrupted state files
- Lost updates

---

### State Schema

**Current Version:** Supports backward compatibility

**Structure:**
```json
{
  "features": [
    {
      "id": 1,
      "type": "mountain",
      "x": 128,
      "y": 256,
      "radius": 56,
      "height": 0.75,
      "steepness": 1.0
    }
  ],
  "seed": 0,
  "next_id": 2,
  "semantic_scene": {
    "version": 1,
    "root": {
      "name": "/World",
      "children": {
        "Features": {...},
        "Semantics": {...}
      }
    }
  }
}
```

---

## Deterministic Generation

### Key Principles

1. **Seeded RNG**: All randomness uses NumPy `RandomState(seed)`
2. **Deterministic Seeds**: Feature seeds derived from feature ID + global seed
3. **State-Based**: Same state + same seed = same terrain

**Example:**
```python
# Feature seed derivation
feature_seed = hash(f"{feature_id}_{global_seed}") % (2**31)
rng = np.random.RandomState(feature_seed)
```

**Benefits:**
- Reproducible results
- Consistent regeneration
- No random drift

---

## Performance Considerations

### Single-Pass Generation

**Problem:** Old system rebuilt terrain twice (once for existing features, once for new)

**Solution:** `TerrainBuilder` pattern
- Features applied incrementally
- Single finalization step
- No redundant computation

### Caching Opportunities

**Current:** None (deterministic generation is fast enough)

**Future:** Could cache:
- Base biome generation
- Common feature stamps
- Splatmap calculations

---

## Error Handling

### Layered Error Handling

1. **API Layer** (`main.py`):
   - Validates input (Pydantic)
   - Catches exceptions
   - Returns HTTP error codes

2. **Orchestrator** (`terrain.py`):
   - Handles parser failures (fallback)
   - Validates feature parameters
   - Recovers from state corruption

3. **Engine Layer** (`engine/`):
   - Validates array bounds
   - Handles edge cases (flat terrain, etc.)

### Recovery Strategies

- **Parser Failure**: Falls back to regex parser
- **State Corruption**: Resets to empty state
- **Generation Failure**: Returns error message to user

---

## Testing Strategy

### Unit Tests

- **Primitives**: Test each stamp generator independently
- **Spatial Resolution**: Test region → coordinate conversion
- **Reference Resolution**: Test "the dunes" → feature IDs

### Integration Tests

- **End-to-End**: Command → Heightmap → Splatmap
- **State Persistence**: Save/load state files
- **Scene Graph**: Entity creation and querying

### Visual Tests

- Compare generated terrains
- Verify aesthetic improvements
- Check edge cases (flat terrain, etc.)

---

## Common Issues & Solutions

### Issue: "The dunes" doesn't resolve

**Cause:** Scene graph entity not created or label mismatch

**Solution:** Check `semantic_scene` in state file, verify entity label matches reference

### Issue: Non-deterministic terrain

**Cause:** Python `random` module instead of NumPy `RandomState`

**Solution:** All randomness should use `np.random.RandomState(seed)`

### Issue: Race conditions in state file

**Cause:** Concurrent API requests modifying state simultaneously

**Solution:** File locking in `engine/state_lock.py` prevents this

### Issue: Features not appearing

**Cause:** Feature coordinates out of bounds or blending mode issue

**Solution:** Check feature bounds (0-511), verify blending mode is correct

---

## Future Enhancements

### Planned Features

1. **Query System**: USD-style path queries for scene graph
2. **Feature Registry**: Plugin system for adding features
3. **Configuration System**: Centralized defaults and parameters
4. **Performance Optimization**: Caching and incremental updates

### Architecture Improvements

1. **Feature Classes**: Object-oriented features (currently dict-based)
2. **Plugin System**: External feature definitions
3. **Multi-Biome Support**: Easy biome switching
4. **Advanced Erosion**: Hydraulic and thermal erosion

---

## Summary

**OpenEnvironment** is a sophisticated system that combines:
- **LLM-powered parsing** for natural language understanding
- **Semantic scene graph** for reference resolution
- **Deterministic terrain generation** for reproducibility
- **Single-pass building** for performance
- **Atomic state management** for reliability

The architecture is designed for **extensibility** - new features can be added without modifying core code. The system maintains **deterministic behavior** while supporting **natural language interactions** through its semantic understanding layer.


