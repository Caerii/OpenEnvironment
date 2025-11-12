import * as THREE from 'three'

export function makeVoxelMaterial(
  splatTex: THREE.Texture,
  grass: THREE.Texture,
  rock: THREE.Texture,
  sand: THREE.Texture,
  snow: THREE.Texture
) {
  splatTex.wrapS = splatTex.wrapT = THREE.RepeatWrapping
  ;[grass, rock, sand, snow].forEach(t => {
    t.wrapS = t.wrapT = THREE.RepeatWrapping
    t.anisotropy = 16 // Higher anisotropy for better quality
    t.minFilter = THREE.LinearMipMapLinearFilter
    t.magFilter = THREE.LinearFilter
  })

  const uniforms: Record<string, any> = {
    uSplat: { value: splatTex },
    uGrass: { value: grass },
    uRock: { value: rock },
    uSand: { value: sand },
    uSnow: { value: snow },
    uTilingGrass: { value: 12.0 },
    uTilingRock: { value: 10.0 },
    uTilingSand: { value: 8.0 },
    uTilingSnow: { value: 12.0 },
    uTime: { value: 0 },
    // Default sun direction: 82° azimuth at 5° elevation (low sunrise/sunset)
    // Calculated: x=cos(5)*sin(82)≈0.985, y=sin(5)≈0.087, z=-cos(5)*cos(82)≈-0.138
    uSunDirection: { value: new THREE.Vector3(0.985, 0.087, -0.138) }
  }

  // Enhanced voxel shader with triplanar mapping and advanced lighting
  const vsh = /* glsl */`
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying vec3 vCameraPosition;
    varying float vHeight;

    void main() {
      vUv = uv;
      
      // Calculate WORLD-SPACE normal (not view-space)
      // This ensures normals don't rotate with the camera
      vNormal = normalize(mat3(modelMatrix) * normal);
      
      vec4 worldPos = modelMatrix * vec4(position, 1.0);
      vWorldPosition = worldPos.xyz;
      vHeight = worldPos.y; // World-space height for fog
      
      // Pass world-space camera position for view direction calculation
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
    uniform float uTime;
    uniform vec3 uSunDirection; // Controllable sun direction

    // Triplanar mapping for better texture projection on voxel faces
    vec3 triplanarMap(sampler2D tex, vec3 worldPos, vec3 normal, float scale) {
      // Calculate blend weights based on normal
      vec3 blend = abs(normal);
      blend = normalize(max(blend, 0.00001));
      float b = (blend.x + blend.y + blend.z);
      blend /= vec3(b, b, b);
      
      // Sample texture from 3 directions
      vec3 xaxis = texture2D(tex, worldPos.yz * scale).rgb;
      vec3 yaxis = texture2D(tex, worldPos.xz * scale).rgb;
      vec3 zaxis = texture2D(tex, worldPos.xy * scale).rgb;
      
      // Blend together
      return xaxis * blend.x + yaxis * blend.y + zaxis * blend.z;
    }

    // Blinn-Phong specular lighting
    float blinnPhongSpecular(vec3 lightDir, vec3 viewDir, vec3 normal, float shininess) {
      vec3 halfDir = normalize(lightDir + viewDir);
      return pow(max(dot(normal, halfDir), 0.0), shininess);
    }

    // Fresnel effect (Schlick approximation)
    float fresnel(vec3 viewDir, vec3 normal, float power) {
      return pow(1.0 - max(dot(viewDir, normal), 0.0), power);
    }

    // Ambient occlusion approximation based on normal
    float approximateAO(vec3 normal) {
      // Darken downward-facing surfaces
      float ao = mix(0.6, 1.0, normal.y * 0.5 + 0.5);
      return ao;
    }

    void main() {
      vec3 normal = normalize(vNormal);
      
      // Calculate view direction in WORLD SPACE
      // This ensures lighting doesn't change as camera rotates
      vec3 viewDir = normalize(vCameraPosition - vWorldPosition);
      
      // Sample splatmap to get terrain texture blend weights
      vec4 w = texture2D(uSplat, vUv);
      float sumw = max(1e-4, w.r + w.g + w.b + w.a);
      vec4 wn = w / sumw;

      // Use triplanar mapping for better texture quality on voxel faces
      float triplanarScale = 0.05; // Adjust for texture density
      vec3 cGrass = triplanarMap(uGrass, vWorldPosition, normal, triplanarScale * uTilingGrass);
      vec3 cRock  = triplanarMap(uRock,  vWorldPosition, normal, triplanarScale * uTilingRock);
      vec3 cSand  = triplanarMap(uSand,  vWorldPosition, normal, triplanarScale * uTilingSand);
      vec3 cSnow  = triplanarMap(uSnow,  vWorldPosition, normal, triplanarScale * uTilingSnow);

      // Blend textures based on splatmap
      vec3 albedo = cGrass * wn.r + cRock * wn.g + cSand * wn.b + cSnow * wn.a;
      
      // === LIGHTING SETUP (MINECRAFT-STYLE) ===
      
      // Sun light (main directional light) - FIXED IN WORLD SPACE
      // Direction is controllable via uniform, never changes with camera movement
      vec3 sunDir = normalize(uSunDirection);
      
      // Dynamic sun color based on elevation (like Minecraft sunsets/sunrises)
      float sunHeight = sunDir.y;  // 0 = horizon, 1 = zenith
      vec3 sunColor;
      if (sunHeight < 0.2) {
        // Low sun: warm sunrise/sunset (orange-red)
        sunColor = mix(vec3(1.0, 0.4, 0.2), vec3(1.0, 0.8, 0.6), sunHeight / 0.2);
      } else if (sunHeight < 0.5) {
        // Rising sun: warm to white
        sunColor = mix(vec3(1.0, 0.8, 0.6), vec3(1.0, 0.98, 0.95), (sunHeight - 0.2) / 0.3);
      } else {
        // High sun: bright white
        sunColor = vec3(1.0, 0.98, 0.95);
      }
      
      // Sky light (ambient from above) - BRIGHT like Minecraft
      vec3 skyColor = vec3(0.6, 0.65, 0.75);
      
      // Ground bounce (ambient from below) - BRIGHTER than before
      vec3 groundColor = vec3(0.3, 0.28, 0.25);
      
      // === DIFFUSE LIGHTING (MINECRAFT-STYLE) ===
      
      // Simple diffuse with soft falloff (like Minecraft smooth lighting)
      float sunDiffuse = max(dot(normal, sunDir), 0.0);
      
      // Soften lighting to preserve colors (Minecraft never has harsh shadows)
      // Remap [0,1] to [0.5, 1.0] so shadows are never completely dark
      float smoothDiffuse = sunDiffuse * 0.5 + 0.5;
      
      // Bright sky/ground ambient (Minecraft is bright even in shadows)
      float skyInfluence = normal.y * 0.5 + 0.5;
      vec3 ambient = mix(groundColor, skyColor, skyInfluence) * 0.65; // Much brighter!
      
      // === SPECULAR HIGHLIGHTS ===
      
      // Terrain should be mostly matte, only subtle specular on wet surfaces
      float shininess = mix(4.0, 12.0, wn.g); // Much lower shininess (was 8-40)
      float specular = blinnPhongSpecular(sunDir, viewDir, normal, shininess);
      // Dramatically reduced specular strength for natural terrain look
      float specularStrength = mix(0.02, 0.08, wn.g) * wn.a * 0.5; // Was 0.1-0.3
      
      // === AMBIENT OCCLUSION (SUBTLE like Minecraft) ===
      
      // Very subtle AO - Minecraft style (mostly bright)
      float ao = normal.y * 0.15 + 0.85;  // Only 15% variation, mostly bright
      
      // === FRESNEL RIM LIGHT ===
      
      // Subtle rim only on edges, much less dramatic
      float rim = fresnel(viewDir, normal, 4.0); // Higher power = less intense
      vec3 rimColor = skyColor * rim * 0.08; // Reduced from 0.4 to 0.08
      
      // === SUBSURFACE SCATTERING (fake, for snow) ===
      
      // Subtle backlit glow for snow only
      float sss = max(0.0, dot(normal, -sunDir)) * wn.a; // Snow only
      vec3 sssColor = sunColor * sss * 0.15; // Reduced from 0.3 to 0.15
      
      // === COMBINE LIGHTING (MINECRAFT-STYLE: SIMPLE & VIBRANT) ===
      
      // Direct sun lighting with dynamic color
      vec3 sunLight = sunColor * smoothDiffuse * albedo * 0.9;
      
      // Bright ambient lighting
      vec3 ambientLight = ambient * albedo * 0.7;
      
      // Very subtle specular (almost none, like Minecraft)
      vec3 specularContrib = sunColor * specular * specularStrength * 0.3;
      
      // Combine everything (additive keeps colors vibrant)
      vec3 finalColor = sunLight + ambientLight + specularContrib + rimColor + sssColor;
      
      // Apply subtle AO (just multiply, no aggressive darkening)
      finalColor *= ao;
      
      // Ensure minimum brightness (Minecraft is NEVER too dark)
      finalColor = max(finalColor, albedo * 0.5);  // Minimum 50% of original color
      
      // === HEIGHT FOG ===
      
      // Add atmospheric depth based on height
      float fogStart = 0.0;
      float fogEnd = 60.0;
      float fogFactor = smoothstep(fogStart, fogEnd, vHeight);
      vec3 fogColor = vec3(0.7, 0.8, 0.9) * 0.3;
      finalColor = mix(finalColor, fogColor, fogFactor * 0.15);
      
      // === COLOR GRADING (MINIMAL - Keep it vibrant like Minecraft) ===
      
      // Very subtle contrast (Minecraft colors are flat and vibrant)
      finalColor = pow(finalColor, vec3(0.95)); // Minimal contrast boost
      
      // NO black crush (Minecraft doesn't do this)
      
      // NO color temperature shift (keep original colors)
      
      // Simple tone mapping (just prevent overbright, don't desaturate)
      finalColor = finalColor / (finalColor + vec3(1.2));  // Very gentle
      
      // Gamma correction (standard)
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

