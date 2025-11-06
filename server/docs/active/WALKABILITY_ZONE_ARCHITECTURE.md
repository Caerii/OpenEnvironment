# Walkability Zone Architecture - Proactive Terrain Design

## Problem Statement

**Current Approach (Reactive):**
1. Generate terrain with mountains, valleys, etc.
2. Try to find/force paths through terrain
3. Clamp/flatten terrain to create walkable areas
4. Result: Contrived paths, extra smoothing needed

**Proposed Approach (Proactive):**
1. Reserve walkability zones FIRST (flat areas, paths)
2. Place obstacles around them (mountains, etc.)
3. Features naturally respect walkability zones
4. Result: Natural paths, no post-processing needed

## Architecture Design

### 1. Walkability Zone Primitives

New primitive types that reserve flat/walkable space:

#### `flat_zone` - Reserved Flat Area
```python
{
    "type": "flat_zone",
    "x": 256,
    "y": 256,
    "radius": 80,        # Circular flat area
    "priority": "high"   # How strictly to enforce (high = no features can block)
}
```

#### `path` - Linear Walkability Zone
```python
{
    "type": "path",
    "start": [100, 100],
    "end": [400, 400],
    "width": 30,        # Path width in pixels
    "priority": "high"
}
```

#### `clearing` - Large Open Area
```python
{
    "type": "clearing",
    "x": 256,
    "y": 256,
    "radius": 120,      # Large flat clearing
    "priority": "medium" # Can have minor features (hills, mounds)
}
```

### 2. Constraint System

Track reserved zones and enforce constraints during feature placement:

```python
class WalkabilityConstraint:
    """Tracks walkability zones and enforces constraints."""
    
    def __init__(self):
        self.zones = []  # List of reserved zones
        self.constraint_map = None  # 512x512 map of constraints
    
    def add_zone(self, zone: Dict):
        """Add a walkability zone."""
        self.zones.append(zone)
        self._update_constraint_map()
    
    def can_place_feature(self, feature_type: str, position: Tuple[int, int], 
                          radius: int) -> bool:
        """Check if feature can be placed without violating constraints."""
        # Check if feature overlaps with high-priority zones
        # Allow overlap with low-priority zones (mountains can "bleed" a bit)
    
    def find_placement_away_from_zones(self, feature_type: str, 
                                       preferred_pos: Tuple[int, int],
                                       min_distance: int = 50) -> Tuple[int, int]:
        """Find valid placement position away from walkability zones."""
```

### 3. Integration with TerrainBuilder

```python
class TerrainBuilder:
    def __init__(self, ...):
        # ...
        self.walkability_constraints = WalkabilityConstraint()
        self.walkability_zones = []  # Track zones for visualization
    
    def reserve_walkability_zone(self, zone_type: str, **params):
        """Reserve a walkability zone BEFORE placing features."""
        zone = self._create_zone(zone_type, **params)
        self.walkability_constraints.add_zone(zone)
        self.walkability_zones.append(zone)
        
        # Apply flat terrain to zone (subtract height, ensure flatness)
        self._apply_flat_zone(zone)
    
    def apply_feature(self, feature_stamp, ...):
        """Apply feature with constraint checking."""
        # Check if feature violates walkability constraints
        # If so, adjust position or reject
```

### 4. Semantic Understanding Integration

Parser understands walkability-aware commands:

```python
# User: "add a path from center to top-right, then place mountains around it"
# System:
1. Creates path zone (flat_zone or path primitive)
2. Reserves flat area
3. Places mountains with constraint: "away from path"
4. Mountains naturally form around the path
```

Semantic relationships:
- `"path_between"`: Path connecting two features
- `"around_path"`: Features placed around a path
- `"away_from_path"`: Constraint to avoid blocking paths

### 5. Feature Placement with Constraints

Modify `resolve_position` to respect constraints:

```python
def resolve_position_with_constraints(
    position_spec: Optional[Dict],
    feature_type: str,
    feature_radius: int,
    walkability_constraints: WalkabilityConstraint,
    existing_features: List[Dict] = None,
    seed: int = 0
) -> Tuple[int, int]:
    """
    Resolve position while respecting walkability constraints.
    
    If position would violate constraints, finds alternative nearby position.
    """
    # Try preferred position
    preferred_pos = resolve_position(position_spec, existing_features, seed)
    
    # Check constraints
    if walkability_constraints.can_place_feature(feature_type, preferred_pos, feature_radius):
        return preferred_pos
    
    # Find alternative position away from constraints
    return walkability_constraints.find_placement_away_from_zones(
        feature_type, preferred_pos, min_distance=feature_radius + 20
    )
```

## Implementation Plan

### Phase 1: Walkability Zone Primitives
1. Create `primitives/walkability_zones.py`
   - `generate_flat_zone()` - Flat circular area
   - `generate_path()` - Linear flat path
   - `generate_clearing()` - Large open area
2. Register in `FeatureRegistry`
3. Use `BlendingMode.MIN` or `SUBTRACT` to ensure flatness

### Phase 2: Constraint System
1. Create `engine/walkability_constraints.py`
   - `WalkabilityConstraint` class
   - Constraint map generation
   - Placement validation
2. Integrate with `TerrainBuilder`
3. Track zones in builder state

### Phase 3: Constraint-Aware Placement
1. Modify `spatial_resolver.py`
   - Add constraint checking to `resolve_position()`
   - Add `find_placement_away_from_zones()`
2. Update `AddFeatureCommand.execute()`
   - Pass constraints to position resolver
   - Respect constraints during placement

### Phase 4: Semantic Understanding
1. Update `semantic/parser.py`
   - Recognize walkability commands
   - Extract path/zone specifications
2. Create semantic relationships:
   - `"path_between"` relationship
   - `"around_path"` constraint
3. Update `tool_registry.py`
   - Add tools for walkability zones
   - Add "path" and "flat_zone" tools

### Phase 5: Integration & Testing
1. Test constraint enforcement
2. Test semantic commands
3. Visualize walkability zones
4. Ensure backward compatibility

## Example Usage

### Natural Language Commands

```python
# User: "add a path from center to top-right, then place 3 mountains around it"
# System:
1. Creates path zone: path(start=(256,256), end=(341,0), width=30)
2. Reserves flat area
3. Places 3 mountains with constraint: min_distance=50 from path
4. Mountains naturally form around the path

# User: "add a flat clearing in the center, then place hills around it"
# System:
1. Creates clearing zone: clearing(x=256, y=256, radius=120)
2. Places hills with constraint: can overlap slightly (priority=medium)
3. Hills surround but don't block clearing
```

### Programmatic Usage

```python
builder = TerrainBuilder(base_biome_fn, seed=0)

# Reserve walkability zones FIRST
builder.reserve_walkability_zone("path", 
    start=(100, 100), end=(400, 400), width=30, priority="high")
builder.reserve_walkability_zone("flat_zone",
    x=256, y=256, radius=80, priority="high")

# Then place features - they automatically respect constraints
builder.apply_feature(mountain_stamp, ...)  # Constraint-aware
```

## Benefits

1. **No Post-Processing**: Paths are natural, no clamping needed
2. **Semantic Clarity**: "path between mountains" is explicit
3. **Proactive Design**: Terrain designed around walkability
4. **Flexible**: Can have multiple priority levels
5. **Visualizable**: Zones can be rendered for debugging

## Edge Cases

1. **Overlapping Zones**: Higher priority wins, or merge zones
2. **Too Many Constraints**: If no valid placement, reduce constraint strictness
3. **Path Intersections**: Allow paths to cross, create intersections
4. **Feature Bleeding**: Allow mountains to "bleed" slightly into low-priority zones

## Future Enhancements

1. **Path Networks**: Connect multiple paths, create route networks
2. **Dynamic Constraints**: Adjust constraints based on terrain type
3. **Path Optimization**: AI finds optimal path through terrain
4. **Multi-Level Walkability**: Different zones for different movement types
5. **Semantic Paths**: "trade route", "mountain pass", "river path"

