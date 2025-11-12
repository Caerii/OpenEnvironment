# Documentation Cleanup Analysis - November 2025

**Date:** November 11, 2025  
**Purpose:** Comprehensive analysis of all active docs vs actual implementation

---

## Files Requiring Updates/Archiving

### 1. **Integration Docs** - OUTDATED Parser Order

**Files:**
- `active/integration/PARSER_INTEGRATION_FIX.md`
- `active/integration/SEMANTIC_INTEGRATION_TESTS.md`

**Issue:** Claim SemanticParser is primary, but narrative pipeline is actually primary

**Actual Flow:**
```
1. Narrative Pipeline (run_narrative_pipeline) ← PRIMARY
2. SemanticParser ← FALLBACK  
3. CommandParser (regex) ← FINAL FALLBACK
```

**Action:** Archive with note about actual parser order

---

### 2. **Walkability Docs** - Implementation Status Mismatch

**Files:**
- `active/features/WALKABILITY_ZONE_ARCHITECTURE.md`
- `active/features/WALKABILITY_ZONE_ANALYSIS.md`
- `active/features/WALKABILITY_IMPLEMENTATION_SUMMARY.md`
- `active/features/WALKABILITY_HEURISTICS.md`

**Issue:** Describe walkability as "proposed" but infrastructure is actually implemented

**Actual Status:**
- ✅ Primitives exist (flat_zone, path, clearing)
- ✅ Constraint system exists (WalkabilityConstraint)
- ✅ Builder integration exists
- ❌ Enforcement during placement NOT wired up
- ❌ Two-phase execution NOT implemented

**Action:** Update to reflect "infrastructure complete, enforcement pending"

---

### 3. **Architecture Docs** - Need Verification

**Files:**
- `active/architecture/ENCAPSULATION_DESIGN.md`
- `active/architecture/ARCHITECTURE_PRINCIPLES.md`

**Status:** Need to verify if design matches implementation

**Action:** Review and update if needed

---

### 4. **Performance Docs** - ACCURATE ✅

**Files:**
- `active/performance/OPTIMIZATION_INTEGRATION_COMPLETE.md`
- `active/performance/BOTTLENECK_FIXES_COMPLETE.md`
- `active/performance/OPTIMIZATION_SUMMARY.md`

**Status:** Accurately describe implemented optimizations

**Action:** Keep as-is

---

### 5. **Roadmap Docs** - Need Status Updates

**Files:**
- `active/roadmap/NEXT_STEPS_ROADMAP.md`
- `active/roadmap/FURTHER_IMPROVEMENTS_NEEDED.md`
- `active/roadmap/NEXT_STEPS_DETAILED.md`

**Issue:** May list items as "needed" that are actually done

**Action:** Review and update with actual status

---

## Summary of Actions Needed

1. ✅ Archive outdated integration docs (parser order)
2. ✅ Update walkability docs (implementation status)
3. ⚠️ Review architecture docs (verify accuracy)
4. ✅ Keep performance docs (accurate)
5. ⚠️ Update roadmap docs (status check)

