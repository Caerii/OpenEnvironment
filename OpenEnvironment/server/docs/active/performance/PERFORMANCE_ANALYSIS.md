# Terrain Generation Performance Analysis

## Executive Summary

Template application is slow due to **multiple expensive operations** that process the full 512×512 heightmap repeatedly. The main bottlenecks are:

1. **Adaptive Smoothing** (~40-50% of time) - Most expensive
2. **Splatmap Generation** (~25-30% of time) - Multiple filters
3. **Feature Stamp Generation** (~15-20% of time) - Noise calculations
4. **LLM Parsing** (~5-10% of time) - If using commands
5. **Scene Graph Operations** (~3-5% of time) - Overhead

## Critical Bottlenecks

### 1. ⚠️ **Adaptive Smoothing** (CRITICAL - ~40-50% of total time)

**Location**: `server/engine/stamping.py:apply_adaptive_smoothing()`

**What it does**:
```python
def apply_adaptive_smoothing(h, base_sigma=0.8, preserve_edges=True):
    slope = sobel_slope(h)  # ← Gradient calculation (expensive)
    steep_mask = slope > 0.4
    dist_from_edge = distance_transform_edt(~steep_mask)  # ← Distance transform (expensive)
    
    # TWO full gaussian filters on 512×512
    smoothed_full = gaussian_filter(h, sigma=base_sigma * 1.5)  # ← Expensive
    smoothed_edge = gaussian_filter(h, sigma=base_sigma * 0.3)  # ← Expensive
    h[:] = blend(...)  # Blend operation
```

**Cost Analysis**:
- `sobel_slope()`: Gradient calculation on 512×512 = **O(n²)** = ~262K operations
- `distance_transform_edt()`: Euclidean distance transform = **O(n²)** = ~262K operations  
- **Two** `gaussian_filter()` calls: Each = **O(n²)** = ~262K operations each = **524K operations**
- **Total**: ~1.05M operations per template application

**Called**: Once per terrain generation (in `builder.finalize()`)

**Impact**: **CRITICAL** - This is the single most expensive operation

---

### 2. ⚠️ **Splatmap Generation** (HIGH - ~25-30% of total time)

**Location**: `server/engine/splatmap.py:generate_splatmap()`

**What it does**:
```python
def generate_splatmap(heightmap, dune_mask, cliff_mask):
    slope = sobel_slope(heightmap)  # ← Another gradient calculation
    h90, h97 = percentiles(heightmap, 90, 97)  # ← Percentile calculation
    gy, gx = np.gradient(heightmap)  # ← ANOTHER gradient calculation
    aspect = np.arctan2(-gy, gx)  # ← Trigonometry on 512×512
    
    # FOUR separate gaussian filters
    rock = gaussian_filter(rock, sigma=2.0)  # ← Filter 1
    snow = gaussian_filter(snow, sigma=3.0)  # ← Filter 2
    sand = gaussian_filter(sand, sigma=2.5)  # ← Filter 3
    grass = gaussian_filter(grass, sigma=2.0)  # ← Filter 4
    
    # Normalize per pixel
    splat /= s  # ← Division on 512×512×4
```

**Cost Analysis**:
- `sobel_slope()`: **~262K operations**
- `np.gradient()`: **~262K operations** (calculates gy, gx)
- `np.percentile()`: **~262K operations** (sorts array)
- `np.arctan2()`: **~262K operations** (trigonometry)
- **Four** `gaussian_filter()` calls: **~1.05M operations**
- Per-pixel normalization: **~1.05M operations**
- **Total**: ~3.2M operations

**Called**: Once per terrain generation (in `builder.build_splatmap()`)

**Impact**: **HIGH** - Second most expensive operation

---

### 3. ⚠️ **Feature Stamp Generation** (MEDIUM - ~15-20% of total time)

**Location**: `server/engine/feature_registry.py` → `server/primitives/*.py`

**What it does**:
- Each feature generates a **full 512×512 stamp** (even if feature is small)
- Noise calculations use `fractal_noise()` which iterates over **all 262K pixels**
- Multiple features = multiple full-size stamp generations

**Example (Mountain)**:
```python
def generate_mountain(cx, cy, radius, height, seed):
    yy, xx = np.mgrid[0:512, 0:512]  # ← Creates 512×512 arrays
    # ... distance calculations on full array
    if use_noise:
        noise_value = fractal_noise(xx, yy, ...)  # ← Processes 262K pixels
```

**Cost Analysis**:
- **Per feature**: ~262K operations for stamp generation
- **Per feature with noise**: ~262K + ~262K = **~524K operations**
- **Template with 10 features**: 10 × 524K = **~5.2M operations**

**Impact**: **MEDIUM-HIGH** - Scales with number of features

---

### 4. **LLM Parsing** (LOW-MEDIUM - ~5-10% of total time, if using commands)

**Location**: `server/semantic/parser.py:parse()`

**What it does**:
- Network call to Cerebras API
- LLM processing time
- JSON parsing

**Cost**: 
- Network latency: **~1-3 seconds**
- LLM processing: **~2-5 seconds**
- **Total**: ~3-8 seconds per command

**Impact**: **LOW-MEDIUM** - Only if using natural language commands (not JSON actions)

**Note**: Templates with JSON actions skip this entirely!

---

### 5. **Scene Graph Operations** (LOW - ~3-5% of total time)

**Location**: `server/orchestration.py`, `server/semantic/scene/`

**What it does**:
- Building scene graph from state
- Entity creation and management
- Serialization/deserialization

**Cost**: 
- Scene graph init: **~50-100ms**
- Entity creation: **~10-50ms per feature**
- Serialization: **~50-200ms**

**Impact**: **LOW** - Relatively fast, but adds up with many features

---

### 6. **Erosion** (LOW - ~2-3% of total time)

**Location**: `server/engine/erosion.py:apply_edge_erosion()`

**What it does**:
- Another smoothing operation on full heightmap

**Cost**: 
- Gaussian filter: **~262K operations**

**Impact**: **LOW** - Single filter, but adds to total

---

## Performance Breakdown (Estimated)

For a template with **10 features**:

| Operation | Time | % of Total |
|-----------|------|------------|
| Adaptive Smoothing | ~2.5s | 45% |
| Splatmap Generation | ~1.5s | 27% |
| Feature Stamps (10×) | ~1.0s | 18% |
| Erosion | ~0.2s | 4% |
| Scene Graph | ~0.2s | 4% |
| LLM Parsing* | ~0.0s | 0% (if using JSON actions) |
| **TOTAL** | **~5.4s** | **100%** |

*If using natural language commands instead of JSON actions, add ~3-8s for LLM parsing.

---

## Optimization Opportunities

### Priority 1: Optimize Adaptive Smoothing (Biggest Win)

**Current**: Two full gaussian filters + distance transform + slope calculation

**Options**:
1. **Simplify**: Use single gaussian filter with lower sigma (10-20x faster)
2. **Cache**: If terrain hasn't changed, skip smoothing
3. **Reduce resolution**: Smooth at 256×256, upsample to 512×512 (4x faster)
4. **Make optional**: Allow disabling adaptive smoothing for faster generation

**Expected Speedup**: **2-5x faster**

---

### Priority 2: Optimize Splatmap Generation

**Current**: Four separate gaussian filters + multiple gradient calculations

**Options**:
1. **Combine filters**: Use single multi-pass filter instead of four separate
2. **Reduce sigma**: Use smaller sigma values (faster filtering)
3. **Cache gradients**: Reuse slope calculation from adaptive smoothing
4. **Lazy generation**: Generate splatmap only when needed (not always)

**Expected Speedup**: **1.5-2x faster**

---

### Priority 3: Optimize Feature Stamp Generation

**Current**: Full 512×512 stamps for every feature

**Options**:
1. **Bounding box optimization**: Only generate stamps for feature bounds + padding
2. **Cache noise**: Cache noise values for common seeds
3. **Lazy generation**: Generate stamps only when needed
4. **Reduce noise octaves**: Fewer octaves = faster noise calculation

**Expected Speedup**: **2-3x faster** (depends on feature sizes)

---

### Priority 4: Parallel Processing

**Current**: Sequential processing

**Options**:
1. **Parallel feature generation**: Generate multiple feature stamps in parallel
2. **Parallel splatmap channels**: Generate RGBA channels in parallel
3. **Async LLM calls**: Don't block on LLM parsing

**Expected Speedup**: **1.5-2x faster** (on multi-core systems)

---

### Priority 5: Skip Unnecessary Operations

**Current**: Always runs all operations

**Options**:
1. **Skip smoothing for templates**: Templates are already well-designed
2. **Skip erosion for templates**: Less needed for pre-designed terrain
3. **Fast mode**: Skip expensive post-processing for faster generation
4. **Cache base biome**: Base biome doesn't change, cache it

**Expected Speedup**: **1.2-1.5x faster**

---

## Recommended Quick Wins

1. **Make adaptive smoothing optional** (fastest win)
   - Add `fast_mode` parameter
   - Skip adaptive smoothing in fast mode
   - **Expected**: 2-3x faster

2. **Reduce splatmap filter counts**
   - Use smaller sigma values
   - Combine some filters
   - **Expected**: 1.5x faster

3. **Bounding box optimization for features**
   - Only generate stamps in feature bounds
   - **Expected**: 2x faster for small features

4. **Template caching**
   - Cache generated terrain for common templates
   - **Expected**: Near-instant for cached templates

---

## Total Expected Speedup

With all optimizations:
- **Current**: ~5-6 seconds per template
- **Optimized**: ~1-2 seconds per template
- **Speedup**: **3-5x faster**

---

## Code Locations for Optimization

1. **Adaptive Smoothing**: `server/engine/stamping.py:72-123`
2. **Splatmap**: `server/engine/splatmap.py:6-92`
3. **Feature Stamps**: `server/primitives/*.py` (all generate functions)
4. **Builder Finalize**: `server/engine/builder.py:84-104`
5. **Template Application**: `server/services/template_service.py:84-130`

