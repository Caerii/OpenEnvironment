# Development Guide

## Project structure

```
server/
  main.py              # FastAPI app, routes, service wiring
  terrain.py           # Main orchestrator (apply_actions)
  orchestration.py     # Parsing cascade, action execution helpers
  parsing.py           # Regex-based CommandParser
  bootstrap.py         # sys.path setup
  api/
    controllers/       # TerrainController, TemplateController, MCPController, StatusController
    models.py          # Pydantic request models (Command, MultiAgentRequest)
  services/            # TerrainService, StateService, AssetService, MCPService, etc.
  engine/
    builder.py         # TerrainBuilder (single-pass heightmap construction)
    feature_registry.py # Maps feature types -> generators + default params
    commands.py        # Command pattern (AddFeatureCommand, etc.)
    stamping.py        # Blending primitives onto heightmaps
    splatmap.py        # Height/slope-based RGBA texture generation
    templates.py       # TemplateRegistry (16+ curated terrains)
    variation.py       # VariationEngine for parameter jitter
  primitives/          # One file per terrain type (mountains.py, valleys.py, ...)
  semantic/
    parser.py          # SemanticParser (LLM + scene context)
    react_agent_v2.py  # ReAct reasoning agent
    scene/             # TerrainSceneGraph, entities, resolver, queries
    evaluation/        # Feature metrics, texture metrics, quality rubrics
    narrative/         # Story-driven generation pipeline
    llm/               # LLM client factory (Cerebras, Together, Gemini)
    tools/             # Tool functions for ReAct agent
    tool_registry.py   # MCP-style tool schema registry
  domain/              # Typed Feature/Position dataclasses (partial migration)
  features/            # Typed feature bridge layer (adapters.py)
  tests/               # pytest suite
  tools/               # Manual test/analysis scripts

web/
  src/
    App.tsx            # Main UI shell
    api.ts             # Axios API client
    state.ts           # Zustand store
    components/        # TerrainViewer, controls, selectors
    shaders/           # GLSL as TypeScript modules
  public/
    assets/            # Generated heightmaps/splatmaps (written by backend)
    textures/          # Biome textures (grass.jpg, rock.jpg, sand.jpg, snow.jpg)
```

## Adding a new terrain primitive

1. Create a generator in `server/primitives/`:

```python
# server/primitives/my_feature.py
import numpy as np

def generate_my_feature(cx, cy, radius, height, seed=0):
    """Return a 2D numpy stamp array."""
    ...
    return stamp
```

2. Register it in `server/engine/feature_registry.py`:

```python
FeatureRegistry.register("my_feature", {
    "generator": generate_my_feature,
    "defaults": {"height": 0.5, "radius": 60},
    ...
})
```

3. Add tool schema in `server/semantic/tool_registry.py` so the LLM knows about it.

4. The narrative archetypes in `semantic/narrative/archetypes.py` can reference it if it should appear in story-driven generation.

## Adding a new API endpoint

1. Add controller method in `server/api/controllers/`.
2. Wire the route in `server/main.py`.
3. Add the frontend call in `web/src/api.ts`.

## Adding a new LLM provider

1. Implement `LLMClient` interface in `server/semantic/llm/clients.py`.
2. Add the provider branch in `server/semantic/llm/factory.py` (`create_llm_client()`).
3. Document the env var in `ENV_TEMPLATE.md`.

## Running the backend

```bash
.\start-backend-uv.ps1
# or manually:
cd server && uv sync && cd ..
uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
```

## Running the frontend

```bash
.\start-frontend.ps1
# or manually:
cd web && pnpm install && pnpm dev
```

## Linting

```bash
cd server
uv run ruff check .
uv run ruff format .
```
