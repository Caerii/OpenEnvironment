# QueryEngine: Complex Spatial Queries ✅

**Date:** October 31, 2025  
**Status:** ✅ Implemented  
**Impact:** Full-featured spatial query system for scene graph

---

## 🎯 What Was Implemented

### **QueryEngine Class** (`server/semantic/scene/query.py`)

A comprehensive query engine with **complex spatial query capabilities**:

#### **Spatial Queries:**
1. ✅ **`find_near(position, radius)`** - Find features within radius
2. ✅ **`find_within_region(bounds)`** - Find features in rectangular region
3. ✅ **`find_between(start, end, width)`** - Find features in corridor between points
4. ✅ **`find_near_feature(feature_id, radius)`** - Find features near another feature
5. ✅ **`find_closest(position, n)`** - Find N closest features
6. ✅ **`find_in_direction(position, direction, angle_range)`** - Find features in direction

#### **Metadata Queries:**
- ✅ **`find_by_metadata(filters)`** - Filter by metadata with operators ($gt, $lt, $in, $regex)
- ✅ **`find_by_type(feature_type)`** - Find all features of a type

#### **Path Queries:**
- ✅ **`query_path(pattern)`** - USD-style path pattern matching with wildcards

#### **Query Composition:**
- ✅ **`and_(*queries)`** - Intersection (features in ALL queries)
- ✅ **`or_(*queries)`** - Union (features in ANY query)
- ✅ **`not_(query)`** - Complement (features NOT in query)

#### **Convenience Methods:**
- ✅ **`count(results)`** - Count query results
- ✅ **`get_feature_ids(results)`** - Extract feature IDs
- ✅ **`get_positions(results)`** - Extract positions
- ✅ **`get_bounds(results)`** - Get bounding box
- ✅ **`get_center(results)`** - Get center point

---

## 🔧 Integration Updates

### **1. Enhanced `integration.py`**
- ✅ Stores feature data (positions, metadata) in scene graph nodes
- ✅ Handles both point features (x, y) and box features (x0, y0, x1, y1)
- ✅ Stores all metadata for spatial queries

### **2. Updated `terrain.py`**
- ✅ Passes feature data to scene graph integration
- ✅ Enables spatial queries to access feature positions

### **3. Updated `__init__.py`**
- ✅ Exports `QueryEngine` in public API

---

## 📊 Usage Examples

### **Basic Spatial Queries:**

```python
from semantic.scene import TerrainSceneGraph, QueryEngine

graph = TerrainSceneGraph()
graph.from_dict(state["semantic_scene"])
engine = QueryEngine(graph)

# Find all mountains within 100 pixels of center
mountains = engine.find_near((256, 256), radius=100, feature_type="mountain")

# Find features in left half
left_features = engine.find_within_region((0, 0, 256, 512))

# Find features between two points (corridor)
valley = engine.find_between((100, 100), (400, 400), width=80)

# Find features near mountain 5
nearby = engine.find_near_feature(5, radius=150)

# Find 3 closest mountains to center
closest = engine.find_closest((256, 256), n=3, feature_type="mountain")

# Find features to the right of center
right_features = engine.find_in_direction((256, 256), direction=0, angle_range=45)
```

### **Complex Queries:**

```python
# Find tall mountains in left half
tall_mountains = engine.find_by_metadata({"height": {"$gt": 0.7}, "type": "mountain"})
left_half = engine.find_within_region((0, 0, 256, 512))
result = engine.and_(tall_mountains, left_half)

# Find mountains OR hills near center
mountains = engine.find_by_type("mountain")
hills = engine.find_by_type("hill")
near_center = engine.find_near((256, 256), radius=100)
result = engine.and_(engine.or_(mountains, hills), near_center)

# Find all features EXCEPT valleys
all_features = engine.graph.get_all_features()
valleys = engine.find_by_type("valley")
others = engine.not_(valleys)
```

### **Metadata Filtering:**

```python
# Find mountains taller than 0.7
tall = engine.find_by_metadata({"height": {"$gt": 0.7}})

# Find features with height between 0.5 and 0.8
medium = engine.find_by_metadata({
    "height": {"$gte": 0.5, "$lte": 0.8}
})

# Find mountains or hills
mountains_or_hills = engine.find_by_metadata({
    "type": {"$in": ["mountain", "hill"]}
})

# Find features matching regex pattern
dunes = engine.find_by_metadata({
    "label": {"$regex": "dune.*"}
})
```

### **Query Composition:**

```python
# Complex query: Tall mountains in left half, near center
tall = engine.find_by_metadata({"height": {"$gt": 0.7}})
mountains = engine.find_by_type("mountain")
left = engine.find_within_region((0, 0, 256, 512))
near = engine.find_near((256, 256), radius=100)

# Combine: tall AND mountains AND left AND near
result = engine.and_(tall, mountains, left, near)

# Get feature IDs
feature_ids = engine.get_feature_ids(result)

# Get bounding box
bounds = engine.get_bounds(result)  # (x0, y0, x1, y1)

# Get center
center = engine.get_center(result)  # (x, y)
```

---

## 🎯 Real-World Use Cases

### **1. Spatial Reasoning**
```python
# User: "add a valley between the mountains"
mountains = engine.find_by_type("mountain")
mountain_positions = engine.get_positions(mountains)

if len(mountain_positions) >= 2:
    # Calculate midpoint
    center = engine.get_center(mountains)
    # Place valley at center
    place_valley(center)
```

### **2. Proximity-Based Operations**
```python
# User: "make mountains near the dunes taller"
dunes = engine.find_by_type("dunes")
dune_positions = engine.get_positions(dunes)

for pos in dune_positions:
    nearby_mountains = engine.find_near(pos, radius=100, feature_type="mountain")
    for mountain in nearby_mountains:
        modify_feature(mountain.feature_ids[0], {"height": +0.1})
```

### **3. Region-Based Modifications**
```python
# User: "make all features in the left half smaller"
left_features = engine.find_within_region((0, 0, 256, 512))
for feature in left_features:
    modify_feature(feature.feature_ids[0], {"height": -0.1})
```

### **4. Directional Queries**
```python
# User: "add a hill to the right of the mountains"
mountains = engine.find_by_type("mountain")
mountain_positions = engine.get_positions(mountains)

if mountain_positions:
    # Get rightmost mountain
    rightmost = max(mountain_positions, key=lambda p: p[0])
    # Find features to the right
    right_features = engine.find_in_direction(rightmost, direction=0, angle_range=30)
    # Place hill to the right
    new_pos = (rightmost[0] + 50, rightmost[1])
    place_hill(new_pos)
```

---

## 🔍 Technical Details

### **Position Extraction:**
- Handles **point features** (x, y): mountains, hills, valleys, etc.
- Handles **box features** (x0, y0, x1, y1): dunes, plateaus, etc.
- For box features, uses center point for spatial calculations

### **Spatial Algorithms:**
- **Distance calculation**: Euclidean distance `sqrt((x-x0)² + (y-y0)²)`
- **Corridor search**: Distance from point to line segment
- **Directional search**: Angular range matching with angle normalization

### **Metadata Operators:**
- `$gt`: Greater than
- `$lt`: Less than
- `$gte`: Greater than or equal
- `$lte`: Less than or equal
- `$in`: In list
- `$regex`: Regex pattern matching

### **Performance:**
- O(n) traversal for most queries (n = number of features)
- No indexing (can be added later for optimization)
- Efficient set operations for composition

---

## ✅ Success Criteria Met

- [x] Complex spatial queries implemented
- [x] Distance-based queries (near, closest)
- [x] Region-based queries (within bounds)
- [x] Directional queries (in direction)
- [x] Corridor queries (between points)
- [x] Metadata filtering with operators
- [x] Query composition (AND, OR, NOT)
- [x] Feature data storage for spatial queries
- [x] Support for both point and box features
- [x] Convenience methods (count, bounds, center)

---

## 🚀 Next Steps

### **Potential Enhancements:**
1. **Query Optimization:**
   - Spatial indexing (R-tree, quadtree)
   - Query result caching
   - Parallel query execution

2. **Advanced Spatial Queries:**
   - Polygon-based queries (irregular regions)
   - Line-of-sight queries
   - Visibility queries

3. **Natural Language Queries:**
   - Parse natural language to spatial queries
   - "features near the dunes" → `find_near_feature()`
   - "mountains in the left half" → `find_within_region()`

---

## 📝 Summary

**What We Built:**
- Full-featured QueryEngine with complex spatial queries
- Distance, region, directional, and corridor queries
- Metadata filtering with operators
- Query composition (AND, OR, NOT)
- Feature data storage for spatial access

**What This Enables:**
- **Spatial reasoning**: "between the mountains", "near the dunes"
- **Proximity-based operations**: Modify features near others
- **Region-based modifications**: Modify features in areas
- **Complex queries**: Combine multiple spatial and metadata filters

**The QueryEngine is now fully functional and ready for spatial reasoning!** ✅

You can now perform complex spatial queries like:
- "Find mountains near the dunes"
- "Find features between two points"
- "Find features in a region"
- "Find features in a direction"
- "Combine spatial and metadata filters"

**Ready for advanced terrain generation workflows!** 🎉


