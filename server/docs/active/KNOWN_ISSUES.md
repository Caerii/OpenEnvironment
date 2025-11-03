# Known Issues & Missing Features

**Last Updated:** November 3, 2025

This document tracks critical bugs, missing features, and production issues that need attention.

---

## 🚨 Critical Issues (Fix Immediately)

### 1. Race Conditions: State File Corruption
**Problem:** Multiple concurrent requests can corrupt `terrain_state.json`
- No file locking mechanism
- Last write wins, others lose changes
- Partial writes if server crashes

**Fix:** Implement file locking (fcntl/msvcrt) or use SQLite

---

### 2. Scene Graph Cleanup on Feature Removal
**Problem:** When features are removed, scene graph isn't cleaned up:
- Entities still reference deleted features
- Feature nodes remain in scene graph  
- Orphaned relationships

**Fix:** Call `scene_graph.remove_feature()` and cleanup entities after removal

**Files:** `server/terrain.py`, `server/semantic/scene/integration.py`

---

### 3. Non-Deterministic Randomness
**Problem:** `engine/spatial.py` uses Python's `random` module (not seeded)
- Same seed ≠ same result
- Breaks determinism guarantee
- Testing impossible

**Fix:** Use `np.random.RandomState(seed)` everywhere

---

### 4. No Error Handling in API
**Problem:** API endpoints lack try/except blocks
- Server crashes on invalid JSON
- No user feedback on errors
- State corruption on write failures

**Fix:** Wrap endpoints in comprehensive error handling

---

## ⚠️ High Priority

### 5. Resource Leaks: File Accumulation
Generated PNGs accumulate forever (no cleanup policy)

**Fix:** Keep only last N files, cleanup old files on startup

---

### 6. Timestamp Collisions
Multiple requests in same second overwrite files

**Fix:** Use UUIDs or millisecond precision + counter

---

### 7. Input Validation Missing
`Command` model doesn't validate length or content

**Fix:** Add Pydantic validators (min_length, max_length, sanitization)

---

### 8. Bounds Checking Missing
Feature coordinates not validated (can create out-of-bounds features)

**Fix:** Validate x, y, radius before feature creation

---

### 9. Testing & Validation
No comprehensive tests for scene graph, relationships, or query operations

**Fix:** Add unit tests + integration tests

---

## 🔧 Medium Priority

### 10. Entity Update on Feature Modification
When features modified, entity metadata isn't updated

**Fix:** Update entities when features change position/properties

---

### 11. Reset/Clear Operations
Terrain reset doesn't clear scene graph (stale entities remain)

**Fix:** Create fresh `TerrainSceneGraph()` on reset

---

### 12. Error Recovery
No rollback mechanism if operations fail partially

**Fix:** Implement atomic operations with rollback

---

### 13. LLM Error Handling
Silent fallback to regex parser, no user notification

**Fix:** Add retry logic, user notifications, cost tracking

---

### 14. Normalization Edge Cases
`normalize01()` doesn't handle NaN/Inf values

**Fix:** Add validation for NaN/Inf, handle flat terrain edge case

---

### 15. Frontend Query Integration
Spatial queries work in backend but not exposed to frontend

**Fix:** Add `POST /api/query` endpoint + UI integration

---

## ⬇️ Low Priority

### 16. Relationship Update on Entity Modification
When entities updated, relationships aren't recalculated

### 17. Entity ID Uniqueness Edge Cases
Rapid successive commands might create duplicate IDs

### 18. Concurrency Control
No request queuing or cancellation support

### 19. Frontend-Backend Sync
No WebSocket for real-time updates (uses hacky cache busting)

### 20. Asset File Management
No file organization, metadata tracking, or compression

---

## 🏗️ Missing Infrastructure

- **Logging:** Using `print()` instead of proper logging module
- **Monitoring:** No metrics collection (generation time, error rates, LLM usage)
- **Configuration:** Hardcoded values instead of env-based config
- **Documentation:** API docs incomplete

---

## 🎯 Recommended Implementation Order

### Phase 1: Critical (2-3 hours)
1. File locking for state
2. Scene graph cleanup on removal
3. Fix non-deterministic randomness
4. Add API error handling

### Phase 2: High Priority (2-3 hours)
5. File cleanup policy
6. Input validation
7. Bounds checking
8. Basic testing

### Phase 3: Polish (3-4 hours)
9. Entity/relationship updates
10. Reset operations
11. Frontend integration
12. LLM error handling

**Total:** ~8-10 hours to address critical issues

---

## 🏁 Production Readiness Checklist

Before deploying:
- [ ] Fix race conditions
- [ ] Add comprehensive error handling
- [ ] Implement input validation
- [ ] Fix non-deterministic randomness
- [ ] Add file cleanup policy
- [ ] Implement bounds checking
- [ ] Add logging system
- [ ] Write tests (unit + integration)
- [ ] Security audit (CORS, input sanitization)

