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

```bash
# 1. Start backend
.\start-backend-uv.ps1

# 2. Start frontend (new terminal)
.\start-frontend.ps1

# 3. Open http://localhost:5173
```

See **[SETUP.md](SETUP.md)** for detailed instructions.

## Example Commands

```
create a desert with rolling dunes and two mountains on the left
add a valley in the center
make the mountain taller
add three hills on the right
remove valley
create a mountain pass between the mountains
```

## Documentation

- **[SETUP.md](SETUP.md)** - Installation and getting started
- **[server/docs/](server/docs/)** - All technical documentation

## Architecture

```
┌──────────────────────────────────────┐
│  Frontend (React + Three.js)         │
│  - Natural language input            │
│  - Real-time 3D visualization        │
└────────────┬─────────────────────────┘
             │ REST API
             ▼
┌──────────────────────────────────────┐
│  Backend (FastAPI + Python)          │
│  - LLM-powered semantic parser       │
│  - Scene graph (USD-inspired)        │
│  - Procedural generation engine      │
└──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Outputs                             │
│  - 16-bit heightmaps (Unity)         │
│  - 8-bit heightmaps (Web)            │
│  - RGBA splatmaps (texture blend)    │
└──────────────────────────────────────┘
```

## Tech Stack

- **Backend:** FastAPI (Python) + NumPy + Perlin noise
- **Frontend:** React + Vite + React Three Fiber + Three.js
- **Shaders:** Custom GLSL for vertex displacement + splatmap blending
- **AI:** Cerebras Llama for semantic parsing

## License

MIT - Use this as a foundation for your projects!
