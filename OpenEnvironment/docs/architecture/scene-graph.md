# Scene Graph

**Package:** `semantic/scene/`

A USD-inspired scene graph that tracks what features exist, what they're called, and where they are. Enables commands like "make the mountains taller" and "add a valley between the dunes".

## Structure

```
TerrainSceneGraph
  entities:
    - label: "the dunes", feature_ids: [3, 4], keywords: ["dune", "sand"]
    - label: "two mountains", feature_ids: [5, 6], keywords: ["mountain", "peak"]
  relationships:
    - from: "the dunes", to: "two mountains", type: "near", distance: 120
```

Entities are created automatically when features are added (via `SceneGraphIntegrator`). They're removed when features are deleted.

## Reference resolution

When a command says "the dunes", the resolution order is:

1. **Exact label match** -- entity whose label is "the dunes"
2. **Keyword match** -- entity with keyword "dune"
3. **Type match** -- all features where `type == "dunes"`
4. **Ordinal** -- "first mountain" = earliest mountain by creation order

This happens in `orchestration.resolve_removal_targets()` for removals, and in `SemanticParser` / ReAct agent for spatial references.

## Spatial queries

The scene graph supports finding features by location:

- **Near** -- features within a radius of a reference point
- **Region** -- features within a named region (center, top-left, etc.)
- **Between** -- position midpoint between two reference features
- **Directional** -- north_of, south_of, east_of, west_of a reference

These are exposed as tools the ReAct agent can call (`semantic/tools/spatial_tools.py`).

## Serialization

The scene graph is stored in `state["semantic_scene"]` as a dict and round-trips through `SceneGraphSerializer.to_dict()` / `from_dict()`. It persists across commands so references work across sessions.

## Key classes

| Class | File | Role |
|-------|------|------|
| `TerrainSceneGraph` | `scene/graph.py` | Root container |
| `SemanticEntity` | `scene/entities.py` | A labeled group of features |
| `EntityManager` | `scene/entities.py` | CRUD for entities |
| `ReferenceResolver` | `scene/resolver.py` | Label/keyword/type/ordinal resolution |
| `QueryEngine` | `scene/queries.py` | Spatial queries |
| `SceneGraphSerializer` | `scene/serializer.py` | Dict serialization |
| `SceneGraphIntegrator` | `scene/integrator.py` | Creates/updates/cleans entities during terrain generation |
