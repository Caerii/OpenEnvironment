# Semantic Terrain

A real-time web-based terrain generation system with natural language input. Generate Unity-ready heightmaps and splatmaps using semantic commands like "add a mountain on the left" or "create rolling dunes."

## Features

- 🗣️ **Natural language input** - "add a valley in the center", "make the mountain taller"
- 🏔️ **Procedural generation** - Mountains, hills, valleys, dunes with Perlin noise & Gaussian stamps
- 🎨 **Smart splatmaps** - Auto-generated RGBA terrain blending (grass, rock, sand, snow)
- 🌐 **Real-time 3D viewer** - React Three Fiber with custom displacement shaders
- 🎮 **Unity export** - 16-bit heightmaps + splatmaps ready for Unity TerrainData import
- ⚡ **Fast iteration** - Modify terrain on the fly, deterministic rebuilds from feature state

## Quick Start

See **[SETUP.md](SETUP.md)** for detailed installation instructions.

### TL;DR

1. **Backend (with uv):** 
   - Setup: `cd server && uv sync`
   - Run: `uv run --directory server uvicorn server.main:app --reload` (from repo root)
   - ⚠️ **Set PYTHONPATH first:** `export PYTHONPATH="$(pwd)"` (Unix) or `$env:PYTHONPATH = (Get-Location).Path` (PowerShell)
   - Or use provided scripts: `.\start-backend-uv.ps1` (Windows) / `./start-backend-uv.sh` (Unix)
   - ✅ **Placeholder textures are auto-generated on startup!**
2. **Frontend:** `cd web && npm install && npm run dev`
3. Open `http://localhost:5173` and start creating terrain!

## Example Commands

```
create a desert with rolling dunes and two mountains on the left
add a valley in the center
make the mountain taller
add three hills on the right
remove valley
```

## Tech Stack

- **Backend:** FastAPI (Python) + NumPy + Perlin noise
- **Frontend:** React + Vite + React Three Fiber + Three.js
- **Shaders:** Custom GLSL for vertex displacement + splatmap blending

## License

MIT - Use this as a foundation for your projects!
