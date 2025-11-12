# Undocumented Features Analysis

**Date:** November 11, 2025  
**Status:** 🔍 **GAP ANALYSIS COMPLETE**

This document identifies features and capabilities that exist in the codebase but are not yet documented in the main documentation.

---

## 🎯 **IMPORTANT: Production vs Experimental Features**

**Many features in this codebase are experimental and have NOT been fully integrated into the production pipeline.** This document distinguishes between:

- ✅ **Production Features** - Active in the main `/api/generate` pipeline
- 🧪 **Experimental Features** - Built but not integrated, or only used in alternative workflows
- ⚠️ **Partial Integration** - Partially connected but not fully utilized

### **The Active Production Pipeline**

The main production pipeline for terrain generation is:

```
API Request (/api/generate)
  ↓
TerrainController.generate()
  ↓
TerrainService.generate_terrain()
  ↓
terrain.apply_actions() [main orchestrator]
  ↓
orchestration.py [parsing & state management]
  ├─ parse_command_to_actions() [uses multiple parsers]
  ├─ execute_state_actions() [remove/modify]
  └─ execute_add_actions() [add features]
  ↓
TerrainBuilder [terrain generation]
  ├─ Base biome generation
  ├─ Feature stamping (via FeatureRegistry)
  ├─ Adaptive smoothing (optimized)
  ├─ Edge erosion
  └─ Splatmap generation (optimized)
  ↓
AssetService.save_terrain_outputs()
  ↓
Response with heightmap, splatmap, voxel (optional)
```

**Key Production Components:**
- ✅ `terrain.apply_actions()` - Main orchestrator
- ✅ `orchestration.py` - State management and parsing coordination
- ✅ `TerrainBuilder` - Terrain generation engine
- ✅ `FeatureRegistry` - Feature rendering (dict-based, NOT RendererRegistry)
- ✅ Multiple parsing strategies (narrative, semantic, regex fallback)
- ✅ Scene graph for reference resolution
- ✅ State persistence with atomic file locking

**Experimental/Alternative Workflows:**
- 🧪 `/api/design/multi-agent` - Multi-agent design workflow (separate endpoint)
- 🧪 ReAct agent (`react_agent_v2.py`) - Used in multi-agent workflow, not main pipeline
- 🧪 Rubric evolution - Optional quality improvement, not in main pipeline
- 🧪 RendererRegistry - Built but never integrated (orphaned)

---

## 🔴 Critical Missing Documentation

### 1. **Erosion System** (`server/engine/erosion.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **PRODUCTION** (partial)

**What it does:**
- Natural weathering simulation at feature edges
- Slope-based erosion (steeper areas erode more)
- Edge smoothing for natural appearance
- Configurable erosion strength and radius

**Key Functions:**
- `apply_edge_erosion()` - Erodes feature edges ✅ **PRODUCTION** - Used in `TerrainBuilder.finalize()`
- `apply_slope_erosion()` - Slope-based erosion ❌ **EXPERIMENTAL** - Exists but never called

**Pipeline Status:**
- ✅ **Production:** Edge erosion is active in main pipeline (`TerrainBuilder.finalize()`)
- ❌ **Experimental:** Slope erosion exists but is never called - **DISCONNECTED**

**Impact:** Important for natural-looking terrain, should be documented in Architecture and Examples. Slope erosion should be integrated or removed.

---

### 2. **Variation System** (`server/engine/variation.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **PRODUCTION**

**What it does:**
- Adds subtle procedural variation to features (±8-12%)
- Deterministic seed-based variation
- Prevents "cookie cutter" identical features
- Bounded variation within safe ranges

**Key Components:**
- `VariationEngine` - Main variation engine
- `VARIATION_CONFIG` - Configuration for each feature type
- Applies to height, radius, and other parameters

**Pipeline Status:**
- ✅ **Production:** Fully integrated in main pipeline
- ✅ Used extensively in `terrain.py` and `feature_registry.py`
- ✅ Applied to all feature types (mountains, valleys, dunes, cliffs, etc.)
- ✅ Active in production code - critical for natural appearance

**Impact:** Critical for natural appearance, mentioned in features but not explained.

---

### 3. **Multiple Biomes** (`server/primitives/base.py`)

**Status:** ⚠️ **PARTIALLY DOCUMENTED** | ✅ **FULLY CONNECTED**

**What exists:**
- `base_flat()` - Flat terrain
- `base_desert()` - Desert biome (soft rolling hills with dunes)
- `base_forest()` - Forest biome (rolling hills and valleys)
- `base_arctic()` - Arctic biome (hilly tundra and snow peaks)

**Connection Status:**
- ✅ Fully integrated via `terrain_service.get_biome_function()`
- ✅ All 4 biomes available and functional
- ✅ Used in `terrain_service.py` and `template_service.py`
- ⚠️ Only "desert" is documented as default, but all biomes work

**Current Documentation:** Only mentions "desert" as default, doesn't explain biome system.

**Impact:** Users don't know they can use different biomes.

---

### 4. **Voxel Generation Details** (`server/engine/voxel.py`)

**Status:** ⚠️ **MENTIONED BUT NOT DETAILED** | ✅ **CONNECTED**

**What exists:**
- `heightmap_to_voxels()` - Converts heightmap to 3D voxel grid
- `voxels_to_mesh()` - Converts voxel grid to .obj/.bin mesh
- Configurable resolution (128³ to 2048³)
- Height scaling and voxel size parameters

**Connection Status:**
- ✅ Integrated in `asset_service.py` (line 70)
- ✅ Called when `voxel=True` in API requests
- ✅ Exports `.obj` and `.bin` mesh formats
- ✅ Fully functional in production

**Current Documentation:** Mentions voxel generation exists but doesn't explain how it works, parameters, or use cases.

**Impact:** Users don't know how to use voxel generation effectively.

---

### 5. **Walkability System Details** (`server/engine/walkability.py`)

**Status:** ⚠️ **MENTIONED BUT NOT DETAILED** | ✅ **FULLY CONNECTED**

**What exists:**
- `WalkabilityConfig` - Comprehensive configuration system
- Slope-based walkability (max walkable slope, impassable slope)
- Terrain type costs (grass, sand, rock, snow)
- Feature-specific penalties (cliffs, dunes)
- Height restrictions
- Cost-based pathfinding support

**Connection Status:**
- ✅ Fully integrated in `builder.py` (`calculate_walkability()` method)
- ✅ Used in `walkability_constraints.py` for feature placement
- ✅ Walkability zones (flat zones, paths, clearings) are functional
- ✅ Multiple config presets available (DEFAULT, VEHICLE, AGILE)

**Current Documentation:** Mentions walkability zones exist but doesn't explain the analysis system, costs, or configuration.

**Impact:** Users don't understand how walkability works or how to configure it.

---

## 🟡 Important Missing Documentation

### 6. **Optimized Versions** (`stamping_optimized.py`, `splatmap_optimized.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **FULLY CONNECTED**

**What exists:**
- Optimized versions of stamping and splatmap generation
- Performance improvements for large terrains
- Used automatically when available

**Connection Status:**
- ✅ Fully integrated - Used in `builder.py` (lines 5-6)
- ✅ `apply_adaptive_smoothing_fast()` replaces old smoothing
- ✅ `generate_splatmap_fast()` replaces old splatmap generation
- ✅ Active in production, old versions not used

**Impact:** Performance characteristics not documented.

---

### 7. **Asset Cleanup System** (`server/engine/cleanup.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **CONNECTED** (probabilistic)

**What exists:**
- Automatic cleanup of old terrain assets
- Retention policy: Keep last 50 assets + assets newer than 24 hours
- Prevents disk space issues
- Configurable retention settings

**Connection Status:**
- ✅ Integrated in `asset_service.py` and `terrain_service.py`
- ⚠️ Called probabilistically (10% chance per generation) - not guaranteed
- ✅ Functional but runs randomly, not on every generation

**Impact:** Users don't know about automatic cleanup or how to configure it.

---

### 8. **Feature Renderer System** (`server/engine/renderers.py`)

**Status:** ❌ **NOT DOCUMENTED** | 🧪 **EXPERIMENTAL** (orphaned code)

**What exists:**
- `FeatureRenderer` - Abstract base class for renderers
- Type-specific renderers (MountainRenderer, etc.)
- `RendererRegistry` - Central registry for renderers
- Clean separation of data (Feature) from behavior (rendering)

**Pipeline Status:**
- 🧪 **Experimental/Orphaned:** NOT used in production pipeline
- ❌ Only exists in tests (`test_renderers.py`)
- ❌ **Production uses:** `FeatureRegistry` (dict-based) in `terrain.py`
- ❌ `feature_registry.py` doesn't use `RendererRegistry`
- 📝 **Historical note:** Built as refactoring attempt but rejected in favor of keeping `FeatureRegistry`
- ⚠️ **This is experimental code that was never integrated**

**Impact:** Important architectural component not documented. **Should be removed or integrated.**

**Recommendation:** Either integrate `RendererRegistry` into production code OR remove it to reduce confusion. Currently, production uses `FeatureRegistry` (dict-based approach).

---

### 9. **State Lock System** (`server/engine/state_lock.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **FULLY CONNECTED**

**What exists:**
- Cross-platform file locking (Windows + Unix)
- Atomic read/write operations
- Prevents race conditions in concurrent requests
- Thread-safe state management

**Connection Status:**
- ✅ Fully integrated in `state_service.py` (lines 5, 26, 35, 44)
- ✅ All state reads use `atomic_read_state()`
- ✅ All state writes use `atomic_write_state()`
- ✅ Critical for production - prevents file corruption

**Impact:** Critical for production reliability, should be documented.

---

### 10. **Texture Service** (`server/services/texture_service.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **CONNECTED** (initialization only)

**What exists:**
- Texture file management
- Placeholder texture generation
- Automatic texture creation (grass, rock, sand, snow)
- Texture directory management

**Connection Status:**
- ✅ Initialized in `main.py` (line 50)
- ✅ Creates placeholder textures on startup
- ⚠️ Not actively used in terrain generation (splatmaps are generated, not loaded)
- ✅ Serves as fallback/placeholder system

**Impact:** Users don't know about texture management system.

---

### 11. **Bootstrap System** (`server/bootstrap.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **FULLY CONNECTED**

**What exists:**
- Import normalization across runtimes
- sys.path setup
- Module aliases (engine, domain, terrain)
- Ensures consistent import environment

**Connection Status:**
- ✅ Called automatically on import (line 58)
- ✅ Used in `main.py` (line 11) before any other imports
- ✅ Ensures consistent imports across tests, scripts, and server
- ✅ Critical for avoiding import errors

**Impact:** Important for understanding import system, troubleshooting.

---

### 12. **Prompt Profiles** (`server/semantic/prompt_profiles.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **FULLY CONNECTED**

**What exists:**
- Configurable prompt budgets for ReAct agent
- Profiles: compact, standard, extended32k, omni
- Controls token limits, iterations, history
- Allows tuning for different LLM contexts

**Connection Status:**
- ✅ Fully integrated in `react_agent_v2.py` (lines 14, 55-56)
- ✅ Used to configure ReAct agent behavior
- ✅ Defaults to "compact" profile
- ✅ All 4 profiles functional

**Impact:** Users don't know they can configure ReAct agent behavior.

---

### 13. **Rubric Evolution System** (`server/semantic/rubric_evolution.py`)

**Status:** ❌ **NOT DOCUMENTED** | 🧪 **EXPERIMENTAL**

**What exists:**
- LLM-as-a-Judge meta-learning system
- Analyzes terrains and evolves quality rubrics
- Uses Gemini Vision for visual analysis
- Learns what makes terrain aesthetically pleasing

**Pipeline Status:**
- 🧪 **Experimental:** NOT in main production pipeline
- ⚠️ Conditionally imported in `quality_tools.py` (lines 63-67)
- ⚠️ Only used if `google-genai` package is available
- ✅ Used in test tools (`test_rubric_evolution.py`, etc.)
- ⚠️ Not guaranteed to be available - optional dependency
- ⚠️ May fail silently if Gemini API key missing
- ⚠️ Used in multi-agent workflow tools, not main `/api/generate` endpoint

**Impact:** Advanced experimental feature for improving quality over time, completely undocumented. **Requires optional dependency. Not part of production pipeline.**

---

### 14. **Context System** (`server/semantic/context.py`)

**Status:** ❌ **NOT DOCUMENTED** | ✅ **FULLY CONNECTED**

**What exists:**
- `summarize_scene()` - Concise scene summaries
- `summarize_recent_actions()` - Action history summaries
- `infer_active_aesthetic_goals()` - Goal inference
- Used for ReAct prompt engineering

**Connection Status:**
- ✅ Fully integrated in `react_agent_v2.py` (lines 9-11, 107, 111)
- ✅ Used to build context for ReAct agent prompts
- ✅ Active in production - critical for agent understanding
- ✅ Tested in `test_context_helpers.py`

**Impact:** Important for understanding how ReAct agent builds context.

---

### 15. **Domain Models** (`server/domain/models.py`)

**Status:** ❌ **NOT DOCUMENTED** | 🧪 **EXPERIMENTAL** (partial migration)

**What exists:**
- `Feature` - Typed feature model (replaces dicts)
- `Position` - Position specification with multiple modes
- `FeatureParameters` - Typed parameters
- `RegionType` - Enum for named regions

**Pipeline Status:**
- 🧪 **Experimental:** Partial migration, not fully integrated
- ⚠️ Models exist and are used in some places
- ⚠️ **Production pipeline still uses dict-based features** (`terrain.py`, `feature_registry.py`)
- ✅ Used in `renderers.py` (but renderers are experimental/orphaned)
- ⚠️ Mixed usage - both dicts and typed models coexist
- ⚠️ **Migration incomplete** - production still uses dicts

**Impact:** Important architectural improvement, should be documented. **Migration incomplete - production still uses dict-based features.**

---

### 16. **Configuration System** (`server/engine/config.py`)

**Status:** ❌ **NOT DOCUMENTED** | 🧪 **EXPERIMENTAL** (not utilized)

**What exists:**
- Centralized configuration system
- `TerrainConfig` - Main configuration
- Feature-specific configs (MountainConfig, HillConfig, etc.)
- Default parameters and variation settings
- Global config instance

**Pipeline Status:**
- 🧪 **Experimental:** System exists but NOT used in production
- ⚠️ Imported in `builder.py` (line 8) but `get_config()` not actively used
- ⚠️ Config classes exist but defaults are hardcoded elsewhere
- ⚠️ **Production uses hardcoded defaults** in `feature_registry.py`
- ⚠️ System exists but not actively used in production pipeline

**Impact:** Users don't know they can customize default parameters. **System exists but not utilized - production uses hardcoded values.**

---

### 17. **Controller-Service Architecture**

**Status:** ⚠️ **IMPLIED BUT NOT EXPLICITLY DOCUMENTED**

**What exists:**
- Clear separation: Controllers → Services → Domain
- Controllers handle HTTP requests
- Services contain business logic
- Domain models represent data

**Impact:** Important architectural pattern should be documented.

---

### 18. **MCP (Model Context Protocol) Implementation**

**Status:** ⚠️ **MENTIONED BUT NOT DETAILED**

**What exists:**
- Full MCP server implementation
- Tools, resources, prompts
- Integration with LLM agents
- Standard MCP protocol support

**Current Documentation:** Lists endpoints but doesn't explain MCP protocol or integration.

**Impact:** Users don't understand MCP integration or how to use it.

---

## 🟢 Nice to Have Documentation

### 19. **Noise Systems** (`server/utils/noise.py`, `noise_optimized.py`)

**Status:** ❌ **NOT DOCUMENTED**

**What exists:**
- Perlin noise generation
- Optimized noise functions
- Used for base biomes and features

**Impact:** Low priority, but useful for developers.

---

### 20. **Modification System** (`server/engine/modification.py`)

**Status:** ❌ **NOT DOCUMENTED**

**What exists:**
- Feature modification logic
- Parameter adjustment system
- Modification validation

**Impact:** Important for understanding how modifications work.

---

## 🔌 Pipeline Status Summary

### ✅ Production Features (Active in Main Pipeline)
These features are **actively used in the main `/api/generate` production pipeline:**

1. **Variation System** - Extensively used in production (`terrain.py`, `feature_registry.py`)
2. **Multiple Biomes** - All 4 biomes functional (`TerrainService.get_biome_function()`)
3. **Voxel Generation** - Integrated in asset service (optional output)
4. **Walkability System** - Fully integrated with constraints (`TerrainBuilder.calculate_walkability()`)
5. **Optimized Versions** - Active in builder (`TerrainBuilder.finalize()`)
6. **State Lock** - Critical for production reliability (`StateService`)
7. **Bootstrap** - Ensures consistent imports (called in `main.py`)
8. **Context System** - Used in parsing/ReAct agent (part of parsing pipeline)
9. **Edge Erosion** - Active in `TerrainBuilder.finalize()`

### ⚠️ Partially Integrated (Production but Incomplete)
1. **Erosion System** - Edge erosion ✅ production, slope erosion ❌ experimental
2. **Asset Cleanup** - Runs probabilistically (10% chance) - production but non-deterministic
3. **Texture Service** - Initialized but not actively used (placeholder system)
4. **Prompt Profiles** - Used in ReAct agent (experimental workflow), not main pipeline

### 🧪 Experimental Features (NOT in Main Pipeline)
These features exist but are **NOT part of the main production pipeline:**

1. **Feature Renderer System** (`RendererRegistry`) - Orphaned code, only in tests
   - **Production uses:** `FeatureRegistry` (dict-based)
   - **Recommendation:** Remove or integrate

2. **Rubric Evolution** - Only used in multi-agent workflow tools, not main pipeline
   - Requires optional `google-genai` dependency
   - Used in `/api/design/multi-agent` endpoint (experimental)

3. **Domain Models** - Partial migration, production still uses dicts
   - **Production uses:** Dict-based features
   - **Experimental:** Typed `Feature` models exist but not integrated

4. **Configuration System** - Exists but production uses hardcoded defaults
   - **Production uses:** Hardcoded values in `feature_registry.py`
   - **Experimental:** `TerrainConfig` exists but not used

5. **Slope Erosion** - Function exists but never called
   - **Recommendation:** Integrate or remove

---

## 📋 Documentation Gaps Summary

### By Category

**Engine Features:**
- ❌ Erosion system
- ❌ Variation system
- ❌ Voxel generation details
- ❌ Walkability analysis details
- ❌ Optimized versions
- ❌ Cleanup system
- ❌ Renderer system
- ❌ State locking

**Biomes & Configuration:**
- ⚠️ Multiple biomes (flat, desert, forest, arctic)
- ❌ Configuration system
- ❌ Default parameters

**Services:**
- ❌ Texture service
- ⚠️ MCP service details
- ❌ Bootstrap system

**Semantic Layer:**
- ❌ Prompt profiles
- ❌ Rubric evolution
- ❌ Context system

**Architecture:**
- ⚠️ Controller-Service pattern
- ❌ Domain models
- ❌ State management details

---

## 🎯 Recommended Documentation Additions

### High Priority (Add Immediately)

1. **docs/EROSION_SYSTEM.md** - Natural weathering and edge smoothing
2. **docs/VARIATION_SYSTEM.md** - Procedural variation for natural appearance
3. **docs/BIOMES.md** - Multiple biome system (flat, desert, forest, arctic)
4. **docs/VOXEL_GENERATION.md** - Detailed voxel generation guide
5. **docs/WALKABILITY_SYSTEM.md** - Complete walkability analysis documentation
6. **Update ARCHITECTURE.md** - Add erosion, variation, cleanup, state lock

### Medium Priority (Add Soon)

7. **docs/CONFIGURATION.md** - Configuration system and customization
8. **docs/MCP_INTEGRATION.md** - MCP protocol integration details
9. **docs/PROMPT_PROFILES.md** - ReAct agent prompt configuration
10. **Update DEVELOPMENT.md** - Add domain models, renderer system

### Low Priority (Nice to Have)

11. **docs/RUBRIC_EVOLUTION.md** - LLM-as-a-Judge meta-learning
12. **docs/CONTEXT_SYSTEM.md** - Context helpers for ReAct
13. **docs/PERFORMANCE.md** - Optimized versions and performance tips

---

## 📊 Impact Assessment

### User-Facing Features Missing:
- **Biomes** - Users don't know they can use forest/arctic biomes
- **Voxel Generation** - Users don't know how to use it effectively
- **Walkability** - Users don't understand the analysis system
- **Configuration** - Users can't customize defaults

### Developer-Facing Features Missing:
- **Erosion System** - Important for natural appearance
- **Variation System** - Critical for avoiding identical features
- **State Lock** - Important for production reliability
- **Domain Models** - Architectural improvement not documented

### Advanced Features Missing:
- **Rubric Evolution** - Meta-learning system
- **Prompt Profiles** - ReAct configuration
- **MCP Integration** - Protocol details

---

## ✅ Action Items

### Documentation Priority
1. **Document the production pipeline** - Clearly explain the main `/api/generate` flow
2. **Mark experimental features** - Clearly distinguish production vs experimental
3. Create documentation for high-priority production features (variation, biomes, voxel, walkability)
4. Add examples showing biome usage, voxel generation, walkability
5. Explain controller-service architecture pattern

### Code Cleanup Priority (Experimental Features)
1. **Remove or integrate `RendererRegistry`** - Currently orphaned, only in tests
   - **Decision needed:** Keep `FeatureRegistry` (production) or migrate to `RendererRegistry`?
2. **Integrate or remove `apply_slope_erosion()`** - Exists but never called
3. **Complete domain model migration** - Finish transition from dicts to typed models OR document that dicts are production
4. **Utilize configuration system** - Actually use `TerrainConfig` instead of hardcoded defaults OR remove it
5. **Make asset cleanup deterministic** - Currently probabilistic, consider scheduled cleanup

### Integration Priority (Experimental → Production)
1. **Connect slope erosion** - Either use it or remove it
2. **Complete domain model migration** - Remove dict-based features OR document that dicts are production
3. **Activate configuration system** - Use centralized config instead of hardcoded values OR remove it
4. **Make cleanup more reliable** - Consider scheduled cleanup instead of probabilistic

---

## 📊 Summary

**Key Finding:** Many features are **experimental** and have NOT been fully integrated into the production pipeline. The main production pipeline uses:

- ✅ `FeatureRegistry` (dict-based) - NOT `RendererRegistry`
- ✅ Dict-based features - NOT typed `Feature` models
- ✅ Hardcoded defaults - NOT `TerrainConfig`
- ✅ Edge erosion only - NOT slope erosion
- ✅ Multiple parsing strategies (narrative, semantic, regex) - Production
- ✅ Scene graph for reference resolution - Production
- ✅ Optimized smoothing and splatmap - Production

**Experimental workflows** (separate from main pipeline):
- 🧪 Multi-agent design (`/api/design/multi-agent`)
- 🧪 ReAct agent (used in multi-agent workflow)
- 🧪 Rubric evolution (optional quality improvement)

**Recommendation:** Document which features are production vs experimental, and either integrate experimental features or remove them to reduce confusion.

