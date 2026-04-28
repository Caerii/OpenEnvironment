<!--
METADATA:
  File: ROOT_CAUSE_ANALYSIS.md
  Created: November 2025
  Last Modified: 2025-11-11
  Status: PARTIALLY OUTDATED - Core insights still valid, many issues addressed
  Purpose: Root cause analysis of architectural issues and disconnects
  Archive Date: 2025-11-11
-->

# Root Cause Analysis: Deep Architectural Issues

## 📋 Document Purpose

This document was created to identify the **root causes** of architectural problems in the terrain generation and quality evaluation system. It analyzed the disconnect between three layers: Narrative, Terrain Generation, and Quality Evaluation.

## ✅ Current Status

**Many issues have been addressed**, but the core architectural insights remain valid:

- ✅ **Texture-to-feature mapping** - IMPLEMENTED (`analyze_texture_feature_relationship`)
- ✅ **Parameter modification** - IMPLEMENTED (`modify_feature_parameters`)
- ✅ **Archetype matching** - IMPROVED (feature combinations)
- ✅ **Context rubric** - FIXED (uses archetype + goals)
- ⚠️ **Three-layer architecture** - Still valid insight, but communication improved

## 🎯 Core Insight (Still Valid)

The system operates in **three disconnected layers**:

1. **Narrative Layer** (Aesthetic Intent) - Command → Archetype → Story → Feature Types
2. **Terrain Generation Layer** (Geometry) - Features → Heightmap Stamps → Heightmap + Splatmap
3. **Quality Evaluation Layer** (Visual Assessment) - Heightmap + Splatmap → Metrics → Scores

**The Critical Gap:** These layers didn't communicate effectively, but tools have been added to bridge the gap.

---

## 🔴 Root Cause #1: Texture Generation is Indirect (Addressed)

### The Problem

Texture is **derived from heightmap slope/height** after all features are applied, not directly from features. Most features don't generate texture masks - only `dunes` and `cliffs` have direct texture control.

**Why Refinement Failed:**
- Refinement adjusted positions → didn't change heightmap significantly → didn't change texture
- Refinement added features → might help, but didn't modify existing feature texture contribution

### The Solution (Implemented)

✅ **Texture-to-feature mapping** - Understand which features affect which texture regions  
✅ **Parameter modification** - Direct control over feature parameters (radius, height) to affect texture

**Status:** Tools implemented in `server/semantic/tools/quality_tools.py`

---

## 🔴 Root Cause #2: Context Rubric Uses Wrong Input (Fixed)

### The Problem

Context rubric generation used **command string**, not **archetype + goals**. This caused:
- Wrong rubric → Wrong thresholds → Wrong evaluation → Wrong refinement targets
- Gemini had to guess context from text, not from structured data

### The Solution (Implemented)

✅ **Context rubric now uses archetype + goals** - Structured data preferred over command string  
✅ **Fallback to command** - Only if no narrative metadata available

**Status:** Fixed in `server/semantic/rubric_evolution.py` and `server/semantic/tools/quality_tools.py`

---

## 🔴 Root Cause #3: Archetype Matching is Keyword-Based (Improved)

### The Problem

Simple keyword matching caused wrong archetype selection:
- "hills and valleys" → Wind Architect (wrong)
- Should be Water's Legacy

### The Solution (Implemented)

✅ **Feature combination checking** - Strong signals override individual keywords  
✅ **Keyword weighting** - Important keywords weighted higher  
✅ **Primary/secondary feature matching** - Better scoring system

**Status:** Improved in `server/semantic/narrative/archetypes.py`

---

## 📝 Historical Analysis (Preserved for Reference)

### Evidence from Logs (Historical)

*Original analysis preserved below - these issues have been addressed*

### Proposed Solutions (Historical)

*Original solutions preserved below - many have been implemented*

---

## 💡 Key Takeaways

1. **Architecture insight still valid** - Three-layer separation is real, but bridges exist now
2. **Indirect texture problem addressed** - Tools now bridge texture issues → feature changes
3. **Context rubric fixed** - Uses structured data instead of command strings
4. **Archetype matching improved** - Feature combinations properly handled

---

*Original detailed analysis preserved below for historical context*

---

## Original Analysis (Historical Reference)

### Fundamental Architecture Disconnect

*Original three-layer analysis - still conceptually valid*

### Root Cause #1: Texture Generation is Indirect

*Original problem description - addressed via texture-to-feature mapping*

### Root Cause #2: Context Rubric Uses Wrong Input

*Original problem description - fixed via archetype-based rubric*

### Root Cause #3: Archetype Matching is Keyword-Based

*Original problem description - improved via combination matching*

---

*End of historical content*
