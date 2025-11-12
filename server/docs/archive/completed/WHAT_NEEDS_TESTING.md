<!--
METADATA:
  File: WHAT_NEEDS_TESTING.md
  Created: November 2025
  Last Modified: 2025-11-11
  Status: See README.md for current status
  Purpose: AI-generated planning/analysis document
  Archive Date: 2025-11-11
-->


## 📋 Document Purpose

This document was created during active development to list areas that need testing.

## ⚠️ Status: See README.md for current status

# What Needs to be Tested - Complete Checklist

## ✅ **Fixed Issues**

1. ✅ **Import conflicts resolved** - `evaluation.py` vs `evaluation/` package conflict fixed
2. ✅ **Archetype matcher response parsing** - Fixed to handle different LLM client formats
3. ✅ **Bootstrap import** - Fixed logger issue in generation.py

## 🧪 **Critical Tests Needed**

### **1. Import Tests** ✅ **PARTIALLY WORKING**

**Status:** 4/7 tests passing (57%)

**What Works:**
- ✅ Config module imports
- ✅ State initializer imports  
- ✅ Feature types imports
- ✅ Warning types imports
- ✅ Archetype matcher imports

**What Needs Fixing:**
- ⚠️ Quality tools integration (import conflict resolved, but needs full test)
- ⚠️ Narrative pipeline integration (bootstrap import issue)

**Test File:** `server/tools/test_refactored_modules.py`

---

### **2. Semantic Archetype Matcher** ✅ **WORKING**

**Status:** ✅ **PASSING** - LLM matching works correctly!

**Test Results:**
- ✅ "create dramatic mountains" → Ancient Uplift
- ✅ "desert with dunes" → Wind Architect  
- ✅ "valley with hills" → Water's Legacy

**What's Verified:**
- LLM matching works with Cerebras API
- Fallback to keywords works
- Returns valid archetypes

**Still Need:**
- [ ] Test with Gemini API
- [ ] Test with Together API
- [ ] Test error handling (API failures)
- [ ] Test response parsing edge cases

---

### **3. Configuration Module** ✅ **WORKING**

**Status:** ✅ **PASSING**

**What's Verified:**
- ✅ All constants accessible
- ✅ `get_parameter_modification()` works
- ✅ Feature type helpers work

**Still Need:**
- [ ] Test all config values are used correctly
- [ ] Test adaptive parameter calculations with different feature sizes
- [ ] Test texture contribution mappings

---

### **4. State Initializer** ✅ **WORKING**

**Status:** ✅ **PASSING**

**What's Verified:**
- ✅ Initialize with None works
- ✅ Initialize with existing state works
- ✅ Validation works

**Still Need:**
- [ ] Test edge cases (empty dict, None values)
- [ ] Test `ensure_next_id()` calculates correctly
- [ ] Test doesn't overwrite important values

---

### **5. Structured Warnings** ✅ **WORKING**

**Status:** ✅ **PASSING**

**What's Verified:**
- ✅ `classify_warning()` works
- ✅ Structured warnings work
- ✅ `is_texture_warning()` works

**Still Need:**
- [ ] Test all warning categories are classified correctly
- [ ] Test backward compatibility with string warnings
- [ ] Test refinement uses categories correctly

---

### **6. Quality Tools Refactoring** ⚠️ **NEEDS FULL TEST**

**Status:** Import fixed, but needs end-to-end test

**What Needs Testing:**
- [ ] `evaluate_terrain_quality()` uses config constants
- [ ] `refine_composition()` uses structured warnings
- [ ] `analyze_texture_feature_relationship()` uses adaptive thresholds
- [ ] `modify_feature_parameters()` uses adaptive modifications
- [ ] `_render_terrain_preview()` uses StateInitializer
- [ ] No regressions in quality scores
- [ ] Refinement still improves quality

**Test File:** `server/tools/test_quality_tools_refactored.py` (needs creation)

---

### **7. Narrative Pipeline Integration** ⚠️ **NEEDS FIX**

**Status:** Bootstrap import issue

**What Needs Testing:**
- [ ] `develop_terrain_narrative()` uses semantic matcher
- [ ] Fallback to keywords works
- [ ] End-to-end narrative generation works
- [ ] Quality hasn't degraded
- [ ] Handles LLM failures gracefully

**Test File:** `server/tools/test_narrative_semantic.py` (needs creation)

---

### **8. Adaptive Parameter Modifications** ⚠️ **NEEDS TEST**

**Status:** Code implemented, needs verification

**What Needs Testing:**
- [ ] Modifications scale with feature size (percentage-based)
- [ ] Min/max clamping works
- [ ] Different textures get different strategies
- [ ] Improvements in refinement quality
- [ ] Better than fixed increments

**Test File:** `server/tools/test_adaptive_parameters.py` (needs creation)

---

### **9. End-to-End Integration** ⚠️ **CRITICAL**

**Status:** Needs comprehensive test

**What Needs Testing:**
- [ ] Full ReAct workflow with new modules
- [ ] Narrative → quality evaluation → refinement
- [ ] Quality improvements over iterations
- [ ] No regressions in existing functionality
- [ ] Error handling throughout
- [ ] Performance (no significant slowdowns)

**Test File:** `server/tools/test_integration_refactored.py` (needs creation)

---

### **10. Regression Tests** ⚠️ **CRITICAL**

**Status:** Need to verify existing tests still pass

**What Needs Testing:**
- [ ] Run existing test suite
- [ ] Verify no breaking changes
- [ ] Check quality scores haven't degraded
- [ ] Verify refinement still works

**Command:**
```bash
cd server
uv run python -m pytest tests/ -v
```

---

## 🔍 **Specific Test Cases Needed**

### **Import Edge Cases:**
- [ ] Test when `evaluation/` package exists but `evaluation.py` module also exists
- [ ] Test import from different execution contexts
- [ ] Test relative vs absolute imports

### **Archetype Matcher Edge Cases:**
- [ ] Test with very short commands
- [ ] Test with ambiguous commands
- [ ] Test with commands that don't match any archetype
- [ ] Test LLM returns invalid archetype name
- [ ] Test LLM returns multiple words

### **Config Edge Cases:**
- [ ] Test with missing config values
- [ ] Test with extreme parameter values
- [ ] Test feature types not in mapping

### **State Initializer Edge Cases:**
- [ ] Test with partial state (some keys missing)
- [ ] Test with invalid state (wrong types)
- [ ] Test with very large state

### **Warning Types Edge Cases:**
- [ ] Test with empty warning list
- [ ] Test with malformed warnings
- [ ] Test with warnings in different languages (edge case)

---

## 📋 **Test Execution Plan**

### **Phase 1: Fix Remaining Import Issues** (15 min)
1. Fix narrative pipeline bootstrap import
2. Verify all imports work
3. Run import test suite

### **Phase 2: Unit Tests** (30 min)
1. Test each module independently
2. Test edge cases
3. Verify no regressions

### **Phase 3: Integration Tests** (45 min)
1. Test modules working together
2. Test full workflows
3. Verify quality improvements

### **Phase 4: Regression Tests** (30 min)
1. Run existing test suite
2. Compare quality scores
3. Verify no breaking changes

**Total Estimated Time:** ~2 hours

---

## 🚨 **Critical Issues to Address**

1. **Narrative Pipeline Bootstrap Import** - Needs fix for `server` module import
2. **Quality Tools Full Test** - Need end-to-end test with real terrain
3. **Integration Test** - Need full workflow test
4. **Regression Test** - Need to verify existing tests pass

---

## ✅ **What's Already Working**

1. ✅ **Semantic Archetype Matching** - LLM matching works perfectly!
2. ✅ **Config Module** - All constants accessible
3. ✅ **State Initializer** - Consistent initialization
4. ✅ **Structured Warnings** - Type-safe matching
5. ✅ **Feature Types** - Helpers work correctly

---

## 🎯 **Priority Order**

### **Must Test Before Production:**
1. ⚠️ **End-to-End Integration** - Full workflow test
2. ⚠️ **Regression Tests** - Verify no breakage
3. ⚠️ **Quality Tools** - Verify refactoring works
4. ⚠️ **Narrative Pipeline** - Fix bootstrap, test semantic matching

### **Should Test Soon:**
5. ✅ **Adaptive Parameters** - Verify improvements
6. ✅ **Edge Cases** - Robustness testing

---

## 📝 **Next Steps**

1. **Fix narrative pipeline bootstrap import** (5 min)
2. **Create comprehensive integration test** (30 min)
3. **Run regression test suite** (15 min)
4. **Test adaptive parameters** (20 min)
5. **Document test results** (10 min)

**Total:** ~80 minutes to complete all critical testing




