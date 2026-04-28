# Encapsulation Design - Walkability Zone Integration

## Overview

This document describes the properly encapsulated integration of walkability zones into the terrain generation system, following SOLID principles and maintaining clean architecture.

## Design Principles

### 1. **Encapsulation**
- Constraint system is **internal** to `TerrainBuilder`
- No external code directly accesses `WalkabilityConstraint`
- Public API methods provide controlled access

### 2. **Single Responsibility**
- `WalkabilityConstraint`: Tracks zones and validates placements
- `TerrainBuilder`: Manages terrain construction and constraints
- `FeatureGenerator`: Generates stamps (including walkability zones)
- `SpatialResolver`: Resolves positions (optionally using constraints)

### 3. **Dependency Injection**
- Constraints passed to position resolver (optional parameter)
- No hard dependencies - works with or without constraints
- Backward compatible

## Architecture

### Component Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│ TerrainBuilder (Owner)                                   │
│  - Encapsulates WalkabilityConstraint                    │
│  - Tracks zones when walkability features are applied    │
│  - Provides public API for constraint checking           │
└─────────────────────────────────────────────────────────┘
                    │
                    │ uses (internal)
                    ▼
┌─────────────────────────────────────────────────────────┐
│ WalkabilityConstraint (Encapsulated)                     │
│  - Tracks reserved zones                                 │
│  - Validates placements                                  │
│  - Finds alternative positions                           │
└─────────────────────────────────────────────────────────┘
                    │
                    │ used by (injected)
                    ▼
┌─────────────────────────────────────────────────────────┐
│ SpatialResolver (Optional Dependency)                    │
│  - Resolves positions                                    │
│  - Can use constraints if provided                       │
│  - Works without constraints (backward compatible)       │
└─────────────────────────────────────────────────────────┘
```

### Encapsulation Boundaries

#### 1. **TerrainBuilder (Public API)**

```python
class TerrainBuilder:
    # Private: Constraint system (encapsulated)
    _walkability_constraints = None
    
    # Public: Constraint checking API
    def can_place_feature(self, feature_type, position, radius):
        """Check if feature can be placed."""
    
    def find_placement_away_from_zones(self, feature_type, preferred_pos, radius):
        """Find valid placement."""
    
    # Internal: Zone tracking (called automatically)
    def _track_walkability_zone(self, zone_type, params):
        """Track zone when walkability feature is applied."""
```

**Key Points:**
- Constraint system is **private** (`_walkability_constraints`)
- Public methods provide controlled access
- Automatic tracking when walkability zones are applied
- No external code needs to know about constraints

#### 2. **WalkabilityConstraint (Encapsulated Implementation)**

```python
class WalkabilityConstraint:
    """Internal constraint system - only used by TerrainBuilder."""
    
    def add_zone(self, zone_type, params, priority):
        """Add zone (called by builder)."""
    
    def can_place_feature(self, feature_type, position, radius):
        """Validate placement (called by builder)."""
    
    def find_placement_away_from_zones(self, ...):
        """Find alternative position (called by builder)."""
```

**Key Points:**
- Only used internally by `TerrainBuilder`
- Not exposed to external code
- Encapsulates all constraint logic

#### 3. **FeatureRegistry (Feature Generator Pattern)**

```python
class FlatZoneGenerator(FeatureGenerator):
    """Generator for flat zones - follows standard pattern."""
    
    def generate_stamp(self, feat, seed):
        """Generate flat zone stamp."""
    
    def get_blending_mode(self):
        return BlendingMode.MIN  # Ensures flatness
```

**Key Points:**
- Walkability zones are **just features** using FeatureGenerator pattern
- Use MIN blending to ensure flatness
- No special handling needed - works like any other feature
- Automatically tracked when applied to builder

#### 4. **SpatialResolver (Optional Dependency Injection)**

```python
def resolve_position(position_spec, existing_features, constraints=None, seed=0):
    """Resolve position - optionally uses constraints."""
    # Resolve position normally
    pos = _resolve_internal(position_spec, existing_features, seed)
    
    # If constraints provided, can adjust position
    if constraints:
        # Use constraints if needed
        pass
    
    return pos
```

**Key Points:**
- Constraints are **optional parameter**
- Works without constraints (backward compatible)
- Dependency injection pattern
- No hard coupling

#### 5. **AddFeatureCommand (Integration Point)**

```python
class AddFeatureCommand:
    def execute(self, builder, feature_state, seed):
        # Get constraints from builder (if available)
        constraints = builder._get_walkability_constraints() if hasattr(...) else None
        
        # Resolve position with constraints (optional)
        pos = resolve_position(..., constraints=constraints, ...)
        
        # Check constraints before placing (if available)
        if constraints and constraints.has_zones():
            can_place, reason = builder.can_place_feature(...)
            if not can_place:
                pos = builder.find_placement_away_from_zones(...)
        
        # Place feature (automatically tracked if walkability zone)
        _apply_feature_to_builder(builder, feat, seed)
```

**Key Points:**
- Optional constraint checking
- Uses builder's public API
- Works with or without constraints
- Automatic tracking of walkability zones

## Integration Flow

### 1. Walkability Zone Placement

```
User/Command → AddFeatureCommand.execute()
  → FeatureRegistry.generate_stamp("flat_zone", ...)
  → builder.apply_feature(stamp, MIN, feature_type="flat_zone", ...)
  → builder._track_walkability_zone("flat_zone", params)  # Automatic
  → WalkabilityConstraint.add_zone(...)  # Encapsulated
```

**Key:** Zones are tracked automatically when applied - no special handling needed.

### 2. Feature Placement with Constraints

```
User/Command → AddFeatureCommand.execute()
  → Get constraints from builder (optional)
  → resolve_position(..., constraints=constraints)  # Optional
  → Check constraints: builder.can_place_feature(...)  # Public API
  → If blocked: builder.find_placement_away_from_zones(...)  # Public API
  → Place feature
```

**Key:** Constraint checking is optional and uses public API.

## Benefits of This Design

### 1. **Encapsulation**
- Constraint system is internal to builder
- External code doesn't need to know about constraints
- Clear public API boundaries

### 2. **Backward Compatibility**
- Works without constraints (optional dependency injection)
- Existing code continues to work
- No breaking changes

### 3. **Extensibility**
- Easy to add new constraint types
- Easy to modify constraint logic
- Changes isolated to encapsulated components

### 4. **Testability**
- Can test constraint system independently
- Can test builder with/without constraints
- Can mock constraints for testing

### 5. **Maintainability**
- Clear separation of concerns
- Single responsibility per component
- Easy to understand and modify

## Usage Examples

### Programmatic (With Constraints)

```python
builder = TerrainBuilder(base_biome_fn, seed=0)

# Add walkability zone (automatically tracked)
feat = {"type": "flat_zone", "x": 256, "y": 256, "radius": 80}
stamp = FeatureRegistry.generate_stamp("flat_zone", feat, seed)
builder.apply_feature(stamp, BlendingMode.MIN, 
                     feature_type="flat_zone", feature_params=feat)

# Place feature (automatically respects constraints)
feat = {"type": "mountain", "x": 256, "y": 256, "radius": 56}
# Position will be adjusted if violates constraints
can_place, reason = builder.can_place_feature("mountain", (256, 256), 56)
if not can_place:
    pos = builder.find_placement_away_from_zones("mountain", (256, 256), 56)
```

### Natural Language (Automatic)

```python
# User: "add a flat zone at center, then add 3 mountains"
# System automatically:
# 1. Places flat zone (tracked in constraints)
# 2. Places mountains (position adjusted if violates constraints)
```

## Summary

The design uses proper encapsulation with:
- **Private constraint system** in builder
- **Public API** for constraint checking
- **Optional dependency injection** for position resolution
- **Automatic tracking** of walkability zones
- **Backward compatibility** (works without constraints)

This maintains clean architecture while providing powerful constraint checking capabilities.

