# Semantic Terrain Server

FastAPI backend for procedural terrain generation with natural language commands.

## Setup with `uv` (Recommended)

[uv](https://github.com/astral-sh/uv) is a blazingly fast Python package manager.

### First-time setup

```bash
cd server
uv sync  # Install dependencies + create .venv + generate uv.lock
```

### Run the server

**Easiest way:** Use the launcher script from repo root:

```bash
.\start-backend-uv.ps1
```

**Manual way:** Run from repo root (not from inside `server/`):

```bash
# Set PYTHONPATH so Python can find the 'server' module
export PYTHONPATH="$(pwd)"  # macOS/Linux
# OR
$env:PYTHONPATH = (Get-Location).Path  # Windows PowerShell

uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
```

Server runs at `http://localhost:8001`

### Adding/removing dependencies

```bash
uv add python-dotenv        # Add package
uv remove python-dotenv     # Remove package
uv sync                     # Re-sync after manual edits
uv lock                     # Update lock file
```

### Development tools

```bash
uv sync --all-extras        # Install dev dependencies (ruff, pytest)
uv run ruff check .         # Run linter
uv run pytest               # Run tests (when added)
```

## Setup with `pip` (Alternative)

```bash
cd server
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

- `GET /api/state` - Get current terrain state (feature list)
- `POST /api/generate` - Generate terrain from command text
- `POST /api/modify` - Modify existing terrain (same as generate)
- `GET /assets/*` - Serve generated heightmaps/splatmaps

## Project Structure

```
server/
├── docs/              # Documentation hub
├── engine/            # Terrain generation engine
│   ├── builder.py    # TerrainBuilder (single-pass generation)
│   ├── commands.py   # Command pattern (Add/Remove/Modify)
│   ├── stamping.py   # Feature stamping & blending
│   └── splatmap.py   # Texture map generation
├── primitives/        # Feature generators
│   ├── mountains.py  # Mountains, hills, mesas
│   ├── valleys.py    # Valleys, canyons
│   ├── dunes.py      # Desert dunes
│   └── [16 more]     # Cliffs, slopes, ridges, etc.
├── semantic/          # Natural language processing
│   ├── parser.py     # LLM-powered semantic parser
│   ├── scene/        # Scene graph (USD-inspired)
│   ├── state_manager.py
│   └── spatial_resolver.py
├── main.py            # FastAPI app + endpoints
├── terrain.py         # Main orchestrator
└── pyproject.toml     # Dependencies
```

## Troubleshooting

**ImportError: attempted relative import**
- Always run from repo root with `server.` prefix
- Use the launcher scripts (they handle this automatically)

**NumPy/SciPy compilation slow**
- Use Python 3.10-3.12 for pre-built wheels
- Check CPU architecture matches available wheels

**CORS errors from frontend**
- Backend allows all origins by default (`allow_origins=["*"]`)
- Lock down in production by editing `main.py`

**Port already in use**
- Change port in launcher scripts or manual command
- Default: 8001

## Documentation

See [docs/](docs/) for:
- Architecture principles
- Development context
- Testing guides
- Refactoring recommendations
