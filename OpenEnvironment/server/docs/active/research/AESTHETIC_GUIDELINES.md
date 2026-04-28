# System Critique & Context Documentation

## System Critique

### ✅ Strengths

1. **Modular Architecture**
   - Clean separation: primitives → engine → semantic layers
   - Easy to extend with new features
   - Well-organized codebase

2. **State Management**
   - Deterministic rebuilds (seed-based)
   - Feature tracking with IDs
   - Persistent state across sessions

3. **Blending System**
   - Multiple blending modes (MAX, SUBTRACT, ADD, WEIGHTED)
   - Smooth edge falloff for dunes (recently fixed)
   - Post-processing smoothing

4. **Semantic Parsing**
   - LLM-based understanding with regex fallback
   - Structured JSON output
   - Multi-action support

### ⚠️ Current Limitations

1. **Feature Variety**
   - Only 4 feature types implemented (need 7+)
   - Missing: canyons, plateaus, cliffs, mesas, slopes, glaciers, spurs
   - Scaffolded but not functional

2. **Aesthetic Issues**
   - **Overly uniform**: Features use fixed radii/heights → repetitive
   - **Lack of variation**: No randomness in feature placement within regions
   - **No erosion**: Features look "stamped" rather than naturally eroded
   - **Splatmap simplicity**: Basic threshold-based texture assignment
   - **No feature relationships**: Features don't interact or influence each other

3. **Spatial Intelligence**
   - Limited positioning (only 9 regions + coords)
   - No relative positioning ("next to mountain", "between hills")
   - No scattered distribution
   - No edge-aware placement

4. **Blending Quality**
   - Features can overlap awkwardly (mountains merge but don't feel natural)
   - No conflict resolution for overlapping features
   - Smoothing is uniform (doesn't respect feature boundaries)

### 🎯 Critical Gaps for Aesthetic Quality

1. **Variation & Randomness**
   - Features are too uniform (same radius/height)
   - Need: ±10-20% random variation in dimensions
   - Need: Multiple variations of same feature type

2. **Natural Erosion**
   - Features look "plopped" down
   - Need: Gentle erosion at feature edges
   - Need: Slope-based erosion simulation

3. **Feature Relationships**
   - Features don't "know" about each other
   - Need: Valley flows between mountains
   - Need: Features adapt to nearby terrain

4. **Texture Sophistication**
   - Splatmap is too simple (threshold-based)
   - Need: Distance-based texture blending
   - Need: Feature-aware texture assignment (rock near cliffs, etc.)

---

## Design Decisions & Rationale

### Why We Made These Choices

1. **Modular Architecture**
   - **Decision**: Separate primitives/engine/semantic
   - **Rationale**: Makes it easy to add new features without touching core logic
   - **Trade-off**: More files, but better organization

2. **State-Based Rebuilds**
   - **Decision**: Always rebuild from state, never mutate
   - **Rationale**: Ensures determinism and consistency
   - **Trade-off**: Slightly slower, but more reliable

3. **Gaussian-Based Stamping**
   - **Decision**: Use Gaussian falloff for mountains/hills
   - **Rationale**: Natural-looking, smooth transitions
   - **Trade-off**: Can look too uniform without variation

4. **Perlin Noise for Dunes**
   - **Decision**: Use directional Perlin noise
   - **Rationale**: Natural-looking wave patterns
   - **Trade-off**: Can look repetitive over large areas

5. **Simple Splatmap**
   - **Decision**: Threshold-based texture assignment
   - **Rationale**: Fast and predictable
   - **Trade-off**: Less realistic than distance-based blending

---

## Aesthetic Principles

### What Makes Terrain Look Good

1. **Variation & Naturalness**
   - ✅ Features should vary in size (±15-20%)
   - ✅ Heights should vary slightly
   - ✅ Multiple feature types should coexist
   - ❌ Avoid: Identical features placed symmetrically

2. **Proportional Relationships**
   - ✅ Mountains should be 2-3x taller than hills
   - ✅ Valleys should be proportionally deep (not too shallow)
   - ✅ Feature sizes should relate to terrain scale (512x512)
   - ❌ Avoid: Features that are too small or too large for the terrain

3. **Natural Blending**
   - ✅ Features should blend smoothly into terrain
   - ✅ Edge falloff should be gradual (40px+ feathering)
   - ✅ Overlapping features should merge naturally
   - ❌ Avoid: Hard edges, visible seams, abrupt transitions

4. **Spatial Distribution**
   - ✅ Features should cluster naturally (not grid-like)
   - ✅ Empty spaces are important (breathing room)
   - ✅ Groups of features should have varied spacing
   - ❌ Avoid: Regular grids, uniform spacing, crowding

5. **Elevation Contrast**
   - ✅ Mix of high and low areas
   - ✅ Valleys should be noticeably deep (not subtle)
   - ✅ Mountains should dominate the landscape
   - ❌ Avoid: Flat terrain with tiny bumps

6. **Texture Coherence**
   - ✅ Textures should match elevation/slope
   - ✅ Smooth transitions between textures
   - ✅ Feature-aware textures (rock near cliffs, etc.)
   - ❌ Avoid: Random texture placement, harsh boundaries

### Common Mistakes to Avoid

1. **"Stamped Cookie Cutter" Terrain**
   - **Problem**: Features look identical, placed uniformly
   - **Fix**: Add random variation (±15% size, ±10% height)

2. **"Flat Desert Syndrome"**
   - **Problem**: Too flat, no elevation variation
   - **Fix**: Ensure valleys are deep (0.55+), mountains are tall (0.75+)

3. **"Hard Edge Hell"**
   - **Problem**: Features have visible boundaries
   - **Fix**: Use smooth falloff (feathering), better blending modes

4. **"Grid Placement"**
   - **Problem**: Features placed in regular patterns
   - **Fix**: Use scattered distribution, Poisson disk sampling

5. **"Feature Soup"**
   - **Problem**: Too many features, no empty space
   - **Fix**: Limit features per region, add spacing constraints

---

## Parameter Guidelines

### Default Parameters (Current)

```python
# Mountains
height: 0.75      # Peak height (0-1 normalized)
radius: 56        # Base radius (pixels, 512x512 terrain)
steepness: 1.0    # Side steepness multiplier

# Hills
height: 0.45      # Peak height
radius: 42        # Base radius
steepness: 0.7    # Gentler than mountains

# Valleys
depth: 0.55       # Maximum depth (was 0.35, increased for drama)
radius: 64        # Valley radius

# Dunes
amp: 0.08         # Amplitude of height variation
freq: 18.0        # Frequency (lower = larger dunes)
angle: 20.0       # Wind direction (degrees)
feather: 40px     # Edge feathering distance
```

### Recommended Variations

When creating features, add natural variation:

```python
# Good: Add randomness
radius = base_radius * random.uniform(0.85, 1.15)  # ±15% variation
height = base_height * random.uniform(0.90, 1.10)  # ±10% variation

# Bad: Always use exact values
radius = 56  # Too uniform!
height = 0.75
```

### Proportions That Work

- **Mountain**: 2-3x taller than hills
- **Valley depth**: Should be 40-60% of surrounding mountain height
- **Feature spacing**: Minimum 20-30px between features
- **Terrain scale**: 512x512 pixels, so features should be 40-128px radius

---

## Feature Interaction Rules

### How Features Should Relate

1. **Mountains & Hills**
   - Should cluster naturally (not grid-like)
   - Mountains form backdrops, hills form foreground
   - Use MAX blending to merge upward

2. **Valleys**
   - Should flow between mountains (not random placement)
   - Depth should relate to surrounding height
   - Use SUBTRACT blending to carve downward

3. **Dunes**
   - Should blend smoothly with surrounding terrain
   - Should respect elevation (don't put dunes on mountains)
   - Use ADD blending with smooth falloff

### Spatial Relationships

- **"Between mountains"**: Place valley in the midpoint between two mountains
- **"Next to mountain"**: Place feature 1.5x mountain radius away
- **"Scattered"**: Use Poisson disk sampling for natural distribution
- **"Along edge"**: Place features near terrain boundaries with spacing

---

## Splatmap Aesthetic Guidelines

### Current Logic (Simple)

```python
Rock: slope > 0.35
Snow: elevation > 90th percentile
Sand: dunes OR (flat AND low)
Grass: everything else
```

### Better Approach (More Natural)

```python
Rock: 
  - Steep slopes (slope > 0.35)
  - Near cliffs/edges
  - High elevation + high slope

Snow:
  - Very high elevation (top 7-10%)
  - Gradual falloff (not binary)
  - Blend with rock at edges

Sand:
  - Dune areas (strong signal)
  - Flat lowlands (gentle signal)
  - Blend smoothly with grass

Grass:
  - Default texture
  - Mid-elevation, gentle slopes
  - Transition zones
```

### Texture Transition Rules

- **Smooth transitions**: Use distance-based blending, not thresholds
- **Feature-aware**: Rock near cliffs, sand in valleys, etc.
- **Elevation-aware**: Snow on peaks, sand in lowlands
- **Slope-aware**: Rock on steep slopes, grass on gentle

---

## Implementation Patterns

### ✅ Good Patterns

```python
# Natural variation
radius = base_radius * random.uniform(0.85, 1.15)

# Smooth blending
feather_distance = min(40, region_size // 4)
falloff_mask = np.clip(dist_to_edge / feather_distance, 0.0, 1.0)

# Proportional relationships
valley_depth = surrounding_height * 0.5  # Relative to context

# Feature-aware placement
if near_mountain:
    spacing = mountain_radius * 1.5
```

### ❌ Bad Patterns

```python
# Too uniform
radius = 56  # Always the same!

# Hard edges
mask[y0:y1, x0:x1] = 1.0  # No falloff!

# Ignore context
valley_depth = 0.35  # Fixed, doesn't consider mountains

# Grid placement
for i in range(3):
    x = i * 100  # Regular spacing!
```

---

## Future Improvements (Priority Order)

1. **Add Variation** (HIGH)
   - Randomize feature dimensions (±15%)
   - Multiple feature variations
   - Natural spacing (Poisson disk)

2. **Natural Erosion** (HIGH)
   - Edge erosion at feature boundaries
   - Slope-based erosion simulation
   - Weathering patterns

3. **Feature Relationships** (MEDIUM)
   - "Between" positioning logic
   - Feature-aware spacing
   - Context-aware depth/height

4. **Better Splatmap** (MEDIUM)
   - Distance-based texture blending
   - Feature-aware texture assignment
   - Smooth transitions

5. **More Features** (LOW)
   - Canyons, plateaus, cliffs, etc.
   - But only if they follow aesthetic principles!

---

## Testing Checklist

Before considering terrain "good", verify:

- [ ] Features have natural variation (not identical)
- [ ] Valleys are noticeably deep (not subtle)
- [ ] Mountains dominate the landscape
- [ ] Features blend smoothly (no hard edges)
- [ ] Empty spaces exist (not crowded)
- [ ] Textures match elevation/slope
- [ ] No visible seams or artifacts
- [ ] Proportions feel natural (not too big/small)

---

## Context for AI Agents

### Key Files to Understand

1. **`server/primitives/`** - Feature generators
   - `mountains.py` - Mountains, hills, mesas, plateaus
   - `valleys.py` - Valleys, canyons
   - `dunes.py` - Dune generation with edge feathering
   - `base.py` - Base biomes (flat, desert, forest, arctic)

2. **`server/engine/`** - Core systems
   - `stamping.py` - Blending modes and stamping
   - `splatmap.py` - Texture splatmap generation
   - `spatial.py` - Position resolution utilities

3. **`server/semantic/`** - Natural language
   - `parser.py` - LLM/regex command parsing
   - `state_manager.py` - Feature tracking with IDs
   - `spatial_resolver.py` - Position interpretation

4. **`server/terrain.py`** - Main orchestrator
   - Coordinates all systems
   - Feature creation and modification
   - State management

### Critical Design Decisions

- **State-based rebuilds**: Always rebuild from state, never mutate
- **Deterministic**: Seed-based generation for reproducibility
- **Modular**: Features are isolated primitives
- **Backward compatible**: Old state files should still work

### What NOT to Change

- **State format**: Features array structure is stable
- **Blending modes**: MAX for mountains, SUBTRACT for valleys
- **Normalization**: Always normalize heightmap to 0-1 range
- **Splatmap channels**: RGBA mapping (grass, rock, sand, snow)

### What TO Improve

- **Add variation**: Randomize dimensions (±15%)
- **Better blending**: Feature-aware smoothing
- **Natural spacing**: Poisson disk sampling
- **Feature relationships**: Context-aware placement
- **Erosion**: Edge erosion simulation

---

## Example: Good vs Bad Terrain

### ❌ Bad Terrain
```
- 5 identical mountains in a grid
- Valleys too shallow (barely visible)
- Hard edges on dunes
- No variation in sizes
- Crowded features (no empty space)
- Textures don't match terrain
```

### ✅ Good Terrain
```
- 3-5 varied mountains (different sizes)
- Deep valleys that flow between mountains
- Smooth dune blending with 40px feathering
- Natural spacing (clustered, not grid)
- Empty spaces for breathing room
- Textures match elevation (snow on peaks, rock on slopes)
```

---

## Quick Reference: Default Parameters

```python
# Mountains
height: 0.75, radius: 56, steepness: 1.0

# Hills  
height: 0.45, radius: 42, steepness: 0.7

# Valleys
depth: 0.55, radius: 64

# Dunes
amp: 0.08, freq: 18.0, angle: 20.0, feather: 40px

# Smoothing
sigma: 0.8 (post-processing)

# Splatmap thresholds
rock_slope: 0.35
snow_percentile: 90th
sand_threshold: 0.35 elevation, 0.2 slope
```

---

## Final Notes

**Remember**: The goal is natural-looking terrain, not perfection. Add variation, respect proportions, and blend smoothly. Avoid uniform grids, hard edges, and ignoring context.

**When in doubt**: Add randomness (±15%), increase feathering (40px+), and ensure features relate to each other spatially.

