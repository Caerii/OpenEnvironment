import * as THREE from 'three'

export function makeTerrainMaterial(
  heightTex: THREE.Texture,
  splatTex: THREE.Texture,
  grass: THREE.Texture,
  rock: THREE.Texture,
  sand: THREE.Texture,
  snow: THREE.Texture,
  dispScale = 50
) {
  heightTex.wrapS = heightTex.wrapT = THREE.RepeatWrapping
  splatTex.wrapS = splatTex.wrapT = THREE.RepeatWrapping
  ;[grass,rock,sand,snow].forEach(t => {
    t.wrapS = t.wrapT = THREE.RepeatWrapping
    t.anisotropy = 8
    t.minFilter = THREE.LinearMipMapLinearFilter
    t.magFilter = THREE.LinearFilter
  })

  const uniforms: Record<string, any> = {
    uHeight: { value: heightTex },
    uSplat:  { value: splatTex },
    uGrass:  { value: grass },
    uRock:   { value: rock },
    uSand:   { value: sand },
    uSnow:   { value: snow },
    uDispScale: { value: dispScale },
    uTilingGrass: { value: 8.0 },
    uTilingRock:  { value: 8.0 },
    uTilingSand:  { value: 6.0 },
    uTilingSnow:  { value: 8.0 },
    // Sun position for lighting (matches voxel shader)
    uSunDirection: { value: new THREE.Vector3(0.985, 0.087, -0.138) }  // 82° azimuth at 5° elevation
  }

  const vsh = /* glsl */`
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying vec3 vCameraPosition;
    varying float vHeight;
    
    uniform sampler2D uHeight;
    uniform float uDispScale;

    void main() {
      vUv = uv;
      
      // Sample heightmap
      float h = texture2D(uHeight, vUv).r;
      
      // Calculate proper terrain normals from heightmap gradients
      // Sample neighboring heights for gradient calculation
      float texelSize = 1.0 / 512.0; // Assuming 512x512 heightmap
      float hL = texture2D(uHeight, vUv + vec2(-texelSize, 0.0)).r;
      float hR = texture2D(uHeight, vUv + vec2(texelSize, 0.0)).r;
      float hD = texture2D(uHeight, vUv + vec2(0.0, -texelSize)).r;
      float hU = texture2D(uHeight, vUv + vec2(0.0, texelSize)).r;
      
      // Calculate gradients (in world space)
      float dx = (hR - hL) * uDispScale;
      float dy = (hU - hD) * uDispScale;
      
      // Construct normal from gradients
      // The terrain is in XZ plane, displaced in Y
      vec3 terrainNormal = normalize(vec3(-dx, 2.0, -dy));
      
      // Transform to world space
      vNormal = normalize(mat3(modelMatrix) * terrainNormal);
      
      // Displaced position
      vec3 displaced = position + normal * (h * uDispScale);
      
      // World position
      vec4 worldPos = modelMatrix * vec4(displaced, 1.0);
      vWorldPosition = worldPos.xyz;
      vHeight = worldPos.y;
      
      // Camera position for view direction
      vCameraPosition = cameraPosition;
      
      gl_Position = projectionMatrix * viewMatrix * worldPos;
    }
  `

  const fsh = /* glsl */`
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying vec3 vCameraPosition;
    varying float vHeight;
    
    uniform sampler2D uSplat;
    uniform sampler2D uGrass, uRock, uSand, uSnow;
    uniform float uTilingGrass, uTilingRock, uTilingSand, uTilingSnow;
    uniform vec3 uSunDirection;

    void main() {
      // Use calculated terrain normals for realistic lighting
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vCameraPosition - vWorldPosition);
      
      // Sample textures
      vec4 w = texture2D(uSplat, vUv);
      float sumw = max(1e-4, w.r + w.g + w.b + w.a);
      vec4 wn = w / sumw;

      vec3 cGrass = texture2D(uGrass, vUv * uTilingGrass).rgb;
      vec3 cRock  = texture2D(uRock,  vUv * uTilingRock ).rgb;
      vec3 cSand  = texture2D(uSand,  vUv * uTilingSand ).rgb;
      vec3 cSnow  = texture2D(uSnow,  vUv * uTilingSnow ).rgb;

      vec3 albedo = cGrass*wn.r + cRock*wn.g + cSand*wn.b + cSnow*wn.a;
      
      // === REALISTIC LIGHTING WITH DYNAMIC SUN COLOR ===
      
      vec3 sunDir = normalize(uSunDirection);
      
      // Dynamic sun color based on elevation
      float sunHeight = sunDir.y;
      vec3 sunColor;
      if (sunHeight < 0.2) {
        sunColor = mix(vec3(1.0, 0.4, 0.2), vec3(1.0, 0.8, 0.6), sunHeight / 0.2);
      } else if (sunHeight < 0.5) {
        sunColor = mix(vec3(1.0, 0.8, 0.6), vec3(1.0, 0.98, 0.95), (sunHeight - 0.2) / 0.3);
      } else {
        sunColor = vec3(1.0, 0.98, 0.95);
      }
      
      // Realistic diffuse lighting with proper contrast
      float NdotL = max(dot(normal, sunDir), 0.0);
      
      // Softer transition but still realistic (not as flat as Minecraft)
      float diffuse = smoothstep(0.0, 0.3, NdotL);
      
      // Ambient lighting - bright enough to see detail, but allows shadows
      vec3 skyColor = vec3(0.5, 0.55, 0.65);
      vec3 groundColor = vec3(0.25, 0.22, 0.20);
      float skyInfluence = normal.y * 0.5 + 0.5;
      vec3 ambient = mix(groundColor, skyColor, skyInfluence) * 0.45;
      
      // Ambient occlusion based on normal (downward faces darker)
      float ao = mix(0.65, 1.0, normal.y * 0.5 + 0.5);
      
      // Subtle rim lighting for depth perception
      float rim = pow(1.0 - max(dot(viewDir, normal), 0.0), 3.0);
      vec3 rimColor = skyColor * rim * 0.15;
      
      // Combine lighting with realistic contrast
      vec3 directLight = sunColor * diffuse * 1.0;
      vec3 finalColor = albedo * (ambient + directLight) * ao + rimColor;
      
      // Preserve color vibrancy (minimum brightness)
      finalColor = max(finalColor, albedo * 0.35);
      
      // Gamma correction
      finalColor = pow(finalColor, vec3(1.0 / 2.2));
      
      gl_FragColor = vec4(finalColor, 1.0);
    }
  `

  const mat = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: vsh,
    fragmentShader: fsh,
    lights: false
  })
  mat.side = THREE.DoubleSide
  return mat
}

