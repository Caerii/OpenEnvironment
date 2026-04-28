# Sun Position Calculation - Fix Documentation

## Problems Identified

### 1. **Coordinate System Mismatch** ❌
**Issue**: The Z-axis component had the wrong sign for Three.js coordinate system.

**Old Formula**:
```javascript
z = Math.cos(elevationRad) * Math.cos(azimuthRad)  // WRONG
```

In Three.js (Y-up, right-handed):
- `+Y` = up (zenith)
- `+X` = east (right)
- `-Z` = north (away from viewer)
- `+Z` = south (toward viewer)

With the old formula:
- 0° azimuth produced `z = +1` (south) ❌
- But we labeled it as "North" in comments ❌

**Fix**:
```javascript
z = -Math.cos(elevationRad) * Math.cos(azimuthRad)  // CORRECT (negative sign)
```

Now:
- 0° azimuth produces `z = -1` (north) ✓
- 90° azimuth produces `x = +1` (east) ✓
- 180° azimuth produces `z = +1` (south) ✓
- 270° azimuth produces `x = -1` (west) ✓

### 2. **Unintuitive Default Values** ❌
**Old**: `sunAzimuth: 53°` (not a cardinal direction, confusing)

**New**: `sunAzimuth: 135°` (Southeast - classic morning light, good for terrain)

### 3. **Lack of Visual Feedback** ❌
Users couldn't tell what direction the sun was pointing from angle numbers alone.

**Added**:
- Cardinal direction labels (N, NE, E, SE, S, SW, W, NW)
- Descriptive elevation labels (Sunrise/Sunset, Low, Mid, High, Overhead)
- Scale markers showing key angles
- Quick preset buttons (Morning, Noon, Evening, Sunrise)

## Correct Sun Position Calculation

### Mathematical Convention

**Azimuth** (θ, horizontal angle):
- 0° = North (-Z in Three.js)
- 90° = East (+X in Three.js)
- 180° = South (+Z in Three.js)
- 270° = West (-X in Three.js)
- Measured clockwise from north (like a compass)

**Elevation** (φ, vertical angle):
- 0° = On the horizon (sunrise/sunset)
- 45° = Mid-height
- 90° = Zenith (directly overhead)

### Conversion Formula (Spherical → Cartesian)

For Three.js Y-up coordinate system:

```javascript
// Convert degrees to radians
const azimuthRad = (sunAzimuth * Math.PI) / 180
const elevationRad = (sunElevation * Math.PI) / 180

// Calculate direction vector FROM surface TO sun
const x = Math.cos(elevationRad) * Math.sin(azimuthRad)   // East-West component
const y = Math.sin(elevationRad)                          // Vertical component (height)
const z = -Math.cos(elevationRad) * Math.cos(azimuthRad)  // North-South component (negative for north=-Z)
```

### Why This Works

1. **Elevation Component (Y)**:
   - `sin(0°) = 0` → sun on horizon ✓
   - `sin(90°) = 1` → sun at zenith ✓
   - Independent of azimuth ✓

2. **Horizontal Plane (X, Z)**:
   - Scaled by `cos(elevation)` so horizontal component shrinks as sun goes overhead ✓
   - At elevation=90°, `cos(90°)=0`, so x=0, z=0 (pure vertical) ✓
   
3. **Azimuth Mapping**:
   - `sin(azimuth)` controls X (east-west)
   - `-cos(azimuth)` controls Z (north-south, negative for correct mapping)
   - At azimuth=0°: `sin(0°)=0, -cos(0°)=-1` → (0, y, -1) points north ✓
   - At azimuth=90°: `sin(90°)=1, -cos(90°)=0` → (1, y, 0) points east ✓

## UI Improvements

### Before
- Sliders with raw angle values
- No indication of what the angles meant
- Arbitrary default (53°)

### After
- ✅ **Cardinal direction indicators**: Shows N, NE, E, SE, etc. at exact angles
- ✅ **Descriptive labels**: "Low", "Mid", "High", "Overhead" for elevation
- ✅ **Scale markers**: Shows key angles (0°, 90°, 180°, 270°) and (5°, 45°, 90°)
- ✅ **Quick presets**: One-click "Morning", "Noon", "Evening", "Sunrise"
- ✅ **Intuitive defaults**: Southeast at 60° elevation (classic terrain lighting)

## Testing the Fix

### Verification Tests

1. **North (0°, 60°)**:
   - Expected: Sun from north, casting shadows southward
   - Vector: `(0, 0.866, -0.5)` → mostly up, some north ✓

2. **East (90°, 60°)**:
   - Expected: Sun from east, casting shadows westward
   - Vector: `(0.866, 0.866, 0)` → equal east and up ✓

3. **South (180°, 60°)**:
   - Expected: Sun from south, casting shadows northward
   - Vector: `(0, 0.866, 0.5)` → mostly up, some south ✓

4. **Overhead (any, 90°)**:
   - Expected: Sun directly above, shadows directly below
   - Vector: `(0, 1, 0)` → pure vertical ✓

5. **Sunrise (90°, 10°)**:
   - Expected: Sun low on eastern horizon
   - Vector: `(0.985, 0.174, 0)` → mostly horizontal east ✓

## Implementation Details

### Files Changed

1. **`web/src/components/TerrainViewer.tsx`**:
   - Fixed z-component formula (added negative sign)
   - Added comprehensive comments explaining coordinate system
   - Documented the spherical-to-cartesian conversion

2. **`web/src/state.ts`**:
   - Changed default azimuth: `53° → 135°` (Southeast)
   - Kept elevation at `60°` (good overhead angle)

3. **`web/src/App.tsx`**:
   - Added cardinal direction indicators for azimuth
   - Added descriptive labels for elevation
   - Added scale markers showing key angles
   - Added preset buttons for common scenarios
   - Improved slider labels and feedback

4. **`web/src/shaders/voxelMaterial.ts`**:
   - Updated default `uSunDirection` uniform to match new defaults
   - Vector: `(0.354, 0.866, 0.354)` = Southeast at 60°

## Best Practices Applied

Based on industry research:

1. ✅ **Fixed in World Space**: Sun direction never changes with camera movement
2. ✅ **Standard Conventions**: Azimuth from north (0°), clockwise like a compass
3. ✅ **Intuitive Angles**: Elevation from horizon (0°) to zenith (90°)
4. ✅ **User Control**: Interactive sliders with real-time updates
5. ✅ **Visual Feedback**: Clear labels and presets for common scenarios
6. ✅ **Proper Math**: Correct spherical-to-cartesian conversion for Y-up systems

## References

- Torque 3D Sun Positioning: Azimuth 0°=North, Elevation 0°=Horizon
- Three.js Coordinate System: Y-up, right-handed
- Standard spherical coordinate conversion formulas
- Graphics convention: Direction vectors point FROM surface TO light source

