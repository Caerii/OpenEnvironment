# Setup

## Prerequisites

- Python 3.10-3.12
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [pnpm](https://pnpm.io/) (Node.js package manager)
- At least one LLM API key: [Cerebras](https://console.cerebras.ai/), [Together](https://api.together.xyz/), or [Gemini](https://makersuite.google.com/app/apikey)

## 1. API key

Create `OpenEnvironment/server/.env`:

```
CEREBRAS_API_KEY=your_key_here
```

Without this, the system falls back to regex parsing (no LLM features). The frontend shows a warning banner if the key is missing. See [ENV_TEMPLATE.md](ENV_TEMPLATE.md) for all options.

## 2. Backend

```bash
cd OpenEnvironment/server
uv sync
cd ../..
.\start-backend-uv.ps1
```

Runs on http://localhost:8001.

If you don't have uv:
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 3. Frontend

```bash
cd OpenEnvironment/web
pnpm install
pnpm dev
```

Runs on http://localhost:5173.

If you don't have pnpm: `npm install -g pnpm`

## 4. Verify

Open http://localhost:5173. Try: "create a desert with rolling dunes and two mountains on the left"

## Troubleshooting

**ImportError / ModuleNotFoundError**: Run from the repo root. The launcher scripts handle `PYTHONPATH` automatically.

**API key not detected**: Make sure `OpenEnvironment/server/.env` exists with `CEREBRAS_API_KEY=your_key` (no spaces around `=`). Restart the backend.

**Black screen in browser**: Check that the backend is running on port 8001. Check browser console for errors. Hit http://localhost:8001/api/status to verify.

**NumPy build issues**: Use Python 3.10-3.12 for pre-built wheels.
