# Context for AI Agents: The Essential Guide

> *"Know the rules, respect the constraints, preserve the invariants."*

## The Golden Rules: What Never Changes

These are the immutable laws of the terrain system. Violate them at your peril.

### Critical Invariants

1. **State format is stable** — The feature structure is a contract. Don't break it.
2. **Always normalize** — Heightmaps must exist in the 0-1 range. Always.
3. **Use `base_flat` for reset** — Not `base_desert`. This is intentional.
4. **Variation is essential** — Add ±15% randomness to dimensions. Uniformity is the enemy.
5. **Smooth blending** — 40px+ feathering for edges. Hard edges break immersion.

### Current Defaults: The Established Parameters

These defaults have been tuned through iteration. Change them only with reason:

- **Mountains**: `height=0.75`, `radius=56`
- **Hills**: `height=0.45`, `radius=42`  
- **Valleys**: `depth=0.55`, `radius=64`
- **Dunes**: `amp=0.08`, `freq=18.0`, `feather=40px`

---

## Architecture: The Layered Structure

The system is organized in layers, each with a clear responsibility:

```
primitives/     → Feature generators (mountains, valleys, dunes, base, walkability zones)
engine/         → Core systems (stamping, blending, splatmap, spatial, walkability)
semantic/       → Natural language (narrative pipeline, parser, state_manager, spatial_resolver)
orchestration.py → Main orchestrator (parser coordination, scene graph, action execution)
```

### The Parser Flow: A Cascade of Intelligence

The system processes commands through a three-tier cascade, each tier bringing different capabilities:

1. **Narrative Pipeline** (`run_narrative_pipeline`) ← **PRIMARY**
   - Handles aesthetic and narrative commands
   - Understands intent through geological storytelling
   - Transforms *"create a dramatic desert"* into composition

2. **SemanticParser** (with ReAct agent) ← **FALLBACK**
   - Handles complex spatial reasoning
   - Uses LLM-powered context understanding
   - Resolves ambiguous references

3. **CommandParser** (regex) ← **FINAL FALLBACK**
   - Handles simple, direct commands
   - Always available, no external dependencies
   - Ensures the system never fails silently

---

## Design Philosophy: The Principles That Guide Us

### State-Based Rebuilds

Always rebuild from state. Never mutate. This ensures:
- Deterministic behavior
- Reproducibility
- Clean separation of concerns

### Deterministic Generation

Seed-based randomness ensures:
- Same seed + same state = same terrain
- Reproducible results
- No random drift

### Modular Architecture

Features are isolated primitives. This means:
- Easy to add new features
- Easy to test in isolation
- Easy to reason about behavior

### Backward Compatibility

Old state files must still work. This is a promise we keep.

---

## Aesthetic Principles: The Art of Terrain

These principles guide the creation of beautiful, natural-looking terrain:

1. **Variation** — Features should vary (±15% size, ±10% height). Uniformity kills beauty.
2. **Proportions** — Mountains are 2-3x taller than hills. Respect the hierarchy.
3. **Blending** — Smooth edges (40px+ feathering). Hard edges break immersion.
4. **Spacing** — Natural distribution (Poisson disk, not grid). Grids are unnatural.
5. **Depth** — Valleys must be noticeable (0.55+). Shallow valleys are invisible.

---

## Common Mistakes: What to Avoid

These are the traps that catch the unwary:

- ❌ **Fixed dimensions** → Use random variation
- ❌ **Hard edges** → Use smooth falloff
- ❌ **Grid placement** → Use scattered distribution
- ❌ **Ignore context** → Make features relate to each other
- ❌ **Too uniform** → Add randomness

---

## What to Improve: The Path Forward

These are areas where improvement is welcome:

- ✅ Add variation (±15% randomness)
- ✅ Better blending (feature-aware smoothing)
- ✅ Natural spacing (Poisson disk sampling)
- ✅ Feature relationships (context-aware placement)
- ✅ Edge erosion (weathering simulation)

---

## What NOT to Change: The Sacred Constants

These are the foundations. Don't touch them:

- ❌ State format structure
- ❌ Blending mode constants (`MAX`, `SUBTRACT`, etc.)
- ❌ Normalization (always 0-1)
- ❌ Splatmap channel mapping (`RGBA = grass, rock, sand, snow`)

---

## Further Reading

For detailed documentation, see:
- `AESTHETIC_GUIDELINES.md` — The complete aesthetic guide
- `CURRENT_ARCHITECTURE_STATUS.md` — The verified current state
- `SYSTEM_EXPLANATION.md` — The engineering deep dive
