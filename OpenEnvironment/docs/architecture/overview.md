# Architecture

This codebase is structured as an **environment builder** (API + state + generation engine) rather than a single-purpose “prompt → terrain” demo. The current implemented environment content is terrain/world layout, but the layering is meant to support RL-style workflows where you repeatedly reset/mutate the environment and score it.

## Layer overview

```
Frontend (React + Three.js + custom GLSL)
    | REST
API Layer (FastAPI -- controllers + services)
    |
Orchestration (terrain.py, orchestration.py)
    |
Parsing cascade (Narrative -> SemanticParser -> Regex)
    |
Semantic Layer (scene graph, evaluation, LLM clients, tool registry)
    |
Engine (TerrainBuilder, FeatureRegistry, stamping, splatmap)
    |
Primitives (19+ generators: mountains, valleys, dunes, ...)
    |
Output (heightmaps, splatmaps, voxel meshes, JSON state)
```

## Request lifecycle (environment build step)

1. Frontend (or trainer harness) POSTs to `/api/generate` with a command or template selection
2. `TerrainController` -> `TerrainService.generate_terrain()`
3. `terrain.apply_actions()` orchestrates everything:
   - Loads or creates the scene graph from state
   - Parses command into structured actions (see [parsing](parsing.md))
   - Partitions into remove/modify vs add actions
   - Resolves removal targets via scene graph
   - Executes state mutations (remove, modify)
   - Builds terrain with `TerrainBuilder` (base biome + all features)
   - Executes add actions (creates new features, stamps them)
   - Updates scene graph with new entities
   - Computes quality metrics
4. Service saves state JSON + heightmap/splatmap PNGs to disk
5. Frontend loads assets into Three.js viewer with displacement shaders

## Key files

| File | Role |
|------|------|
| `server/main.py` | FastAPI app, routes, service wiring |
| `server/terrain.py` | Main orchestrator (`apply_actions`) |
| `server/orchestration.py` | Parsing cascade, action partitioning, scene graph plumbing |
| `server/engine/builder.py` | `TerrainBuilder` -- single-pass heightmap construction |
| `server/engine/feature_registry.py` | `FeatureRegistry` -- maps feature types to generators + defaults |
| `server/engine/stamping.py` | Blending primitives onto the heightmap |
| `server/engine/splatmap.py` | Height/slope-based RGBA texture map generation |
| `server/semantic/parser.py` | `SemanticParser` -- LLM parsing with scene context |
| `server/semantic/scene/` | `TerrainSceneGraph`, entity management, reference resolution |
| `server/semantic/evaluation/` | Feature metrics, texture metrics, quality rubrics |
| `server/semantic/narrative/` | Story-driven generation (archetypes, composition, aesthetic goals) |
| `server/semantic/llm/` | Provider-agnostic LLM client factory (Cerebras, Together, Gemini) |
| `server/semantic/react_agent_v2.py` | ReAct reasoning agent with function calling |
| `server/services/` | `TerrainService`, `StateService`, `AssetService`, `MCPService`, etc. |
| `server/primitives/` | One file per terrain type (mountains.py, valleys.py, dunes.py, ...) |
| `web/src/api.ts` | Frontend API client |
| `web/src/components/TerrainViewer.tsx` | Three.js viewer with custom shaders |
| `web/src/state.ts` | Zustand store |

## Frontend

React 18 + Vite + Three.js via React Three Fiber. Two render modes:

- **Heightmap mode**: Flat plane with vertex displacement shader. Splatmap blends grass/rock/sand/snow textures based on RGBA weights.
- **Voxel mode**: OBJ mesh loaded from backend, same splatmap texturing.

Both support real-time sun direction via azimuth/elevation uniforms.

## State model

All terrain state lives in a single JSON file (`terrain_state.json`):

```json
{
  "seed": 42,
  "features": [
    {"id": 1, "type": "mountain", "x": 256, "y": 200, "height": 0.6, "radius": 64, ...}
  ],
  "semantic_scene": { "entities": [...], "relationships": [...] },
  "action_history": [...]
}
```

State is the source of truth. The backend can always regenerate terrain from state alone (empty command = rebuild).

## Experimental features

These exist in the codebase but aren't fully integrated into the production pipeline:

- **Multi-agent workflow** (`/api/design/multi-agent`) -- AG2/autogen artist/critic/judge collaboration. Has edge cases.
- **RendererRegistry** (`engine/renderers.py`) -- parallel feature rendering abstraction. Production uses `FeatureRegistry` instead.
- **Domain models** (`domain/`) -- typed `Feature`/`Position` dataclasses. Partial migration from dict-based features.
- **Rubric evolution** -- context-adaptive quality rubrics. Only used in experimental multi-agent path.
- **Slope erosion** -- function exists but is never called.
- **Configuration system** -- `engine/config.py` exists but production uses hardcoded defaults in `FeatureRegistry`.
