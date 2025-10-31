# Semantic Terrain - Setup Guide

A real-time web-based terrain generation system with natural language input. Generate heightmaps and splatmaps for Unity or web viewing using semantic commands like "add a mountain on the left" or "create rolling dunes."

## Architecture

- **Backend:** FastAPI (Python) - Procedural terrain generation with Perlin noise, Gaussian stamps, and smart splatmap blending
- **Frontend:** React + Vite + React Three Fiber - Real-time 3D viewer with custom displacement shaders
- **Export:** 16-bit heightmaps (Unity-ready) + RGBA splatmaps

---

## Prerequisites

- **Python 3.9+** with `pip`
- **Node.js 18+** with `npm`

---

## Setup Instructions

### 1. Backend Setup

#### Option A: Using `uv` (Recommended - Fast & Modern)

[uv](https://github.com/astral-sh/uv) is a blazingly fast Python package manager written in Rust.

**Install uv:**
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Setup & Run:**
```bash
cd server

# One command: creates .venv, installs deps, generates uv.lock
uv sync
```

**Run the server:**

**Important:** Run from the **repo root** (not from inside `server/`) so Python can find the `server` module:

```bash
# From repo root (semantic-terrain/)
# Set PYTHONPATH so Python can find the 'server' module
export PYTHONPATH="$(pwd)"  # macOS/Linux
# OR
$env:PYTHONPATH = (Get-Location).Path  # Windows PowerShell

uv run --directory server uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the launcher script (handles PYTHONPATH automatically):
```bash
# Windows
.\start-backend-uv.ps1

# macOS/Linux
chmod +x start-backend-uv.sh
./start-backend-uv.sh
```

#### Option B: Using `pip` (Traditional)

```bash
cd server

# Create virtual environment
python -m venv .venv

# Activate it:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server (port 8000)
uvicorn server.main:app --reload --port 8000
```

The backend will be running at `http://localhost:8000`

> **Note:** Always run as `uvicorn server.main:app` (with `server.` prefix) to avoid import errors.

### 2. Frontend Setup

**Note:** The backend automatically creates placeholder textures (solid colors) if they don't exist. You can replace them with real textures later.

```bash
cd web

# Install dependencies
npm install

# Run dev server (port 5173)
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Adding Textures (Required)

The system needs 4 tileable texture images. Place them in `web/public/textures/`:

- `grass.jpg` (512×512+ recommended)
- `rock.jpg`
- `sand.jpg`
- `snow.jpg`

### Quick Test Textures

For immediate testing, you can use solid color images:
- **Grass:** Bright green (#4CAF50)
- **Rock:** Gray (#808080)
- **Sand:** Tan/beige (#D2B48C)
- **Snow:** White (#FFFFFF)

### Free Texture Sources

- [Poly Haven](https://polyhaven.com/textures) - CC0 textures
- [CC0 Textures](https://cc0textures.com/) - Free PBR textures
- Any 512×512 JPG images work for prototyping

---

## Usage

1. **Start both servers** (backend on :8000, frontend on :5173)
2. Open `http://localhost:5173`
3. Enter commands in the sidebar textarea:

### Example Commands

```
create a desert with rolling dunes and two mountains on the left
add a valley in the center
make the mountain taller
add three hills on the right
remove valley
add dunes in the bottom-right
```

### Command Syntax

- **Add features:** `add/create [count] [feature] [in/on] [location]`
  - Features: `mountain`, `hill`, `valley`, `dunes`
  - Locations: `left`, `right`, `top`, `bottom`, `center`, `top-left`, etc.
  - Counts: `one`, `two`, `three`, or `1`, `2`, `3`

- **Modify:** `make the [feature] taller/wider/deeper`
- **Remove:** `remove [feature]`

### Buttons

- **Generate:** Creates new terrain from command
- **Modify:** Applies command to existing terrain state

---

## Output Files

Generated assets are saved to `web/public/assets/`:

- `height_<timestamp>_16.png` - 16-bit grayscale heightmap (Unity import)
- `height_<timestamp>_8.png` - 8-bit grayscale heightmap (web viewer)
- `splat_<timestamp>.png` - RGBA splatmap:
  - **R** = Grass weight
  - **G** = Rock weight
  - **B** = Sand weight
  - **A** = Snow weight

The web viewer automatically loads the latest assets with cache-busting timestamps.

---

## Unity Import (Optional)

The 16-bit heightmaps can be imported directly into Unity:

1. Import `height_*_16.png` as **Raw 16-bit**
2. Use `TerrainData.SetHeights()` to apply
3. Import `splat_*.png` for terrain layers
4. Map RGBA channels → terrain layers (grass, rock, sand, snow)

*(A Unity importer script can be added - let me know if needed)*

---

## Tech Stack Details

### Backend (Python)
- **FastAPI** - Modern async API framework
- **NumPy** - Array operations for heightmap generation
- **SciPy** - Gaussian filtering and smoothing
- **Pillow** - PNG export (8-bit and 16-bit)
- **noise** - Perlin noise generation for dunes and base terrain

### Frontend (TypeScript/React)
- **Vite** - Fast build tool
- **React Three Fiber** - React renderer for Three.js
- **@react-three/drei** - Helpers (OrbitControls, Stats)
- **Three.js** - WebGL rendering
- **Zustand** - Lightweight state management
- **Axios** - HTTP client

### Shader Pipeline
1. **Vertex Shader:** Displaces mesh vertices using 8-bit heightmap
2. **Fragment Shader:** Blends 4 textures using RGBA splatmap weights
3. Custom `ShaderMaterial` with displacement + albedo blending

---

## How It Works

### Terrain Generation Flow

1. **Parse command** → Extract feature type, count, location, modifiers
2. **Rebuild base** → Start with flat desert baseline (Perlin noise)
3. **Apply features** → Stamp mountains/hills (Gaussian), carve valleys, add dunes (directional noise)
4. **Smooth** → Gaussian blur for natural blending
5. **Generate splatmap:**
   - **Rock** = High slope (gradient magnitude)
   - **Snow** = High elevation (top 10%)
   - **Sand** = Dune mask + flat low areas
   - **Grass** = Everything else
6. **Export** → 16-bit + 8-bit heightmaps + RGBA splatmap

### Deterministic Rebuilds

The system stores a **feature list** (JSON state), not the raw heightmap. Every generate/modify rebuilds the entire terrain from this list, ensuring:
- **Undo/redo** is trivial (just revert state)
- **No accumulation artifacts**
- **Reproducible results**

---

## Development Tips

### Adjusting Displacement Scale

Edit `web/src/components/TerrainViewer.tsx`:
```tsx
makeTerrainMaterial(heightTex, splatTex, grass, rock, sand, snow, 50)
                                                               // ↑ Change this value
```

### Changing Terrain Resolution

Edit `server/terrain.py`:
```python
RES = 512  # Change to 1024 for higher detail (slower)
```

### Modifying Splatmap Logic

Edit `server/terrain.py` → `make_splatmap()` function

### Adding More Features

1. Add feature type in `parse_command()` detection
2. Add stamp/generation function (like `add_dunes`)
3. Add feature handling in `apply_actions()`

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.9+)
- Ensure venv is activated (you should see `(.venv)` in prompt)
- Try: `pip install --upgrade pip` then reinstall requirements

### Frontend shows black screen
- Check browser console for texture load errors
- Ensure all 4 textures exist in `web/public/textures/`
- Check backend is running on port 8000

### CORS errors
- Ensure backend is running on `localhost:8000`
- Check FastAPI CORS middleware in `server/main.py`

### Terrain not updating
- Open Network tab in DevTools
- Check `/api/generate` POST requests are succeeding
- Verify `web/public/assets/` directory exists and is writable

---

## Next Steps / Future Enhancements

- **Triplanar mapping** - Eliminate UV stretching on steep slopes
- **Canyon primitive** - Polyline stamp with falloff for river valleys
- **Erosion simulation** - Micro-detail on steep slopes
- **Advanced NL parsing** - "remove the second mountain" by ordinal
- **MCP integration** - Model Context Protocol for AI agent control
- **Unity importer script** - One-click import to Unity terrain system
- **Texture synthesis** - Generate detail maps from splatmap
- **Multi-biome support** - Switch between desert/forest/arctic bases

---

## File Structure

```
semantic-terrain/
├─ server/                    # Python FastAPI backend
│  ├─ requirements.txt        # Python dependencies
│  ├─ main.py                 # API endpoints + CORS
│  ├─ terrain.py              # Core generation logic
│  └─ utils.py                # Math helpers (normalize, slope, etc.)
│
└─ web/                       # React + Vite frontend
   ├─ package.json            # Node dependencies
   ├─ vite.config.ts          # Vite configuration
   ├─ tsconfig.json           # TypeScript config
   ├─ index.html              # HTML entry point
   │
   ├─ src/
   │  ├─ main.tsx             # React app entry
   │  ├─ App.tsx              # Main UI component
   │  ├─ api.ts               # Backend API client (Axios)
   │  ├─ state.ts             # Zustand store (assets/state)
   │  │
   │  ├─ components/
   │  │  └─ TerrainViewer.tsx # 3D canvas + terrain mesh
   │  │
   │  └─ shaders/
   │     └─ terrainMaterial.ts # Custom displacement shader
   │
   └─ public/
      ├─ textures/            # ADD YOUR 4 TEXTURES HERE
      │  ├─ grass.jpg         # (required)
      │  ├─ rock.jpg          # (required)
      │  ├─ sand.jpg          # (required)
      │  └─ snow.jpg          # (required)
      │
      └─ assets/              # Generated heightmaps/splatmaps (auto-created)
```

---

## License

This starter is provided as-is for rapid prototyping. Adapt it for your project needs.

---

## Questions?

This is a **drop-in foundation** meant to get you iterating fast. If something's unclear or you hit issues:
1. Check the browser console and terminal logs
2. Verify both servers are running
3. Ensure textures are in place
4. Check CORS isn't blocked

**Now go make some terrain!** 🏔️🏜️

