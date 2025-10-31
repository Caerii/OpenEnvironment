# Quick Reference: Context for AI Agents

## TL;DR: Don't Break Things

### Critical Rules
1. **State format is stable** - Don't change feature structure
2. **Always normalize** - Heightmaps must be 0-1 range
3. **Use base_flat for reset** - Not base_desert
4. **Variation is key** - Add ±15% randomness to dimensions
5. **Smooth blending** - 40px+ feathering for edges

### Current Defaults (Don't Change Without Reason)
- Mountains: height=0.75, radius=56
- Hills: height=0.45, radius=42  
- Valleys: depth=0.55, radius=64
- Dunes: amp=0.08, freq=18.0, feather=40px

### Architecture Overview
```
primitives/     → Feature generators (mountains, valleys, dunes, base)
engine/         → Core systems (stamping, blending, splatmap, spatial)
semantic/       → Natural language (parser, state_manager, spatial_resolver)
terrain.py      → Main orchestrator
```

### Key Design Decisions
- **State-based rebuilds**: Always rebuild from state, never mutate
- **Deterministic**: Seed-based for reproducibility
- **Modular**: Features are isolated primitives
- **Backward compatible**: Old state files must still work

### Aesthetic Principles
1. **Variation** - Features should vary (±15% size, ±10% height)
2. **Proportions** - Mountains 2-3x taller than hills
3. **Blending** - Smooth edges (40px+ feathering)
4. **Spacing** - Natural distribution (Poisson disk, not grid)
5. **Depth** - Valleys must be noticeable (0.55+)

### Common Mistakes
❌ Fixed dimensions → Use random variation
❌ Hard edges → Use smooth falloff
❌ Grid placement → Use scattered distribution
❌ Ignore context → Make features relate to each other
❌ Too uniform → Add randomness

### What to Improve
✅ Add variation (±15% randomness)
✅ Better blending (feature-aware smoothing)
✅ Natural spacing (Poisson disk sampling)
✅ Feature relationships (context-aware placement)
✅ Edge erosion (weathering simulation)

### What NOT to Change
❌ State format structure
❌ Blending mode constants (MAX, SUBTRACT, etc.)
❌ Normalization (always 0-1)
❌ Splatmap channel mapping (RGBA = grass, rock, sand, snow)

See `AESTHETIC_GUIDELINES.md` for detailed documentation.

