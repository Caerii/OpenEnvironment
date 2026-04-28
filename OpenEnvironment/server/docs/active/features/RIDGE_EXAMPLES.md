# Ridge & Primitive Examples - Complete Guide

**Updated:** October 31, 2025  
**Status:** ✅ **Ridge Smoothing Applied + Examples**

---

## 🔧 Ridge Smoothing Update

**Fixed:** Ridges now use smoother falloff with:
- ✅ Smoothstep-like falloff for gentler transitions
- ✅ Edge blending at start/end (20px smooth transitions)
- ✅ Gaussian smoothing applied (sigma=1.5)
- ✅ Steepness parameter now controls smoothness (lower = smoother)

---

## 🎯 Primitives - Example Prompts

**Note:** The system currently supports multiple primitives including Core 6 (mountain, valley, dunes, cliff, plateau, canyon), specialized primitives (mesa, crater, volcano, pass, spur, terraces, slope), walkability zones (flat_zone, path, clearing), and forest-specific primitives (grove, forest_hill, forest_clearing, forest_valley). See `feature_registry.py` for the complete current list.

### **1. Mountains**
```
"add a mountain"
"add two mountains on the left"
"add three mountains scattered"
"add a tall mountain in the center"
"add mountains across the terrain"
"add five mountains"
```

### **2. Hills**
```
"add a hill"
"add three hills"
"add rolling hills"
"add hills in the center"
"add several hills scattered"
```

### **3. Valleys**
```
"add a valley"
"add two valleys"
"add a deep valley"
"add valleys between the mountains"
"add several valleys"
```

### **4. Dunes**
```
"create rolling dunes"
"add dunes across the desert"
"add dunes in the center"
"create sand dunes"
"add dunes with high frequency"
```

### **5. Mesas**
```
"add a mesa"
"add two mesas"
"add a flat-topped mesa"
"add mesas on the left"
"add several mesas"
```

### **6. Plateaus**
```
"add a plateau"
"add two plateaus"
"add a large plateau"
"add plateaus in the center"
"add several plateaus"
```

### **7. Cliffs**
```
"add a cliff"
"add cliffs along the edge"
"add steep cliffs"
"add cliffs facing north"
"add several cliffs"
```

### **8. Canyons**
```
"add a canyon"
"add a deep canyon"
"add a winding canyon"
"add canyons between points"
"add several canyons"
```

### **9. Slopes**
```
"add a slope"
"add gentle slopes"
"add slopes connecting areas"
"add slopes in the center"
"add several slopes"
```

### **10. Craters** ⭐ NEW
```
"add a crater"
"add an impact crater"
"add a volcanic crater"
"add two craters scattered"
"add craters across the terrain"
"add several craters"
"add a deep crater"
"add craters in the center"
```

### **11. Ridges** ⭐ NEW (NOW SMOOTHER!)
```
"add a ridge"
"add a mountain ridge"
"add ridges connecting the peaks"
"add a ridge from (100, 100) to (400, 400)"
"add two ridges"
"add gentle ridges"
"add ridges across the terrain"
"add several ridges"
"add ridges between mountains"
"add a smooth ridge"
"add ridges with gradual slopes"
```

### **12. Ravines** ⭐ NEW
```
"add a ravine"
"add a narrow ravine"
"add deep ravines"
"add ravines cutting through the terrain"
"add several ravines"
"add ravines between mountains"
"add a steep ravine"
```

### **13. Volcanoes** ⭐ NEW
```
"add a volcano"
"add a volcanic mountain"
"add a volcano with a crater"
"add two volcanoes"
"add volcanoes scattered"
"add a tall volcano"
"add several volcanoes"
"add volcanic terrain"
```

### **14. Passes** ⭐ NEW
```
"add a mountain pass"
"add a pass between mountains"
"add passes connecting valleys"
"add a narrow pass"
"add several passes"
"add a pass at (256, 256)"
```

### **15. Mounds** ⭐ NEW
```
"add mounds"
"add small mounds"
"add mounds scattered"
"add burial mounds"
"add several mounds"
"add mounds in the center"
```

### **16. Basins** ⭐ NEW
```
"add a basin"
"add a large basin"
"add flat basins"
"add basins across the terrain"
"add several basins"
"add a deep basin"
```

### **17. Pinnacles** ⭐ NEW
```
"add a pinnacle"
"add sharp pinnacles"
"add tall pinnacles"
"add pinnacles scattered"
"add several pinnacles"
"add dramatic pinnacles"
```

### **18. Spurs** ⭐ NEW
```
"add a spur"
"add spurs extending from mountains"
"add mountain spurs"
"add spurs from the peaks"
"add several spurs"
"add spurs connecting ridges"
```

### **19. Terraces** ⭐ NEW
```
"add terraces"
"add terraced hillsides"
"add step-like terraces"
"add terraces in the region"
"add several terraces"
"add terraces leading up to a mesa"
```

---

## 🎨 Compositional Examples

### **Desert Landscapes:**
```
"create a desert with rolling dunes and two mountains on the left"
"add dunes across the center, two craters, and a mesa"
"add dunes, a volcano, and craters scattered"
```

### **Mountain Ranges:**
```
"add five mountains scattered, ridges connecting them, and valleys between"
"add three mountains, ridges between peaks, and a pass through"
"add mountains with spurs extending outward"
```

### **Volcanic Terrain:**
```
"add two volcanoes with craters, and volcanic ridges"
"add a volcano, several craters, and ridges connecting them"
"add volcanic terrain with multiple craters"
```

### **Complex Compositions:**
```
"add a volcano at (150, 150), two craters at (300, 300) and (400, 400), and ridges connecting them"
"add terraces leading up to a mesa, with cliffs on the sides"
"add a basin in the center, ridges around it, and mounds scattered"
"add a mountain pass between two peaks, with cliffs on either side"
```

---

## 🔧 Modifier Examples

### **Height Modifiers:**
```
"add a mountain" → "make the mountain taller"
"add a volcano" → "make the volcano taller"
"add a pinnacle" → "make the pinnacle taller"
"add a ridge" → "make the ridge taller"
```

### **Depth Modifiers:**
```
"add a valley" → "make the valley deeper"
"add a crater" → "make the crater deeper"
"add a ravine" → "make the ravine deeper"
"add a basin" → "make the basin deeper"
```

### **Width Modifiers:**
```
"add a ridge" → "make the ridge wider"
"add a canyon" → "make the canyon wider"
"add a pass" → "make the pass wider"
"add terraces" → "make the terraces wider"
```

### **Percentage Modifiers:**
```
"make the volcano 50% taller"
"make the crater 30% deeper"
"make the ridge 25% wider"
"increase crater depth by 40%"
```

---

## 🌟 Ridge-Specific Examples (Smoother Now!)

```
"add a gentle ridge"
"add smooth ridges connecting the mountains"
"add ridges with gradual slopes"
"add a ridge from (100, 100) to (400, 400)"
"add mountain ridges across the terrain"
"add two ridges connecting peaks"
"add ridges with soft edges"
"add a ridge between the mountains"
"add ridges forming a spine"
"add several gentle ridges"
```

---

## 🎯 Testing Scenarios

### **Scenario 1: Mountain Range**
```
1. "add five mountains scattered"
2. "add ridges connecting the peaks"
3. "add valleys between the mountains"
4. "add a pass through the range"
5. "add spurs extending from the peaks"
```

### **Scenario 2: Volcanic Landscape**
```
1. "add a volcano in the center"
2. "add three craters around it"
3. "add ridges radiating outward"
4. "add valleys between ridges"
5. "add mounds scattered"
```

### **Scenario 3: Terraced Hillside**
```
1. "add terraces leading up to a mesa"
2. "add cliffs on the sides"
3. "add a ridge at the top"
4. "add slopes connecting levels"
```

### **Scenario 4: Basin & Ridge System**
```
1. "add a large basin in the center"
2. "add ridges surrounding the basin"
3. "add passes through the ridges"
4. "add mounds in the basin"
```

---

## 📊 Count Extraction Examples

### **Single:**
```
"add a crater" → 1 crater
"add a ridge" → 1 ridge
"add a volcano" → 1 volcano
```

### **Multiple:**
```
"add two craters" → 2 craters
"add three ridges" → 3 ridges
"add five volcanoes" → 5 volcanoes
"add several mounds" → 3-5 mounds
"add many basins" → 5-8 basins
```

### **Mixed:**
```
"add two craters and three ridges" → 2 craters + 3 ridges
"add a volcano, two craters, and ridges connecting them"
"add one volcano, two craters, and three ridges"
```

---

## 🎨 Position Examples

### **With Regions:**
```
"add a crater on the left"
"add ridges in the center"
"add volcanoes on the right"
"add mounds at the top"
"add basins at the bottom"
```

### **With Coordinates:**
```
"add a crater at (100, 200)"
"add a ridge from (100, 100) to (400, 400)"
"add a volcano at (256, 256)"
"add a pass from (200, 200) to (300, 300)"
```

### **Compositional:**
```
"add a volcano at (150, 150), two craters at (300, 300) and (400, 400)"
"add ridges connecting (100, 100) to (400, 400) and (200, 200) to (500, 500)"
```

---

## 🚀 Quick Test Commands

**Copy-paste for quick testing:**

```bash
# Test all new primitives
"add a crater"
"add a ridge"
"add a ravine"
"add a volcano"
"add a pass"
"add a mound"
"add a basin"
"add a pinnacle"
"add a spur"
"add terraces"

# Test ridge smoothing (should be smoother now!)
"add a gentle ridge"
"add smooth ridges"
"add ridges with gradual slopes"

# Test compositional
"add a volcano, two craters, and ridges connecting them"
"add terraces leading up to a mesa"
"add a pass between two mountains"

# Test modifiers
"add a ridge" → "make the ridge wider"
"add a crater" → "make the crater deeper"
"add a volcano" → "make the volcano taller"
```

---

## ✅ Ridge Smoothing Applied

**Changes Made:**
- ✅ Replaced sharp exponential falloff with smoothstep-like falloff
- ✅ Added edge blending at start/end (20px transitions)
- ✅ Applied Gaussian smoothing (sigma=1.5)
- ✅ Steepness parameter now controls smoothness (lower = smoother)

**Result:** Ridges now have smooth, natural edges instead of sharp transitions!

---

**Status:** ✅ **Ridge smoothing complete + comprehensive examples provided!**


