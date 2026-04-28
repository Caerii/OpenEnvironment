# Session & Asset Management - How It Works

## 🎯 Current Architecture (Working Correctly!)

### Backend Asset Management

#### 1. **Timestamped Filenames** ✅
Every terrain generation creates NEW files with timestamps:
```
/assets/height_1762539474_16.png   ← timestamp in filename
/assets/height_1762539474_8.png
/assets/splat_1762539474.png
```

**Why?** 
- Prevents browser cache issues
- Allows rollback to previous terrains
- Each generation is immutable

#### 2. **State Persistence** ✅
Backend maintains a single source of truth:
```json
// server/out/terrain_state.json
{
  "features": [...],              // All terrain features
  "seed": 905110303,              // Current seed
  "semantic_scene": {...},        // Scene graph with entities
  "next_id": 25                   // Next feature ID
}
```

**Why?**
- Survives server restarts
- Enables terrain modifications (add/remove features)
- Tracks semantic entities and relationships

#### 3. **Asset Cleanup** ✅
Old assets are cleaned up based on retention policies:
```python
# server/engine/cleanup.py
- Keep last N generations (default: 10)
- Delete files older than X days (default: 7)
- Preserve currently-used assets
```

---

### Frontend Asset Management

#### 1. **Zustand State Store** ✅
Single source of truth for UI state:
```typescript
// web/src/state.ts
{
  assets: {                       // Current asset URLs
    height8: "/assets/height_XXX_8.png",
    height16: "/assets/height_XXX_16.png",
    splat: "/assets/splat_XXX.png",
    voxel_obj?: "/assets/voxel_XXX.obj",
    voxel_bin?: "/assets/voxel_XXX.bin"
  },
  stateJson: {...},               // Full terrain state (features, entities)
  voxelMode: false,               // Display mode
  seed: -1,                       // User's seed preference (-1 = auto)
  biome: "desert",                // Base biome
  lastGeneratedSeed: null         // Actual seed when seed=-1
}
```

#### 2. **Cache Busting** ✅
Frontend adds timestamps to force texture reloads:
```typescript
// web/src/components/TerrainViewer.tsx
const tex = texLoader.load(url + `?t=${Date.now()}`, ...)
```

**Why?**
- Forces browser to fetch new textures even if filename matches
- Ensures you always see the latest terrain
- Handles edge cases where timestamps overlap

#### 3. **Auto-Load on Mount** ✅
```typescript
// web/src/App.tsx:60-85
useEffect(() => {
  async function loadLastTerrain() {
    const res = await regenerateTerrain(voxelMode, voxelResolution)
    setAssets(res.assets)      // Load current assets
    setStateJson(res.state)    // Load current state
  }
  loadLastTerrain()
}, []) // Run once on mount
```

**Result:** When you refresh the page, it loads the latest terrain from backend.

---

## 🔄 Session Flow

### Normal UI Flow (Working Perfectly)

```
User types command → Click "Generate"
    ↓
Frontend calls postCommand(text, voxel, resolution, seed, biome)
    ↓
Backend:
  1. Parse command → actions
  2. Execute actions → update state
  3. Build terrain → generate heightmap/splatmap
  4. Save assets with timestamp → /assets/height_TIME_16.png
  5. Save state → terrain_state.json
  6. Return { assets: {...}, state: {...} }
    ↓
Frontend:
  1. setAssets(res.assets)    → Update Zustand store
  2. setStateJson(res.state)  → Update Zustand store
    ↓
React re-renders:
  1. TerrainViewer sees new assets
  2. Loads textures with cache-busting ?t=NOW
  3. Updates 3D mesh with new heightmap/splatmap
```

**✅ This flow works perfectly!**

---

### Postman/Direct API Flow (Was Broken, Now Fixed!)

#### ❌ The Problem:
```
Postman → POST /api/generate → Backend updates
    ↓
Frontend React state unchanged (no re-render)
    ↓
User sees old terrain even though backend has new state
```

**Why?** React only updates when you call `setAssets()` / `setStateJson()`.

#### ✅ The Solution: Refresh Button

**NEW CODE ADDED:**
```typescript
// web/src/App.tsx:166-186
async function refreshFromBackend() {
  setIsLoading(true)
  try {
    const res = await regenerateTerrain(voxelMode, voxelResolution)
    setAssets(res.assets)       // Sync assets from backend
    setStateJson(res.state)     // Sync state from backend
    // ... update seed display ...
  } catch (error) {
    console.error('Failed to refresh from backend:', error)
  } finally {
    setIsLoading(false)
  }
}
```

**NEW UI BUTTON:**
```tsx
<button 
  onClick={onRefresh} 
  style={{ background: '#388e3c' }}  // Green color
  title="Sync with backend (useful after Postman/API calls)"
>
  🔄 Refresh
</button>
```

**Usage:**
1. Make API calls via Postman
2. Click 🔄 Refresh button in UI
3. Frontend re-syncs with backend state
4. Terrain updates automatically

---

## 📊 Asset Reference Management

### How Asset URLs Work

#### Backend Returns Relative Paths:
```json
{
  "assets": {
    "height8": "/assets/height_1762539474_8.png",
    "height16": "/assets/height_1762539474_16.png",
    "splat": "/assets/splat_1762539474.png"
  }
}
```

#### Frontend Converts to Full URLs:
```typescript
// web/src/components/TerrainViewer.tsx:294-300
const getAssetUrl = useCallback((path: string) => {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const baseURL = 'http://localhost:8001'
  return baseURL + path
}, [])

// Usage:
const url = getAssetUrl(assets.height8)  // "http://localhost:8001/assets/height_XXX_8.png"
texLoader.load(url + `?t=${Date.now()}`) // Add cache-busting timestamp
```

### Asset Lifecycle

```
1. User generates terrain
   ↓
2. Backend creates files:
   - height_TIME_8.png  (8-bit heightmap for preview)
   - height_TIME_16.png (16-bit heightmap for quality)
   - splat_TIME.png     (texture blend weights)
   ↓
3. Backend returns paths to frontend:
   {assets: {height8: "/assets/...", ...}}
   ↓
4. Frontend loads textures:
   - Adds baseURL: "http://localhost:8001/assets/..."
   - Adds cache-bust: "...?t=1762539999999"
   ↓
5. Three.js renders terrain with textures
   ↓
6. User generates again (new command)
   ↓
7. Backend creates NEW files (new timestamp)
   ↓
8. Frontend updates (new paths trigger useEffect)
   ↓
9. Three.js loads new textures
   ↓
10. After 10 generations, cleanup service runs:
    - Deletes old files (except last 10)
    - Keeps currently-used assets safe
```

---

## 🎛️ State Management Details

### Backend State (`terrain_state.json`)

```json
{
  "features": [
    {
      "type": "mountain",
      "x": 308, "y": 194,
      "radius": 56, "height": 0.787,
      "id": 2
    }
  ],
  "seed": 905110303,
  "semantic_scene": {
    "entities": [
      {
        "id": "mountain_1",
        "label": "the mountains",
        "keywords": ["mountains", "peaks"],
        "feature_refs": [2]
      }
    ]
  },
  "next_id": 3
}
```

**Properties:**
- ✅ Persisted to disk (survives restarts)
- ✅ Atomic read/write with file locking
- ✅ Enables modifications (add/remove features)
- ✅ Tracks semantic relationships

### Frontend State (Zustand)

```typescript
{
  assets: { ... },       // Current asset URLs (from backend)
  stateJson: { ... },    // Full backend state (for debugging/display)
  voxelMode: false,      // UI-only setting (display mode)
  seed: -1,              // UI-only setting (user preference)
  biome: "desert",       // UI-only setting
  sunAzimuth: 82,        // UI-only setting (lighting)
  sunElevation: 5        // UI-only setting (lighting)
}
```

**Properties:**
- ⚠️ NOT persisted (resets on page refresh)
- ✅ Auto-loads from backend on mount
- ✅ Updates via API calls
- ✅ Triggers React re-renders

---

## 🔧 How to Use

### Normal Workflow (UI)
1. Type command in textarea
2. Click "Generate" or "Modify"
3. Frontend calls API → Backend updates → Frontend re-renders
4. ✅ Works automatically

### Postman/API Workflow
1. Make API call via Postman:
   ```
   POST http://localhost:8001/api/generate
   Body: {"text": "create mountains", "seed": 12345}
   ```
2. Click **🔄 Refresh** button in UI
3. Frontend syncs with backend
4. ✅ Terrain updates

### Testing Semantic Features
1. Reset terrain: `POST /api/reset`
2. Create features: `POST /api/generate {"text": "create mountains and dunes"}`
3. Check entities: `GET /api/state` → look at `semantic_scene.entities`
4. Modify by reference: `POST /api/modify {"text": "remove the dunes"}`
5. Click **🔄 Refresh** in UI to see changes

---

## 📝 Summary

### ✅ What Works
- ✅ Timestamped asset filenames (immutable generations)
- ✅ State persistence (survives restarts)
- ✅ Asset cleanup (auto-delete old files)
- ✅ Cache busting (always loads latest textures)
- ✅ Auto-load on mount (page refresh syncs with backend)
- ✅ Semantic scene graph (entities, labels, relationships)

### 🆕 What We Just Added
- ✅ **Refresh button** for Postman/API workflow
- ✅ Manual sync with backend state
- ✅ Green button with 🔄 icon and tooltip

### 🎯 Best Practices

**For UI Users:**
- Just use Generate/Modify buttons
- Refresh button not needed (automatic)

**For API/Postman Users:**
- Make API calls as needed
- Click 🔄 Refresh to sync UI
- Check `/api/state` to verify backend state

**For Developers:**
- Backend state = source of truth
- Frontend state = mirror of backend
- Refresh button = manual sync trigger
- Timestamped filenames = immutable assets

---

## 🚀 Future Enhancements (Optional)

### Auto-Refresh with Polling
```typescript
// Poll backend every N seconds
useEffect(() => {
  const interval = setInterval(async () => {
    const latestState = await fetchState()
    if (JSON.stringify(latestState) !== JSON.stringify(stateJson)) {
      refreshFromBackend()  // Auto-sync if changed
    }
  }, 5000)  // Poll every 5 seconds
  return () => clearInterval(interval)
}, [])
```

### WebSocket for Real-Time Sync
```typescript
// Backend pushes updates to frontend
const ws = new WebSocket('ws://localhost:8001/ws')
ws.onmessage = (event) => {
  const update = JSON.parse(event.data)
  setAssets(update.assets)
  setStateJson(update.state)
}
```

### Session IDs (Multi-User Support)
```typescript
// Each user gets a session ID
const sessionId = generateSessionId()
// Backend tracks sessions: /api/session/{sessionId}/state
// Frontend loads its own session: await fetchState(sessionId)
```

---

**Current Status:** Session and asset management working correctly! Refresh button added for Postman workflow. ✅

