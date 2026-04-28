# OpenEnvironment Server

FastAPI backend for procedural terrain generation.

## Setup

```bash
cd OpenEnvironment/server
uv sync
```

## Run

```bash
# From repo root:
.\start-backend-uv.ps1

# Or manually:
uv run --directory OpenEnvironment/server uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
```

Always run from the repo root. The launcher script sets `PYTHONPATH` automatically.

## Dependencies

Managed via `pyproject.toml` + uv. No `requirements.txt`.

```bash
uv add some-package     # Add
uv remove some-package  # Remove
uv sync                 # Re-sync
uv run ruff check .     # Lint
uv run pytest tests/    # Test
```

## Endpoints

See [docs/usage/api.md](../docs/usage/api.md) for the full list.

Core: `/api/generate`, `/api/modify`, `/api/state`, `/api/reset`, `/api/regenerate`
Templates: `/api/templates`, `/api/templates/{id}/apply`
MCP: `/api/mcp/tools`, `/api/mcp/resources`
Status: `/api/status`
Assets: `/assets/*`
