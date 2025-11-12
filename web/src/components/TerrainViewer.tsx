import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import { OrbitControls, StatsGl } from '@react-three/drei'
import * as THREE from 'three'
import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader'
import { makeTerrainMaterial } from '../shaders/terrainMaterial'
import { makeVoxelMaterial } from '../shaders/voxelMaterial'
import { useStore } from '../state'

function VoxelMesh() {
  const assets = useStore(s => s.assets)
  const sunAzimuth = useStore(s => s.sunAzimuth)
  const sunElevation = useStore(s => s.sunElevation)
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null)
  const materialRef = useRef<THREE.ShaderMaterial | null>(null)
  const [splatReady, setSplatReady] = useState(false)

  // Load textures for terrain material
  const [grass, rock, sand, snow] = useLoader(THREE.TextureLoader as any, [
    '/textures/grass.jpg',
    '/textures/rock.jpg',
    '/textures/sand.jpg',
    '/textures/snow.jpg',
  ]) as THREE.Texture[]

  // Helper to convert relative paths to full URLs (memoized)
  const getAssetUrl = useCallback((path: string) => {
    if (!path) return null
    if (path.startsWith('http://') || path.startsWith('https://')) return path
    const baseURL = 'http://localhost:8001'
    return baseURL + path
  }, [])
  
  const texLoader = new THREE.TextureLoader()
  const splatTex = useMemo(() => {
    if (!assets?.splat) return null
    setSplatReady(false)
    const url = getAssetUrl(assets.splat)
    if (!url) return null
    const tex = texLoader.load(url + `?t=${Date.now()}`, () => {
      setSplatReady(true)
    }, undefined, (error) => {
      console.error('Failed to load splat texture for voxel:', error)
      setSplatReady(true) // Don't block on error
    })
    return tex
  }, [assets, getAssetUrl])

  // Voxel material doesn't need heightmap (it's already 3D)
  const voxelMaterial = useMemo(() => {
    if (!splatTex || !splatReady) return undefined
    const mat = makeVoxelMaterial(splatTex, grass, rock, sand, snow)
    materialRef.current = mat
    return mat
  }, [splatTex, grass, rock, sand, snow, splatReady])
  
  // Update sun direction when angles change
  useFrame(() => {
    if (!materialRef.current) return
    
    // === SUN POSITION CALCULATION (CORRECTED) ===
    // 
    // Three.js Coordinate System (Y-up, right-handed):
    //   +Y = up (zenith)
    //   +X = east (right in top-down view)
    //   -Z = north (away from viewer, top of map)
    //   +Z = south (toward viewer, bottom of map)
    //
    // Azimuth Convention (clockwise from north, like a compass):
    //   0° = North (-Z direction)
    //   90° = East (+X direction)
    //   180° = South (+Z direction)
    //   270° = West (-X direction)
    //
    // Elevation Convention:
    //   0° = on the horizon (sun rising/setting)
    //   90° = zenith (sun directly overhead)
    //
    // This calculates the direction FROM the surface TO the sun
    
    const azimuthRad = (sunAzimuth * Math.PI) / 180
    const elevationRad = (sunElevation * Math.PI) / 180
    
    // Spherical to Cartesian conversion (Y-up, azimuth from north)
    // For azimuth measured clockwise from north (-Z):
    const x = Math.cos(elevationRad) * Math.sin(azimuthRad)   // East-West component
    const y = Math.sin(elevationRad)                          // Vertical component (height)
    const z = -Math.cos(elevationRad) * Math.cos(azimuthRad)  // North-South component (negative for north = -Z)
    
    // Update shader uniform
    materialRef.current.uniforms.uSunDirection.value.set(x, y, z)
  })

  useEffect(() => {
    if (!assets?.voxel_obj) {
      setGeometry(null)
      return
    }

    // Use Three.js OBJLoader - the proper way to load OBJ files
    const objLoader = new OBJLoader()
    const url = getAssetUrl(assets.voxel_obj)
    if (!url) {
      setGeometry(null)
      return
    }
    objLoader.load(
      url + `?t=${Date.now()}`,
      (object: THREE.Group) => {
        try {
          // OBJLoader returns a Group containing meshes
          // Extract the first mesh geometry
          let mergedGeometry: THREE.BufferGeometry | null = null
          
          object.traverse((child: THREE.Object3D) => {
            if (child instanceof THREE.Mesh && child.geometry) {
              if (!mergedGeometry) {
                mergedGeometry = child.geometry.clone()
              } else {
                // If multiple meshes, merge them
                const tempGeom = child.geometry.clone()
                mergedGeometry = mergeGeometries([mergedGeometry, tempGeom]) as THREE.BufferGeometry
              }
            }
          })
          
          if (!mergedGeometry) {
            console.warn('No geometry found in OBJ file')
            setGeometry(null)
            return
          }

          const geom = mergedGeometry as THREE.BufferGeometry
          
          // Get original positions for UV mapping (before transforms)
          const originalPositions = geom.attributes.position.array
          
          let minX = Infinity, maxX = -Infinity
          let minY = Infinity, maxY = -Infinity
          let minZ = Infinity, maxZ = -Infinity
          
          for (let i = 0; i < originalPositions.length; i += 3) {
            const x = originalPositions[i]
            const y = originalPositions[i + 1]
            const z = originalPositions[i + 2]
            minX = Math.min(minX, x)
            maxX = Math.max(maxX, x)
            minY = Math.min(minY, y)
            maxY = Math.max(maxY, y)
            minZ = Math.min(minZ, z)
            maxZ = Math.max(maxZ, z)
          }
          
          // Generate UVs based on original voxel position (before scaling)
          const voxelRangeX = maxX - minX
          const voxelRangeZ = maxZ - minZ
          const uvs: number[] = []
          
          for (let i = 0; i < originalPositions.length; i += 3) {
            const voxelX = originalPositions[i]
            const voxelZ = originalPositions[i + 2]
            
            const u = (voxelX - minX) / voxelRangeX
            const v = (voxelZ - minZ) / voxelRangeZ
            
            uvs.push(
              Math.max(0, Math.min(1, u)),
              Math.max(0, Math.min(1, v))
            )
          }
          
          geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
          
          // Transform positions to match heightmap terrain
          const positions = geom.attributes.position.array as Float32Array
          const targetWidth = 200
          const horizontalScale = targetWidth / voxelRangeX
          
          const voxelHeightY = maxY - minY
          const targetHeight = 50
          const verticalScale = voxelHeightY > 0 ? targetHeight / voxelHeightY : 1.0
          
          // Apply scaling
          for (let i = 0; i < positions.length; i += 3) {
            positions[i] *= horizontalScale
            positions[i + 1] *= verticalScale
            positions[i + 2] *= horizontalScale
          }
          
          // Center at origin
          const centerX = ((minX + maxX) / 2) * horizontalScale
          const centerZ = ((minZ + maxZ) / 2) * horizontalScale
          const minYAfterScale = minY * verticalScale
          
          for (let i = 0; i < positions.length; i += 3) {
            positions[i] -= centerX
            positions[i + 1] -= minYAfterScale
            positions[i + 2] -= centerZ
          }
          
          geom.attributes.position.needsUpdate = true
          geom.computeVertexNormals()
          setGeometry(geom)
        } catch (error) {
          console.error('Failed to process OBJ:', error)
          setGeometry(null)
        }
      },
      undefined,
      (error: ErrorEvent) => {
        console.error('Failed to load voxel OBJ:', error)
        setGeometry(null)
      }
    )
  }, [assets?.voxel_obj, getAssetUrl])
  
  // Helper function to merge geometries
  function mergeGeometries(geometries: THREE.BufferGeometry[]): THREE.BufferGeometry {
    const merged = new THREE.BufferGeometry()
    
    let totalVertices = 0
    let totalIndices = 0
    
    for (const geom of geometries) {
      totalVertices += geom.attributes.position.count
      if (geom.index) {
        totalIndices += geom.index.count
      }
    }
    
    const positions = new Float32Array(totalVertices * 3)
    const indices = new Uint32Array(totalIndices)
    
    let posOffset = 0
    let idxOffset = 0
    let vertexOffset = 0
    
    for (const geom of geometries) {
      const pos = geom.attributes.position.array as Float32Array
      positions.set(pos, posOffset)
      posOffset += pos.length
      
      if (geom.index) {
        const idx = geom.index.array
        for (let i = 0; i < idx.length; i++) {
          indices[idxOffset + i] = idx[i] + vertexOffset
        }
        idxOffset += idx.length
      }
      
      vertexOffset += geom.attributes.position.count
    }
    
    merged.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    merged.setIndex(new THREE.BufferAttribute(indices, 1))
    
    return merged
  }

  if (!geometry || !voxelMaterial) return null

  // Apply voxel-specific material with proper lighting
  // This shader:
  // 1. Samples the splatmap at UV to get texture blend weights
  // 2. Blends terrain textures (grass, rock, sand, snow)
  // 3. Applies proper directional and ambient lighting
  // 4. Adds rim lighting for depth perception
  return (
    <mesh geometry={geometry} position={[0, 0, 0]} material={voxelMaterial as any} />
  )
}

function TerrainMesh() {
  const assets = useStore(s => s.assets)
  const voxelMode = useStore(s => s.voxelMode)
  const sunAzimuth = useStore(s => s.sunAzimuth)
  const sunElevation = useStore(s => s.sunElevation)
  const ref = useRef<THREE.Mesh>(null)
  const materialRef = useRef<THREE.ShaderMaterial | null>(null)
  const [texturesReady, setTexturesReady] = useState(false)

  const [grass, rock, sand, snow] = useLoader(THREE.TextureLoader as any, [
    '/textures/grass.jpg',
    '/textures/rock.jpg',
    '/textures/sand.jpg',
    '/textures/snow.jpg',
  ]) as THREE.Texture[]

  const texLoader = new THREE.TextureLoader()
  const heightTexReady = useRef(false)
  const splatTexReady = useRef(false)
  
  // Helper to convert relative paths to full URLs (memoized)
  const getAssetUrl = useCallback((path: string) => {
    if (!path) return null
    if (path.startsWith('http://') || path.startsWith('https://')) return path
    // If path starts with /, prepend the API base URL
    const baseURL = 'http://localhost:8001'
    return baseURL + path
  }, [])
  
  const heightTex = useMemo(() => {
    if (!assets?.height8) return null
    heightTexReady.current = false
    setTexturesReady(false)
    const url = getAssetUrl(assets.height8)
    if (!url) return null
    const tex = texLoader.load(url + `?t=${Date.now()}`, () => {
      heightTexReady.current = true
      if (splatTexReady.current) setTexturesReady(true)
    }, undefined, (error) => {
      console.error('Failed to load height texture:', error)
      heightTexReady.current = true // Mark as ready even on error to prevent blocking
      if (splatTexReady.current) setTexturesReady(true)
    })
    return tex
  }, [assets, getAssetUrl])
  
  const splatTex = useMemo(() => {
    if (!assets?.splat) return null
    splatTexReady.current = false
    setTexturesReady(false)
    const url = getAssetUrl(assets.splat)
    if (!url) return null
    const tex = texLoader.load(url + `?t=${Date.now()}`, () => {
      splatTexReady.current = true
      if (heightTexReady.current) setTexturesReady(true)
    }, undefined, (error) => {
      console.error('Failed to load splat texture:', error)
      splatTexReady.current = true // Mark as ready even on error to prevent blocking
      if (heightTexReady.current) setTexturesReady(true)
    })
    return tex
  }, [assets, getAssetUrl])
  
  const material = useMemo(() => {
    if (!heightTex || !splatTex || !texturesReady) return undefined
    const mat = makeTerrainMaterial(heightTex, splatTex, grass, rock, sand, snow, 50)
    materialRef.current = mat
    return mat
  }, [heightTex, splatTex, grass, rock, sand, snow, texturesReady])
  
  // Update sun direction for heightmap terrain
  useFrame(() => {
    if (!materialRef.current) return
    
    // Convert azimuth and elevation to 3D direction vector
    const azimuthRad = (sunAzimuth * Math.PI) / 180
    const elevationRad = (sunElevation * Math.PI) / 180
    
    const x = Math.cos(elevationRad) * Math.sin(azimuthRad)
    const y = Math.sin(elevationRad)
    const z = -Math.cos(elevationRad) * Math.cos(azimuthRad)
    
    materialRef.current.uniforms.uSunDirection.value.set(x, y, z)
  })

  // Render voxel mesh if voxel mode is active
  if (voxelMode && assets?.voxel_obj) {
    return <VoxelMesh />
  }

  // Don't render until material is ready
  if (!material) return null

  // Render heightmap terrain 
  // // flat 200x200 plane with high segments to match displacement detail
  // note: 256 segs is fine for preview; 512 is heavier
  return (
    <mesh ref={ref as any} rotation-x={-Math.PI/2} position={[0,0,0]} material={material as any}>
      <planeGeometry args={[200, 200, 256, 256]} />
    </mesh>
  )
}

function LoadingPlaceholder() {
  // Show a simple grid plane when no terrain is loaded
  const assets = useStore(s => s.assets)
  
  if (assets) return null // Don't show if terrain is loaded
  
  return (
    <>
      {/* Grid helper for reference */}
      <gridHelper args={[200, 20, '#444444', '#222222']} position={[0, 0, 0]} />
      
      {/* Placeholder plane */}
      <mesh rotation-x={-Math.PI/2} position={[0, 0, 0]}>
        <planeGeometry args={[200, 200, 4, 4]} />
        <meshStandardMaterial color="#1a1a1a" wireframe />
      </mesh>
      
      {/* Loading text */}
      <group position={[0, 10, 0]}>
        <mesh>
          <boxGeometry args={[0.1, 0.1, 0.1]} />
          <meshBasicMaterial color="#00ff00" />
        </mesh>
      </group>
    </>
  )
}

export default function TerrainViewer() {
  return (
    <Canvas 
      shadows 
      camera={{ 
        position: [120, 120, 160], 
        fov: 45,
        near: 0.1,      // Very close near plane - allows camera to get close without clipping
        far: 10000      // Very far plane - allows deep valleys and tall mountains without clipping
      }}
    >
      {/* Lighter background so it's not completely dark */}
      <color attach="background" args={['#1a1a1a']} />
      
      {/* Higher ambient light for better visibility */}
      <ambientLight intensity={0.8} />
      <directionalLight position={[200, 300, 200]} intensity={1.0} />
      
      {/* Show loading placeholder if no terrain */}
      <LoadingPlaceholder />
      
      {/* Actual terrain mesh */}
      <TerrainMesh />
      
      <OrbitControls makeDefault />
      <StatsGl />
    </Canvas>
  )
}
