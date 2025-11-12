# Semantic Terrain

**A real-time, AI-powered terrain generation system** that converts natural language commands into procedural 3D terrain with heightmaps, splatmaps, and voxel meshes. Features multiple parsing strategies (narrative-driven, LLM-powered, multi-agent), quality evaluation, and a USD-inspired scene graph for semantic understanding.

---

## 🎯 Key Features

### Natural Language Processing
- 🗣️ **Multiple Parsing Strategies** - Narrative pipeline, SemanticParser, ReAct agent, Multi-agent workflow
- 🧠 **LLM-Powered** - Supports Cerebras, Together AI, and Google Gemini
- 📊 **Scene Graph** - USD-inspired semantic representation for reference resolution
- 🔍 **Spatial Queries** - "find features near the dunes", "what's in the center?"

### Terrain Generation
- 🏔️ **19+ Terrain Primitives** - Mountains, hills, valleys, dunes, mesas, plateaus, cliffs, canyons, ridges, volcanoes, craters, and more
- 🎨 **Smart Splatmaps** - Auto-generated RGBA terrain blending (grass, rock, sand, snow) based on height and slope
- ⚡ **Single-Pass Generation** - Efficient TerrainBuilder pattern, no double rebuilds
- 🎮 **Unity Export** - 16-bit heightmaps + splatmaps ready for Unity TerrainData import
- 🧊 **Voxel Generation** - Generate 3D voxel meshes (128³ to 2048³ resolution) for block-based games

### Quality & Refinement
- 📈 **Quality Evaluation** - Feature metrics, texture metrics, and aesthetic quality rubrics ✅ **Production**
- 🔄 **Iterative Refinement** - Automatic parameter adjustments based on quality feedback ✅ **Production**
- 🤝 **Multi-Agent Workflow** - Artist/Critic/Integrator/Judge collaboration for high-quality terrain ⚠️ **Experimental** (edge cases prevent full integration)
- 🎭 **Narrative-Driven** - Story-based terrain generation with archetypes and aesthetic goals ✅ **Production**

### Advanced Features
- 🗺️ **Template System** - 16+ curated terrain templates with natural language or JSON actions
- 🚶 **Walkability Zones** - Proactive path design with flat zones, paths, and clearings
- 🌐 **Real-time 3D Viewer** - React Three Fiber with custom displacement shaders and voxel raytracing
- 📊 **State Persistence** - Atomic state management with scene graph serialization

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10-3.12
- Node.js 18+ (for frontend)
- **[uv](https://github.com/astral-sh/uv)** - Python package manager (required for backend)
- **[pnpm](https://pnpm.io/)** - Node.js package manager (required for frontend)
- At least one LLM API key (Cerebras, Together, or Google Gemini)

### Setup

1. **Configure API Key** (Required for full features):
   ```bash
   # Create .env file in server/ directory
   cd server
   echo CEREBRAS_API_KEY=your_api_key_here > .env
   ```
   
   See **[ENV_TEMPLATE.md](ENV_TEMPLATE.md)** for all available environment variable options.

2. **Install Backend Dependencies** (using `uv`):
   ```bash
   cd server
   uv sync
   ```
   
   **Note:** This project uses `uv` for Python dependency management. If you don't have `uv` installed:
   ```bash
   # Install uv (Windows PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or see: https://github.com/astral-sh/uv#installation
   ```

3. **Install Frontend Dependencies** (using `pnpm`):
   ```bash
   cd web
   pnpm install
   ```
   
   **Note:** This project uses `pnpm` for Node.js dependency management. If you don't have `pnpm` installed:
   ```bash
   # Install pnpm
   npm install -g pnpm
   
   # Or see: https://pnpm.io/installation
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

**For detailed setup instructions and troubleshooting, see [SETUP.md](SETUP.md).**

---

## 💡 Example Commands

### Basic Terrain Generation
```
create a desert with rolling dunes and two mountains on the left
add a valley in the center
add three hills on the right
```

### Modifying Existing Features
```
make the mountain taller
make the valley deeper
remove the first hill
```

### Complex Compositions
```
create a dramatic mountain landscape
design a balanced desert with scattered dunes
build a volcanic field with multiple craters
```

**For comprehensive examples and usage patterns, see [docs/EXAMPLES.md](docs/EXAMPLES.md).**

---

## 📚 Documentation

Complete documentation is available in the **[docs/](docs/)** directory. Start with the **[Documentation Index](docs/README.md)** for an overview.

### Core System Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete system architecture
  - Layer-by-layer breakdown
  - Data flow diagrams
  - Component interactions
  - Design principles

- **[docs/PARSING_STRATEGIES.md](docs/PARSING_STRATEGIES.md)** - Parsing strategies explained
  - Narrative Pipeline (default)
  - SemanticParser (LLM + scene graph)
  - ReAct Agent (tool-calling reasoning)
  - Multi-Agent Workflow (artist/critic)
  - Regex Fallback (basic parsing)

- **[docs/QUALITY_EVALUATION.md](docs/QUALITY_EVALUATION.md)** - Quality evaluation system
  - Feature metrics (spacing, distribution, hierarchy)
  - Texture metrics (coverage, blending, gaps)
  - Quality rubric and scoring
  - Automatic refinement system

- **[docs/SCENE_GRAPH.md](docs/SCENE_GRAPH.md)** - Scene graph system
  - Entity management and labels
  - Reference resolution ("the dunes" → feature IDs)
  - Spatial queries
  - Serialization and persistence

### Usage Documentation

- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API documentation
  - All endpoints with request/response examples
  - Core terrain generation endpoints
  - Template system endpoints
  - Multi-agent workflow endpoints
  - MCP (Model Context Protocol) endpoints

- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Usage examples and patterns
  - Basic terrain generation examples
  - Advanced composition examples
  - API usage examples
  - Command patterns and best practices

### Development Documentation

- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development guide
  - Project structure explained
  - Adding new features (primitives, endpoints, parsing strategies)
  - Testing guidelines
  - Code style and best practices
  - Contributing guidelines

### Setup & Configuration

- **[SETUP.md](SETUP.md)** - Detailed setup and installation guide
  - Step-by-step installation
  - Troubleshooting common issues
  - Platform-specific instructions

- **[ENV_TEMPLATE.md](ENV_TEMPLATE.md)** - Environment variables reference
  - Required API keys
  - Optional configuration
  - Getting API keys from providers

### Additional Resources

- **[server/docs/](server/docs/)** - Technical documentation
  - System explanation
  - Template system guide
  - Walkability architecture
  - Architecture principles

---

## 🏗️ System Architecture

Semantic Terrain uses a **layered architecture** with multiple parsing strategies, quality evaluation, and a scene graph for semantic understanding.

```
Frontend (React + Three.js)
    ↓ REST API
API Layer (FastAPI)
    ↓
Orchestration Layer (Multiple Parsing Strategies)
    ↓
Semantic Layer (Narrative, Quality, Scene Graph)
    ↓
Engine Layer (TerrainBuilder, Feature Registry)
    ↓
Primitives Layer (19+ Terrain Features)
    ↓
Output Layer (Heightmaps, Splatmaps, Voxels)
```

**For complete architecture details, including data flow diagrams and component interactions, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).**

---

## 🧠 Parsing Strategies

The system automatically selects the best parsing strategy based on command complexity:

1. **Narrative Pipeline** (Default) - Story-driven generation with aesthetic goals ✅ **Production**
2. **SemanticParser** - LLM-powered parsing with scene graph context ✅ **Production**
3. **ReAct Agent** - Tool-calling reasoning agent for complex commands ⚠️ **Experimental** (used in multi-agent workflow)
4. **Multi-Agent Workflow** - Artist/Critic/Integrator/Judge collaboration ⚠️ **Experimental** (separate endpoint, has edge cases)
5. **Regex Fallback** - Basic parsing without LLM (no API key required) ✅ **Production**

**Note:** Some parsing strategies (ReAct Agent, Multi-Agent Workflow) are experimental and have edge cases preventing full integration into the main pipeline. They are available via separate endpoints but may have limitations.

**For detailed information on each strategy, when to use them, and how they work, see [docs/PARSING_STRATEGIES.md](docs/PARSING_STRATEGIES.md).**

---

## 📡 API Endpoints

### Core Endpoints
- `POST /api/generate` - Generate terrain from command
- `POST /api/modify` - Modify existing terrain
- `GET /api/state` - Get current terrain state
- `POST /api/reset` - Reset to flat terrain
- `POST /api/regenerate` - Rebuild from current state

### Template Endpoints
- `GET /api/templates` - List all templates
- `GET /api/templates/{id}` - Get template details
- `POST /api/templates/{id}/apply` - Apply template

### Multi-Agent Endpoints
- `POST /api/design/multi-agent` - Run multi-agent terrain design workflow ⚠️ **Experimental** (has edge cases, not fully integrated)

### MCP Endpoints
- `GET /api/mcp` - MCP server information
- `GET /api/mcp/tools` - List available tools
- `POST /api/mcp/tools/{name}/call` - Execute tool

**For complete API documentation with request/response examples, see [docs/API_REFERENCE.md](docs/API_REFERENCE.md).**

---

## 🏔️ Terrain Primitives

The system supports 19+ terrain features:

**Elevation:** Mountains, Hills, Mesas, Plateaus, Mounds, Pinnacles  
**Depression:** Valleys, Canyons, Basins, Craters, Ravines  
**Linear:** Ridges, Spurs, Passes, Slopes, Terraces  
**Special:** Dunes, Cliffs, Volcanoes  
**Walkability:** Flat zones, Paths, Clearings

Each feature supports modifiers (taller, deeper, wider) and spatial relationships. For examples of using each feature type, see [docs/EXAMPLES.md](docs/EXAMPLES.md).

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `server/` directory. See **[ENV_TEMPLATE.md](ENV_TEMPLATE.md)** for complete configuration options.

**Required (at least one LLM API key):**
```bash
CEREBRAS_API_KEY=your_api_key_here
# OR
TOGETHER_API_KEY=your_api_key_here
# OR
GEMINI_API_KEY=your_gemini_api_key_here
```

**Optional Configuration:**
```bash
LLM_PROVIDER=cerebras          # cerebras, together, google
LLM_MODEL=llama3.1-8b          # Model name
PORT=8001                      # Server port
DEBUG=false                    # Debug mode
LOG_LEVEL=INFO                 # Logging level
TERRAIN_RESOLUTION=512         # Terrain size
DEFAULT_SEED=42                # Random seed
```

**Getting API Keys:**
- **Cerebras:** https://console.cerebras.ai/
- **Together AI:** https://api.together.xyz/
- **Google Gemini:** https://makersuite.google.com/app/apikey

**For all available environment variables and their descriptions, see [ENV_TEMPLATE.md](ENV_TEMPLATE.md).**

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Computation:** NumPy, SciPy
- **AI:** Cerebras Cloud SDK, Together AI, Google Gemini
- **Package Manager:** [uv](https://github.com/astral-sh/uv) (required)

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Package Manager:** [pnpm](https://pnpm.io/) (required)
- **3D Engine:** React Three Fiber + Three.js
- **Shaders:** Custom GLSL for displacement, blending, raytracing

---

## ⚠️ Known Issues & Experimental Features

**Important:** This codebase contains experimental features and broken parts of the pipeline that have edge cases preventing full integration into the production system.

### Experimental Features
Several features exist but are **not fully integrated** into the main production pipeline:
- **Feature Renderer System** (`RendererRegistry`) - Orphaned code, production uses `FeatureRegistry` instead
- **Domain Models** - Partial migration, production still uses dict-based features
- **Configuration System** - Exists but production uses hardcoded defaults
- **Slope Erosion** - Function exists but never called
- **Rubric Evolution** - Only used in experimental multi-agent workflow

### Broken/Incomplete Integration
Some features have edge cases or integration issues:
- **Multi-Agent Workflow** - Separate experimental endpoint (`/api/design/multi-agent`)
- **ReAct Agent** - Used in experimental workflows, not main pipeline
- **Domain Model Migration** - Incomplete transition from dicts to typed models
- **Configuration System** - Not utilized, defaults hardcoded in `feature_registry.py`

**For complete details on experimental features, broken integrations, and what's actually used in production, see [docs/UNDOCUMENTED_FEATURES.md](docs/UNDOCUMENTED_FEATURES.md).**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional terrain primitives
- Enhanced semantic parsing
- More template environments
- Performance optimizations
- Documentation improvements
- **Fixing experimental feature integration** - See [docs/UNDOCUMENTED_FEATURES.md](docs/UNDOCUMENTED_FEATURES.md) for details

**For development guidelines, project structure, and contribution process, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).**

---

## 📄 License

MIT - Use this as a foundation for your projects!

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [Three.js](https://threejs.org/)
- LLM support via [Cerebras](https://www.cerebras.net/), [Together AI](https://www.together.ai/), and [Google Gemini](https://deepmind.google/technologies/gemini/)
- Inspired by USD scene graphs and procedural generation techniques

---

## 📖 Documentation Quick Links

- **[Documentation Index](docs/README.md)** - Start here for an overview
- **[Architecture](docs/ARCHITECTURE.md)** - System design and data flow
- **[Parsing Strategies](docs/PARSING_STRATEGIES.md)** - How commands are parsed
- **[Quality Evaluation](docs/QUALITY_EVALUATION.md)** - Quality assessment system
- **[Scene Graph](docs/SCENE_GRAPH.md)** - Semantic understanding system
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Examples](docs/EXAMPLES.md)** - Usage examples and patterns
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development
