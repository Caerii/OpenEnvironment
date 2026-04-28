# OpenEnvironment

OpenEnvironment is an **RL-for-games environment construction toolkit**: generate and mutate game-ready world state and assets via an API so you can run training loops against consistent, replayable environments.

The bigger idea is in [docs/vision/RL_FOR_GAMES.md](docs/vision/RL_FOR_GAMES.md).

Today, the concrete environment module in this repo is **procedural terrain/world layout generation** (heightmaps, splatmaps, optional voxel meshes).

## Quick start

```bash
# 1. Backend
cd server && uv sync && cd ..
echo CEREBRAS_API_KEY=your_key > server/.env
.\start-backend-uv.ps1          # http://localhost:8001

# 2. Frontend (new terminal)
cd web && pnpm install && cd ..
.\start-frontend.ps1             # http://localhost:5173
```

Needs Python 3.10-3.12, Node 18+, [uv](https://github.com/astral-sh/uv), [pnpm](https://pnpm.io/), and at least one LLM API key ([Cerebras](https://console.cerebras.ai/), [Together](https://api.together.xyz/), or [Gemini](https://makersuite.google.com/app/apikey)). Without an API key the system falls back to regex parsing.

See [SETUP.md](SETUP.md) for details, [ENV_TEMPLATE.md](ENV_TEMPLATE.md) for all env vars.

## API

Full reference: [docs/usage/api.md](docs/usage/api.md)

## What exists today (so we stay honest)

- **Environment content generation**: terrain heightmap + splatmap outputs, optional voxel mesh export
- **Stateful iteration**: generate/modify/reset/regenerate using a persisted JSON state
- **Interpretation layer**: command parsing cascade + scene graph reference resolution
- **Evaluation**: composition/texture metrics and rubric scoring (useful as objective signals)

## Docs

- [Vision (RL for games)](docs/vision/RL_FOR_GAMES.md)
- [Architecture](docs/architecture/overview.md)
- [Parsing strategies](docs/architecture/parsing.md)
- [Scene graph](docs/architecture/scene-graph.md)
- [Quality evaluation](docs/architecture/quality.md)
- [API reference](docs/usage/api.md)
- [Examples](docs/usage/examples.md)
- [Development](docs/development/guide.md)
- [Testing](docs/development/testing.md)

## License

MIT