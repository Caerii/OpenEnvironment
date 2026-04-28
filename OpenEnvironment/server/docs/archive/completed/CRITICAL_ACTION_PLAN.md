<!--
METADATA:
  File: CRITICAL_ACTION_PLAN.md
  Created: November 2025
  Last Modified: 2025-11-11
  Status: MOSTLY IMPLEMENTED - Core fixes verified in codebase
  Purpose: Prioritized action plan for critical architectural fixes
  Archive Date: 2025-11-11
-->

# Critical Action Plan: What Actually Makes Sense

## 📋 Document Purpose

This document was created as a **prioritized action plan** to address critical architectural issues in the terrain quality evaluation and refinement system. It identified the core problem: texture optimization is indirect (features → heightmap → texture), making refinement difficult.

## ✅ Implementation Status

**All core fixes have been implemented** (as of Nov 2025):

1. ✅ **Fix #1: Context Rubric Uses Archetype** - IMPLEMENTED
   - Location: `server/semantic/rubric_evolution.py:371-469`
   - Usage: `server/semantic/tools/quality_tools.py:186-191`
   - Status: Working - Archetype + goals preferred over command string

2. ✅ **Fix #2: Refinement Warning Priority** - IMPLEMENTED
   - Location: `server/semantic/tools/quality_tools.py:329-336`
   - Status: Working - Texture warnings processed first

3. ✅ **Fix #3: Archetype Matching** - IMPLEMENTED
   - Location: `server/semantic/narrative/archetypes.py:283-350`
   - Status: Working - Feature combinations properly matched

4. ✅ **Tool #1: Texture-to-Feature Mapping** - IMPLEMENTED
   - Location: `server/semantic/tools/quality_tools.py:922-1020`
   - Function: `analyze_texture_feature_relationship()`

5. ✅ **Tool #2: Parameter Modification** - IMPLEMENTED
   - Location: `server/semantic/tools/quality_tools.py:325-397`
   - Function: `modify_feature_parameters()`

## 🎯 The Core Insight (Still Valid)

**The fundamental problem:** We're trying to optimize texture quality by adjusting features, but texture is **derived from heightmap**, not directly from features. This creates an **indirect optimization problem** that's hard to solve.

**The solution:** We need a **bidirectional bridge**:
- **Forward:** Features → Terrain → Texture ✅ (works)
- **Backward:** Texture Issues → Feature Changes ✅ (now implemented!)

---

## 📝 Historical Content (Preserved for Reference)

### Phase 1: Critical Fixes

#### Fix #1: Context Rubric Uses Archetype (NOT Command String)

**Why Critical:**
- Wrong rubric → Wrong evaluation → Wrong refinement targets
- Currently: Gemini misinterprets command strings
- Should: Use structured archetype + goals data

**Status:** ✅ IMPLEMENTED - See `server/semantic/rubric_evolution.py` and `server/semantic/tools/quality_tools.py`

*Note: Code snippets below are from Nov 2025 planning phase. Actual implementation differs.*

---

#### Fix #2: Reorder Refinement Warning Priority

**Why Critical:**
- Texture warnings never trigger (extent matches first)
- Texture is the bottleneck (0.25-0.38 scores)
- Must check texture FIRST

**Status:** ✅ IMPLEMENTED - Texture warnings have highest priority in `refine_composition()`

---

#### Fix #3: Fix Archetype Matching (Feature Combinations)

**Why Critical:**
- "hills and valleys" → Wind Architect (wrong)
- Should be Water's Legacy
- Wrong archetype → Wrong features → Wrong narrative

**Status:** ✅ IMPLEMENTED - Feature combination matching added to `match_archetype_from_keywords()`

---

### Phase 2: Enable Texture Refinement

#### Tool #1: Texture-to-Feature Mapping

**Why Critical:**
- Need to know which features affect which texture regions
- Without this, can't target specific features for modification

**Status:** ✅ IMPLEMENTED - `analyze_texture_feature_relationship()` in `quality_tools.py`

*Note: Implementation details differ from planning document below.*

---

#### Tool #2: Modify Feature Parameters

**Why Critical:**
- Can't fix texture without modifying feature parameters
- Position changes don't affect texture significantly
- Need direct parameter control

**Status:** ✅ IMPLEMENTED - `modify_feature_parameters()` in `quality_tools.py`

---

## 🎯 What Makes Sense vs What Doesn't (Still Relevant)

### ✅ Makes Sense:
1. **Fix context rubric** - Uses wrong input, easy fix, high impact ✅ DONE
2. **Reorder refinement priority** - Texture is bottleneck, must check first ✅ DONE
3. **Fix archetype matching** - Wrong features = wrong everything ✅ DONE
4. **Add texture-to-feature mapping** - Need to understand relationships ✅ DONE
5. **Add parameter modification** - Need direct control ✅ DONE

### ❌ Doesn't Make Sense:
1. **Regenerating entire composition** - Too expensive, loses narrative coherence
2. **Adding more features** - Already have enough, need to modify existing ones
3. **Complex multi-agent loops** - Current system works, just needs better tools
4. **Redesigning texture generation** - Works fine, just need better refinement

---

## 💡 Key Insight (Still Valid)

**The system architecture is sound, but the refinement layer needed to operate at the parameter level.**

- **Before:** Refinement operated on **feature level** (positions, add/remove)
- **After:** Refinement operates on **parameter level** (radius, height, etc.) ✅

**The fix:** Added tools to bridge texture issues → parameter changes.

This was **much simpler** than redesigning the entire system, and addressed the root cause directly.

---

## 📊 Expected vs Actual Impact

### Expected (from planning):
- **After Phase 1:** Quality scores improve from 0.5-0.7 → 0.6-0.75
- **After Phase 2:** Quality scores improve from 0.6-0.75 → 0.75-0.85

### Actual:
- See test results in `server/logs/test_phase1_phase2_results.json`
- Quality evaluation and refinement system is functional
- Texture analysis and parameter modification tools are working

---

## ⚠️ Code Snippets Below Are Historical

The code snippets in the sections below are from the planning phase (Nov 2025) and may not match the current implementation. They are preserved for historical reference only.

**Always check the current codebase** for actual implementation:
- `server/semantic/tools/quality_tools.py` - Quality evaluation and refinement
- `server/semantic/rubric_evolution.py` - Context rubric generation
- `server/semantic/narrative/archetypes.py` - Archetype matching

---

*Original planning content preserved below for historical context*

---

## Original Implementation Plans (Historical Reference)

### Fix #1: Context Rubric Uses Archetype

*Original planning code snippet - see actual implementation in codebase*

### Fix #2: Reorder Refinement Warning Priority

*Original planning code snippet - see actual implementation in codebase*

### Fix #3: Fix Archetype Matching

*Original planning code snippet - see actual implementation in codebase*

### Tool #1: Texture-to-Feature Mapping

*Original planning code snippet - see actual implementation in `analyze_texture_feature_relationship()`*

### Tool #2: Modify Feature Parameters

*Original planning code snippet - see actual implementation in `modify_feature_parameters()`*

---

*End of historical content*
