"""Profile the full terrain generation pipeline to find remaining bottlenecks."""
import sys
import os
import time
import cProfile
import pstats
import io
from contextlib import contextmanager

# Set up path
current_dir = os.getcwd()
if os.path.basename(current_dir) == "server":
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
else:
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

import numpy as np
from server.terrain import apply_actions
from server.primitives.base import base_desert

print("=" * 70)
print("FULL PIPELINE PROFILING")
print("=" * 70)

# Profiler setup
profiler = cProfile.Profile()

# Timing context manager
timings = {}

@contextmanager
def time_block(name: str):
    """Context manager for timing code blocks."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        if name not in timings:
            timings[name] = []
        timings[name].append(elapsed)

# Profile full terrain generation
print("\nProfiling full terrain generation...")
print("-" * 70)

state = {
    "seed": 42,
    "features": []
}

# Single run for detailed profiling
profiler.enable()
with time_block("Full Generation"):
    heightmap, updated_state, splatmap = apply_actions(
        "add a mountain in the center and a valley on the left",
        state,
        base_biome_fn=base_desert,
        seed=42
    )
profiler.disable()

print(f"Total time: {timings['Full Generation'][0]:.2f}ms ({timings['Full Generation'][0]/1000:.2f}s)")

# Get profiling stats
s = io.StringIO()
ps = pstats.Stats(profiler, stream=s)
ps.sort_stats('cumulative')
ps.print_stats(50)  # Top 50 functions

print("\n" + "=" * 70)
print("TOP FUNCTIONS BY CUMULATIVE TIME")
print("=" * 70)
print(s.getvalue())

# Get top functions by total time
s2 = io.StringIO()
ps2 = pstats.Stats(profiler, stream=s2)
ps2.sort_stats('tottime')
ps2.print_stats(30)  # Top 30 functions by self time

print("\n" + "=" * 70)
print("TOP FUNCTIONS BY SELF TIME (where time is actually spent)")
print("=" * 70)
print(s2.getvalue())

# Extract key statistics
stats_dict = {}
for func_name, (cc, nc, tt, ct, callers) in ps.stats.items():
    stats_dict[func_name] = {
        'cumulative': ct,
        'total': tt,
        'calls': nc
    }

# Analyze bottlenecks
print("\n" + "=" * 70)
print("BOTTLENECK ANALYSIS")
print("=" * 70)

# Find functions taking > 50ms
bottlenecks = []
for func_name, stats in sorted(stats_dict.items(), key=lambda x: x[1]['cumulative'], reverse=True):
    if stats['cumulative'] > 0.05:  # 50ms
        bottlenecks.append((func_name, stats))

print("\nFunctions taking > 50ms:")
for func_name, stats in bottlenecks[:20]:
    func_str = f"{func_name[0]}:{func_name[1]}" if isinstance(func_name, tuple) else str(func_name)
    print(f"  {stats['cumulative']*1000:8.2f}ms ({stats['calls']:4d} calls) - {func_str}")

# Categorize by module
print("\n" + "=" * 70)
print("TIME BREAKDOWN BY MODULE")
print("=" * 70)

module_times = {}
for func_name, stats in stats_dict.items():
    if isinstance(func_name, tuple):
        module = func_name[0]  # File path
    else:
        module = "unknown"
    
    # Extract module name
    if 'server' in module:
        module_short = module.split('server')[1].replace('\\', '/').split('/')[0] if '/' in module or '\\' in module else module
    else:
        module_short = module
    
    if module_short not in module_times:
        module_times[module_short] = {'cumulative': 0, 'calls': 0}
    module_times[module_short]['cumulative'] += stats['cumulative']
    module_times[module_short]['calls'] += stats['calls']

for module, times in sorted(module_times.items(), key=lambda x: x[1]['cumulative'], reverse=True)[:15]:
    if times['cumulative'] > 0.01:  # 10ms
        print(f"  {module:40s}: {times['cumulative']*1000:8.2f}ms ({times['calls']:4d} calls)")

print("\n" + "=" * 70)

