# Walkability Zone Analysis - Semantic Understanding & Proactive Design

## Current Semantic Understanding

### ✅ What We Have

1. **Spatial Relationships** (`semantic/scene/relationships.py`)
   - Tracks "between", "near", "far_from" relationships
   - Calculates distances between features
   - Stores relationship metadata

2. **Relationship Inference** (`semantic/scene/relationship_inference.py`)
   - Automatically detects "between" relationships
   - Detects "near" relationships (within 150px)
   - Calculates angles and distances

3. **Spatial Queries** (`semantic/scene/query.py`)
   - `find_near()` - Find features within radius
   - `find_between()` - Find features in corridor
   - `find_near_feature()` - Find features near another feature

4. **Distance Calculation** (`semantic/spatial_resolver.py`)
   - `min_distance` parameter in `resolve_multiple_positions()`
   - Ensures features don't overlap (minimum 20px spacing)

### ⚠️ What's Missing

1. **No Constraint System**
   - Features can be placed anywhere, no reserved zones
   - No enforcement of "away from paths" or "around walkability zones"

2. **No Walkability Primitives**
   - Can't reserve flat areas
   - Can't create paths before placing obstacles

3. **Reactive Placement**
   - Features placed first, then try to find paths
   - No proactive terrain design

## Proposed Solution: Proactive Walkability Zones

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  User Command: "add path from center to top-right,     │
│  then place 3 mountains around it"                     │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  1. Semantic Parser                                      │
│     - Recognizes "path" command                          │
│     - Extracts path parameters (start, end, width)      │
│     - Recognizes "around" relationship                  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  2. Reserve Walkability Zone                            │
│     - Create path zone (flat_zone/path primitive)       │
│     - Add to WalkabilityConstraint                      │
│     - Apply flat terrain (MIN blending)                 │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  3. Place Features with Constraints                     │
│     - For each mountain:                                 │
│       a. Try preferred position                         │
│       b. Check constraints.can_place_feature()          │
│       c. If blocked, find_placement_away_from_zones()    │
│     - Mountains naturally form around path              │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Walkability Zone Primitives (`primitives/walkability_zones.py`)

**Types:**
- `flat_zone`: Circular flat area (clearing, safe zone)
- `path`: Linear walkable route (road, trail)
- `clearing`: Large open area (lower priority)

**Blending:** Uses `MIN` blending to ensure terrain stays flat

#### 2. Constraint System (`engine/walkability_constraints.py`)

**WalkabilityConstraint class:**
- Tracks all reserved zones
- Validates feature placement
- Finds alternative positions
- Calculates distances to zones

**Priority Levels:**
- `high`: No features can block (paths, critical zones)
- `medium`: Small features can overlap slightly (clearings)
- `low`: Most features can overlap (loose constraints)

#### 3. Constraint-Aware Placement

**Modified `resolve_position()`:**
```python
def resolve_position_with_constraints(
    position_spec: Dict,
    feature_type: str,
    feature_radius: int,
    walkability_constraints: WalkabilityConstraint,
    existing_features: List[Dict],
    seed: int
) -> Tuple[int, int]:
    # Try preferred position
    preferred = resolve_position(position_spec, existing_features, seed)
    
    # Check constraints
    if constraints.can_place_feature(feature_type, preferred, feature_radius):
        return preferred
    
    # Find alternative
    return constraints.find_placement_away_from_zones(
        feature_type, preferred, feature_radius
    )
```

### Semantic Understanding Enhancements

#### 1. Path Relationships

**New relationships:**
- `"path_between"`: Path connecting two features
- `"around_path"`: Features placed around a path
- `"away_from_path"`: Constraint to avoid blocking paths

#### 2. Natural Language Commands

**Examples:**
```
"add a path from center to top-right, then place 3 mountains around it"
→ Creates path zone, places mountains with constraint

"add a flat clearing in the center, then place hills around it"
→ Creates clearing zone, places hills with constraint

"add a mountain pass between the two mountains"
→ Creates path zone between mountains
```

#### 3. Semantic Constraints

**Parser understands:**
- "away from" → constraint to avoid zones
- "around" → constraint to place near but not on zones
- "between" → constraint to place in corridor between zones

## Benefits

### 1. No Post-Processing Needed
- Paths are naturally flat, no clamping required
- No extra smoothing needed
- Terrain is designed correctly from the start

### 2. Semantic Clarity
- "path between mountains" is explicit
- Constraints are visible and understandable
- Natural language commands map directly to constraints

### 3. Proactive Design
- Terrain designed around walkability
- Features naturally respect walkability zones
- No trying to force paths through existing terrain

### 4. Flexible Priority System
- High priority zones: strict enforcement
- Medium priority: allow minor features
- Low priority: allow most features to overlap slightly

## Example Workflows

### Workflow 1: Path with Mountains Around It

```
User: "add a path from center to top-right, then place 3 mountains around it"

System:
1. Parse command → extract path + mountains
2. Reserve path zone: path(start=(256,256), end=(341,0), width=30, priority="high")
3. Apply flat terrain to path (MIN blending)
4. For each mountain:
   a. Try random position
   b. Check: can_place_feature("mountain", pos, radius=56)
   c. If blocked by path, find_placement_away_from_zones()
   d. Place mountain with constraint: min_distance=50 from path
5. Result: Path with mountains naturally forming around it
```

### Workflow 2: Clearing with Hills

```
User: "add a flat clearing in the center, then place 5 hills around it"

System:
1. Reserve clearing zone: clearing(x=256, y=256, radius=120, priority="medium")
2. Apply flat terrain to clearing
3. For each hill:
   a. Try position near clearing
   b. Check: can_place_feature("hill", pos, radius=42)
   c. Hills can overlap slightly with medium-priority clearing
   d. Place hills around clearing
4. Result: Large clearing with hills surrounding it
```

### Workflow 3: Mountain Pass

```
User: "add a mountain pass between the two mountains"

System:
1. Query: find two mountains (or use referenced mountains)
2. Calculate positions: mountain1_pos, mountain2_pos
3. Create path zone between them: path(start=mountain1_pos, end=mountain2_pos, width=40)
4. Apply flat terrain to path
5. Result: Natural mountain pass between mountains
```

## Integration Points

### 1. TerrainBuilder Integration

```python
class TerrainBuilder:
    def __init__(self, ...):
        self.walkability_constraints = WalkabilityConstraint()
        self.walkability_zones = []
    
    def reserve_walkability_zone(self, zone_type: str, **params):
        """Reserve zone BEFORE placing features."""
        zone = self._create_zone(zone_type, **params)
        self.walkability_constraints.add_zone(zone_type, params, priority="high")
        
        # Apply flat terrain
        stamp = generate_flat_zone(...)  # or generate_path(...)
        self.apply_feature(stamp, BlendingMode.MIN)
```

### 2. Command Execution Integration

```python
class AddFeatureCommand:
    def execute(self, builder, feature_state, seed):
        # Check if we have constraints
        constraints = builder.walkability_constraints
        
        # Resolve position with constraints
        if constraints and constraints.zones:
            pos = resolve_position_with_constraints(
                self.position, self.feature_type, radius,
                constraints, existing_features, seed
            )
        else:
            pos = resolve_position(self.position, existing_features, seed)
        
        # Create and place feature
        ...
```

### 3. Semantic Parser Integration

```python
class SemanticParser:
    def parse(self, command: str, state: Dict) -> List[Dict]:
        # Detect walkability commands
        if "path" in command or "flat zone" in command:
            # Extract path/zone parameters
            # Create walkability zone action
            actions.append(CreateWalkabilityZoneAction(...))
        
        # Detect "around" relationships
        if "around" in command:
            # Add constraint: "away_from" walkability zones
            actions.append(AddFeatureWithConstraint(...))
```

## Future Enhancements

1. **Path Networks**: Connect multiple paths, create route networks
2. **Dynamic Constraints**: Adjust constraints based on terrain type
3. **Path Optimization**: AI finds optimal path through terrain
4. **Multi-Level Walkability**: Different zones for different movement types
5. **Semantic Paths**: "trade route", "mountain pass", "river path"

## Conclusion

By reserving walkability zones FIRST and placing features with constraints, we get:
- ✅ Natural paths (no post-processing)
- ✅ Semantic clarity ("path between mountains")
- ✅ Proactive design (terrain designed around walkability)
- ✅ Flexible constraints (priority-based enforcement)

This is much simpler and more robust than trying to force paths through already-generated terrain.

