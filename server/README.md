# Semantic Terrain Server

FastAPI backend for procedural terrain generation with natural language commands.

## Setup with `uv` (Recommended)

[uv](https://github.com/astral-sh/uv) is a blazingly fast Python package manager.

### First-time setup

```bash
cd server

# Install dependencies + create .venv + generate uv.lock
uv sync
```

### Run the server

**Important:** Run from the **repo root** (not from inside `server/`) so Python can find the `server` module:

```bash
# From repo root (semantic-terrain/)
# Set PYTHONPATH so Python can find the 'server' module
export PYTHONPATH="$(pwd)"  # macOS/Linux
# OR
$env:PYTHONPATH = (Get-Location).Path  # Windows PowerShell

uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the provided launcher scripts (they handle PYTHONPATH automatically):

```bash
# Windows
.\start-backend-uv.ps1

# macOS/Linux
chmod +x start-backend-uv.sh
./start-backend-uv.sh
```

That's it! The server will be running at `http://localhost:8000`.

### Adding/removing dependencies

```bash
# Add a new package
uv add python-dotenv

# Remove a package
uv remove python-dotenv

# Re-sync after manual pyproject.toml edits
uv sync

# Update lock file
uv lock
```

### Development tools

```bash
# Install dev dependencies (ruff, pytest)
uv sync --all-extras

# Run linter
uv run ruff check .

# Run tests (when added)
uv run pytest
```

## Setup with `pip` (Alternative)

```bash
cd server

# Create virtual environment
python -m venv .venv

# Activate it
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- `GET /api/state` - Get current terrain state (feature list)
- `POST /api/generate` - Generate terrain from command text
- `POST /api/modify` - Modify existing terrain (same as generate)
- `GET /assets/*` - Serve generated heightmaps/splatmaps

## Project Structure

```
server/
├── pyproject.toml      # uv/pip package definition
├── requirements.txt    # pip compatibility (kept in sync)
├── main.py            # FastAPI app + endpoints
├── terrain.py         # Core generation logic
├── utils.py           # Math helpers
└── __init__.py        # Makes this a package
```

## Important Notes

### Running with uv

Always run as a module to avoid import errors:

```bash
# ✅ Correct
uv run uvicorn server.main:app --reload

# ❌ Wrong (breaks relative imports)
uv run uvicorn main:app --reload
```

### Python Version

Requires Python 3.10+. If using multiple Python versions:

```bash
# Set specific version (optional)
echo "3.11" > .python-version
uv sync
```

### Output Directory

Generated assets are written to `../web/public/assets/` (relative to this directory).

Make sure the web frontend is in the expected location or update `OUT_DIR` in `main.py`.

## Troubleshooting

**ImportError: attempted relative import with no known parent package**
- Make sure you're running `uvicorn server.main:app` (with `server.` prefix)
- Ensure `__init__.py` exists in the server directory

**NumPy/SciPy compilation slow**
- Upgrade to Python 3.10-3.12 for wheel support
- Check CPU architecture (ARM/x86) matches available wheels

**CORS errors from frontend**
- Backend is configured for `allow_origins=["*"]` (permissive)
- Lock it down in production by editing `main.py`

