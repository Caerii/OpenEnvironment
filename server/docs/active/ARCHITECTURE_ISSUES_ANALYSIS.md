# Architecture Issues Analysis - Walkability Zones

## Current System Problems

### ❌ Problem 1: Position Resolution Happens Too Early

**Current Flow:**
```
1. Parse command → actions
2. AddFeatureCommand.execute():
   a. resolve_position() ← Position chosen HERE
   b. FeatureRegistry.create_feature() ← Feature created
   c. _apply_feature_to_builder() ← Builder just applies what it's told
```

**Issue:** Position is resolved BEFORE builder knows about constraints. By the time builder gets the stamp, position is already fixed.

**Why This Breaks Walkability Zones:**
- Can't check constraints during position resolution
- Can't adjust position if it violates walkability zones
- Builder is passive - just applies stamps

### ❌ Problem 2: No Two-Phase System

**Current System:**
- Linear execution: Parse → Resolve → Create → Apply
- No concept of "phase 1: reserve zones, phase 2: place features"
- Everything goes through the same path

**What We Need:**
```
Phase 1: Reserve walkability zones
  - Create flat zones
  - Apply to builder (MIN blending)
  - Track in constraint system

Phase 2: Place features with constraints
  - Check constraints during position resolution
  - Adjust position if violates constraints
  - Place features respecting zones
```

**Current System Can't Do This:**
- No way to distinguish "infrastructure" (paths) from "features" (mountains)
- No way to execute in phases
- Everything is linear

### ❌ Problem 3: Builder is Passive

**TerrainBuilder:**
```python
def apply_feature(self, feature_stamp, blending_mode, ...):
    # Just applies what it's told
    stamp_primitive(self.heightmap, feature_stamp, blending_mode)
```

**Issues:**
- Builder doesn't validate positions
- Builder doesn't know about constraints
- Builder can't reject features
- Builder can't adjust positions

**What We Need:**
- Builder should validate placements
- Builder should have constraint system
- Builder should be able to reject/adjust positions

### ❌ Problem 4: No Constraint State in Builder

**Current Builder:**
```python
class TerrainBuilder:
    def __init__(self, ...):
        self.heightmap = base_biome_fn(seed)
        self.dune_mask = ...
        self.cliff_mask = ...
        # NO constraint system!
```

**Issue:** Builder has no way to track reserved zones or check constraints.

### ❌ Problem 5: Feature Registry Doesn't Support Constraints

**Current FeatureRegistry:**
```python
def generate_stamp(feature_type, feat, seed):
    # Just generates stamp based on feature dict
    # No concept of "can I place this here?"
    # No feedback loop
```

**Issue:** Registry generates stamps, but doesn't validate placements or check constraints.

## Why My Proposed Solution Doesn't Fit

### ❌ Issue 1: Position Resolution Outside Builder

**My Proposal:**
```python
builder.reserve_walkability_zone("path", ...)
# Then later:
pos = resolve_position_with_constraints(..., builder.constraints)
```

**Problem:** `resolve_position()` is called in `AddFeatureCommand.execute()` BEFORE builder has a chance to validate. The command system doesn't know about constraints.

### ❌ Issue 2: No Two-Phase Execution

**My Proposal:** Two-phase system (reserve zones, then place features)

**Problem:** Current system executes actions linearly. No way to:
- Execute "walkability zone" actions first
- Then execute "feature" actions with constraints
- Actions are all executed in the order they're parsed

### ❌ Issue 3: No Distinction Between Infrastructure and Features

**My Proposal:** Walkability zones are "infrastructure" that should be placed first

**Problem:** Current system treats everything as "features" through the same registry. No concept of:
- Infrastructure features (paths, zones)
- Terrain features (mountains, valleys)
- Different execution order

### ❌ Issue 4: Builder Has No Constraint System

**My Proposal:** Builder should have `WalkabilityConstraint` instance

**Problem:** Builder doesn't currently track constraints. Would need to:
- Add constraint system to builder
- Modify `apply_feature()` to check constraints
- Handle constraint violations

## What Actually Needs to Change

### ✅ Solution 1: Add Constraint System to Builder

```python
class TerrainBuilder:
    def __init__(self, ...):
        self.walkability_constraints = WalkabilityConstraint()
        # ...
    
    def reserve_walkability_zone(self, zone_type, params, priority="high"):
        """Reserve zone and apply flat terrain."""
        # Add to constraint system
        self.walkability_constraints.add_zone(zone_type, params, priority)
        
        # Generate flat stamp
        stamp = generate_flat_zone(...)  # or generate_path(...)
        # Apply with MIN blending (ensures flatness)
        self.apply_feature(stamp, BlendingMode.MIN)
    
    def apply_feature(self, feature_stamp, blending_mode, ...):
        """Apply feature with optional constraint checking."""
        # Could check constraints here if needed
        stamp_primitive(self.heightmap, feature_stamp, blending_mode)
```

### ✅ Solution 2: Pass Constraints to Position Resolution

**Modify `resolve_position()` to accept constraints:**

```python
def resolve_position(
    position_spec: Optional[Dict],
    existing_features: List[Dict] = None,
    constraints: Optional[WalkabilityConstraint] = None,  # NEW
    seed: int = 0
) -> Tuple[int, int]:
    """Resolve position, checking constraints if provided."""
    preferred_pos = _resolve_position_internal(position_spec, existing_features, seed)
    
    if constraints:
        # Check if position violates constraints
        # Find alternative if needed
        return constraints.find_placement_away_from_zones(...)
    
    return preferred_pos
```

**Modify `AddFeatureCommand.execute()`:**

```python
def execute(self, builder, feature_state, seed):
    # Get constraints from builder
    constraints = builder.walkability_constraints if hasattr(builder, 'walkability_constraints') else None
    
    # Resolve position with constraints
    pos = resolve_position(
        self.position, 
        existing_features, 
        constraints=constraints,  # NEW
        seed=position_seed
    )
```

### ✅ Solution 3: Two-Phase Action Execution

**Modify `execute_add_actions()` to support phases:**

```python
def execute_add_actions(actions, builder, feature_state, scene_graph, seed, command):
    # Phase 1: Execute walkability zone actions first
    zone_actions = [a for a in actions if a.get("type") in ["path", "flat_zone", "clearing"]]
    feature_actions = [a for a in actions if a.get("type") not in ["path", "flat_zone", "clearing"]]
    
    # Execute zones first
    for action_dict in zone_actions:
        command_obj = create_command_from_dict(action_dict)
        command_obj.execute(builder, feature_state, seed)
    
    # Then execute features (with constraints now active)
    for action_dict in feature_actions:
        command_obj = create_command_from_dict(action_dict)
        command_obj.execute(builder, feature_state, seed)
```

**OR:** Create separate command type:

```python
class ReserveWalkabilityZoneCommand(ActionCommand):
    """Command to reserve walkability zone (infrastructure)."""
    
    def execute(self, builder, feature_state, seed):
        # Reserve zone in builder
        builder.reserve_walkability_zone(
            self.zone_type,
            self.params,
            self.priority
        )
```

### ✅ Solution 4: Register Walkability Zones as Features (But Special)

**Option A: Special handling in FeatureRegistry:**

```python
# In FeatureRegistry
def generate_stamp(feature_type, feat, seed):
    # Special case for walkability zones
    if feature_type in ["path", "flat_zone", "clearing"]:
        # Generate flat stamp
        # Use MIN blending
        return generate_walkability_zone_stamp(feature_type, feat)
    
    # Normal features
    generator = cls._generators.get(feature_type)
    return generator.generate_stamp(feat, seed)
```

**Option B: Separate infrastructure registry:**

```python
class InfrastructureRegistry:
    """Registry for infrastructure (paths, zones)."""
    # Similar to FeatureRegistry but for infrastructure
```

## Recommended Approach

### Phase 1: Minimal Integration (Quick Win)

1. **Add constraint system to builder** (minimal change)
2. **Add `reserve_walkability_zone()` method** to builder
3. **Register walkability zones as special features** in FeatureRegistry
4. **Use MIN blending** for zones (ensures flatness)

**Limitations:**
- Still can't enforce constraints during position resolution
- Zones must be placed manually (programmatic)
- No automatic "away from zones" constraint

### Phase 2: Full Integration (Proper Solution)

1. **Add constraint system to builder** ✅
2. **Modify `resolve_position()` to accept constraints** ✅
3. **Modify `AddFeatureCommand.execute()` to pass constraints** ✅
4. **Two-phase action execution** (zones first, then features) ✅
5. **Semantic parser recognizes walkability commands** ✅

**Benefits:**
- Full constraint enforcement
- Natural language commands work
- Automatic position adjustment

## Conclusion

The walkability zone system I designed is **architecturally sound** but **doesn't fit the current execution flow**. The main issues are:

1. **Position resolution happens too early** (before constraints are checked)
2. **No two-phase system** (can't reserve zones first, then place features)
3. **Builder is passive** (doesn't validate or enforce constraints)
4. **No constraint system in builder** (no way to track reserved zones)

To properly integrate, we need to:
- Add constraint system to builder
- Modify position resolution to check constraints
- Support two-phase execution (zones first, then features)
- Or: Use programmatic API only (skip natural language for now)

