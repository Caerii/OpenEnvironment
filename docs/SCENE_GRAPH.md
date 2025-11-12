# Scene Graph System

The Semantic Terrain system uses a USD-inspired hierarchical scene graph for semantic understanding and reference resolution.

---

## Overview

The scene graph provides:

- **Semantic Entities** - Human-readable representations of features
- **Reference Resolution** - "the dunes" → feature IDs
- **Spatial Queries** - Find features by location or relationship
- **Relationship Tracking** - Spatial and semantic connections

---

## Structure

### USD-Inspired Design

The scene graph follows USD (Universal Scene Description) principles:

- **Hierarchical Nodes** - Parent-child relationships
- **Entity System** - Semantic entities with labels
- **Reference System** - Resolvable references
- **Query System** - Path-based queries

### Graph Components

```
TerrainSceneGraph
├── Features/
│   ├── Mountain_1
│   │   ├── Entity: "two mountains"
│   │   ├── Feature IDs: [4, 5]
│   │   └── Keywords: ["mountain", "peak", "elevation"]
│   ├── Dunes_1
│   │   ├── Entity: "the dunes"
│   │   ├── Feature IDs: [3, 4]
│   │   └── Keywords: ["dune", "sand", "desert"]
│   └── Valley_1
│       ├── Entity: "deep valley"
│       ├── Feature IDs: [6]
│       └── Keywords: ["valley", "depression", "low"]
```

---

## Entity Management

### Entity Creation

Entities are created when features are added:

```python
# When adding features
scene_graph.create_entity(
    label="the dunes",
    feature_ids=[3, 4],
    keywords=["dune", "sand", "desert"],
    position=(256, 256)
)
```

### Entity Properties

- **Label** - Human-readable name ("the dunes", "mountain range")
- **Feature IDs** - Associated feature IDs
- **Keywords** - Searchable keywords
- **Position** - Spatial location
- **Type** - Feature type
- **Relationships** - Connections to other entities

---

## Reference Resolution

### Resolution Process

When a command contains a reference like "the dunes":

1. **Entity Label Match** - Find entity by exact label match
2. **Keyword Match** - Find entity by keyword match
3. **Type Match** - Find all features of that type
4. **Ordinal Resolution** - "first", "last", "second" → resolve by order

### Example

```
User Command: "make the mountains taller"
Scene Graph: 
  - Entity "mountains" → Feature IDs [4, 5, 6]
  - Entity "the dunes" → Feature IDs [3, 4]
Resolution: Modify features 4, 5, and 6 (mountains)
```

### Resolution Types

**Exact Label:**
```
"the dunes" → Entity "the dunes" → Feature IDs [3, 4]
```

**Keyword Match:**
```
"dunes" → Entity with keyword "dune" → Feature IDs [3, 4]
```

**Type Match:**
```
"mountains" → All features of type "mountain" → Feature IDs [4, 5, 6]
```

**Ordinal:**
```
"first mountain" → First created mountain → Feature ID [4]
"last hill" → Last created hill → Feature ID [8]
```

---

## Spatial Queries

The scene graph supports spatial queries to find features by location.

### Query Types

**Near Query:**
```
Query: "find features near the dunes"
→ Resolves "dunes" to Feature IDs [3, 4]
→ Finds features within radius (default: 150 pixels)
→ Returns: [{feature_id: 5, distance: 120}, ...]
```

**Region Query:**
```
Query: "what's in the center?"
→ Defines center region (e.g., 200-300, 200-300)
→ Finds features within region
→ Returns: Feature IDs [6, 7, 8]
```

**Relationship Query:**
```
Query: "features between the mountains"
→ Resolves "mountains" to Feature IDs [4, 5]
→ Finds features between positions
→ Returns: Feature IDs [6, 7]
```

### Query API

```python
# Find features near an entity
nearby = query_engine.find_near_feature(feature_id, radius=150)

# Find features in region
region_features = query_engine.find_within_region((x0, y0, x1, y1))

# Get feature relationships
relationships = query_engine.get_spatial_relationships(feature_id)
```

---

## Integration with Parsing

The scene graph integrates with parsing strategies:

### Narrative Pipeline
- Creates entities during composition generation
- Uses entities for reference resolution
- Maintains semantic relationships

### SemanticParser
- Uses scene graph for context
- Resolves references using entities
- Queries scene graph for spatial information

### ReAct Agent
- Uses query tools to explore scene graph
- Resolves references during reasoning
- Updates scene graph with new entities

---

## Serialization

The scene graph is serialized to JSON for persistence.

### State Format

```json
{
  "semantic_scene": {
    "entities": [
      {
        "label": "the dunes",
        "feature_ids": [3, 4],
        "keywords": ["dune", "sand"],
        "position": [256, 256],
        "type": "dunes"
      }
    ],
    "relationships": [
      {
        "from": "the dunes",
        "to": "mountains",
        "type": "near",
        "distance": 120
      }
    ]
  }
}
```

### Loading and Saving

```python
# Load scene graph from state
scene_graph = SceneGraphSerializer.from_dict(state["semantic_scene"])

# Save scene graph to state
state["semantic_scene"] = SceneGraphSerializer.to_dict(scene_graph)
```

---

## Best Practices

### Entity Labels
- Use descriptive labels ("the dunes", "mountain range")
- Be consistent with naming
- Include type hints in labels

### Reference Resolution
- Use specific labels when possible
- Avoid ambiguous references
- Leverage keywords for flexibility

### Spatial Queries
- Use appropriate radius for "near" queries
- Define clear regions for region queries
- Consider feature sizes when querying

---

## Advanced Features

### Relationship Tracking
- **Spatial Relationships** - Near, far, between
- **Semantic Relationships** - Part of, contains, related to
- **Temporal Relationships** - Created before, after

### Query Optimization
- **Spatial Indexing** - Efficient spatial queries
- **Caching** - Cache query results
- **Batch Queries** - Multiple queries at once

### Entity Updates
- **Automatic Updates** - Entities update when features change
- **Cleanup** - Remove entities when features are deleted
- **Merging** - Merge entities when appropriate

---

See also:
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Parsing Strategies](PARSING_STRATEGIES.md) - How parsing uses scene graph
- [API Reference](API_REFERENCE.md) - Scene graph API endpoints

