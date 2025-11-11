# Testing Checklist: What Needs to be Tested

## ✅ Completed Refactoring

1. ✅ Created `server/semantic/config.py` - Centralized configuration
2. ✅ Created `server/semantic/state/initializer.py` - State initialization
3. ✅ Created `server/semantic/features/types.py` - Feature type constants
4. ✅ Created `server/semantic/evaluation/warning_types.py` - Structured warnings
5. ✅ Created `server/semantic/narrative/archetype_matcher.py` - LLM-based matching
6. ✅ Updated `server/semantic/tools/quality_tools.py` - Uses all new modules
7. ✅ Updated `server/semantic/narrative/narrative_dev.py` - Uses semantic matcher
8. ✅ Updated `server/semantic/narrative/generation.py` - Uses config
9. ✅ Restored `server/semantic/prompts/react_system_prompt.txt` - Full workflows

## 🧪 Critical Tests Needed

### **1. Import Tests** ⚠️ **CRITICAL**

**Issue:** New modules may have import errors

**Tests Needed:**
- [ ] Test all imports in `quality_tools.py` work correctly
- [ ] Test `archetype_matcher.py` imports work
- [ ] Test config module imports from engine.config
- [ ] Test state initializer imports
- [ ] Test feature types imports
- [ ] Test warning types imports

**Test File:** `server/tools/test_imports.py`

---

### **2. Semantic Archetype Matcher** ⚠️ **CRITICAL**

**Issue:** New LLM-based matching needs verification

**Tests Needed:**
- [ ] Test LLM matching works (with API key)
- [ ] Test fallback to keywords when LLM unavailable
- [ ] Test handles synonyms ("ravine" → "valley")
- [ ] Test handles context ("mountain valley" vs "desert valley")
- [ ] Test returns valid archetype
- [ ] Test error handling (API failures)

**Test File:** `server/tools/test_archetype_matcher.py`

---

### **3. Configuration Module** ⚠️ **HIGH PRIORITY**

**Issue:** All magic numbers moved to config - need to verify usage

**Tests Needed:**
- [ ] Test all config constants are accessible
- [ ] Test `get_parameter_modification()` works correctly
- [ ] Test adaptive parameter calculations
- [ ] Test feature type helpers (`is_rock_feature()`, etc.)
- [ ] Test texture contribution mappings

**Test File:** `server/tools/test_config_module.py`

---

### **4. State Initializer** ⚠️ **HIGH PRIORITY**

**Issue:** State initialization now centralized - need to verify consistency

**Tests Needed:**
- [ ] Test `StateInitializer.initialize()` with None
- [ ] Test `StateInitializer.initialize()` with existing state
- [ ] Test `StateInitializer.validate()` works
- [ ] Test ensures all required keys
- [ ] Test doesn't overwrite existing values incorrectly

**Test File:** `server/tools/test_state_initializer.py`

---

### **5. Structured Warnings** ⚠️ **HIGH PRIORITY**

**Issue:** Warning matching changed from strings to categories

**Tests Needed:**
- [ ] Test `classify_warning()` correctly categorizes warnings
- [ ] Test `QualityWarning.is_texture_warning()` works
- [ ] Test backward compatibility (string warnings)
- [ ] Test refinement uses categories correctly
- [ ] Test all warning categories are handled

**Test File:** `server/tools/test_warning_types.py`

---

### **6. Quality Tools Refactoring** ⚠️ **CRITICAL**

**Issue:** Major refactoring - need to verify no regressions

**Tests Needed:**
- [ ] Test `evaluate_terrain_quality()` still works
- [ ] Test `refine_composition()` uses structured warnings
- [ ] Test `analyze_texture_feature_relationship()` uses config thresholds
- [ ] Test `modify_feature_parameters()` uses adaptive modifications
- [ ] Test `_render_terrain_preview()` uses StateInitializer
- [ ] Test all hard-coded values replaced with config

**Test File:** `server/tools/test_quality_tools_refactored.py`

---

### **7. Narrative Pipeline Integration** ⚠️ **CRITICAL**

**Issue:** Narrative pipeline now uses semantic matching

**Tests Needed:**
- [ ] Test `develop_terrain_narrative()` uses semantic matcher
- [ ] Test fallback to keywords works
- [ ] Test narrative generation still works end-to-end
- [ ] Test quality hasn't degraded
- [ ] Test handles LLM failures gracefully

**Test File:** `server/tools/test_narrative_semantic.py`

---

### **8. Adaptive Parameter Modifications** ⚠️ **HIGH PRIORITY**

**Issue:** Parameter changes now adaptive - need to verify effectiveness

**Tests Needed:**
- [ ] Test modifications scale with feature size
- [ ] Test percentage-based changes work
- [ ] Test min/max clamping works
- [ ] Test different textures get different strategies
- [ ] Test improvements in refinement quality

**Test File:** `server/tools/test_adaptive_parameters.py`

---

### **9. End-to-End Integration** ⚠️ **CRITICAL**

**Issue:** All components integrated - need full workflow test

**Tests Needed:**
- [ ] Test full ReAct workflow with new modules
- [ ] Test narrative → quality evaluation → refinement
- [ ] Test quality improvements over iterations
- [ ] Test no regressions in existing functionality
- [ ] Test error handling throughout

**Test File:** `server/tools/test_integration_refactored.py`

---

### **10. Edge Cases** ⚠️ **MEDIUM PRIORITY**

**Tests Needed:**
- [ ] Test empty scene state
- [ ] Test missing API keys (LLM fallback)
- [ ] Test invalid feature types
- [ ] Test malformed warnings
- [ ] Test extreme parameter values
- [ ] Test concurrent requests

**Test File:** `server/tools/test_edge_cases.py`

---

## 🔍 Verification Checklist

### **Code Quality:**
- [ ] No linter errors
- [ ] All imports resolve correctly
- [ ] No circular dependencies
- [ ] Type hints where appropriate

### **Functionality:**
- [ ] All existing tests still pass
- [ ] No regressions in quality scores
- [ ] Refinement still improves quality
- [ ] Narrative pipeline still works

### **Performance:**
- [ ] No significant slowdowns
- [ ] LLM calls are efficient
- [ ] Config lookups are fast

---

## 📋 Test Execution Order

1. **Import Tests** (5 min) - Verify everything imports
2. **Unit Tests** (15 min) - Test each module independently
3. **Integration Tests** (20 min) - Test modules working together
4. **End-to-End Tests** (30 min) - Test full workflows
5. **Regression Tests** (15 min) - Verify no breakage

**Total Estimated Time:** ~85 minutes

---

## 🚨 Critical Issues to Watch For

1. **Import Errors** - New modules may not be in Python path
2. **LLM API Failures** - Semantic matcher needs graceful fallback
3. **Config Access** - Ensure all config constants are accessible
4. **State Consistency** - StateInitializer must work everywhere
5. **Warning Compatibility** - Must handle both string and structured warnings

---

## 📝 Test Files to Create

1. `server/tools/test_imports.py` - Import verification
2. `server/tools/test_archetype_matcher.py` - Semantic matching
3. `server/tools/test_config_module.py` - Configuration
4. `server/tools/test_state_initializer.py` - State management
5. `server/tools/test_warning_types.py` - Structured warnings
6. `server/tools/test_quality_tools_refactored.py` - Quality tools
7. `server/tools/test_narrative_semantic.py` - Narrative pipeline
8. `server/tools/test_adaptive_parameters.py` - Adaptive modifications
9. `server/tools/test_integration_refactored.py` - Full integration
10. `server/tools/test_edge_cases.py` - Edge cases

---

## 🎯 Priority Order

### **Must Test Before Production:**
1. ✅ Import tests
2. ✅ Quality tools refactoring
3. ✅ Narrative pipeline integration
4. ✅ End-to-end integration

### **Should Test Soon:**
5. ✅ Semantic archetype matcher
6. ✅ Configuration module
7. ✅ State initializer
8. ✅ Structured warnings

### **Nice to Have:**
9. ✅ Adaptive parameters
10. ✅ Edge cases

