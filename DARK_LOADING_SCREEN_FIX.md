# Fix: Dark Loading Screen on Initial Load

**Issue:** On initial app load, the screen was completely dark with no visual feedback.

**Root Cause:** 
- The `TerrainViewer` component only renders terrain when `assets` are loaded
- On initial mount, the app attempts to `regenerateTerrain()` to load the last saved state
- If this fails (no saved state, server error, etc.), `assets` remains `null`
- With no assets, the canvas shows only the dark background (`#0b0b0b`) with no terrain

**Solution: Multi-Part Fix**

## 1. Lighter Background & Better Lighting

**File:** `web/src/components/TerrainViewer.tsx`

**Changes:**
- Changed canvas background from `#0b0b0b` (very dark) to `#1a1a1a` (lighter gray)
- Increased ambient light intensity from `0.6` to `0.8` for better visibility
- These changes ensure the scene is never completely black

```typescript
// Before
<color attach="background" args={['#0b0b0b']} />
<ambientLight intensity={0.6} />

// After
<color attach="background" args={['#1a1a1a']} />
<ambientLight intensity={0.8} />
```

## 2. Loading Placeholder

**File:** `web/src/components/TerrainViewer.tsx`

**Added:** `LoadingPlaceholder` component that displays when no terrain is loaded

**Features:**
- Shows a wireframe grid (200x200) for spatial reference
- Displays a small green cube indicator
- Only renders when `assets` is `null`
- Automatically hides once terrain loads

```typescript
function LoadingPlaceholder() {
  const assets = useStore(s => s.assets)
  if (assets) return null // Hide if terrain is loaded
  
  return (
    <>
      <gridHelper args={[200, 20, '#444444', '#222222']} />
      <mesh rotation-x={-Math.PI/2}>
        <planeGeometry args={[200, 200, 4, 4]} />
        <meshStandardMaterial color="#1a1a1a" wireframe />
      </mesh>
      <group position={[0, 10, 0]}>
        <mesh>
          <boxGeometry args={[0.1, 0.1, 0.1]} />
          <meshBasicMaterial color="#00ff00" />
        </mesh>
      </group>
    </>
  )
}
```

## 3. Enhanced Loading UI

**File:** `web/src/App.tsx`

**Added:** Two new UI elements in the sidebar:

### A. Loading Indicator (Spinner)
When `isLoading` is `true`:
- Shows animated spinning loader
- Blue highlight box with border
- Clear "Generating terrain..." message

```typescript
{isLoading && (
  <div style={{ 
    padding: '12px', 
    background: '#1f6feb22', 
    border: '1px solid #1f6feb', 
    borderRadius: 8, 
    fontSize: 13,
    color: '#1f6feb',
    display: 'flex',
    alignItems: 'center',
    gap: 8
  }}>
    <div style={{ 
      width: 12, 
      height: 12, 
      border: '2px solid #1f6feb', 
      borderTop: '2px solid transparent',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    }} />
    <span>Generating terrain...</span>
  </div>
)}
```

### B. No Terrain Warning
When `!isLoading && !assets`:
- Shows warning message in orange/yellow
- Instructs user to click "Generate" or check server
- Clear visual feedback that something needs attention

```typescript
{!isLoading && !assets && (
  <div style={{ 
    padding: '12px', 
    background: '#ffaa0022', 
    border: '1px solid #ffaa00', 
    borderRadius: 8, 
    fontSize: 13,
    color: '#ffaa00'
  }}>
    ⚠️ No terrain loaded. Click "Generate" to create terrain or check if server is running.
  </div>
)}
```

## 4. CSS Animation

**File:** `web/index.html`

**Added:** `@keyframes spin` animation for the loading spinner

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

## 5. Improved Assets Display

**File:** `web/src/App.tsx`

**Changes:**
- Added max height and scrolling to assets JSON display
- Shows "No terrain loaded yet" instead of "—" when no assets
- Better visual feedback

---

## Visual States

### State 1: Initial Load (No Terrain)
- **Canvas:** Light gray background (`#1a1a1a`)
- **3D Scene:** Grid helper and wireframe placeholder visible
- **UI:** Orange warning box: "⚠️ No terrain loaded..."
- **Assets:** Shows "No terrain loaded yet"

### State 2: Loading
- **Canvas:** Unchanged (grid still visible until terrain loads)
- **UI:** Blue loading box with spinner: "Generating terrain..."
- **Buttons:** Disabled
- **Assets:** Shows previous state or "No terrain loaded yet"

### State 3: Terrain Loaded
- **Canvas:** Terrain mesh renders (hides placeholder)
- **UI:** No loading/warning boxes
- **Assets:** Shows current asset URLs
- **Interactive:** Can generate/modify/reset

---

## User Experience Improvements

### Before Fix:
❌ Black screen on load  
❌ No indication of loading  
❌ No way to know if app is working  
❌ Confusing dark void  

### After Fix:
✅ Clear visual reference (grid/wireframe)  
✅ Loading spinner with message  
✅ Warning when no terrain  
✅ Lighter background (never black)  
✅ Higher ambient light (always visible)  
✅ Professional loading states  

---

## Technical Notes

### Why the Grid Helper?
- Provides spatial reference for the camera
- Shows scale (200x200 units)
- Helps user understand they're looking at a 3D scene
- Familiar pattern from 3D software (Blender, Unity, etc.)

### Why Wireframe Plane?
- Visible placeholder that doesn't block view
- Shows ground plane position
- Lightweight (low poly: 4x4 segments)
- Aesthetic match with grid

### Why Separate Loading States?
- **isLoading:** Operation in progress (API call)
- **!assets:** No terrain data loaded
- These can be independent (e.g., initial load fails, assets stays null)
- Clear distinction helps debugging

---

## Files Modified

1. `web/src/components/TerrainViewer.tsx`
   - Added `LoadingPlaceholder` component
   - Lighter background color
   - Higher ambient light

2. `web/src/App.tsx`
   - Added loading spinner UI
   - Added no-terrain warning UI
   - Improved assets display

3. `web/index.html`
   - Added spin animation keyframes

---

## Testing Scenarios

### Scenario 1: Fresh Start (No Saved State)
1. Start server
2. Load frontend
3. **Expected:** Grid visible, warning "No terrain loaded"
4. Click "Generate"
5. **Expected:** Spinner shows, then terrain appears

### Scenario 2: Server Not Running
1. Stop server
2. Load frontend
3. **Expected:** Grid visible, warning after failed regenerate attempt
4. **User knows:** Server needs to be started

### Scenario 3: Normal Operation
1. Start with existing terrain state
2. Load frontend
3. **Expected:** Brief grid view, then terrain loads automatically
4. **Smooth transition** from placeholder to terrain

---

## Future Improvements (Optional)

1. **Better 3D Placeholder**
   - Show a sample terrain (pre-rendered)
   - Animated grid or particles
   
2. **Loading Progress**
   - Show percentage for long generations
   - Estimated time remaining

3. **Error Messages**
   - Specific error details from server
   - Retry button for failed loads

4. **Transition Animation**
   - Fade out placeholder as terrain fades in
   - Smoother visual experience

---

## Conclusion

The dark loading screen issue is **fully resolved**. Users now have:
- ✅ Clear visual feedback at all times
- ✅ Loading state indication
- ✅ Error/warning messages
- ✅ Professional UI polish

**No more dark void!** 🎉

