# Voxel Ray-Traced Shadows & GPU Optimization

## Overview

Implementing GPU-accelerated ray-traced shadows for voxel terrain using WebGL/Three.js shaders.

---

## Challenges in Browser Environment

### WebGL Limitations
- ❌ No dedicated ray tracing hardware access (RTX cores)
- ❌ Limited compute shader support (WebGL 2.0)
- ❌ No bindless textures
- ❌ No ray tracing API (unlike Vulkan RT or DXR)

### What We CAN Do
- ✅ **Ray marching in fragment shaders**
- ✅ **3D texture lookups** (voxel grid sampling)
- ✅ **GPU-accelerated shadow mapping**
- ✅ **Optimized spatial queries**
- ✅ **Ambient occlusion** (screen-space and volumetric)

---

## Architecture: Hybrid Approach

### 1. **Shadow Mapping (Primary Shadows)**
- Fast, hardware-accelerated
- Good for primary shadows from sun
- Less memory than full ray marching

### 2. **Ray Marching (Secondary Effects)**
- Voxel-space ambient occlusion
- Soft shadows in shadowed regions
- Indirect lighting approximation

### 3. **Screen-Space Effects**
- SSAO for micro-detail
- Contact shadows
- Fast post-processing

---

## Implementation Strategy

### Phase 1: Shadow Mapping (Immediate)

**Why Start Here:**
- Fastest path to dynamic shadows
- Hardware-accelerated
- Works with existing geometry
- GPU-efficient

**Implementation:**
```glsl
// 1. Render scene from sun's POV to depth texture
// 2. In main render, sample shadow map to determine if in shadow

uniform sampler2D shadowMap;
uniform mat4 lightSpaceMatrix;

float getShadow(vec3 worldPos) {
  // Transform to light space
  vec4 lightSpacePos = lightSpaceMatrix * vec4(worldPos, 1.0);
  vec3 projCoords = lightSpacePos.xyz / lightSpacePos.w;
  projCoords = projCoords * 0.5 + 0.5;  // [0,1] range
  
  // Sample shadow map
  float closestDepth = texture(shadowMap, projCoords.xy).r;
  float currentDepth = projCoords.z;
  
  // PCF (Percentage Closer Filtering) for soft shadows
  float shadow = 0.0;
  vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
  for(int x = -1; x <= 1; ++x) {
    for(int y = -1; y <= 1; ++y) {
      float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
      shadow += currentDepth - 0.005 > pcfDepth ? 1.0 : 0.0;
    }
  }
  shadow /= 9.0;
  
  return 1.0 - shadow;  // 1.0 = lit, 0.0 = shadowed
}
```

**Benefits:**
- ~1ms GPU time
- Soft shadows (with PCF)
- Dynamic (updates with sun position)
- Standard technique

### Phase 2: Voxel-Based Ambient Occlusion (Enhanced Quality)

**Concept:** Sample voxel grid in cone around surface normal

```glsl
uniform sampler3D voxelGrid;  // 3D texture of voxel occupancy

float getVoxelAO(vec3 worldPos, vec3 normal) {
  float occlusion = 0.0;
  float radius = 2.0;  // World space units
  int samples = 8;
  
  for(int i = 0; i < samples; i++) {
    // Sample in hemisphere around normal
    vec3 sampleDir = getConeDirection(normal, i, samples);
    vec3 samplePos = worldPos + sampleDir * radius;
    
    // Convert to voxel space [0,1]
    vec3 voxelCoord = worldToVoxelSpace(samplePos);
    
    // Sample voxel grid (1.0 = solid, 0.0 = air)
    float voxelDensity = texture(voxelGrid, voxelCoord).r;
    
    // Accumulate occlusion
    occlusion += voxelDensity * (1.0 - length(sampleDir) / radius);
  }
  
  return 1.0 - (occlusion / float(samples));
}
```

**Benefits:**
- True volumetric AO
- Respects voxel geometry
- 3-5ms GPU time (optimized)

### Phase 3: Ray-Marched Soft Shadows (Premium Quality)

**Concept:** March ray from surface to sun through voxel grid

```glsl
float getRayMarchedShadow(vec3 worldPos, vec3 sunDir) {
  float shadow = 1.0;
  float t = 0.1;  // Start slightly offset from surface
  float maxT = 100.0;  // Max ray distance
  
  int steps = 32;  // Quality vs performance trade-off
  float stepSize = maxT / float(steps);
  
  for(int i = 0; i < steps; i++) {
    vec3 samplePos = worldPos + sunDir * t;
    vec3 voxelCoord = worldToVoxelSpace(samplePos);
    
    // Check if we're outside voxel grid
    if(any(lessThan(voxelCoord, vec3(0.0))) || any(greaterThan(voxelCoord, vec3(1.0)))) {
      break;  // Ray escaped, fully lit
    }
    
    // Sample voxel density
    float density = texture(voxelGrid, voxelCoord).r;
    
    if(density > 0.5) {
      // Hit voxel, accumulate shadow
      shadow *= exp(-density * stepSize * 0.5);  // Soft shadowing
      
      if(shadow < 0.01) {
        shadow = 0.0;
        break;  // Fully occluded, early exit
      }
    }
    
    t += stepSize;
  }
  
  return shadow;
}
```

**Benefits:**
- True ray-traced shadows
- Soft shadows (volumetric)
- Respects voxel structure
- 5-10ms GPU time

**Optimizations:**
- **Mipmap cascade**: Sample lower resolution far from camera
- **Early ray termination**: Stop when fully occluded
- **Adaptive step size**: Larger steps in empty space
- **Spatial data structure**: Octree or sparse voxel grid

---

## GPU Optimization Techniques

### 1. **3D Texture Optimization**

```javascript
// Create 3D texture for voxel grid
const texture3D = new THREE.DataTexture3D(voxelData, resX, resY, resZ);
texture3D.format = THREE.RedFormat;  // Single channel (occupancy)
texture3D.type = THREE.UnsignedByteType;  // 8-bit per voxel
texture3D.minFilter = THREE.LinearFilter;  // Hardware interpolation
texture3D.magFilter = THREE.LinearFilter;
texture3D.wrapS = texture3D.wrapT = texture3D.wrapR = THREE.ClampToEdgeWrapping;

// Optimize for sampling
texture3D.unpackAlignment = 1;
texture3D.needsUpdate = true;
```

**Memory Considerations:**
- 128³ voxels = 2 MB (uncompressed)
- 256³ voxels = 16 MB
- 512³ voxels = 128 MB (may cause issues on low-end GPUs)

### 2. **Octree Acceleration Structure**

For sparse voxel grids (terrain is mostly empty):

```glsl
// Octree node structure (stored in texture)
struct OctreeNode {
  uint childMask;     // 8 bits for 8 children
  uint childPointer;  // Index to first child
  float density;      // Average density of this node
};

float sampleOctree(vec3 voxelCoord, float lod) {
  // Start at root
  uint nodeIdx = 0;
  float nodeSize = 1.0;
  vec3 nodeMin = vec3(0.0);
  
  // Traverse to desired LOD
  for(int level = 0; level < lod; level++) {
    OctreeNode node = getNode(nodeIdx);
    
    // Find child containing point
    vec3 mid = nodeMin + nodeSize * 0.5;
    ivec3 childOffset = ivec3(greaterThan(voxelCoord, mid));
    int childIndex = childOffset.x + childOffset.y * 2 + childOffset.z * 4;
    
    // Check if child exists
    if((node.childMask & (1u << childIndex)) == 0u) {
      return node.density;  // Leaf node
    }
    
    // Descend to child
    nodeIdx = node.childPointer + childIndex;
    nodeSize *= 0.5;
    nodeMin += vec3(childOffset) * nodeSize;
  }
  
  return getNode(nodeIdx).density;
}
```

**Benefits:**
- ~8x memory reduction for sparse data
- Faster ray marching (skip empty space)
- Mipmap-like LOD system

### 3. **Compute Shader Pre-Processing** (WebGPU Future)

When WebGPU becomes standard:

```wgsl
@compute @workgroup_size(8, 8, 8)
fn buildOctree(@builtin(global_invocation_id) id: vec3<u32>) {
  // Parallel octree construction
  let voxelCoord = id;
  let density = sampleVoxelDirect(voxelCoord);
  
  // Write to octree structure
  writeOctreeNode(voxelCoord, density);
}
```

---

## Practical Implementation for Our System

### **Current Approach: Hybrid Shadow System**

```glsl
// In voxel fragment shader
void main() {
  vec3 normal = normalize(vNormal);
  vec3 worldPos = vWorldPosition;
  vec3 sunDir = normalize(uSunDirection);
  
  // 1. BASE LIGHTING (Existing - keep vibrant colors)
  vec3 albedo = getAlbedo();
  float diffuse = max(dot(normal, sunDir), 0.0);
  vec3 ambient = getAmbient(normal);
  
  // 2. SHADOW MAPPING (NEW - fast dynamic shadows)
  float shadowFactor = 1.0;
  #ifdef USE_SHADOW_MAP
    shadowFactor = getShadowMapFactor(worldPos, lightSpaceMatrix, shadowMap);
  #endif
  
  // 3. VOXEL AO (NEW - volumetric occlusion)
  float ao = 1.0;
  #ifdef USE_VOXEL_AO
    ao = getVoxelAO(worldPos, normal, voxelGrid);
  #endif
  
  // 4. RAY-MARCHED SOFT SHADOWS (OPTIONAL - quality mode)
  float softShadow = 1.0;
  #ifdef USE_RAY_MARCHED_SHADOWS
    softShadow = getRayMarchedShadow(worldPos, sunDir, voxelGrid);
  #endif
  
  // COMBINE
  vec3 directLight = sunColor * diffuse * shadowFactor * softShadow;
  vec3 indirectLight = ambient * ao;
  
  vec3 finalColor = albedo * (directLight + indirectLight);
  
  // Preserve vibrancy
  finalColor = max(finalColor, albedo * 0.5);
  
  // Gamma correction
  finalColor = pow(finalColor, vec3(1.0 / 2.2));
  
  gl_FragColor = vec4(finalColor, 1.0);
}
```

### **Quality Settings**

```javascript
const QUALITY_PRESETS = {
  performance: {
    shadowMap: true,
    shadowMapSize: 1024,
    voxelAO: false,
    rayMarchedShadows: false
  },
  balanced: {
    shadowMap: true,
    shadowMapSize: 2048,
    voxelAO: true,
    voxelAOSamples: 8,
    rayMarchedShadows: false
  },
  quality: {
    shadowMap: true,
    shadowMapSize: 4096,
    voxelAO: true,
    voxelAOSamples: 16,
    rayMarchedShadows: true,
    rayMarchSteps: 32
  }
};
```

---

## Performance Targets

| Technique | GPU Time | Quality | Notes |
|-----------|----------|---------|-------|
| Shadow Mapping | 1-2ms | Good | Standard, fast |
| + Voxel AO | 3-5ms | Better | Volumetric detail |
| + Ray Marching | 8-15ms | Best | Soft shadows |

**Target:** Stay under 16ms (60 FPS) even on mid-range GPUs

---

## Implementation Roadmap

### Phase 1: Shadow Mapping (Week 1)
- [x] Research complete
- [ ] Implement shadow map rendering pass
- [ ] Add shadow map sampling to voxel shader
- [ ] Add PCF for soft shadows
- [ ] Connect to sun position controls

### Phase 2: Voxel AO (Week 2)
- [ ] Create 3D voxel texture from grid
- [ ] Implement cone-traced AO sampling
- [ ] Optimize sampling pattern
- [ ] Add quality settings

### Phase 3: Ray-Marched Shadows (Week 3)
- [ ] Implement ray marching algorithm
- [ ] Add octree acceleration
- [ ] Optimize step size
- [ ] Performance profiling

### Phase 4: Polish (Week 4)
- [ ] Quality presets UI
- [ ] Performance monitoring
- [ ] Mobile optimization
- [ ] WebGPU future-proofing

---

## Conclusion

The hybrid approach balances:
- ✅ **Performance** (shadow mapping)
- ✅ **Quality** (voxel AO + ray marching)
- ✅ **Compatibility** (WebGL 2.0)
- ✅ **Future-proof** (WebGPU ready)

We achieve dynamic, ray-traced quality shadows while maintaining 60 FPS on reasonable hardware!

