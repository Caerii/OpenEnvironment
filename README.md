# OpenEnvironment

OpenEnvironment is an **RL-for-games environment construction toolkit**: generate and mutate game-ready world state and assets via an API so you can run training loops against consistent, replayable environments.

Today, the concrete environment module in this repo is **procedural terrain/world layout generation** (heightmaps, splatmaps, optional voxel meshes). The long-term target is a broader environment builder (scenarios, constraints, evaluation signals) suitable for reinforcement learning workflows.

## Quick start

```bash
# 1. Backend
cd OpenEnvironment/server && uv sync && cd ../..
echo CEREBRAS_API_KEY=your_key > OpenEnvironment/server/.env
.\start-backend-uv.ps1          # http://localhost:8001

# 2. Frontend (new terminal)
cd OpenEnvironment/web && pnpm install && cd ../..
.\start-frontend.ps1             # http://localhost:5173
```

Needs Python 3.10-3.12, Node 18+, [uv](https://github.com/astral-sh/uv), [pnpm](https://pnpm.io/), and at least one LLM API key ([Cerebras](https://console.cerebras.ai/), [Together](https://api.together.xyz/), or [Gemini](https://makersuite.google.com/app/apikey)). Without an API key the system falls back to regex parsing.

See [OpenEnvironment/SETUP.md](OpenEnvironment/SETUP.md) for details, [OpenEnvironment/ENV_TEMPLATE.md](OpenEnvironment/ENV_TEMPLATE.md) for all env vars.

## How it works

```
User command
  -> Parsing cascade (Narrative pipeline -> SemanticParser -> Regex)
  -> Scene graph resolves references ("make the mountains taller")
  -> TerrainBuilder stamps features onto heightmap
  -> Splatmap generator assigns textures by height/slope
  -> Frontend renders via Three.js displacement shader
```

19+ terrain primitives (mountains, valleys, dunes, cliffs, mesas, ridges, volcanoes, ...). Quality evaluation scores composition and texture coverage after each generation.

## API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/generate` | POST | Generate terrain from text |
| `/api/modify` | POST | Modify existing terrain |
| `/api/state` | GET | Current terrain state |
| `/api/reset` | POST | Reset terrain |
| `/api/templates` | GET | List templates |
| `/api/templates/{id}/apply` | POST | Apply a template |
| `/api/mcp/tools` | GET | List MCP tools |
| `/api/status` | GET | Server/API key status |

Full reference: [OpenEnvironment/docs/usage/api.md](OpenEnvironment/docs/usage/api.md)

## Project layout

```
server/           Python backend (FastAPI)
  engine/         TerrainBuilder, stamping, splatmap, feature registry
  primitives/     One file per terrain type
  semantic/       LLM parsing, scene graph, evaluation, narrative pipeline
  services/       TerrainService, StateService, AssetService
  api/            Controllers + request models
web/              React + Three.js frontend
  src/shaders/    Custom GLSL (displacement, splatmap blending, voxel)
docs/             Documentation
```

## Tech

FastAPI, NumPy, SciPy, Pillow (backend). React 18, Vite, Three.js, Zustand (frontend). Cerebras/Together/Gemini for LLM.

## Docs

- [Architecture](OpenEnvironment/docs/architecture/overview.md)
- [Parsing strategies](OpenEnvironment/docs/architecture/parsing.md)
- [Scene graph](OpenEnvironment/docs/architecture/scene-graph.md)
- [Quality evaluation](OpenEnvironment/docs/architecture/quality.md)
- [API reference](OpenEnvironment/docs/usage/api.md)
- [Examples](OpenEnvironment/docs/usage/examples.md)
- [Development](OpenEnvironment/docs/development/guide.md)
- [Testing](OpenEnvironment/docs/development/testing.md)

## License

MIT
