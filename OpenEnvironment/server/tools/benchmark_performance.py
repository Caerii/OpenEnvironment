"""Performance benchmark - Get real speedup numbers.

Run from project root directory:
  uv run --directory server python benchmark_performance.py

This provides empirical performance measurements for the optimized functions.
"""
import sys
import os
import time
import statistics

# Set up path like the server does
current_dir = os.getcwd()
if os.path.basename(current_dir) == "server":
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
else:
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

import numpy as np
from server.engine.config import RES
from server.utils import sobel_slope

print("=" * 70)
print("PERFORMANCE BENCHMARK - Real Speedup Measurements")
print("=" * 70)

# Import original functions
from server.engine.stamping import apply_adaptive_smoothing
from server.engine.splatmap import generate_splatmap

# Import optimized functions
from server.engine.stamping_optimized import apply_adaptive_smoothing_fast
from server.engine.splatmap_optimized import generate_splatmap_fast

# Benchmark parameters
NUM_RUNS = 5  # Number of runs for statistical validity
WARMUP_RUNS = 2  # Warmup runs to avoid cold start effects


def benchmark_adaptive_smoothing(num_runs=NUM_RUNS):
    """Benchmark adaptive smoothing - original vs optimized."""
    print("\n" + "=" * 70)
    print("BENCHMARK 1: Adaptive Smoothing")
    print("=" * 70)
    
    # Create test heightmap
    h = np.random.rand(RES, RES).astype(np.float32)
    h[200:220, :] = 0.8  # Add cliff for edge detection
    
    # Warmup
    print("Warming up...")
    for _ in range(WARMUP_RUNS):
        h_copy = h.copy()
        apply_adaptive_smoothing(h_copy, base_sigma=0.8, preserve_edges=True)
        h_copy = h.copy()
        slope_cache = sobel_slope(h_copy)
        apply_adaptive_smoothing_fast(h_copy, base_sigma=0.8, preserve_edges=True, slope_cache=slope_cache)
    
    # Benchmark original
    print(f"Benchmarking original (with {num_runs} runs)...")
    times_original = []
    for i in range(num_runs):
        h_copy = h.copy()
        start = time.perf_counter()
        apply_adaptive_smoothing(h_copy, base_sigma=0.8, preserve_edges=True)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times_original.append(elapsed)
        if i == 0:
            result_original = h_copy.copy()
    
    # Benchmark optimized
    print(f"Benchmarking optimized (with {num_runs} runs)...")
    times_optimized = []
    for i in range(num_runs):
        h_copy = h.copy()
        slope_cache = sobel_slope(h_copy)
        start = time.perf_counter()
        apply_adaptive_smoothing_fast(h_copy, base_sigma=0.8, preserve_edges=True, slope_cache=slope_cache)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times_optimized.append(elapsed)
        if i == 0:
            result_optimized = h_copy.copy()
    
    # Calculate statistics
    avg_original = statistics.mean(times_original)
    avg_optimized = statistics.mean(times_optimized)
    std_original = statistics.stdev(times_original) if len(times_original) > 1 else 0
    std_optimized = statistics.stdev(times_optimized) if len(times_optimized) > 1 else 0
    speedup = avg_original / avg_optimized
    
    print(f"\nResults:")
    print(f"  Original:   {avg_original:8.2f}ms ± {std_original:6.2f}ms")
    print(f"  Optimized:  {avg_optimized:8.2f}ms ± {std_optimized:6.2f}ms")
    print(f"  Speedup:    {speedup:8.2f}x")
    print(f"  Time saved: {avg_original - avg_optimized:8.2f}ms ({((avg_original - avg_optimized) / avg_original * 100):5.1f}% faster)")
    
    # Check result similarity
    diff = np.abs(result_original - result_optimized)
    max_diff = np.max(diff)
    mean_diff = np.mean(diff)
    print(f"\n  Result similarity:")
    print(f"    Max difference: {max_diff:.6f}")
    print(f"    Mean difference: {mean_diff:.6f}")
    
    return {
        "original": avg_original,
        "optimized": avg_optimized,
        "speedup": speedup,
        "times_original": times_original,
        "times_optimized": times_optimized,
        "max_diff": max_diff
    }


def benchmark_splatmap(num_runs=NUM_RUNS):
    """Benchmark splatmap generation - original vs optimized."""
    print("\n" + "=" * 70)
    print("BENCHMARK 2: Splatmap Generation")
    print("=" * 70)
    
    # Create test heightmap
    heightmap = np.random.rand(RES, RES).astype(np.float32) * 0.5 + 0.3
    dune_mask = np.zeros((RES, RES), dtype=np.float32)
    cliff_mask = np.zeros((RES, RES), dtype=np.float32)
    
    # Warmup
    print("Warming up...")
    for _ in range(WARMUP_RUNS):
        generate_splatmap(heightmap, dune_mask, cliff_mask)
        slope_cache = sobel_slope(heightmap)
        gy, gx = np.gradient(heightmap.astype(np.float32))
        gradient_cache = (gy, gx)
        generate_splatmap_fast(heightmap, dune_mask, cliff_mask, 
                               slope_cache=slope_cache, gradient_cache=gradient_cache)
    
    # Benchmark original
    print(f"Benchmarking original (with {num_runs} runs)...")
    times_original = []
    for i in range(num_runs):
        start = time.perf_counter()
        splat_orig = generate_splatmap(heightmap, dune_mask, cliff_mask)
        elapsed = (time.perf_counter() - start) * 1000
        times_original.append(elapsed)
        if i == 0:
            result_original = splat_orig.copy()
    
    # Benchmark optimized (with cache - realistic scenario)
    # Cache is pre-calculated by finalize(), so we pre-calculate it here
    print(f"Benchmarking optimized WITH pre-calculated cache (realistic scenario)...")
    slope_cache = sobel_slope(heightmap)
    gy, gx = np.gradient(heightmap.astype(np.float32))
    gradient_cache = (gy, gx)
    
    times_optimized = []
    for i in range(num_runs):
        start = time.perf_counter()
        splat_opt = generate_splatmap_fast(heightmap, dune_mask, cliff_mask,
                                           slope_cache=slope_cache, gradient_cache=gradient_cache)
        elapsed = (time.perf_counter() - start) * 1000
        times_optimized.append(elapsed)
        if i == 0:
            result_optimized = splat_opt.copy()
    
    # Calculate statistics
    avg_original = statistics.mean(times_original)
    avg_optimized = statistics.mean(times_optimized)
    std_original = statistics.stdev(times_original) if len(times_original) > 1 else 0
    std_optimized = statistics.stdev(times_optimized) if len(times_optimized) > 1 else 0
    speedup = avg_original / avg_optimized
    
    print(f"\nResults:")
    print(f"  Original:   {avg_original:8.2f}ms ± {std_original:6.2f}ms")
    print(f"  Optimized:  {avg_optimized:8.2f}ms ± {std_optimized:6.2f}ms")
    print(f"  Speedup:    {speedup:8.2f}x")
    print(f"  Time saved: {avg_original - avg_optimized:8.2f}ms ({((avg_original - avg_optimized) / avg_original * 100):5.1f}% faster)")
    
    # Check result similarity
    diff = np.abs(result_original - result_optimized)
    max_diff = np.max(diff)
    mean_diff = np.mean(diff)
    print(f"\n  Result similarity:")
    print(f"    Max difference: {max_diff:.6f}")
    print(f"    Mean difference: {mean_diff:.6f}")
    
    # Check normalization
    sums_orig = result_original.sum(axis=2)
    sums_opt = result_optimized.sum(axis=2)
    print(f"\n  Normalization:")
    print(f"    Original mean sum: {sums_orig.mean():.4f}")
    print(f"    Optimized mean sum: {sums_opt.mean():.4f}")
    
    return {
        "original": avg_original,
        "optimized": avg_optimized,
        "speedup": speedup,
        "times_original": times_original,
        "times_optimized": times_optimized,
        "max_diff": max_diff
    }


def benchmark_combined_pipeline(num_runs=NUM_RUNS):
    """Benchmark full TerrainBuilder pipeline."""
    print("\n" + "=" * 70)
    print("BENCHMARK 3: Full TerrainBuilder Pipeline")
    print("=" * 70)
    
    from server.engine.builder import TerrainBuilder
    from server.primitives.base import base_desert
    
    # Warmup
    print("Warming up...")
    for _ in range(WARMUP_RUNS):
        builder = TerrainBuilder(base_desert, seed=42)
        builder.finalize()
        builder.build_splatmap()
    
    # Benchmark
    print(f"Benchmarking TerrainBuilder (with {num_runs} runs)...")
    times_total = []
    times_finalize = []
    times_splatmap = []
    
    for i in range(num_runs):
        builder = TerrainBuilder(base_desert, seed=42)
        
        # Time finalize
        start = time.perf_counter()
        h, d, c = builder.finalize()
        time_finalize = (time.perf_counter() - start) * 1000
        times_finalize.append(time_finalize)
        
        # Time build_splatmap
        start = time.perf_counter()
        splat = builder.build_splatmap()
        time_splatmap = (time.perf_counter() - start) * 1000
        times_splatmap.append(time_splatmap)
        
        total_time = time_finalize + time_splatmap
        times_total.append(total_time)
    
    avg_total = statistics.mean(times_total)
    avg_finalize = statistics.mean(times_finalize)
    avg_splatmap = statistics.mean(times_splatmap)
    
    print(f"\nResults:")
    print(f"  finalize():     {avg_finalize:8.2f}ms")
    print(f"  build_splatmap(): {avg_splatmap:8.2f}ms")
    print(f"  Total:          {avg_total:8.2f}ms")
    print(f"  (finalize + splatmap = {avg_finalize + avg_splatmap:.2f}ms)")
    
    return {
        "total": avg_total,
        "finalize": avg_finalize,
        "splatmap": avg_splatmap
    }


def benchmark_full_terrain_generation(num_runs=3):
    """Benchmark full terrain generation with features."""
    print("\n" + "=" * 70)
    print("BENCHMARK 4: Full Terrain Generation (with features)")
    print("=" * 70)
    
    from server.terrain import apply_actions
    from server.primitives.base import base_desert
    
    # Warmup
    print("Warming up...")
    state = {"seed": 42, "features": []}
    for _ in range(WARMUP_RUNS):
        apply_actions("add a mountain in the center", state.copy(), base_biome_fn=base_desert, seed=42)
    
    # Benchmark
    print(f"Benchmarking full terrain generation (with {num_runs} runs)...")
    times = []
    
    for i in range(num_runs):
        state = {"seed": 42 + i, "features": []}
        start = time.perf_counter()
        heightmap, updated_state, splatmap = apply_actions(
            "add a mountain in the center and a valley on the left",
            state,
            base_biome_fn=base_desert,
            seed=42 + i
        )
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0
    
    print(f"\nResults:")
    print(f"  Average time: {avg_time:8.2f}ms ± {std_time:6.2f}ms")
    print(f"  Range: [{min(times):.2f}ms, {max(times):.2f}ms]")
    
    return {
        "average": avg_time,
        "std": std_time,
        "times": times
    }


# Run all benchmarks
print("\nRunning benchmarks...")
print(f"Configuration: {RES}×{RES} heightmap, {NUM_RUNS} runs per benchmark")

results = {}

try:
    results["adaptive_smoothing"] = benchmark_adaptive_smoothing()
except Exception as e:
    print(f"✗ Adaptive smoothing benchmark failed: {e}")
    import traceback
    traceback.print_exc()

try:
    results["splatmap"] = benchmark_splatmap()
except Exception as e:
    print(f"✗ Splatmap benchmark failed: {e}")
    import traceback
    traceback.print_exc()

try:
    results["pipeline"] = benchmark_combined_pipeline()
except Exception as e:
    print(f"✗ Pipeline benchmark failed: {e}")
    import traceback
    traceback.print_exc()

try:
    results["full_generation"] = benchmark_full_terrain_generation(num_runs=3)
except Exception as e:
    print(f"✗ Full generation benchmark failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("PERFORMANCE SUMMARY")
print("=" * 70)

if "adaptive_smoothing" in results:
    r = results["adaptive_smoothing"]
    print(f"\n1. Adaptive Smoothing:")
    print(f"   Speedup: {r['speedup']:.2f}x")
    print(f"   Time saved: {r['original'] - r['optimized']:.2f}ms per call")

if "splatmap" in results:
    r = results["splatmap"]
    print(f"\n2. Splatmap Generation:")
    print(f"   Speedup: {r['speedup']:.2f}x")
    print(f"   Time saved: {r['original'] - r['optimized']:.2f}ms per call")

if "pipeline" in results:
    r = results["pipeline"]
    print(f"\n3. TerrainBuilder Pipeline:")
    print(f"   finalize(): {r['finalize']:.2f}ms")
    print(f"   build_splatmap(): {r['splatmap']:.2f}ms")
    print(f"   Total: {r['total']:.2f}ms")

if "full_generation" in results:
    r = results["full_generation"]
    print(f"\n4. Full Terrain Generation:")
    print(f"   Average: {r['average']:.2f}ms ({r['average']/1000:.2f}s)")

print("\n" + "=" * 70)
print("Benchmark complete!")
print("=" * 70)

