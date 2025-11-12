# System Architecture

Complete architecture overview of the Semantic Terrain system.

---

## Architecture Overview

Semantic Terrain uses a **layered architecture** with multiple parsing strategies, quality evaluation, and a scene graph for semantic understanding.

### Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + Three.js)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  UI Components                                            │  │
│  │  - Command input (natural language)                       │  │
│  │  - Template selector                                      │  │
│  │  - 3D viewer (heightmap & voxel)                          │  │
│  │  - API key status                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Shaders (GLSL)                                           │  │
│  │  - Vertex displacement (heightmap)                        │  │
│  │  - Splatmap blending (RGBA textures)                     │  │
│  │  - Voxel raytracing (3D visualization)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (FastAPI)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer (main.py)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Controllers                                               │  │
│  │  - TerrainController (generate, modify, reset)          │  │
│  │  - TemplateController (list, apply templates)           │  │
│  │  - MCPController (tool registry, resources)             │  │
│  │  - StatusController (API key status)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services                                                  │  │
│  │  - TerrainService (generation orchestration)              │  │
│  │  - StateService (persistence, atomic operations)         │  │
│  │  - AssetService (file management)                         │  │
│  │  - MultiAgentService (artist/critic workflow)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Orchestration Layer (orchestration.py)             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Command Parsing (Multiple Strategies)                    │  │
│  │  1. Narrative Pipeline (story-driven)                    │  │
│  │  2. SemanticParser (LLM + scene graph)                   │  │
│  │  3. ReAct Agent (tool-calling reasoning)                  │  │
│  │  4. Multi-Agent Workflow (artist/critic)                 │  │
│  │  5. Regex Fallback (basic parsing)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Scene Graph Integration                                  │  │
│  │  - TerrainSceneGraph (USD-inspired)                      │  │
│  │  - Entity management (labels, references)                 │  │
│  │  - Reference resolution ("the dunes" → IDs)               │  │
│  │  - Spatial queries (find features by location)            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Semantic Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Narrative System (narrative/)                           │  │
│  │  - Archetype matching (desert, mountain, etc.)           │  │
│  │  - Story generation                                      │  │
│  │  - Feature composition (focal, supporting, accent)       │  │
│  │  - Aesthetic goals (drama, balance, etc.)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Quality Evaluation (evaluation.py)                      │  │
│  │  - Feature metrics (spacing, distribution)                │  │
│  │  - Texture metrics (coverage, blending)                   │  │
│  │  - Quality rubric (composition, textures)                 │  │
│  │  - Refinement suggestions                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tools (tools/)                                           │  │
│  │  - Query tools (entities, relationships)                  │  │
│  │  - Spatial tools (position calculation)                   │  │
│  │  - Resolution tools (reference resolution)                │  │
│  │  - Narrative tools (composition generation)               │  │
│  │  - Quality tools (evaluation, refinement)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LLM Clients (llm/)                                      │  │
│  │  - CerebrasLLMClient                                     │  │
│  │  - TogetherLLMClient                                      │  │
│  │  - GoogleLLMClient (Gemini)                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Engine Layer                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TerrainBuilder (builder.py)                              │  │
│  │  - Single-pass construction                               │  │
│  │  - Feature application                                    │  │
│  │  - Adaptive smoothing                                    │  │
│  │  - Walkability constraints                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Feature Registry (feature_registry.py)                  │  │
│  │  - 19+ terrain primitives                                 │  │
│  │  - Default parameters                                     │  │
│  │  - Variation system                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Stamping System (stamping.py)                            │  │
│  │  - Blending modes (add, max, smooth)                      │  │
│  │  - Adaptive smoothing                                    │  │
│  │  - Edge erosion                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Splatmap Generation (splatmap.py)                       │  │
│  │  - Height-based texture selection                         │  │
│  │  - Slope-based texture blending                           │  │
│  │  - RGBA channel mapping                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Primitives Layer                              │
│  Elevation: Mountains, Hills, Mesas, Plateaus, Mounds, Pinnacles │
│  Depression: Valleys, Canyons, Basins, Craters, Ravines         │
│  Linear: Ridges, Spurs, Passes, Slopes, Terraces                │
│  Special: Dunes, Cliffs, Volcanoes                               │
│  Walkability: Flat zones, Paths, Clearings                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Output Layer                                   │
│  Heightmaps (16-bit Unity, 8-bit Web) | Splatmaps (RGBA)        │
│  Voxel Meshes (.obj, .bin) | State Persistence (JSON)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Complete Data Flow: Command to Terrain

```
User Command
    │
    ▼
┌─────────────────────────────────────┐
│  Parsing Strategy Selection          │
│  (Narrative → Semantic → ReAct)      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Action Generation                  │
│  - Parse to structured actions      │
│  - Resolve references ("the dunes") │
│  - Calculate positions              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Quality Evaluation (Optional)      │
│  - Assess composition               │
│  - Check texture coverage            │
│  - Generate refinement suggestions  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Terrain Generation                 │
│  - Build base biome                 │
│  - Apply features (single-pass)     │
│  - Generate splatmap                │
│  - Apply smoothing                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Scene Graph Update                 │
│  - Create entities                  │
│  - Update relationships             │
│  - Store semantic labels            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Output Generation                  │
│  - Heightmap (16-bit, 8-bit)       │
│  - Splatmap (RGBA)                  │
│  - Voxel mesh (optional)             │
└──────────────┬──────────────────────┘
               │
               ▼
         Frontend Display
```

---

## Layer Details

### Frontend Layer
- **React + Three.js** - Modern web UI with 3D visualization
- **Custom GLSL Shaders** - Vertex displacement, splatmap blending, voxel raytracing
- **Real-time Updates** - Live terrain preview as commands are processed

### API Layer
- **FastAPI** - Modern Python web framework
- **Controller-Service Pattern** - Clean separation of concerns
- **RESTful Endpoints** - Standard HTTP API
- **CORS Support** - Cross-origin resource sharing enabled

### Orchestration Layer
- **Multiple Parsing Strategies** - Automatic selection based on command complexity
- **Scene Graph Integration** - Semantic understanding and reference resolution
- **State Management** - Atomic operations for consistency

### Semantic Layer
- **Narrative System** - Story-driven terrain generation
- **Quality Evaluation** - Feature and texture metrics
- **Tool System** - Query, spatial, resolution, narrative, quality tools
- **LLM Integration** - Multiple provider support (Cerebras, Together, Google)

### Engine Layer
- **TerrainBuilder** - Single-pass construction pattern
- **Feature Registry** - Centralized feature management
- **Stamping System** - Efficient feature application
- **Splatmap Generation** - Texture blending algorithms

### Primitives Layer
- **19+ Terrain Features** - Elevation, depression, linear, special, walkability
- **Variation System** - Procedural variation for natural appearance
- **Parameter System** - Configurable feature properties

### Output Layer
- **Multiple Formats** - Heightmaps, splatmaps, voxels
- **Unity Export** - Ready for Unity TerrainData import
- **State Persistence** - JSON-based state management

---

## Component Interactions

### Command Processing Flow

1. **User Input** → Frontend sends command to API
2. **API Layer** → Routes to TerrainController
3. **Orchestration** → Selects parsing strategy
4. **Semantic Layer** → Parses command, evaluates quality
5. **Engine Layer** → Generates terrain
6. **Output** → Returns heightmap, splatmap, state
7. **Frontend** → Displays terrain in 3D viewer

### State Management Flow

1. **Read State** → Atomic read from JSON file
2. **Apply Actions** → Modify state in memory
3. **Generate Terrain** → Build from updated state
4. **Update Scene Graph** → Add/modify entities
5. **Write State** → Atomic write to JSON file

### Quality Evaluation Flow

1. **Generate Actions** → Parse command to actions
2. **Evaluate Features** → Calculate feature metrics
3. **Render Preview** → Generate temporary terrain
4. **Evaluate Textures** → Calculate texture metrics
5. **Quality Rubric** → Combine metrics into scores
6. **Refinement** → Suggest improvements if needed

---

## Design Principles

- **Single Responsibility** - Each layer has a clear purpose
- **Separation of Concerns** - Semantic, engine, and output layers are independent
- **Extensibility** - Easy to add new features, primitives, or parsing strategies
- **Determinism** - Seed-based generation for reproducibility
- **Performance** - Single-pass generation, efficient algorithms

---

See also:
- [Parsing Strategies](PARSING_STRATEGIES.md) - Detailed parsing strategy documentation
- [Quality Evaluation](QUALITY_EVALUATION.md) - Quality system details
- [Scene Graph](SCENE_GRAPH.md) - Scene graph system documentation

