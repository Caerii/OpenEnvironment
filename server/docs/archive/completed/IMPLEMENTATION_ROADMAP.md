# Implementation Roadmap - Semantic Terrain System

## Current State Summary

### ✅ Completed
- **Modular architecture** - Organized into `primitives/`, `engine/`, `semantic/` folders
- **Basic features** - Mountains, hills, valleys, dunes (4/11+ required)
- **LLM parser** - Cerebras/Qwen-3-Coder integration with structured JSON output
- **State management** - FeatureState class with ID tracking
- **Spatial resolver** - Position resolution utilities
- **Blending engine** - Multiple blending modes (MAX, SUBTRACT, ADD, WEIGHTED, etc.)
- **Splatmap generation** - 4-channel RGBA texture blending

### ⚠️ Partial/Incomplete
- **Feature tracking** - Has IDs but ordinal support not fully integrated
- **Semantic parser** - Only knows 4 feature types (needs expansion)
- **Relative positioning** - Infrastructure exists but not implemented
- **Feature primitives** - Only 4 implemented (need 7+ more)

### ❌ Missing
- **Canyons, plateaus, cliffs, mesas, slopes, glaciers, spurs** - No implementations
- **Ordinal feature selection** - "second mountain" not working
- **Relative positioning** - "next to mountain", "between hills"
- **Scattered distribution** - "scattered across terrain"
- **Biome variants** - Only desert base
- **Erosion simulation** - Not implemented
- **Metadata export** - No JSON with feature list/timestamps

---

## Phase 1: Core Infrastructure (✅ DONE)
**Status:** Complete

- [x] Modular folder structure
- [x] Primitives extracted (mountains, valleys, dunes, base)
- [x] Engine extracted (stamping, blending, splatmap, spatial)
- [x] Semantic layer (parser, state_manager, spatial_resolver)
- [x] Orchestrator refactored

---

## Phase 2: Expand Feature Vocabulary (HIGH PRIORITY)
**Goal:** Add remaining terrain features so parser can execute them

### 2.1 Add Missing Primitives (3-4 days)

**Priority Order:**
1. **Canyons** (`primitives/valleys.py` - already scaffolded)
   - Linear cuts with depth falloff
   - Polyline-based stamping
   - **Complexity:** Medium

2. **Plateaus** (`primitives/mountains.py` - already scaffolded)
   - Flat elevated areas with steep edges
   - Rectangular stamps with falloff
   - **Complexity:** Medium

3. **Mesas** (`primitives/mountains.py` - already scaffolded)
   - Flat-topped hills
   - Circular base with flat top
   - **Complexity:** Easy

4. **Cliffs** (`primitives/cliffs.py` - NEW)
   - Steep vertical drops
   - Edge detection + height cutoff
   - **Complexity:** Medium

5. **Slopes** (`primitives/slopes.py` - NEW)
   - Gradual inclines
   - Directional height gradient
   - **Complexity:** Easy

### 2.2 Update Execution Engine (1 day)
- Add feature handlers in `terrain.py` → `_create_feature()`
- Add reapply logic in `_reapply_feature()`
- Test each new feature type

### 2.3 Update Semantic Parser (1 day)
- Expand `parser.py` system prompt to include all feature types
- Update JSON schema to include new types
- Test LLM parsing for new features

**Estimated Time:** 5-6 days

---

## Phase 3: Enhanced Spatial Understanding (HIGH PRIORITY)
**Goal:** Support relative positioning and complex spatial commands

### 3.1 Relative Positioning (2-3 days)
- Implement `_resolve_relative()` in `spatial_resolver.py`
- Support: "next to mountain", "between hills", "along edge"
- Add feature relationship tracking

### 3.2 Scattered Distribution (1 day)
- Implement "scattered" keyword handling
- Poisson disk sampling for natural distribution
- Minimum distance enforcement

### 3.3 Ordinal Feature Selection (1 day)
- Extract ordinal from parser ("second", "third", etc.)
- Update `FeatureState.find_feature()` to handle ordinals
- Test "remove second mountain" commands

**Estimated Time:** 4-5 days

---

## Phase 4: Feature Memory & Modifications (MEDIUM PRIORITY)
**Goal:** Robust feature tracking for complex edits

### 4.1 Feature IDs Integration (1 day)
- Ensure all features get IDs on creation
- Update state serialization/deserialization
- Backward compatibility with existing state files

### 4.2 Ordinal Support (1 day)
- Parser extracts ordinals ("second mountain")
- State manager resolves ordinals to IDs
- Execution engine uses IDs for operations

### 4.3 Feature Relationships (2 days)
- Track spatial relationships ("between", "next to")
- Support dependent features ("valley between mountains")
- Relationship-aware positioning

**Estimated Time:** 4 days

---

## Phase 5: Advanced Features (STRETCH GOALS)
**Goal:** Professional-quality terrain generation

### 5.1 Erosion Simulation (3-5 days)
- Water flow simulation
- Thermal erosion
- Weathering patterns
- **Complexity:** High

### 5.2 Biome System (2-3 days)
- Multiple base biomes (forest, arctic, etc.)
- Biome-specific feature variations
- Biome transitions

### 5.3 Advanced Blending (2 days)
- Feature-aware blending (mountains merge naturally)
- Conflict resolution (overlapping features)
- Seam smoothing improvements

### 5.4 Metadata Export (1 day)
- JSON export with feature list, commands, timestamps
- Unity import metadata
- Generation statistics

**Estimated Time:** 8-11 days

---

## Phase 6: Testing & Polish (ONGOING)
**Goal:** Ensure robustness and handle edge cases

### 6.1 Test Suite
- Unit tests for each primitive
- Integration tests for command parsing
- Edge case handling (invalid coords, empty commands, etc.)

### 6.2 Performance Optimization
- Profile generation time
- Optimize hot paths (stamping, blending)
- Cache computations where possible

### 6.3 Documentation
- API documentation
- Feature reference guide
- Usage examples

**Estimated Time:** 3-5 days

---

## Recommended Implementation Order

### Week 1: Feature Expansion
1. **Day 1-2:** Implement canyons + plateaus + mesas
2. **Day 3:** Update parser + execution engine
3. **Day 4:** Test all features, fix bugs
4. **Day 5:** Implement cliffs + slopes

### Week 2: Spatial Intelligence
1. **Day 1-2:** Relative positioning ("next to", "between")
2. **Day 3:** Scattered distribution
3. **Day 4:** Ordinal feature selection
4. **Day 5:** Integration testing

### Week 3: Polish & Stretch Goals
1. **Day 1-2:** Biome system
2. **Day 3:** Metadata export
3. **Day 4:** Advanced blending
4. **Day 5:** Documentation + demo prep

---

## Critical Gaps to Address First

### 1. Parser Knows More Than Engine (CRITICAL)
**Problem:** LLM can parse "add canyon" but engine doesn't know what a canyon is.

**Solution:** 
- Add canyon/plateau/mesa implementations
- Update `_create_feature()` to handle new types
- Test end-to-end

### 2. Ordinal Support Missing (HIGH)
**Problem:** "Remove second mountain" doesn't work reliably.

**Solution:**
- Parser extracts ordinal from command
- State manager tracks features by type + order
- Execution uses ordinal → ID resolution

### 3. Relative Positioning Not Implemented (HIGH)
**Problem:** "Add valley between mountains" doesn't work.

**Solution:**
- Implement `_resolve_relative()` function
- Add feature relationship tracking
- Support "between", "next to", "along" keywords

---

## Success Metrics

### Minimum Viable (Week 1)
- ✅ 7+ terrain features implemented
- ✅ Parser can extract all feature types
- ✅ Engine can execute all feature types
- ✅ Basic spatial commands work

### Full Implementation (Week 2-3)
- ✅ Relative positioning works
- ✅ Ordinal selection works
- ✅ Scattered distribution works
- ✅ Complex compositions work

### Stretch Goals (Ongoing)
- ✅ Erosion simulation
- ✅ Multiple biomes
- ✅ Metadata export
- ✅ Performance <1 minute

---

## Next Immediate Steps

1. **Backup current terrain.py** (keep as `terrain_old.py`)
2. **Replace terrain.py with terrain_new.py** (after fixing imports)
3. **Test basic functionality** (ensure nothing broke)
4. **Implement canyons** (first missing feature)
5. **Update parser schema** (add canyons to feature types)
6. **Test end-to-end** ("add canyon" command)

---

## Notes

- **Backward Compatibility:** Old state files should still work (feature IDs auto-assigned)
- **Gradual Migration:** Can implement features incrementally
- **Testing:** Add unit tests as you implement each feature
- **Documentation:** Update README as features are added

