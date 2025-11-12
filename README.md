# Semantic Terrain

A real-time web-based terrain generation system with natural language input. Generate Unity-ready heightmaps, splatmaps, and voxel meshes using semantic commands like "add a mountain on the left" or "create rolling dunes."

## Features

- 🗣️ **Natural language input** - "add a valley in the center", "make the mountain taller"
- 🧠 **LLM-powered parsing** - Uses Cerebras Llama for intelligent command understanding
- 🏔️ **19+ terrain primitives** - Mountains, hills, valleys, dunes, mesas, plateaus, cliffs, canyons, ridges, volcanoes, craters, and more
- 🎨 **Smart splatmaps** - Auto-generated RGBA terrain blending (grass, rock, sand, snow) based on height and slope
- 🌐 **Real-time 3D viewer** - React Three Fiber with custom displacement shaders and voxel raytracing
- 🎮 **Unity export** - 16-bit heightmaps + splatmaps ready for Unity TerrainData import
- 🧊 **Voxel generation** - Generate 3D voxel meshes (128³ to 2048³ resolution) for block-based games
- 🗺️ **Template system** - 16+ curated terrain templates with natural language or JSON actions
- 🚶 **Walkability zones** - Proactive path design with flat zones, paths, and clearings
- ⚡ **Fast iteration** - Modify terrain on the fly, deterministic rebuilds from feature state
- 📊 **Scene graph** - USD-inspired scene representation for semantic relationships

## Quick Start

### Prerequisites

- Python 3.10-3.12
- Node.js 18+ (for frontend)
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Cerebras API key (for full LLM functionality)

### Setup

1. **Configure Cerebras API Key** (Required for full features):
   ```bash
   # Create .env file in server/ directory
   cd server
   echo CEREBRAS_API_KEY=your_api_key_here > .env
   ```
   
   **Note:** Without the API key, the system will use regex-based parsing (limited features). The frontend will display a warning if the key is missing.

2. **Install Backend Dependencies**:
   ```bash
   # Using uv (recommended)
   cd server
   uv sync
   
   # OR using pip
   cd server
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**:
   ```bash
   cd web
   npm install
   # OR
   pnpm install
   ```

4. **Start the System**:
   ```bash
   # Terminal 1: Start backend
   .\start-backend-uv.ps1
   
   # Terminal 2: Start frontend
   .\start-frontend.ps1
   ```

5. **Open in Browser**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8001

See **[SETUP.md](SETUP.md)** for detailed instructions and troubleshooting.

## Example Commands

### Basic Terrain Generation
```
create a desert with rolling dunes and two mountains on the left
add a valley in the center
add three hills on the right
create a mountain pass between the mountains
```

### Modifying Existing Features
```
make the mountain taller
make the valley deeper
remove the first hill
```

### Complex Compositions
```
create a desert biome
add a large mountain in the top-left
add a large mountain in the top-right
add a mountain pass between the two mountains
add a deep valley in the center
add three hills scattered in the bottom half
```

### Walkability Zones
```
add a path from the center to the top-right
add a flat clearing near the center
add mountains on the left and right of the path
```

## Terrain Templates

The system includes 16+ curated templates showcasing different terrain types:

- **Mountain Landscapes**: Mountain ranges, alpine terrain
- **Desert Landscapes**: Dunes, canyons, mesas
- **Valley Systems**: River valleys, mountain basins
- **Volcanic Landscapes**: Volcanic fields with craters
- **Walkability Systems**: Paths, trading routes, mountain passes
- **Mixed Terrain**: Diverse landscapes showcasing all features

Templates can be applied via the API or frontend, and support both natural language commands and pre-composed JSON actions for deterministic generation.

## API Endpoints

### Core Endpoints
- `GET /api/status` - Server status and API key configuration
- `GET /api/state` - Get current terrain state
- `POST /api/generate` - Generate terrain from command
- `POST /api/modify` - Modify existing terrain
- `POST /api/reset` - Reset to flat terrain
- `POST /api/regenerate` - Rebuild from current state

### Template Endpoints
- `GET /api/templates` - List all templates
- `GET /api/templates/{id}` - Get template details
- `POST /api/templates/{id}/apply` - Apply template

### Assets
- `GET /assets/*` - Serve generated heightmaps, splatmaps, voxel meshes

## Documentation

- **[SETUP.md](SETUP.md)** - Installation and getting started
- **[server/docs/](server/docs/)** - Complete technical documentation
  - **[SYSTEM_EXPLANATION.md](server/docs/active/SYSTEM_EXPLANATION.md)** - How the system works
  - **[TEMPLATE_SYSTEM.md](server/docs/active/TEMPLATE_SYSTEM.md)** - Template system guide
  - **[WALKABILITY_ZONE_ARCHITECTURE.md](server/docs/active/WALKABILITY_ZONE_ARCHITECTURE.md)** - Walkability features
  - **[ARCHITECTURE_PRINCIPLES.md](server/docs/active/ARCHITECTURE_PRINCIPLES.md)** - Design principles

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + Three.js)                             │
│  - Natural language input                                │
│  - Real-time 3D visualization (heightmap & voxel)        │
│  - Template selector                                      │
│  - API key status monitoring                             │
└────────────┬────────────────────────────────────────────┘
             │ REST API (FastAPI)
             ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI + Python)                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Semantic Layer                                   │   │
│  │ - LLM parser (Cerebras Llama)                    │   │
│  │ - Regex parser (fallback)                        │   │
│  │ - Scene graph (USD-inspired)                     │   │
│  │ - Spatial resolver                                │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Engine Layer                                      │   │
│  │ - TerrainBuilder (single-pass generation)       │   │
│  │ - Feature registry (19+ primitives)             │   │
│  │ - Command pattern (Add/Remove/Modify)             │   │
│  │ - Walkability constraints                       │   │
│  │ - Template system                                │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Primitives Layer                                  │   │
│  │ - Mountains, hills, valleys, dunes              │   │
│  │ - Mesas, plateaus, cliffs, canyons               │   │
│  │ - Ridges, spurs, passes, volcanoes               │   │
│  │ - Walkability zones (paths, clearings)           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│  Outputs                                                 │
│  - 16-bit heightmaps (Unity TerrainData)                │
│  - 8-bit heightmaps (Web viewer)                        │
│  - RGBA splatmaps (texture blending)                    │
│  - Voxel meshes (.obj, .bin)                            │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Computation:** NumPy, SciPy
- **Noise:** Perlin noise (fBm with multiple octaves)
- **AI:** Cerebras Cloud SDK (Llama 3.1 8B)
- **Package Manager:** uv (recommended) or pip

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **3D Engine:** React Three Fiber + Three.js
- **Shaders:** Custom GLSL for:
  - Vertex displacement (heightmap)
  - Splatmap blending (RGBA textures)
  - Voxel raytracing (3D voxel visualization)

### Key Libraries
- **Backend:** `cerebras-cloud-sdk`, `python-dotenv`, `Pillow`
- **Frontend:** `@react-three/fiber`, `@react-three/drei`, `axios`

## Terrain Primitives

The system supports 19+ terrain features:

**Elevation Features:**
- Mountains, Hills, Mesas, Plateaus, Mounds, Pinnacles

**Depression Features:**
- Valleys, Canyons, Basins, Craters, Ravines

**Linear Features:**
- Ridges, Spurs, Passes, Slopes, Terraces

**Special Features:**
- Dunes, Cliffs, Volcanoes

**Walkability Zones:**
- Flat zones, Paths, Clearings

Each feature supports modifiers (taller, deeper, wider) and spatial relationships (relative positioning, semantic references).

## Configuration

### Environment Variables

Create a `.env` file in the `server/` directory:

```bash
# Required for full LLM functionality
CEREBRAS_API_KEY=your_api_key_here
```

**Getting a Cerebras API Key:**
1. Sign up at [Cerebras Cloud](https://www.cerebras.net/cloud)
2. Get your API key from the dashboard
3. Add it to `server/.env`

**Note:** Without the API key, the system falls back to regex-based parsing which has limited capabilities. The frontend will display a warning if the key is missing.

### Server Configuration

The server runs on `http://localhost:8001` by default. You can change the port in:
- `start-backend-uv.ps1` (Windows)
- Manual command: `uvicorn server.main:app --host 0.0.0.0 --port 8001`

### Frontend Configuration

The frontend runs on `http://localhost:5173` by default (Vite dev server).

## Development

### Project Structure

```
SemanticTerrain/
├── server/                 # Backend (FastAPI)
│   ├── engine/            # Core generation engine
│   ├── primitives/         # Terrain feature generators
│   ├── semantic/          # LLM parsing & scene graph
│   ├── main.py            # FastAPI app
│   ├── terrain.py         # Main orchestrator
│   └── .env              # API keys (create this)
├── web/                   # Frontend (React)
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── shaders/       # GLSL shaders
│   │   └── api.ts        # API client
│   └── public/           # Static assets
└── README.md             # This file
```

### Adding New Features

1. **New Terrain Primitive:**
   - Create generator in `server/primitives/`
   - Register in `server/engine/feature_registry.py`
   - Add to semantic parser tool registry

2. **New API Endpoint:**
   - Add route in `server/main.py`
   - Update `web/src/api.ts` for frontend

3. **New Template:**
   - Add to `server/engine/templates.py`
   - Use natural language commands or JSON actions

## Troubleshooting

### Backend Issues

**"CEREBRAS_API_KEY not found"**
- Create `server/.env` file with your API key
- Restart the server

**"ImportError: attempted relative import"**
- Always run from repo root (not from `server/`)
- Use the launcher scripts (`start-backend-uv.ps1`)

**Port already in use**
- Change port in launcher script or command
- Default: 8001

### Frontend Issues

**CORS errors**
- Backend allows all origins by default
- Check that backend is running on port 8001

**Terrain not loading**
- Check browser console for errors
- Verify backend is running and accessible
- Check API key status in the warning banner

### API Key Issues

**Frontend shows warning banner:**
- The `CEREBRAS_API_KEY` environment variable is not set
- Create `server/.env` with your key
- Restart the backend server
- The system will use limited regex parsing until configured

## Contributing

Contributions welcome! Areas for improvement:
- Additional terrain primitives
- Enhanced semantic parsing
- More template environments
- Performance optimizations
- Documentation improvements

## License

MIT - Use this as a foundation for your projects!
