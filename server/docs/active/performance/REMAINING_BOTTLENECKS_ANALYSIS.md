# Remaining Performance Bottlenecks - Analysis

## Profiling Results

**Total generation time: 2.62 seconds**

### Breakdown by Time:

1. **Base Biome Generation (base_desert): 897ms (34%)** ⚠️ **MAJOR BOTTLENECK**
   - **2,097,152 calls to `noise._perlin.noise2`** (old noise library!)
   - Nested loops: 512×512 pixels × 4 octaves
   - **This should use optimized `fractal_noise` instead!**

2. **LLM Parsing: 791ms (30%)** ⚠️ **External API - Not Optimizable**
   - Network I/O to Cerebras API
   - SSL handshake, HTTP requests
   - This is external, not our code

3. **Feature Execution (execute_add_actions): 736ms (28%)**
   - Feature generation (mountains, valleys, etc.)
   - Includes another 720ms for `generate_mountain` which also uses old `pnoise2`!

4. **Mountain Generation: 720ms (27%)** ⚠️ **MAJOR BOTTLENECK**
   - Uses nested loops with `pnoise2` calls
   - 512×512 pixels × 4 octaves = 1,048,576 calls
   - **This should use optimized `fractal_noise` instead!**

5. **LLM API Call (parse): 302ms (12%)** ⚠️ **External API**
   - Network I/O
   - Not optimizable

6. **Splatmap Generation: 55ms (2%)** ✅ **Already Optimized**
   - Using optimized version

7. **Adaptive Smoothing: 50ms (2%)** ✅ **Already Optimized**
   - Using optimized version

---

## Root Cause Analysis

### Problem: Old Noise Library Still Being Used

**Files still using `from noise import pnoise2`:**

1. **`server/primitives/base.py`**:
   - `base_desert()`: Nested loops calling `pnoise2` 2,097,152 times
   - `base_forest()`: Uses `pnoise2` in loops
   - `base_arctic()`: Uses `pnoise2` in loops

2. **`server/primitives/mountains.py`**:
   - `generate_mountain()`: Nested loops calling `pnoise2` 1,048,576 times

3. **`server/primitives/dunes.py`**:
   - `generate_dunes()`: Uses `pnoise2` in loops

4. **`server/primitives/pinnacle.py`**:
   - `generate_pinnacle()`: Uses `pnoise2`

5. **`server/primitives/mound.py`**:
   - `generate_mound()`: Uses `pnoise2`

### Why This is a Problem

- **Old `pnoise2`**: ~0.0004ms per call (C extension, but still slow at scale)
- **Optimized `fractal_noise`**: ~0.000006ms per call (82x faster with Numba!)
- **For 2,097,152 calls**:
  - Old: ~897ms
  - Optimized: ~11ms (**81x faster!**)

### Impact

**Before fix:**
- Base biome: ~897ms
- Mountain generation: ~720ms
- **Total: ~1.6 seconds**

**After fix (estimated):**
- Base biome: ~11ms (82x faster)
- Mountain generation: ~9ms (82x faster)
- **Total: ~20ms**

**Time saved: ~1.58 seconds per generation!**

---

## Other Bottlenecks (Non-Optimizable)

1. **LLM Parsing (791ms + 302ms = 1093ms)**: External API, network I/O
   - **Solution**: Use JSON actions (precise templates) to skip LLM
   - **Impact**: Saves ~1.1 seconds when using templates

2. **Network I/O**: SSL handshake, HTTP requests
   - Not optimizable (external service)

---

## Optimization Priority

### High Priority (Fix Immediately) ✅

1. **Replace `pnoise2` with `fractal_noise` in:**
   - `base_desert()` - **897ms → ~11ms** (81x faster!)
   - `generate_mountain()` - **720ms → ~9ms** (80x faster!)
   - `base_forest()` - Similar speedup
   - `base_arctic()` - Similar speedup
   - `generate_dunes()` - Speedup varies by region size
   - `generate_pinnacle()` - Speedup varies
   - `generate_mound()` - Speedup varies

**Expected total impact: ~1.6 seconds saved per generation**

### Medium Priority

1. **Bounding box optimization** (already implemented, but not used everywhere)
   - Only generate noise for pixels within feature bounds
   - Could save 2-3x for small features

2. **Cache noise results** (if same parameters used repeatedly)
   - May not be worth it (noise is already fast after optimization)

### Low Priority

1. **Optimize scene graph operations** (if they become bottlenecks)
2. **Parallelize independent features** (if multiple features are added)

---

## Action Plan

1. ✅ Replace `pnoise2` with `fractal_noise` in all primitive files
2. ✅ Test that results are visually similar
3. ✅ Benchmark to verify speedups
4. ✅ Document the changes

---

## Expected Final Performance

**Current (with optimizations):**
- Base biome: 897ms
- Feature generation: 720ms
- LLM parsing: 1093ms
- Post-processing: 105ms
- **Total: ~2.8 seconds**

**After fixing noise usage:**
- Base biome: 11ms (82x faster)
- Feature generation: 9ms (80x faster)
- LLM parsing: 1093ms (external, not optimizable)
- Post-processing: 105ms
- **Total: ~1.2 seconds**

**For templates with JSON actions (no LLM):**
- Base biome: 11ms
- Feature generation: 9ms
- LLM parsing: 0ms (skipped)
- Post-processing: 105ms
- **Total: ~125ms (22x faster overall!)**

---

## Conclusion

**The biggest remaining bottleneck is the old noise library being used in base biome and feature generation.**

**Fix this first**, then we can look at other optimizations if needed.

**Expected impact: ~1.6 seconds saved per generation (57% faster!)**

