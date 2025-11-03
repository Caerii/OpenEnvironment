# Recommended Additional Primitives

**Date:** October 31, 2025  
**Status:** 📋 **Recommendation Document**

---

## 🎯 Current Primitives (9 Types)

✅ **Mountain** - Tall peaks  
✅ **Hill** - Gentle elevations  
✅ **Valley** - Bowl depressions  
✅ **Dunes** - Sand waves  
✅ **Mesa** - Flat-topped hills  
✅ **Plateau** - Large flat areas  
✅ **Cliff** - Steep drops  
✅ **Canyon** - Linear valleys  
✅ **Slope** - Gradual inclines  

---

## 🚀 Recommended Additions (Priority Order)

### **TIER 1: High Impact, Easy Implementation** ⭐⭐⭐

#### **1. Crater** 🔴 **TOP PRIORITY**
- **Why:** Adds dramatic visual impact, common in games/visualization
- **Use Cases:** Impact craters, volcanic craters, sinkholes
- **Parameters:** 
  - `center` (x, y)
  - `radius` (outer rim radius)
  - `depth` (crater depth)
  - `rim_height` (elevated rim around crater)
  - `steepness` (how steep the walls are)
- **Visual Impact:** Very high - creates dramatic focal points
- **Complexity:** Low-Medium (similar to valley but with rim)
- **Prompt Examples:**
  - `"add a crater"`
  - `"create a volcanic crater"`
  - `"add a deep impact crater"`
  - `"add craters scattered across the terrain"`

**Implementation:** Similar to valley but with elevated rim around edge

---

#### **2. Ridge** 🔴 **HIGH PRIORITY**
- **Why:** Common linear feature, complements existing features
- **Use Cases:** Mountain ridges, elevation lines, terrain boundaries
- **Parameters:**
  - `start` (x, y)
  - `end` (x, y)
  - `height` (ridge height)
  - `width` (ridge width perpendicular to line)
  - `steepness` (how steep the sides are)
- **Visual Impact:** High - creates natural boundaries
- **Complexity:** Low (similar to canyon but positive elevation)
- **Prompt Examples:**
  - `"add a ridge"`
  - `"create a mountain ridge"`
  - `"add a ridge from (100, 100) to (400, 400)"`
  - `"add ridges connecting the mountains"`

**Implementation:** Similar to canyon but inverted (positive elevation)

---

#### **3. Ravine** 🟡 **MEDIUM PRIORITY**
- **Why:** More narrow than canyon, adds variety
- **Use Cases:** Narrow valleys, erosion channels, gullies
- **Parameters:**
  - `start` (x, y)
  - `end` (x, y)
  - `width` (narrower than canyon, ~5-8 pixels)
  - `depth` (ravine depth)
  - `steepness` (very steep walls)
- **Visual Impact:** Medium-High - creates fine detail
- **Complexity:** Low (similar to canyon but narrower)
- **Prompt Examples:**
  - `"add a ravine"`
  - `"create narrow ravines"`
  - `"add a deep ravine"`
  - `"add ravines cutting through the terrain"`

**Implementation:** Similar to canyon but narrower and steeper

---

### **TIER 2: Medium Impact, Medium Complexity** ⭐⭐

#### **4. Volcano** 🟡 **MEDIUM PRIORITY**
- **Why:** Visually distinct, common in terrain generation
- **Use Cases:** Volcanic terrain, cone-shaped mountains
- **Parameters:**
  - `center` (x, y)
  - `base_radius` (volcano base)
  - `height` (peak height)
  - `crater_radius` (optional crater at top)
  - `crater_depth` (optional crater depth)
  - `steepness` (cone steepness)
- **Visual Impact:** Very High - distinctive shape
- **Complexity:** Medium (cone shape with optional crater)
- **Prompt Examples:**
  - `"add a volcano"`
  - `"create a volcanic mountain"`
  - `"add a volcano with a crater"`
  - `"add volcanoes scattered"`

**Implementation:** Cone-shaped mountain (like mountain but steeper) with optional crater at top

---

#### **5. Pass** 🟡 **MEDIUM PRIORITY**
- **Why:** Connects features naturally, creates gameplay paths
- **Use Cases:** Mountain passes, gaps between peaks, navigation routes
- **Parameters:**
  - `start` (x, y) - one side of pass
  - `end` (x, y) - other side of pass
  - `width` (pass width)
  - `depth` (how much lower than surrounding terrain)
  - `elevation` (base elevation of pass)
- **Visual Impact:** Medium - creates natural connections
- **Complexity:** Medium (depression between two elevated areas)
- **Prompt Examples:**
  - `"add a mountain pass"`
  - `"create a pass between the mountains"`
  - `"add passes connecting valleys"`
  - `"add a narrow pass"`

**Implementation:** Depressed corridor between elevated areas

---

#### **6. Mound** 🟢 **LOW PRIORITY**
- **Why:** Small-scale feature, adds detail variety
- **Use Cases:** Small hills, burial mounds, subtle elevation
- **Parameters:**
  - `center` (x, y)
  - `radius` (small, ~20-30 pixels)
  - `height` (low, ~0.15-0.25)
- **Visual Impact:** Low-Medium - subtle detail
- **Complexity:** Very Low (mini hill)
- **Prompt Examples:**
  - `"add mounds"`
  - `"create small mounds"`
  - `"add mounds scattered"`
  - `"add burial mounds"`

**Implementation:** Small hill (like hill but smaller)

---

### **TIER 3: Lower Priority, Higher Complexity** ⭐

#### **7. Basin** 🟢 **LOW PRIORITY**
- **Why:** Large-scale depression, complements valleys
- **Use Cases:** Large depressions, dry lake beds, basins
- **Parameters:**
  - `center` (x, y)
  - `radius` (large, ~100-150 pixels)
  - `depth` (depth of basin)
  - `flatness` (flat bottom vs bowl-shaped)
- **Visual Impact:** Medium - large-scale feature
- **Complexity:** Low-Medium (large valley variant)
- **Prompt Examples:**
  - `"add a basin"`
  - `"create a large basin"`
  - `"add a flat basin"`
  - `"add basins across the terrain"`

**Implementation:** Large valley with optional flat bottom

---

#### **8. Pinnacle** 🟢 **LOW PRIORITY**
- **Why:** Dramatic vertical feature
- **Use Cases:** Sharp peaks, spires, dramatic mountains
- **Parameters:**
  - `center` (x, y)
  - `height` (very tall)
  - `radius` (very narrow base)
  - `steepness` (very steep, >1.5)
- **Visual Impact:** High - dramatic feature
- **Complexity:** Low (mountain variant with extreme parameters)
- **Prompt Examples:**
  - `"add a pinnacle"`
  - `"create sharp pinnacles"`
  - `"add a tall pinnacle"`
  - `"add pinnacles scattered"`

**Implementation:** Very narrow, very tall mountain

---

#### **9. Spur** 🟢 **LOW PRIORITY**
- **Why:** Extends from mountains naturally
- **Use Cases:** Mountain spurs, ridges extending from peaks
- **Parameters:**
  - `start` (x, y) - attached to mountain
  - `end` (x, y) - extends outward
  - `width` (spur width)
  - `height` (spur height, decreases toward end)
- **Visual Impact:** Medium - natural extension
- **Complexity:** Medium (slope-like but decreasing height)
- **Prompt Examples:**
  - `"add a spur"`
  - `"create spurs extending from the mountains"`
  - `"add mountain spurs"`
  - `"add spurs from the peaks"`

**Implementation:** Ridge that extends from elevated area with decreasing height

---

#### **10. Terraces** 🟢 **LOW PRIORITY**
- **Why:** Unique step-like feature
- **Use Cases:** Terraced hillsides, step-like terrain
- **Parameters:**
  - `region` (x0, y0, x1, y1) - bounding box
  - `levels` (number of terrace levels)
  - `height_per_level` (height increase per level)
  - `width_per_level` (width of each terrace)
- **Visual Impact:** Medium - unique appearance
- **Complexity:** Medium-High (requires multiple levels)
- **Prompt Examples:**
  - `"add terraces"`
  - `"create terraced hillsides"`
  - `"add step-like terraces"`
  - `"add terraces in the region"`

**Implementation:** Multiple flat levels stacked vertically

---

## 📊 Summary Table

| Primitive | Priority | Complexity | Visual Impact | Use Cases |
|-----------|----------|------------|---------------|-----------|
| **Crater** | 🔴 HIGH | Low-Med | Very High | Impact sites, volcanoes |
| **Ridge** | 🔴 HIGH | Low | High | Boundaries, elevation lines |
| **Ravine** | 🟡 MED | Low | Med-High | Narrow valleys, erosion |
| **Volcano** | 🟡 MED | Medium | Very High | Volcanic terrain |
| **Pass** | 🟡 MED | Medium | Medium | Navigation routes |
| **Mound** | 🟢 LOW | Very Low | Low-Med | Small details |
| **Basin** | 🟢 LOW | Low-Med | Medium | Large depressions |
| **Pinnacle** | 🟢 LOW | Low | High | Sharp peaks |
| **Spur** | 🟢 LOW | Medium | Medium | Mountain extensions |
| **Terraces** | 🟢 LOW | Med-High | Medium | Step-like terrain |

---

## 🎯 Recommended Implementation Order

### **Phase 1: Quick Wins (1-2 days)**
1. **Crater** - High impact, similar to valley
2. **Ridge** - High impact, similar to canyon
3. **Mound** - Quick addition, adds variety

### **Phase 2: Medium Complexity (2-3 days)**
4. **Ravine** - Narrow canyon variant
5. **Volcano** - Cone + optional crater
6. **Pass** - Depressed corridor

### **Phase 3: Lower Priority (as needed)**
7. **Basin** - Large valley variant
8. **Pinnacle** - Extreme mountain variant
9. **Spur** - Ridge variant
10. **Terraces** - Complex multi-level feature

---

## 💡 Implementation Notes

### **Crater Implementation:**
```python
def generate_crater(cx: int, cy: int, radius: int, depth: float, 
                   rim_height: float = 0.1, steepness: float = 1.0):
    """
    Generate a crater with elevated rim.
    
    Similar to valley but with positive rim around edge.
    """
    # Create bowl depression (like valley)
    # Add elevated rim around perimeter (like small hill ring)
    # Blend smoothly
```

### **Ridge Implementation:**
```python
def generate_ridge(start: Tuple[int, int], end: Tuple[int, int], 
                   height: float, width: int, steepness: float = 0.8):
    """
    Generate a linear ridge.
    
    Similar to canyon but inverted (positive elevation).
    """
    # Create elevated line between start/end
    # Add width perpendicular to line
    # Use steep falloff for sides
```

### **Ravine Implementation:**
```python
def generate_ravine(start: Tuple[int, int], end: Tuple[int, int],
                    width: int, depth: float, steepness: float = 1.2):
    """
    Generate a narrow, steep ravine.
    
    Similar to canyon but narrower and steeper.
    """
    # Like canyon but width ~5-8 pixels (vs 12 for canyon)
    # Steeper walls (steepness > 1.0)
```

---

## 🎨 Visual Diversity Goals

**Current:** 9 primitives  
**After Phase 1:** 12 primitives (+3)  
**After Phase 2:** 15 primitives (+6)  
**Full Set:** 19 primitives (+10)

**Target:** 15-20 primitives for comprehensive terrain generation

---

## ✅ Recommended Next Steps

1. **Start with Crater** - Highest impact, easiest implementation
2. **Add Ridge** - Common feature, complements existing
3. **Add Ravine** - Quick variant, adds detail
4. **Then Volcano** - Distinctive feature
5. **Then Pass** - Natural connections

**Focus on:** High visual impact + Low complexity first!

---

## 📝 Notes

- All primitives should follow existing patterns:
  - Deterministic (seed-based)
  - Smooth blending (40px+ feathering)
  - Variation support (±15% randomness)
  - Integration with scene graph
  - Splatmap support

- Consider visual variety:
  - Different scales (mound vs basin)
  - Different shapes (crater vs valley)
  - Different orientations (ridge vs canyon)

- Prioritize based on:
  - Visual impact
  - Implementation ease
  - User requests
  - Terrain variety needs

---

**Status:** 📋 **Ready for implementation prioritization!**


