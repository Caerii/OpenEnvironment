# Additional Critical Issues - What Was Missed

## 🚨 Critical Production Issues

### 1. Race Conditions: State File Corruption

**Problem:**
```python
# main.py lines 71-75
with open(STATE_PATH, "r") as f:
    state = json.load(f)
h, state, splat = apply_actions(cmd.text, state)
with open(STATE_PATH, "w") as f:
    json.dump(state, f, indent=2)
```

**Impact:**
- **Multiple concurrent requests** → Last write wins, others lose changes
- **State corruption** → Partial writes if server crashes mid-write
- **Lost updates** → User A's changes overwritten by User B
- **No locking** → File system doesn't prevent concurrent access

**Example Failure:**
```
Request 1: Reads state {features: [mountain1]}
Request 2: Reads state {features: [mountain1]}  ← Same state!
Request 1: Adds valley → Writes {features: [mountain1, valley]}
Request 2: Adds hill → Writes {features: [mountain1, hill]}  ← Lost valley!
```

**Fix:**
- File locking (fcntl/flock on Unix, msvcrt on Windows)
- Database instead of JSON file (SQLite)
- Atomic writes (write to temp file, then rename)
- Transaction system (lock → read → modify → write → unlock)

### 2. Non-Deterministic Randomness

**Problem:**
```python
# engine/spatial.py line 42
import random
return (random.randint(x0, x1-1), random.randint(y0, y1-1))

# No seed! Uses global random state!
```

**Impact:**
- **Non-reproducible** → Same seed + same state ≠ same result
- **Breaks determinism** → Can't replay sequences
- **Testing impossible** → Can't verify correctness

**Fix:**
```python
# Use NumPy's seeded RNG
rng = np.random.RandomState(seed)
return (rng.randint(x0, x1), rng.randint(y0, y1))
```

### 3. Normalization Edge Cases

**Problem:**
```python
# utils.py normalize01()
def normalize01(h: np.ndarray) -> np.ndarray:
    h = h - h.min()
    mx = h.max() or 1.0  # ← Handles flat terrain, but...
    return h / mx
```

**Issues:**
- **NaN/Inf values** → Not handled (could come from bad math)
- **All zeros** → Divides by 1.0 (correct, but no validation)
- **Empty arrays** → Would crash
- **Negative values** → Could produce negative normalized values

**Fix:**
```python
def normalize01(h: np.ndarray) -> np.ndarray:
    # Handle empty arrays
    if h.size == 0:
        return h
    
    # Handle NaN/Inf
    if np.any(np.isnan(h)) or np.any(np.isinf(h)):
        raise ValueError("Heightmap contains NaN or Inf values")
    
    # Normalize
    h_min = h.min()
    h_max = h.max()
    
    if h_max == h_min:
        return np.zeros_like(h)  # Flat terrain → all zeros
    
    return (h - h_min) / (h_max - h_min)
```

### 4. No Error Handling in API

**Problem:**
```python
@app.post("/api/generate")
def generate(cmd: Command):
    with open(STATE_PATH, "r") as f:  # ← Could fail!
        state = json.load(f)  # ← Could fail!
    h, state, splat = apply_actions(cmd.text, state)  # ← Could fail!
    with open(STATE_PATH, "w") as f:  # ← Could fail!
        json.dump(state, f, indent=2)
    # ... no try/except!
```

**Impact:**
- **Server crashes** on invalid JSON
- **500 errors** with no user feedback
- **State corruption** if write fails mid-stream
- **No rollback** on partial failures

**Fix:**
```python
@app.post("/api/generate")
def generate(cmd: Command):
    try:
        # Validate input
        if not cmd.text or len(cmd.text.strip()) == 0:
            raise HTTPException(400, "Command cannot be empty")
        
        # Atomic state read
        try:
            with open(STATE_PATH, "r") as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {"features": [], "seed": 0}
        except json.JSONDecodeError as e:
            raise HTTPException(500, f"Invalid state file: {e}")
        
        # Generate terrain
        try:
            h, state, splat = apply_actions(cmd.text, state)
        except Exception as e:
            logger.error("Terrain generation failed", exc_info=e)
            raise HTTPException(500, f"Generation failed: {str(e)}")
        
        # Atomic state write
        temp_path = STATE_PATH + ".tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(state, f, indent=2)
            os.replace(temp_path, STATE_PATH)  # Atomic rename
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(500, f"State save failed: {e}")
        
        # Save outputs
        tag = str(int(time.time() * 1000))  # Millisecond precision
        urls = save_outputs(h, splat, tag)
        
        return {"ok": True, "state": state, "assets": urls}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in generate", exc_info=e)
        raise HTTPException(500, "Internal server error")
```

### 5. Resource Leaks: File Accumulation

**Problem:**
```python
# main.py save_outputs()
tag = str(int(time.time()))  # ← Timestamp-based filenames
# Files accumulate forever!
```

**Impact:**
- **Disk space exhaustion** → Thousands of PNG files
- **No cleanup** → Old files never deleted
- **Performance degradation** → Directory listing slows down
- **No retention policy** → All files kept forever

**Fix:**
- Keep only last N files (e.g., last 10)
- Cleanup old files on startup
- Use UUIDs instead of timestamps (avoid collisions)
- Implement retention policy

### 6. Timestamp Collisions

**Problem:**
```python
tag = str(int(time.time()))  # ← Second precision!
# Multiple requests in same second → same filename → overwrite!
```

**Impact:**
- **Lost outputs** → Concurrent requests overwrite each other
- **Race conditions** → Request 1's files replaced by Request 2
- **No uniqueness** → Can't have multiple generations per second

**Fix:**
```python
import uuid
tag = str(uuid.uuid4())  # Guaranteed unique

# Or with timestamp + counter
from threading import Lock
_counter = 0
_counter_lock = Lock()

def get_unique_tag():
    global _counter
    with _counter_lock:
        _counter += 1
        return f"{int(time.time() * 1000)}_{_counter}"
```

### 7. Frontend Error Handling

**Problem:**
```typescript
// App.tsx - Errors are logged but not shown
catch (error) {
  console.error('Failed to load last terrain:', error)
  // User sees nothing!
}
```

**Impact:**
- **Silent failures** → User doesn't know what went wrong
- **Poor UX** → No feedback on errors
- **No retry logic** → Network errors are permanent

**Fix:**
- Show error messages to user
- Retry logic for transient failures
- Graceful degradation (show last known state)

### 8. Input Validation Missing

**Problem:**
```python
class Command(BaseModel):
    text: str  # ← Only validates it's a string!

# No length limits, no content validation
```

**Impact:**
- **DoS attacks** → Huge strings could crash server
- **Invalid commands** → Parsed but produce garbage
- **No sanitization** → Could inject malicious content

**Fix:**
```python
from pydantic import Field, validator

class Command(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Command cannot be empty or whitespace")
        # Could add more validation (no SQL injection, etc.)
        return v.strip()
```

### 9. LLM Error Handling

**Problem:**
```python
# parser.py - Silently falls back
except Exception as e:
    print(f"LLM parsing failed: {e}, falling back to regex parser")
    return self._fallback_parse(command)
```

**Impact:**
- **No user notification** → User doesn't know LLM failed
- **No retry logic** → Temporary API failures are permanent
- **No cost tracking** → Can't monitor LLM usage
- **No rate limiting** → Could hit API limits

**Fix:**
- Retry logic with exponential backoff
- User notification when LLM unavailable
- Cost tracking/metrics
- Rate limiting

### 10. Splatmap Edge Cases

**Problem:**
```python
# splatmap.py line 32
snow = np.clip((heightmap - h90) / (max(1e-6, h97 - h90)), 0, 1)
# If h90 == h97 (flat terrain), divides by 1e-6 → could produce huge values
```

**Impact:**
- **Invalid splatmap** → Could have negative or >1.0 values before normalization
- **Flat terrain** → Unnatural texture assignment
- **Edge cases** → Not handled gracefully

**Fix:**
```python
# Better handling for flat terrain
if h97 - h90 < 1e-6:
    # Flat terrain → no snow
    snow = np.zeros_like(heightmap)
else:
    snow = np.clip((heightmap - h90) / (h97 - h90), 0, 1)
```

### 11. Determinism: Seed Usage Inconsistency

**Problem:**
```python
# Some places use seed correctly
generate_dunes(..., seed=seed)

# But dunes use seed+17 hack
n = pnoise2(..., base=seed+17)  # ← Why +17?
```

**Impact:**
- **Non-deterministic** → Same seed produces different results
- **Hard to debug** → Can't reproduce issues
- **Magic numbers** → No documentation for why +17

**Fix:**
- Use deterministic seed derivation
- Hash feature ID + global seed for feature-specific seeds
- Document seed derivation strategy

### 12. Missing Bounds Checking

**Problem:**
```python
# terrain.py _create_feature()
return {"type": "mountain", "x": cx, "y": cy, "radius": radius, ...}
# No validation that x, y, radius are in valid ranges!
```

**Impact:**
- **Array out of bounds** → Could crash on invalid coordinates
- **Invalid features** → Could create features outside terrain
- **Runtime errors** → Should be caught at creation time

**Fix:**
```python
def _create_feature(ftype: str, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
    # Validate coordinates
    if not (0 <= cx < RES and 0 <= cy < RES):
        raise ValueError(f"Coordinates ({cx}, {cy}) out of bounds [0, {RES})")
    
    # Validate radius
    if radius < 1 or radius > RES:
        raise ValueError(f"Radius {radius} out of valid range [1, {RES}]")
    
    # ... rest of creation
```

### 13. No Concurrency Control

**Problem:**
- Multiple requests can run simultaneously
- No queuing system
- No request cancellation
- No priority handling

**Impact:**
- **Race conditions** → State corruption
- **Resource exhaustion** → Too many simultaneous generations
- **No cancellation** → Can't stop long-running operations

**Fix:**
- Request queue (Celery, etc.)
- Single-threaded generation (mutex lock)
- Request cancellation support
- Priority queue for operations

### 14. Frontend-Backend Sync Issues

**Problem:**
- Frontend auto-loads on mount
- But what if backend is generating?
- No WebSocket for real-time updates
- Timestamp-based cache busting (`?t=${Date.now()}`) is hacky

**Impact:**
- **Stale data** → Frontend shows old terrain
- **Race conditions** → Load happens during generation
- **No real-time updates** → Must poll or refresh

**Fix:**
- WebSocket for real-time updates
- Proper cache headers
- ETags for conditional requests
- Generation status endpoint

### 15. Asset File Management

**Problem:**
- No cleanup of old asset files
- No file organization
- No metadata tracking
- No compression

**Impact:**
- **Disk space** → Unlimited growth
- **Performance** → Directory listing slows
- **Organization** → Hard to find specific files
- **Storage** → Uncompressed PNGs waste space

**Fix:**
- Cleanup policy (keep last N, delete older)
- Organize by date/user/session
- Metadata database (SQLite)
- Compression for old files

---

## 🔧 Missing Infrastructure

### 1. Logging System
- **Current**: `print()` statements
- **Need**: Structured logging (logging module)
- **Impact**: Can't debug production issues

### 2. Monitoring & Metrics
- **Current**: No metrics
- **Need**: Generation time, error rates, LLM usage
- **Impact**: Can't optimize or detect issues

### 3. Testing Infrastructure
- **Current**: No tests
- **Need**: Unit tests, integration tests, visual regression tests
- **Impact**: Can't verify correctness or prevent regressions

### 4. Configuration Management
- **Current**: Hardcoded values
- **Need**: Environment-based config, feature flags
- **Impact**: Can't tune without code changes

### 5. Documentation
- **Current**: Some markdown files
- **Need**: API docs, architecture diagrams, user guides
- **Impact**: Hard to onboard new developers

---

## 🎯 Priority Fixes

### Critical (Fix Immediately)
1. **Race conditions** → File locking or database
2. **Non-deterministic randomness** → Use NumPy seeded RNG
3. **Error handling** → Try/except in all endpoints
4. **Input validation** → Pydantic validators

### High Priority
5. **File accumulation** → Cleanup policy
6. **Timestamp collisions** → UUIDs or better tag generation
7. **Frontend error display** → User-friendly error messages
8. **Bounds checking** → Validate all inputs

### Medium Priority
9. **LLM error handling** → Retry logic, notifications
10. **Normalization edge cases** → Handle NaN/Inf/flat terrain
11. **Splatmap edge cases** → Better handling for edge cases
12. **Logging** → Structured logging system

### Low Priority
13. **Concurrency control** → Request queue
14. **Asset management** → File organization, compression
15. **Monitoring** → Metrics collection

---

## 🏗️ Production Readiness Checklist

Before deploying to production:

- [ ] Fix race conditions (file locking or database)
- [ ] Add comprehensive error handling
- [ ] Implement input validation
- [ ] Add logging system
- [ ] Fix non-deterministic randomness
- [ ] Add file cleanup policy
- [ ] Implement bounds checking
- [ ] Add monitoring/metrics
- [ ] Write tests (unit + integration)
- [ ] Add retry logic for external APIs
- [ ] Implement concurrency control
- [ ] Add request timeout handling
- [ ] Implement graceful degradation
- [ ] Add rate limiting
- [ ] Security audit (CORS, input sanitization)

---

This document identifies **production-critical issues** that could cause data loss, crashes, or security vulnerabilities. These should be fixed before any real-world deployment.

