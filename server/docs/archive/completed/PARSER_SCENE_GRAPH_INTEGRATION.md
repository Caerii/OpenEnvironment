# Enhanced Semantic Parser: Structured Scene Graph Context

**Date:** October 31, 2025  
**Status:** ✅ Implemented  
**Impact:** LLM now has rich, structured metadata about the scene

---

## 🎯 What Was Enhanced

### **Problem Identified:**
The semantic parser was receiving basic scene state but not leveraging the structured scene graph metadata. The LLM couldn't easily see:
- Which semantic entities exist
- What "the dunes" refers to (feature IDs)
- Entity relationships and metadata
- How to resolve references intelligently

### **Solution Implemented:**
Enhanced `SemanticParser` to generate **structured scene graph context** that provides:
- ✅ Semantic entities with full metadata
- ✅ Feature ID mappings
- ✅ Keywords and labels
- ✅ Reference resolution instructions
- ✅ Quick lookup tables

---

## 🔧 Implementation Details

### **New Method: `_generate_scene_graph_context()`**

**Location:** `server/semantic/parser.py`

**What It Does:**
1. Loads scene graph from state (`semantic_scene`)
2. Extracts all semantic entities
3. Formats them with structured metadata
4. Provides reference resolution instructions
5. Creates quick lookup tables

**Output Format:**
```
=== SEMANTIC SCENE GRAPH (Structured Context) ===

GROUP ENTITIES (1):
  • the dunes
    - Entity ID: dunes_1
    - Feature IDs: [1, 2, 3]
    - Feature Count: 3
    - Keywords: dunes, desert, sandy
    - Description: Rolling sand dunes
    - Created from: 'create a desert with rolling dunes'
    - Can be referenced as: 'the dunes'
    - Also responds to keywords: dunes, desert, sandy

QUICK REFERENCE MAP:
  'the dunes' or keywords: dunes, desert, sandy → Feature IDs: [1, 2, 3]
  'two mountains' or keywords: mountain, peak → Feature IDs: [4, 5]

FEATURE INVENTORY BY TYPE:
  - dunes: 3 features [1, 2, 3]
  - mountain: 2 features [4, 5]

REFERENCE RESOLUTION INSTRUCTIONS:
When user says:
  - "the dunes" → Use entity "the dunes" → Feature IDs: [lookup above]
  - "make the mountains taller" → Find entity with label/keyword "mountains"
  - "last mountain" → Use ordinal resolution (most recent mountain feature)
```

---

## 📊 What the LLM Now Sees

### **Before Enhancement:**
```python
# Basic scene context
"Feature Inventory:
  - mountain: 2
  - dunes: 1

Spatial Layout:
  - left: 1 features
  - center: 1 features"
```

**LLM doesn't know:**
- ❌ What "the dunes" refers to
- ❌ Which feature IDs belong to which entity
- ❌ How to resolve references

### **After Enhancement:**
```python
# Structured scene graph context
"GROUP ENTITIES (1):
  • the dunes
    - Entity ID: dunes_1
    - Feature IDs: [1, 2, 3]
    - Keywords: dunes, desert, sandy
    - Can be referenced as: 'the dunes'

QUICK REFERENCE MAP:
  'the dunes' → Feature IDs: [1, 2, 3]
  'two mountains' → Feature IDs: [4, 5]

REFERENCE RESOLUTION INSTRUCTIONS:
  - 'the dunes' → Use entity → Feature IDs: [1, 2, 3]"
```

**LLM now knows:**
- ✅ Exact feature IDs for each entity
- ✅ How to resolve "the dunes" → [1, 2, 3]
- ✅ Keywords that match entities
- ✅ Structured metadata for decision-making

---

## 🎯 New Capabilities

### **1. Structured Entity Metadata**

The LLM sees entities with:
- **Labels:** "the dunes", "two mountains"
- **Feature IDs:** Direct mapping [1, 2, 3]
- **Keywords:** Alternative ways to reference
- **Descriptions:** Context about what it is
- **User Intent:** Original command that created it

### **2. Quick Reference Map**

One-line lookup table:
```
'the dunes' → Feature IDs: [1, 2, 3]
'two mountains' → Feature IDs: [4, 5]
```

### **3. Reference Resolution Instructions**

Clear guidance on how to resolve references:
- "the [entity]" → Use entity's feature_refs
- "[ordinal] [type]" → Use ordinal resolution
- "[type]" → Use all features of that type

### **4. Optional `target_feature_ids` Output**

LLM can optionally include resolved feature IDs:
```json
{
  "kind": "modify",
  "type": "dunes",
  "target_feature_ids": [1, 2, 3],  // LLM resolved "the dunes"
  "modifiers": {"taller": true}
}
```

**Benefits:**
- System can use pre-resolved IDs (faster)
- Fallback to reference resolver if not provided
- Clearer intent from LLM

---

## 🔄 Integration Flow

```
User Command: "make the dunes taller"
    ↓
Parser receives scene_state with semantic_scene
    ↓
_generate_scene_graph_context() extracts:
  - Entity "the dunes" → Feature IDs [1, 2, 3]
  - Keywords: dunes, desert, sandy
  - Metadata
    ↓
LLM sees structured context:
  "QUICK REFERENCE MAP:
   'the dunes' → Feature IDs: [1, 2, 3]"
    ↓
LLM can optionally include:
  {"target_feature_ids": [1, 2, 3]}
    ↓
System uses target_feature_ids OR falls back to resolver
    ↓
Modifies correct features ✅
```

---

## 📈 Benefits

### **For LLM:**
- ✅ **Rich Context:** Sees full semantic structure
- ✅ **Clear Mapping:** Knows what "the dunes" means
- ✅ **Better Decisions:** Can resolve references intelligently
- ✅ **Optional Pre-resolution:** Can include feature IDs directly

### **For System:**
- ✅ **Faster Execution:** Pre-resolved IDs skip resolver step
- ✅ **Better Accuracy:** LLM makes informed decisions
- ✅ **Fallback Support:** Resolver still works if LLM doesn't provide IDs
- ✅ **Structured Data:** Easy to parse and use

### **For Users:**
- ✅ **Natural References:** "the dunes" just works
- ✅ **Context-Aware:** System understands scene
- ✅ **Intelligent Parsing:** LLM makes smart decisions

---

## 🎯 Example: What LLM Sees

### **User Command:** "make the dunes taller"

### **Scene Graph Context Provided:**
```
=== SEMANTIC SCENE GRAPH (Structured Context) ===

GROUP ENTITIES (1):
  • the dunes
    - Entity ID: dunes_1
    - Feature IDs: [1, 2, 3]
    - Feature Count: 3
    - Keywords: dunes, desert, sandy
    - Description: Rolling sand dunes
    - Created from: 'create a desert with rolling dunes'
    - Can be referenced as: 'the dunes'
    - Also responds to keywords: dunes, desert, sandy

QUICK REFERENCE MAP:
  'the dunes' or keywords: dunes, desert, sandy → Feature IDs: [1, 2, 3]

REFERENCE RESOLUTION INSTRUCTIONS:
When user says:
  - "the dunes" → Use entity "the dunes" → Feature IDs: [1, 2, 3]
```

### **LLM Output (Option 1 - With Pre-resolution):**
```json
{
  "actions": [{
    "kind": "modify",
    "type": "dunes",
    "target_feature_ids": [1, 2, 3],
    "modifiers": {"taller": true}
  }]
}
```

### **LLM Output (Option 2 - Without Pre-resolution):**
```json
{
  "actions": [{
    "kind": "modify",
    "type": "dunes",
    "modifiers": {"taller": true}
  }]
}
```
*(System resolves "the dunes" → [1, 2, 3] via ReferenceResolver)*

**Both work!** Option 1 is faster, Option 2 is more flexible.

---

## 📊 Code Changes

### **File:** `server/semantic/parser.py`

**Changes:**
1. ✅ Added `_generate_scene_graph_context()` method (120 lines)
2. ✅ Enhanced `_build_system_prompt()` to include scene graph context
3. ✅ Added reference resolution instructions
4. ✅ Added examples with scene graph context
5. ✅ Updated output format to include `target_feature_ids`
6. ✅ Enhanced normalization to handle `target_feature_ids`

**Total:** ~150 lines added/modified

---

## 🚀 Next Steps

### **Phase 2.6: Integration**
Update `terrain.py` and `commands.py` to:
1. Use `target_feature_ids` if provided by LLM
2. Fall back to `ReferenceResolver` if not provided
3. Integrate scene graph creation/updates

**Example:**
```python
# In commands.py ModifyFeatureCommand:
if action.get("target_feature_ids"):
    # Use pre-resolved IDs from LLM
    target_ids = action["target_feature_ids"]
else:
    # Fall back to resolver
    resolver = ReferenceResolver(scene_graph)
    target_ids = resolver.resolve(action.get("target", ""))
```

---

## ✅ Success Criteria Met

- [x] Structured scene graph context generated
- [x] LLM sees semantic entities with metadata
- [x] Feature ID mappings provided
- [x] Reference resolution instructions included
- [x] Optional `target_feature_ids` support
- [x] Backward compatible (works without scene graph)
- [x] Clear, structured format for LLM

---

## 🎉 Impact

**Before:** LLM parsed commands blindly, system resolved references separately

**After:** LLM sees structured scene metadata and can:
- ✅ Resolve references intelligently
- ✅ Understand semantic relationships
- ✅ Make context-aware decisions
- ✅ Optionally pre-resolve feature IDs

**This transforms the parser from "command interpreter" to "intelligent scene-aware agent"!** 🚀

---

## 📝 Summary

**What We Built:**
- Structured scene graph context generation
- Rich metadata formatting
- Reference resolution instructions
- Optional pre-resolution support

**What This Enables:**
- LLM understands scene structure
- References can be resolved intelligently
- Better parsing accuracy
- Context-aware decision making

**The semantic parser is now truly scene-aware!** ✅

