# Semantic Parser: Parameter Selection & Terrain Visibility Analysis

**Date:** October 31, 2025  
**Status:** ✅ **Analysis Complete**

---

## 🔍 Question: Can the LLM Choose Arguments?

### **Current State: LIMITED**

The semantic parser **CANNOT** currently choose specific primitive parameters (like `width`, `height`, `steepness` for ridges) because:

1. **JSON Schema Output Only:**
   - The LLM outputs actions in a simplified JSON format:
   ```json
   {
     "actions": [{
       "kind": "add",
       "type": "ridge",
       "count": 1,
       "position": {"region": "center"},
       "modifiers": {"taller": false, "wider": false}
     }]
   }
   ```

2. **No Parameter Fields:**
   - The output schema doesn't include primitive-specific parameters
   - Parameters like `width`, `height`, `steepness` are handled by `_create_feature()` defaults
   - Only high-level modifiers (`taller`, `wider`, `deeper`) are supported

3. **Tool Registry Visibility:**
   - ✅ The LLM **SEES** all available tools and their parameters
   - ✅ It knows `add_ridge` has: `start`, `end`, `width`, `height`, `steepness`
   - ❌ But it **CANNOT** specify these in the JSON output

---

## 👁️ Terrain Visibility: What the LLM Sees

### **1. Scene Graph Context (Rich Semantic Info)**

The LLM receives:

```
=== CURRENT SCENE CONTEXT ===

Feature Inventory:
  - mountain: 3
  - valley: 2
  - ridge: 1

Spatial Layout:
  - left: 2 features
  - center: 3 features
  - right: 1 feature

Semantic Entities:
  - "the dunes": 2 features
  - "two mountains": 2 features
  - "the valley": 1 feature

SEMANTIC ENTITIES (Detailed):
  • "the dunes"
    - Entity ID: dunes_1
    - Feature IDs: [1, 2]
    - Feature Count: 2
    - Keywords: dune, dunes, sand, desert
    - Description: Rolling sand dunes
    - Created from: 'create rolling dunes'
    - Can be referenced as: 'the dunes'
    - Also responds to keywords: dune, dunes, sand, desert

  • "two mountains"
    - Entity ID: mountain_2
    - Feature IDs: [4, 5]
    - Feature Count: 2
    - Keywords: mountain, mountains, peak, peaks
    - Created from: 'add two mountains'
    - Can be referenced as: 'two mountains'
```

### **2. Feature Inventory by Type**

```
FEATURE INVENTORY BY TYPE:
  - mountain: 3 features [4, 5, 6]
  - valley: 2 features [1, 2]
  - ridge: 1 feature [7]
```

### **3. Spatial Relationships**

The LLM can see:
- Entity positions (feature IDs)
- Spatial relationships (`BETWEEN`, `NEAR`, `LEFT_OF`, etc.)
- Reference resolution examples

### **4. Available Tools (MCP Registry)**

```
=== AVAILABLE TOOLS (MCP Registry) ===

PRIMITIVE FEATURES:
  - add_ridge: Add a ridge (linear elevated feature) to the terrain. Creates a raised line between two points.
    Parameters:
      - start: Start position (required)
      - end: End position (required)
      - width: Ridge width (default=20, min=10, max=40)
      - height: Maximum height (default=0.50, min=0.2, max=0.8)
      - steepness: Side steepness (default=0.8, min=0.3, max=1.0)
```

---

## ❌ What's Missing: Parameter Specification

### **Current Flow:**
1. User: `"add a ridge"`
2. LLM sees: Tool registry with `add_ridge` parameters
3. LLM outputs: `{"type": "ridge", "count": 1}` (no parameters)
4. System: Uses defaults from `_create_feature()`
5. Result: Ridge with default `width=20`, `height=0.50`, `steepness=0.8`

### **What We Need:**
1. User: `"add a ridge"`
2. LLM sees: Tool registry + scene context
3. LLM outputs: `{"type": "ridge", "count": 1, "parameters": {"width": 30, "height": 0.6}}`
4. System: Uses LLM-specified parameters
5. Result: Ridge with custom parameters

---

## 🎯 Current Parameter Handling

### **Defaults Applied:**
- **Ridge:** `width=20`, `height=0.50`, `steepness=0.8`
- **Volcano:** `base_radius=56`, `height=0.80`, `crater_radius=0.15`
- **Crater:** `radius=64`, `depth=0.55`, `rim_height=0.1`

### **Variation Engine:**
- `_create_feature()` applies subtle variation (±10-20%)
- Deterministic based on position and seed
- User cannot control this variation

### **Modifiers Supported:**
- ✅ `taller` / `height_percent`
- ✅ `wider` / `width_percent`
- ✅ `deeper` / `depth_percent`

**But these are applied AFTER creation, not during.**

---

## 🔧 Implementation Gap

### **To Enable Parameter Selection:**

1. **Update JSON Schema:**
   ```json
   {
     "actions": [{
       "kind": "add",
       "type": "ridge",
       "count": 1,
       "position": {...},
       "parameters": {  // NEW FIELD
         "width": 30,
         "height": 0.6,
         "steepness": 0.7
       }
     }]
   }
   ```

2. **Update `_create_feature()`:**
   - Check for `parameters` field in action
   - Override defaults with LLM-specified values
   - Still apply variation if no explicit parameters

3. **Update System Prompt:**
   - Tell LLM it CAN specify parameters
   - Show examples with parameter specification
   - Encourage intelligent parameter selection based on context

---

## 📊 Current Visibility Summary

### **What LLM Sees:**
✅ **Feature Inventory** - Counts by type  
✅ **Spatial Layout** - Distribution by region  
✅ **Semantic Entities** - Labels, keywords, feature IDs  
✅ **Tool Registry** - All available tools + parameters  
✅ **Reference Resolution** - How to resolve "the dunes"  
✅ **Spatial Relationships** - Between entities  
✅ **Feature IDs** - For modify/remove operations  

### **What LLM CANNOT See:**
❌ **Current Parameter Values** - Doesn't know existing ridge width  
❌ **Heightmap Data** - No visual/height information  
❌ **Spatial Coordinates** - Only regions, not exact positions  
❌ **Feature Details** - Only counts, not individual feature params  

### **What LLM CANNOT Control:**
❌ **Primitive Parameters** - Cannot specify `width`, `height`, `steepness`  
❌ **Exact Coordinates** - Only regions or explicit user coordinates  
❌ **Variation** - Cannot control variation engine  
❌ **Blending Modes** - Fixed per primitive type  

---

## 🚀 Recommendations

### **Option 1: Enable Parameter Selection (Recommended)**

**Pros:**
- LLM can intelligently choose parameters based on context
- More precise control over terrain generation
- Better compositional understanding

**Cons:**
- More complex JSON schema
- Need to validate parameters
- LLM might make poor choices

**Implementation:**
```python
# In parser.py - update output schema
{
  "actions": [{
    "kind": "add",
    "type": "ridge",
    "parameters": {
      "width": 30,      // Optional: LLM can specify
      "height": 0.6,    // Optional: LLM can specify
      "steepness": 0.7  // Optional: LLM can specify
    }
  }]
}

# In terrain.py - update _create_feature()
def _create_feature(ftype: str, cx: int, cy: int, modifiers: Dict, 
                    parameters: Optional[Dict] = None, seed: int) -> Dict:
    # If parameters provided, use them (override defaults)
    if parameters:
        return {**default_feature, **parameters}
    # Otherwise use defaults + variation
    ...
```

### **Option 2: Enhanced Natural Language Parsing**

**Pros:**
- Users can say "add a wide ridge" or "add a gentle ridge"
- LLM extracts intent and maps to parameters
- More intuitive for users

**Cons:**
- Need to map natural language to parameters
- Ambiguity in interpretation

**Implementation:**
```python
# Map language to parameters
"wide ridge" → width=35
"narrow ridge" → width=15
"gentle ridge" → steepness=0.4
"steep ridge" → steepness=0.9
"tall ridge" → height=0.7
"low ridge" → height=0.3
```

### **Option 3: Scene-Aware Parameter Selection**

**Pros:**
- LLM chooses parameters based on existing terrain
- More intelligent composition
- Better spatial awareness

**Cons:**
- Requires analyzing existing features
- More complex prompt engineering

**Implementation:**
```python
# In scene context, add:
"Existing Feature Parameters:
  - Ridge #1: width=20, height=0.5, steepness=0.8
  - Mountain #1: radius=56, height=0.75
  - Valley #1: radius=64, depth=0.55"

# LLM can then choose:
"Add a ridge matching the existing ridge style"
→ Use similar parameters
```

---

## 📝 Example: What LLM Currently Sees

```
=== CURRENT SCENE CONTEXT ===

Feature Inventory:
  - mountain: 2
  - ridge: 1

Spatial Layout:
  - left: 1 feature
  - center: 1 feature

Semantic Entities:
  - "two mountains": 2 features
  - "the ridge": 1 feature

=== AVAILABLE TOOLS (MCP Registry) ===

PRIMITIVE FEATURES:
  - add_ridge: Add a ridge (linear elevated feature) to the terrain. Creates a raised line between two points.
    Parameters:
      - start: Start position (required)
      - end: End position (required)
      - width: Ridge width (default=20, min=10, max=40)
      - height: Maximum height (default=0.50, min=0.2, max=0.8)
      - steepness: Side steepness (default=0.8, min=0.3, max=1.0)
```

**User Input:** `"add a ridge connecting the mountains"`

**LLM Output:**
```json
{
  "actions": [{
    "kind": "add",
    "type": "ridge",
    "count": 1,
    "position": {"region": "center"},
    "modifiers": {}
  }]
}
```

**System Creates:** Ridge with defaults (width=20, height=0.50, steepness=0.8)

---

## ✅ Summary

**Parameter Selection:** ❌ **NOT CURRENTLY SUPPORTED**  
- LLM sees tool parameters but cannot specify them
- System uses defaults + variation engine
- Only modifiers (`taller`, `wider`) work after creation

**Terrain Visibility:** ✅ **GOOD**  
- Feature inventory (counts by type)
- Spatial layout (region distribution)
- Semantic entities (labels, keywords, IDs)
- Tool registry (all tools + parameters)
- Reference resolution (how to resolve "the dunes")

**Recommendation:** Enable parameter selection for more intelligent terrain generation!


