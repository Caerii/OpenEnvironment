# Architecture Reorganization Plan

## Goal
Reorganize codebase into modular, extensible structure matching requirements specification.

## Target Structure

```
server/
├── primitives/          # Terrain feature generators
│   ├── __init__.py
│   ├── mountains.py    # Mountain/hill generation
│   ├── valleys.py       # Valley generation
│   ├── dunes.py         # Dune generation
│   └── base.py          # Base biome generation
│
├── engine/              # Core generation systems
│   ├── __init__.py
│   ├── stamping.py      # Primitive placement & blending
│   ├── blending.py      # Feature blending algorithms
│   ├── splatmap.py      # Texture splatmap generation
│   └── spatial.py       # Spatial utilities (regions, coords)
│
├── semantic/            # Natural language processing
│   ├── __init__.py
│   ├── parser.py        # LLM/regex command parsing
│   ├── state_manager.py # Feature tracking & state
│   └── spatial_resolver.py # Position interpretation
│
├── terrain.py           # Main orchestrator (thin)
├── utils.py             # Shared math utilities
└── main.py              # FastAPI app
```

## Migration Strategy

### Phase 1: Extract Primitives
- Move `base_desert()` → `primitives/base.py`
- Move `add_valley()` → `primitives/valleys.py`
- Move `add_dunes()` → `primitives/dunes.py`
- Create `primitives/mountains.py` with mountain/hill functions

### Phase 2: Extract Engine
- Move `stamp_gaussian()` → `engine/stamping.py`
- Create `engine/blending.py` with blending modes
- Move `make_splatmap()` → `engine/splatmap.py`
- Move `region_box()` + `random_point_in()` → `engine/spatial.py`

### Phase 3: Extract Semantic
- `parser.py` already exists ✓
- Create `semantic/state_manager.py` for feature tracking
- Create `semantic/spatial_resolver.py` for position resolution

### Phase 4: Refactor Orchestrator
- `terrain.py` becomes thin orchestrator
- Imports from primitives/engine/semantic
- Coordinates the workflow

## Benefits

1. **Modularity**: Each feature type is isolated
2. **Extensibility**: Add new features by creating new primitive files
3. **Testability**: Each module can be tested independently
4. **MCP-Ready**: Clear boundaries for tool conversion
5. **Maintainability**: Related code grouped together

## Implementation Order

1. Create folder structure
2. Extract primitives (mountains, valleys, dunes, base)
3. Extract engine (stamping, blending, splatmap, spatial)
4. Extract semantic helpers (state_manager, spatial_resolver)
5. Refactor terrain.py to use new modules
6. Update imports throughout
7. Test that everything still works

