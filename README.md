# OpenEnvironment

OpenEnvironment is an **RL-for-games environment construction toolkit**: generate and mutate game-ready world state and assets via an API so you can run training loops against consistent, replayable environments.

Today, the concrete environment module in this repo is **terrain/world layout generation** (heightmaps, splatmaps, optional voxel meshes). The longer-term goal is a broader environment builder (scenarios, constraints, evaluation signals) suitable for RL workflows.

- **Vision**: [OpenEnvironment/docs/vision/RL_FOR_GAMES.md](OpenEnvironment/docs/vision/RL_FOR_GAMES.md)

## Quick start

Everything lives under `OpenEnvironment/`. The repo root only contains launcher scripts and this README.

```bash
# 1. Backend
cd OpenEnvironment/server && uv sync && cd ../..
echo CEREBRAS_API_KEY=your_key > OpenEnvironment/server/.env
.\start-backend-uv.ps1          # http://localhost:8001

# 2. Frontend (new terminal)
cd OpenEnvironment/web && pnpm install && cd ../..
.\start-frontend.ps1             # http://localhost:5173
```

Needs Python 3.10-3.12, Node 18+, [uv](https://github.com/astral-sh/uv), [pnpm](https://pnpm.io/), and at least one LLM API key ([Cerebras](https://console.cerebras.ai/), [Together](https://api.together.xyz/), or [Gemini](https://makersuite.google.com/app/apikey)).

Without an API key the system falls back to **regex parsing** (no LLM parsing features).

See [OpenEnvironment/SETUP.md](OpenEnvironment/SETUP.md) for details, [OpenEnvironment/ENV_TEMPLATE.md](OpenEnvironment/ENV_TEMPLATE.md) for all env vars.

## What you get today

- **Stateful environment iteration**: generate/modify/reset/regenerate from a persisted JSON state
- **Generation outputs**: heightmap + splatmap (+ optional voxel mesh export)
- **Reference resolution**: scene graph entities (“the dunes”, “first mountain”)
- **Evaluation signals**: composition/texture metrics + rubric scoring
- **Two clients**: REST API + a React/Three.js viewer

## High-level flow

```
Command or template
  -> parse to actions (narrative -> semantic -> regex)
  -> apply actions to state (add/modify/remove)
  -> build terrain from state (heightmap + splatmap)
  -> evaluate (metrics/rubric)
  -> return state + asset paths
```

## API (backend on http://localhost:8001)

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
OpenEnvironment/
  server/         Python backend (FastAPI)
  web/            React + Three.js frontend
  docs/           Documentation (vision, architecture, usage, development)
  SETUP.md        Setup instructions
  ENV_TEMPLATE.md Env var template (copy to OpenEnvironment/server/.env)
```

## Tech

FastAPI, NumPy, SciPy, Pillow (backend). React 18, Vite, Three.js, Zustand (frontend). Cerebras/Together/Gemini for LLM.

## Documentation

- **Start here**: [OpenEnvironment/README.md](OpenEnvironment/README.md)
- **Docs index**: [OpenEnvironment/docs/README.md](OpenEnvironment/docs/README.md)
- **Vision**: [OpenEnvironment/docs/vision/RL_FOR_GAMES.md](OpenEnvironment/docs/vision/RL_FOR_GAMES.md)

## License

MIT
