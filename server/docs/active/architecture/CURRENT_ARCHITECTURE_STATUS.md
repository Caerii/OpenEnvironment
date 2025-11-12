# Current Architecture Status

**Last Updated:** November 11, 2025

This document describes the **actual** current state of the architecture, verified against the codebase. It is the source of truth for what exists, what works, and what remains to be done.

---

## Parser System: The Three-Tier Cascade

The system processes natural language through a carefully orchestrated cascade, each tier bringing different capabilities and ensuring graceful degradation.

### Implementation Order

1. **Narrative Pipeline** (`run_narrative_pipeline`) — **PRIMARY**
   - Called first in `orchestration.py:71`
   - Handles aesthetic and narrative commands
   - Transforms intent into composition through geological storytelling
   - Returns actions with rich metadata

2. **SemanticParser** — **FALLBACK**
   - Used if narrative pipeline fails or is unavailable
   - Includes ReAct agent support for complex reasoning
   - Uses scene graph context for reference resolution
   - Handles spatial relationships and ambiguous references

3. **CommandParser** (regex) — **FINAL FALLBACK**
   - Used if SemanticParser is unavailable (no API key, network failure)
   - Simple pattern matching for direct commands
   - Always works—no external dependencies
   - Ensures the system never fails silently

**Code Location:** `server/orchestration.py:41-118`

---

## Walkability Zones: Infrastructure Complete, Enforcement Pending

The walkability zone system provides a foundation for gameplay-aware terrain generation. The infrastructure is complete; enforcement integration is the remaining work.

### ✅ Implemented Infrastructure

- **Constraint System:** `WalkabilityConstraint` class (`server/engine/walkability_constraints.py`)
- **Builder Integration:** Fully integrated into `TerrainBuilder` (`server/engine/builder.py:45-250`)
- **Primitives:** `flat_zone`, `path`, `clearing` exist (`server/primitives/walkability_zones.py`)
- **Feature Registry:** Registered and working (`server/engine/feature_registry.py:1374+`)

### ✅ What Works

- Zones can be created via natural language or JSON actions
- Builder automatically tracks zones when applied (`builder.py:75-77`)
- Constraint checking APIs exist:
  - `can_place_feature()` — Check if placement is valid
  - `find_placement_away_from_zones()` — Find valid placement
- Walkability calculation available (`builder.calculate_walkability()`)

### ⚠️ What's Partially Implemented

- **Constraint checking during placement:** EXISTS in `commands.py:85-97` — checks constraints if available
- **Automatic position adjustment:** EXISTS — calls `find_placement_away_from_zones()` if placement invalid

### ❌ What's Missing

- **Two-phase execution:** No automatic "zones first, then features" ordering
- **Guaranteed enforcement:** Constraint checking only happens if builder and constraints are available

**Status:** Infrastructure complete, constraint checking implemented but needs verification of all code paths.

---

## Performance Optimizations: Production Ready

The performance optimization system is fully integrated and in production use.

### ✅ Implemented

- **Optimized Smoothing:** `stamping_optimized.py` with separable Gaussian filters
- **Optimized Splatmap:** `splatmap_optimized.py` with caching
- **Slope/Gradient Caching:** Reused between smoothing and splatmap
- **Edge Erosion:** Applied in builder finalization
- **Bounding Box Optimization:** For small features

**Code Location:** `server/engine/builder.py:108-149`

**Status:** Fully integrated and in production use.

---

## LLM Model Configuration: The Intelligence Layer

The system uses multiple LLM providers, each optimized for specific tasks.

### Current Defaults

- **Together.ai:** `llama-3.3-70b` (65k context) — Default for ReAct agent
- **Gemini:** `gemini-2.5-flash-image` (65k context) — Default for visual critique
- **Cerebras:** `llama3.1-8b` (8k context) — Legacy, not recommended

**Code Location:** `server/semantic/llm/factory.py:21-23`

---

## Quality Evaluation: Implemented with Caveats

The quality evaluation system provides progressive scoring and rubric evolution, but may have import issues that need verification.

### ✅ Implemented

- **Progressive Scoring:** `evaluation_v2.py` with granular rubrics
- **Rubric Evolution:** `rubric_evolution.py` — LLM-as-a-Judge meta-learning
- **Quality Tools:** `quality_tools.py` — ReAct agent tools

**Status:** Implemented, may have import issues (needs verification).

---

## Scene Graph: Fully Functional

The scene graph system provides semantic understanding and reference resolution.

### ✅ Implemented

- **TerrainSceneGraph:** Full implementation (`server/semantic/scene/`)
- **Integration:** Used in orchestration (`server/orchestration.py:15-38`)
- **Serialization:** State persisted in terrain state

**Status:** Fully functional.

---

## Summary: The State of the System

### What's Complete ✅

- Parser system (three-tier fallback)
- Walkability zone infrastructure
- Performance optimizations
- Scene graph
- LLM model configuration

### What's Partial ⚠️

- Walkability constraint enforcement (infrastructure ready, not fully wired)
- Quality evaluation (implemented, may have import issues)

### What Needs Work ❌

- Two-phase walkability execution
- Constraint-aware position resolution
- File locking verification
- Deterministic randomness verification

---

## How to Use This Document

This document is the **source of truth** for the current architecture state. When in doubt about what exists or what works, consult this document first. It is verified against the actual codebase, not against plans or aspirations.

For implementation details, see:
- `SYSTEM_EXPLANATION.md` — The engineering deep dive
- `SEMANTIC_SCENE_REPRESENTATION.md` — The semantic layer architecture
- `CONTEXT_FOR_AI.md` — Quick reference for AI agents
