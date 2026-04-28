# Walkability Heuristics

## Overview

The walkability system provides cost-based and threshold-based analysis for terrain navigation. It uses:

- **Slope gradient** (steepness) - calculated via Sobel operator
- **Terrain type** (from splatmap: grass, rock, sand, snow)
- **Feature masks** (cliffs, dunes)
- **Height restrictions** (optional min/max height)

## Basic Usage

### Calculate Movement Cost Map

```python
from server.engine.walkability import calculate_walkability_cost, DEFAULT_CONFIG
from server.engine.builder import TerrainBuilder
from server.primitives.base import base_desert

# Generate terrain
builder = TerrainBuilder(base_desert, seed=0)
# ... add features ...
heightmap, dune_mask, cliff_mask = builder.finalize()
splatmap = builder.build_splatmap()

# Calculate walkability costs
cost_map = calculate_walkability_cost(
    heightmap,
    splatmap=splatmap,
    cliff_mask=cliff_mask,
    dune_mask=dune_mask,
    config=DEFAULT_CONFIG
)

# Lower values = easier, higher = harder/impassable
# Typical range: 1.0 (easy) to 10.0+ (impassable)
```

### Binary Walkability Mask

```python
from server.engine.walkability import calculate_walkability_mask

walkable = calculate_walkability_mask(
    heightmap,
    splatmap=splatmap,
    cliff_mask=cliff_mask
)

# True = walkable, False = impassable
```

### Difficulty Zones

```python
from server.engine.walkability import calculate_difficulty_zones

zones = calculate_difficulty_zones(
    heightmap,
    splatmap=splatmap,
    cliff_mask=cliff_mask,
    dune_mask=dune_mask
)

# zones["easy"] - boolean mask
# zones["moderate"] - boolean mask
# zones["hard"] - boolean mask
# zones["very_hard"] - boolean mask
# zones["impassable"] - boolean mask
```

## Configuration

### Default (Human Walkability)

- **Max walkable slope**: 0.6 (~35°)
- **Impassable slope**: 0.85 (~50°)
- **Terrain costs**: Grass=1.0, Sand=1.3, Rock=1.8, Snow=2.0
- **Cliff penalty**: 10.0 (effectively impassable)

### Vehicle Configuration

```python
from server.engine.walkability import VEHICLE_CONFIG

cost_map = calculate_walkability_cost(
    heightmap, splatmap=splatmap,
    config=VEHICLE_CONFIG
)
```

- More restrictive slopes (~22° max)
- Higher penalties for sand/snow

### Agile Character Configuration

```python
from server.engine.walkability import AGILE_CONFIG

cost_map = calculate_walkability_cost(
    heightmap, splatmap=splatmap,
    config=AGILE_CONFIG
)
```

- More lenient slopes (~48° max, can climb)
- Better rock climbing (lower rock cost)

### Custom Configuration

```python
from server.engine.walkability import WalkabilityConfig

custom_config = WalkabilityConfig(
    max_walkable_slope=0.5,      # ~28° max
    impassable_slope=0.8,        # ~38° impassable
    grass_cost=1.0,
    sand_cost=1.5,
    rock_cost=2.0,
    snow_cost=2.5,
    cliff_penalty=15.0,
    min_height=0.1,             # Below 10% = water/too deep
    max_height=0.9                # Above 90% = too high
)
```

## Heuristics Breakdown

### 1. Slope-Based Cost

- **0-0.4 (steep_penalty_slope)**: Normal cost (1.0)
- **0.4-0.6 (max_walkable)**: Quadratic penalty (up to 3x cost)
- **0.6-0.85 (impassable)**: Very high cost (+5.0)
- **>0.85**: Impassable (cliff_penalty = 10.0+)

### 2. Terrain Type Multipliers

Applied multiplicatively:

- **Grass**: 1.0x (easy)
- **Sand**: 1.3x (slightly harder, sinking)
- **Rock**: 1.8x (uneven footing)
- **Snow**: 2.0x (slippery, deep)

### 3. Feature Penalties

- **Cliffs**: +10.0 cost (effectively impassable)
- **Dunes**: +0.2 cost (moderate penalty)

### 4. Height Restrictions

- **Too low** (< min_height): +3.0 cost (water, deep valleys)
- **Too high** (> max_height): +2.0 cost (altitude)

## Integration with Pathfinding

The cost map can be used directly with pathfinding algorithms:

```python
import networkx as nx
from scipy.spatial.distance import euclidean

# Create graph from cost map
# (simplified example - use proper grid-based pathfinding)
# A* or Dijkstra would use cost_map as edge weights
```

## Visualization

Cost maps can be visualized for debugging:

```python
import matplotlib.pyplot as plt

# Normalize cost map for visualization
cost_normalized = np.clip(cost_map / 10.0, 0.0, 1.0)

plt.imshow(cost_normalized, cmap='RdYlGn_r')  # Red = hard, Green = easy
plt.colorbar()
plt.show()
```

## Research Notes

The heuristics are based on:

1. **Human biomechanics**: Max sustainable slope ~35° (0.6 normalized)
2. **Terrain analysis**: Different surface types have measurable friction coefficients
3. **Game development**: Standard industry practices for terrain navigation
4. **Real-world data**: Hiking trail difficulty ratings, mountaineering classifications

## Example: Finding Optimal Path

```python
from server.engine.walkability import find_walkable_path_cost

start = (100, 100)
end = (400, 400)

estimated_cost = find_walkable_path_cost(start, end, cost_map)
# This is a heuristic - use proper A* for actual pathfinding
```

## Future Enhancements

- **A* pathfinding integration** - Full pathfinding algorithm
- **Flow field generation** - For crowd simulation
- **Coverage analysis** - Which areas are reachable from a point
- **Terrain traversal time** - Speed-based cost calculation

