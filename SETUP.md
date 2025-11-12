# Semantic Terrain - Setup Guide

Get started with the Semantic Terrain system in minutes.

## Prerequisites

- **Python 3.10-3.12** ([uv](https://github.com/astral-sh/uv) recommended or pip)
- **Node.js 18+** with npm or pnpm
- **Cerebras API Key** (for full LLM functionality) - [Get one here](https://www.cerebras.net/cloud)

## Quick Start

### 1. Configure Cerebras API Key (Important!)

**This step is required for full LLM-powered natural language parsing.**

Create a `.env` file in the `server/` directory:

```bash
cd server
echo CEREBRAS_API_KEY=your_api_key_here > .env
```

**Getting your API key:**
1. Sign up at [Cerebras Cloud](https://www.cerebras.net/cloud)
2. Navigate to your dashboard
3. Copy your API key
4. Add it to `server/.env` as shown above

**Note:** Without the API key, the system will use regex-based parsing with limited capabilities. The frontend will display a warning banner if the key is missing.

### 2. Backend Setup

**Easiest way (uses uv):**
```bash
.\start-backend-uv.ps1
```

Server runs on `http://localhost:8001`

**Manual setup with uv:**
```bash
cd server
uv sync  # Install dependencies
cd ..
uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
```

**Manual setup with pip:**
```bash
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cd ..
uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
```

See [server/README.md](server/README.md) for more detailed instructions.

### 3. Frontend Setup

```bash
cd web
npm install
# OR
pnpm install

npm run dev
# OR
pnpm dev
```

Frontend runs on `http://localhost:5173`

### 4. Verify Installation

1. Open http://localhost:5173 in your browser
2. Check for API key warning banner (if key is missing)
3. Try generating terrain with a command like: "create a desert with rolling dunes"

## Troubleshooting

**Backend won't start:**
- Install uv: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
- Or use pip: See [server/README.md](server/README.md)
- Make sure you're running from the repo root, not inside `server/`

**Frontend shows warning about API key:**
- Create `server/.env` file with `CEREBRAS_API_KEY=your_key`
- Restart the backend server
- The frontend will automatically detect when the key is configured

**Frontend shows black screen:**
- Check backend is running on port 8001
- Check browser console for errors
- Verify API endpoint is accessible: http://localhost:8001/api/status
- Textures auto-generate on first backend run

**Module not found errors:**
- Make sure you run from repo root, not inside `server/`
- Use the provided launcher scripts
- Check that PYTHONPATH is set correctly (launcher scripts handle this)

**CEREBRAS_API_KEY not found:**
- Verify `.env` file exists in `server/` directory
- Check that the file contains: `CEREBRAS_API_KEY=your_actual_key`
- Make sure there are no spaces around the `=` sign
- Restart the backend after adding the key

**LLM parsing not working:**
- Check that API key is valid and not expired
- Verify the Cerebras SDK is installed: `uv sync` or `pip install cerebras-cloud-sdk`
- Check backend logs for API errors
- System will fall back to regex parsing if LLM fails

## Next Steps

- Try the example commands in the README
- Explore the template system (16+ pre-built terrains)
- Read the [technical documentation](server/docs/)
- Check out [SYSTEM_EXPLANATION.md](server/docs/active/SYSTEM_EXPLANATION.md) to understand how it works
