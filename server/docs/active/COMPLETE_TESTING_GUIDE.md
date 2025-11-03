# Complete Testing Guide: Primitives & Prompts

**Date:** October 31, 2025  
**Status:** ✅ **Complete Reference**

---

## 🎯 Available Primitives (9 Types)

### **1. Mountains** (`mountain`)
- **Description:** Tall, peaked elevations with Gaussian falloff
- **Parameters:** height, radius, steepness
- **Default:** height=0.75, radius=56

### **2. Hills** (`hill`)
- **Description:** Gentler, lower elevations than mountains
- **Parameters:** height, radius
- **Default:** height=0.45, radius=42

### **3. Valleys** (`valley`)
- **Description:** Bowl-shaped depressions (negative elevation)
- **Parameters:** depth, radius
- **Default:** depth=0.55, radius=64

### **4. Dunes** (`dunes`)
- **Description:** Rolling sand dunes with wavelike patterns
- **Parameters:** amplitude, frequency, angle (wind direction)
- **Default:** amp=0.08, freq=18.0, angle=20.0
- **Special:** Uses region-based placement (box coordinates)

### **5. Mesas** (`mesa`)
- **Description:** Flat-topped hills with steep sides
- **Parameters:** height, radius, flatness
- **Default:** height=0.65, radius=56, flatness=0.3

### **6. Plateaus** (`plateau`)
- **Description:** Large flat elevated areas (rectangular)
- **Parameters:** width, length, height, orientation
- **Default:** width=80, length=120, height=0.50, orientation=0.0

### **7. Cliffs** (`cliff`)
- **Description:** Steep vertical or near-vertical elevation changes
- **Parameters:** length, height, orientation, steepness
- **Default:** length=80, height=0.55, orientation=0.0, steepness=0.9

### **8. Canyons** (`canyon`)
- **Description:** Deep linear valleys carved between two points
- **Parameters:** start, end, width, depth, falloff
- **Default:** width=12, depth=0.60, falloff=0.5

### **9. Slopes** (`slope`)
- **Description:** Gradual directional inclines
- **Parameters:** start, end, width, height, falloff (or radial: position, radius, direction, steepness)
- **Default:** height=0.35, radius=60

---

## 📝 Prompt Patterns & Examples

### **Basic Add Commands**

#### **Single Feature:**
- `"add a mountain"`
- `"create a hill"`
- `"add a valley"`
- `"place a mesa"`
- `"add a plateau"`
- `"create a cliff"`
- `"add a canyon"`
- `"place a slope"`
- `"create rolling dunes"`

#### **Multiple Features (Count Extraction):**
- `"add two mountains"`
- `"create three hills"`
- `"add five valleys"`
- `"place a couple of mesas"`
- `"add several plateaus"`
- `"create a few cliffs"`
- `"add a dozen canyons"`
- `"place many slopes"`
- `"add one mountain, two hills, and three valleys"`

#### **With Positions (Regions):**
- `"add a mountain on the left"`
- `"create hills in the center"`
- `"add valleys on the right"`
- `"place mesas at the top"`
- `"add plateaus at the bottom"`
- `"create cliffs in the top-left"`
- `"add canyons in the bottom-right"`
- `"place slopes in the top-right"`

**Available Regions:**
- `"top-left"`, `"top"`, `"top-right"`
- `"left"`, `"center"`, `"right"`
- `"bottom-left"`, `"bottom"`, `"bottom-right"`

#### **With Explicit Coordinates:**
- `"add a mountain at (100, 200)"`
- `"create a hill at coordinates (300, 150)"`
- `"add a valley at position (250, 250)"`
- `"place a mesa at (150, 100)"`
- `"add a plateau centered at (256, 256)"`

#### **Compositional Commands (Multiple Features):**
- `"create a desert with rolling dunes and two mountains on the left"`
- `"add a mountain at (100, 100), a valley at (300, 300), and a hill at (200, 200)"`
- `"place three hills on the right, two valleys in the center, and one mountain on the left"`
- `"create rolling dunes across the center, add a mesa at (256, 256), and place cliffs along the northern edge"`

---

### **Modify Commands**

#### **Modify by Reference:**
- `"make the mountains taller"`
- `"make the valley deeper"`
- `"make the dunes wider"`
- `"make the last hill taller"`
- `"make the first mountain taller"`
- `"make the plateau wider"`

#### **Modify with Percentages:**
- `"make the mountain 50% taller"`
- `"make the valley 30% deeper"`
- `"make the hill 25% wider"`
- `"increase mountain height by 75%"`

#### **Modify with Explicit IDs (via Scene Graph):**
- `"make the dunes taller"` → Uses scene graph to find "the dunes" entity
- `"make the mountains wider"` → Uses scene graph to find "the mountains" entity
- `"make the valley deeper"` → Uses scene graph to find "the valley" entity

---

### **Remove Commands**

#### **Remove by Type:**
- `"remove the mountain"`
- `"delete the hills"`
- `"remove the valleys"`
- `"delete the dunes"`
- `"remove the mesas"`
- `"delete the plateaus"`
- `"remove the cliffs"`
- `"delete the canyons"`
- `"remove the slopes"`

#### **Remove by Reference:**
- `"remove the mountains"` → Uses scene graph to find entity
- `"delete the dunes"` → Uses scene graph to find entity
- `"remove the last mountain"`
- `"delete the first hill"`

#### **Remove Multiple:**
- `"remove two mountains"`
- `"delete three hills"`
- `"remove all valleys"`

---

### **Spatial Queries**

#### **Find Features:**
- `"find features near the dunes"`
- `"show features in the left half"`
- `"list features on the right"`
- `"query features in the center"`
- `"search for features near the mountains"`
- `"what features are near the valley"`

#### **Region Queries:**
- `"find features in the left region"`
- `"show features in the right half"`
- `"list features in the center area"`

---

## 🧪 Comprehensive Test Plan

### **Test Category 1: Basic Primitives**

#### **Mountains:**
```
✅ "add a mountain"
✅ "add two mountains"
✅ "add three mountains on the left"
✅ "add a mountain at (100, 200)"
✅ "add five mountains scattered"
```

#### **Hills:**
```
✅ "add a hill"
✅ "add three hills"
✅ "add hills in the center"
✅ "add a hill at (300, 150)"
✅ "add several hills"
```

#### **Valleys:**
```
✅ "add a valley"
✅ "add two valleys"
✅ "add a valley in the center"
✅ "add a valley at (250, 250)"
✅ "add deep valleys"
```

#### **Dunes:**
```
✅ "create rolling dunes"
✅ "add dunes across the desert"
✅ "create dunes in the center"
✅ "add dunes with high frequency"
✅ "create rolling sand dunes"
```

#### **Mesas:**
```
✅ "add a mesa"
✅ "add two mesas"
✅ "add a mesa at (256, 256)"
✅ "create flat-topped mesas"
✅ "add mesas on the left"
```

#### **Plateaus:**
```
✅ "add a plateau"
✅ "add two plateaus"
✅ "add a plateau in the center"
✅ "create a large plateau"
✅ "add plateaus on the right"
```

#### **Cliffs:**
```
✅ "add a cliff"
✅ "add cliffs along the edge"
✅ "create steep cliffs"
✅ "add a cliff at (200, 100)"
✅ "add cliffs facing north"
```

#### **Canyons:**
```
✅ "add a canyon"
✅ "create a deep canyon"
✅ "add a winding canyon"
✅ "add canyons between points"
```

#### **Slopes:**
```
✅ "add a slope"
✅ "add gentle slopes"
✅ "create slopes connecting areas"
✅ "add slopes in the center"
```

---

### **Test Category 2: Count Extraction**

```
✅ "add one mountain" → 1 mountain
✅ "add two mountains" → 2 mountains
✅ "add three hills" → 3 hills
✅ "add four valleys" → 4 valleys
✅ "add five mesas" → 5 mesas
✅ "add a couple of mountains" → 2 mountains
✅ "add several hills" → 3-5 hills
✅ "add many valleys" → 5-8 valleys
✅ "add a dozen mesas" → 12 mesas
✅ "add two mountains and three hills" → 2 mountains + 3 hills
✅ "add one mountain, two hills, and three valleys" → 1 + 2 + 3
```

---

### **Test Category 3: Position Placement**

#### **Regions:**
```
✅ "add a mountain on the left"
✅ "add hills in the center"
✅ "add valleys on the right"
✅ "add mesas at the top"
✅ "add plateaus at the bottom"
✅ "add cliffs in the top-left"
✅ "add canyons in the bottom-right"
✅ "add slopes in the top-right"
```

#### **Coordinates:**
```
✅ "add a mountain at (100, 200)"
✅ "add a hill at (300, 150)"
✅ "add a valley at (250, 250)"
✅ "add a mesa at (150, 100)"
✅ "add a plateau at (256, 256)"
```

#### **Mixed:**
```
✅ "add two mountains on the left and one hill in the center"
✅ "add a mountain at (100, 100), a valley at (300, 300)"
```

---

### **Test Category 4: Modifiers**

#### **Height Modifiers:**
```
✅ "make the mountain taller"
✅ "make the hill taller"
✅ "make the mesa taller"
✅ "make the plateau taller"
✅ "make the mountain 50% taller"
✅ "make the hill 30% taller"
✅ "increase mountain height by 75%"
```

#### **Depth Modifiers:**
```
✅ "make the valley deeper"
✅ "make the canyon deeper"
✅ "make the valley 50% deeper"
✅ "make the canyon 30% deeper"
```

#### **Width Modifiers:**
```
✅ "make the mountain wider"
✅ "make the hill wider"
✅ "make the plateau wider"
✅ "make the canyon wider"
✅ "make the mountain 25% wider"
✅ "make the plateau 50% wider"
```

---

### **Test Category 5: Scene Graph & References**

#### **Context-Aware Commands:**
```
✅ "create a desert with rolling dunes and two mountains on the left"
   → Then: "make the dunes taller"
   → Then: "make the mountains wider"
   → Then: "remove the dunes"
```

#### **Reference Resolution:**
```
✅ "add two mountains" → "make the mountains taller"
✅ "add rolling dunes" → "make the dunes wider"
✅ "add a valley" → "make the valley deeper"
✅ "add three hills" → "remove the hills"
```

#### **Ordinal References:**
```
✅ "add a mountain, then add another mountain" → "make the last mountain taller"
✅ "add three hills" → "remove the first hill"
✅ "add valleys" → "make the last valley deeper"
```

---

### **Test Category 6: Removal & Cleanup**

```
✅ "add two mountains" → "remove the mountain" (removes most recent)
✅ "add three hills" → "remove the hills" (removes all)
✅ "add a valley" → "delete the valley"
✅ "add dunes and mountains" → "remove the dunes"
✅ "add multiple features" → "reset" (should clear everything)
```

---

### **Test Category 7: Compositional Commands**

```
✅ "create a desert with rolling dunes and two mountains on the left"
✅ "add a mountain at (100, 100), a valley at (300, 300), and a hill at (200, 200)"
✅ "place three hills on the right, two valleys in the center, and one mountain on the left"
✅ "create rolling dunes across the center, add a mesa at (256, 256), and place cliffs along the northern edge"
✅ "add two mountains, three hills, and five valleys scattered"
```

---

### **Test Category 8: Spatial Queries**

```
✅ "find features near the dunes"
✅ "show features in the left half"
✅ "list features on the right"
✅ "query features in the center"
✅ "what features are near the mountains"
```

---

### **Test Category 9: Edge Cases**

```
✅ "add a mountain" → "add a mountain" → "add a mountain" (multiple same type)
✅ "add two mountains" → "add three mountains" (count preservation)
✅ "add a mountain" → "remove the mountain" → "add a mountain" (cleanup)
✅ "reset" → "add features" (fresh start)
✅ "add many features" → "reset" → "add features again" (clean reset)
✅ Empty command: "" (should rebuild from state)
✅ "add a mountain" → modify → remove → add again (full cycle)
```

---

### **Test Category 10: Complex Scenarios**

#### **Scenario 1: Desert Landscape**
```
1. "create a desert with rolling dunes"
2. "add two mountains on the left"
3. "add a mesa in the center"
4. "make the mountains taller"
5. "make the dunes wider"
6. "add a valley between the mountains"
7. "remove the mesa"
```

#### **Scenario 2: Mountain Range**
```
1. "add five mountains scattered"
2. "add valleys between the mountains"
3. "add cliffs along the edges"
4. "make the mountains taller"
5. "add plateaus at the base"
```

#### **Scenario 3: Canyon System**
```
1. "add a mesa at (150, 150)"
2. "add a mesa at (350, 350)"
3. "add canyons connecting the mesas"
4. "add slopes around the canyons"
5. "make the canyons deeper"
```

---

## 🎯 Testing Checklist

### **✅ Primitives (9 types):**
- [ ] Mountain
- [ ] Hill
- [ ] Valley
- [ ] Dunes
- [ ] Mesa
- [ ] Plateau
- [ ] Cliff
- [ ] Canyon
- [ ] Slope

### **✅ Operations (3 types):**
- [ ] Add
- [ ] Modify
- [ ] Remove

### **✅ Positions:**
- [ ] Regions (9 regions)
- [ ] Coordinates (explicit)
- [ ] Scattered/random

### **✅ Modifiers:**
- [ ] Taller/deeper/wider
- [ ] Percentage modifiers (height_percent, depth_percent, width_percent)

### **✅ Count Extraction:**
- [ ] Single (1)
- [ ] Multiple (2-12)
- [ ] Words (one, two, three, several, many, dozen)
- [ ] Multiple types in one command

### **✅ Scene Graph:**
- [ ] Entity creation
- [ ] Reference resolution
- [ ] Context-aware commands
- [ ] Cleanup on removal

### **✅ Spatial Queries:**
- [ ] Find near
- [ ] Find in region
- [ ] Query results

---

## 🚀 Quick Test Commands

**Copy-paste these for quick testing:**

```bash
# Basic primitives
"add a mountain"
"add two hills"
"add a valley"
"create rolling dunes"
"add a mesa"
"add a plateau"
"add a cliff"
"add a canyon"
"add a slope"

# With positions
"add two mountains on the left"
"add three hills in the center"
"add a valley at (250, 250)"

# Modifiers
"add a mountain" → "make the mountain taller"
"add a valley" → "make the valley deeper"
"add a hill" → "make the hill wider"

# Compositional
"create a desert with rolling dunes and two mountains on the left"
"add a mountain at (100, 100), a valley at (300, 300), and a hill at (200, 200)"

# Removal
"add two mountains" → "remove the mountain"
"add three hills" → "remove the hills"

# Reset
"reset"
```

---

## 📊 Expected Behavior

### **✅ Count Extraction:**
- "two mountains" → count: 2
- "three hills" → count: 3
- "a valley" → count: 1
- "several mesas" → count: 3-5

### **✅ Position Resolution:**
- "on the left" → region: "left"
- "at (100, 200)" → coords: [100, 200]
- "in the center" → region: "center"

### **✅ Reference Resolution:**
- "the mountains" → Uses scene graph to find entity
- "the dunes" → Uses scene graph to find entity
- "last mountain" → Uses ordinal resolution

### **✅ Cleanup:**
- Removing features → Entities updated
- Removing all features → Entities removed
- Reset → Fresh scene graph

---

## 🎉 Success Criteria

**All tests pass if:**
1. ✅ All 9 primitives can be added
2. ✅ Counts are extracted correctly
3. ✅ Positions are resolved correctly
4. ✅ Modifiers work correctly
5. ✅ References resolve correctly
6. ✅ Cleanup works correctly
7. ✅ Reset works correctly
8. ✅ Scene graph stays consistent

---

**Status:** ✅ **Ready for comprehensive testing!**


