# Master Architecture Plan - OpenEnvironment System

## Overview

This document ties together all research and architectural decisions for transforming our terrain system into a professional-grade, semantically-aware, GPU-accelerated terrain editing platform.

---

## Three Pillars of Enhancement

### 1. **Semantic Scene Representation** (USD + Neural Scene Graphs)
**Goal:** Transform from geometric shapes to intelligent scene understanding

**Key Components:**
- Hierarchical scene graph (USD-inspired)
- Semantic entity tracking
- Spatial relationship understanding
- Compositional memory

**Benefits:**
- Natural language references ("the dunes", "the mountains")
- Spatial reasoning ("between", "near", "surrounding")
- Scene composition ("mountain pass", "crater")
- Context-aware modifications

**Status:** ✅ **IMPLEMENTED** - Scene graph fully integrated (November 2025)

### 2. **MCP-Style Tool Registry** (Model Context Protocol)
**Goal:** Structure LLM interactions as discoverable, self-documenting tool calls

**Key Components:**
- Runtime tool discovery
- JSON Schema tool definitions
- Function introspection
- Context-aware prompting

**Benefits:**
- LLM knows exactly what tools it has
- Self-documenting system
- Type-safe execution
- Easy to extend (just add functions!)

**Status:** ✅ **IMPLEMENTED** - Tool registry system in use (November 2025)

### 3. **GPU-Accelerated Ray-Traced Shadows** (Modern Graphics)
**Goal:** Dynamic, realistic shadows for voxel terrain

**Key Components:**
- Shadow mapping (primary shadows)
- Voxel-based ambient occlusion
- Ray-marched soft shadows (optional quality mode)
- 3D texture optimization

**Benefits:**
- Dynamic shadows follow sun position
- True volumetric effects
- Maintains 60 FPS
- Scalable quality settings

**Status:** 📋 **Research Complete** - Implementation plan ready (GPU features not yet implemented in frontend)

---

## Architectural Integration

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                         │
│           "add a valley between the mountains"               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP TOOL REGISTRY                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Semantic  │  │   Spatial    │  │  Geometric   │       │
│  │   Parser    │  │   Resolver   │  │  Primitives  │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  Tools are auto-discovered, schema-validated, context-aware │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              SEMANTIC SCENE GRAPH (USD-inspired)             │
│                                                              │
│  /World                                                      │
│    /Features                                                 │
│      /Mountain_Group [semantic: "the mountains"]            │
│        /Mountain_Left  [geometry]                           │
│        /Mountain_Right [geometry]                           │
│      /Desert_Scene [semantic: "the desert"]                 │
│        /Dunes [geometry]                                    │
│    /Semantics                                               │
│      spatial_relationships: [valley BETWEEN mountains]      │
│                                                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 GPU RENDERING PIPELINE                       │
│                                                              │
│  Geometry Pass  →  Shadow Map  →  Voxel AO  →  Ray March   │
│                                                              │
│  Outputs: Beautiful, ray-traced terrain with dynamic shadows│
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### **Phase 1: MCP Tool Registry** (Foundation)
**Why First:** Enables all future LLM improvements

**Tasks:**
1. Create `ToolRegistry` class
2. Auto-discover tools from primitives/operations
3. Generate JSON Schema for each tool
4. Update semantic parser to use tool registry
5. Add context passing (scene state, spatial layout)

**Impact:** LLM has full awareness of capabilities

**Time:** ~2-3 days

---

### **Phase 2: Basic Semantic Scene Graph** (Intelligence)
**Why Second:** Unlocks context-aware operations

**Tasks:**
1. Create `SceneNode` and `TerrainSceneGraph` classes
2. Hierarchical structure (/Features, /Semantics)
3. Path-based querying
4. Feature grouping
5. Semantic entity tracking

**Impact:** "the dunes" now resolves to specific features

**Time:** ~3-4 days

---

### **Phase 3: Shadow Mapping** (Visual Polish)
**Why Third:** Biggest visual improvement for least effort

**Tasks:**
1. Add shadow map render pass
2. Update voxel shader to sample shadow map
3. Implement PCF for soft shadows
4. Connect to sun position controls
5. Optimize performance

**Impact:** Dynamic shadows, 1-2ms GPU time

**Time:** ~2-3 days

---

### **Phase 4: Semantic Relationship Tracking** (Advanced Intelligence)
**Why Fourth:** Builds on scene graph

**Tasks:**
1. Add spatial relationship tracking
2. Implement reference resolution ("the mountains")
3. Contextual placement ("between")
4. Compositional memory ("mountain pass")

**Impact:** Advanced spatial reasoning

**Time:** ~2-3 days

---

### **Phase 5: Voxel AO** (Quality Enhancement)
**Why Fifth:** Requires 3D texture infrastructure

**Tasks:**
1. Create 3D texture from voxel grid
2. Implement cone-traced AO
3. Optimize sampling
4. Add quality settings

**Impact:** Volumetric ambient occlusion, +3-4ms GPU

**Time:** ~2-3 days

---

### **Phase 6: Layered Composition** (Advanced Features)
**Why Sixth:** Power-user features

**Tasks:**
1. Implement layer system (base/user/semantic)
2. Property override mechanics
3. Variant sets
4. Non-destructive editing

**Impact:** Professional workflow capabilities

**Time:** ~3-4 days

---

### **Phase 7: Ray-Marched Shadows** (Premium Quality)
**Why Last:** Optional quality mode, complex

**Tasks:**
1. Implement ray marching algorithm
2. Add octree acceleration
3. Optimize step size and early termination
4. Performance profiling
5. Quality presets UI

**Impact:** True ray-traced soft shadows, +5-10ms GPU

**Time:** ~4-5 days

---

## Technical Details

### MCP Tool Registry Example

```python
# server/semantic/tool_registry.py
class TerrainToolRegistry:
    """MCP-style tool registry with runtime discovery."""
    
    def __init__(self):
        self.tools = {}
        self._discover_tools()
    
    def _discover_tools(self):
        """Auto-discover tools from codebase."""
        # Scan primitives
        from ..primitives import mountains, valleys, dunes
        
        for module in [mountains, valleys, dunes]:
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith('generate_'):
                    self.register_tool_from_function(func)
    
    def register_tool_from_function(self, func):
        """Create tool from function signature."""
        sig = inspect.signature(func)
        tool = Tool(
            name=func.__name__,
            func=func,
            description=func.__doc__ or "",
            parameters=self._extract_schema(sig),
            category=self._infer_category(func)
        )
        self.tools[tool.name] = tool
    
    def to_llm_context(self) -> str:
        """Generate context string for LLM."""
        lines = ["Available terrain generation tools:\n"]
        for tool in self.tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
            lines.append(f"  Parameters: {tool.parameters}")
        return "\n".join(lines)
    
    def execute(self, tool_name: str, **kwargs):
        """Execute tool with validation."""
        tool = self.tools[tool_name]
        validated = self._validate(kwargs, tool.parameters)
        return tool.func(**validated)
```

### Semantic Scene Graph Example

```python
# server/semantic/scene_graph.py
class TerrainSceneGraph:
    """USD-inspired hierarchical scene graph."""
    
    def __init__(self):
        self.root = SceneNode("/World")
        self.features_root = self.root.add_child("Features")
        self.semantics_root = self.root.add_child("Semantics")
        self.relationships = []
    
    def add_feature_group(self, name: str, semantic_label: str):
        """Add a group of related features."""
        group = self.features_root.add_child(name)
        group.metadata["semantic_label"] = semantic_label
        return group
    
    def query(self, path_pattern: str):
        """Query by USD-style path."""
        # "/Features/Mountain_Group/*" -> all mountains
        return self._pattern_match(path_pattern)
    
    def resolve_reference(self, text: str):
        """Resolve natural language reference to features."""
        # "the mountains" -> [feature_id_4, feature_id_5]
        for node in self.traverse():
            if node.metadata.get("semantic_label") in text:
                return node.get_all_feature_ids()
        return []
```

### Shadow Mapping Shader Example

```glsl
// Shadow map rendering
uniform sampler2D shadowMap;
uniform mat4 lightSpaceMatrix;

float getShadow(vec3 worldPos) {
  vec4 lightSpacePos = lightSpaceMatrix * vec4(worldPos, 1.0);
  vec3 projCoords = lightSpacePos.xyz / lightSpacePos.w;
  projCoords = projCoords * 0.5 + 0.5;
  
  float shadow = 0.0;
  vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
  
  // PCF (3x3 kernel for soft shadows)
  for(int x = -1; x <= 1; ++x) {
    for(int y = -1; y <= 1; ++y) {
      float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x,y) * texelSize).r;
      shadow += projCoords.z - 0.005 > pcfDepth ? 1.0 : 0.0;
    }
  }
  
  return 1.0 - (shadow / 9.0);
}
```

---

## Expected Outcomes

### After Phase 1-2 (MCP + Semantic)
- ✅ LLM understands all available tools
- ✅ "make the dunes taller" works naturally
- ✅ "add a valley between the mountains" with spatial reasoning
- ✅ Scene composition memory

### After Phase 3 (Shadow Mapping)
- ✅ Dynamic shadows follow sun position
- ✅ Soft shadows (PCF)
- ✅ Still 60 FPS
- ✅ Beautiful, realistic terrain

### After Phase 4-5 (Advanced Semantic + Voxel AO)
- ✅ Full spatial relationship understanding
- ✅ Compositional operations ("widen the mountain pass")
- ✅ Volumetric ambient occlusion
- ✅ Professional-quality rendering

### After Phase 6-7 (Layered + Ray Tracing)
- ✅ Non-destructive editing
- ✅ True ray-traced soft shadows
- ✅ Production-grade workflow
- ✅ Industry-leading quality

---

## Performance Targets

| Component | Target Time | Current | After Optimization |
|-----------|-------------|---------|-------------------|
| Semantic Parsing | <500ms | ~300ms | ✓ Already good |
| Scene Graph Queries | <10ms | N/A | <5ms (estimated) |
| Shadow Mapping | <2ms | N/A | 1-2ms (target) |
| Voxel AO | <5ms | N/A | 3-5ms (target) |
| Ray Marching | <10ms | N/A | 8-10ms (target) |
| **Total Frame Time** | **<16ms** | ~2ms | **~12ms (quality mode)** |

**Result:** 60 FPS maintained even with all features enabled!

---

## Next Steps

### Immediate Action Items

1. **Start with MCP Tool Registry** (biggest impact, enables everything else)
   - Create tool registry infrastructure
   - Auto-discover existing primitives
   - Update semantic parser

2. **Basic Scene Graph** (foundational)
   - Hierarchical structure
   - Path-based queries
   - Feature grouping

3. **Shadow Mapping** (quick visual win)
   - Render shadow map
   - Update shaders
   - Connect to sun controls

### Long-term Vision

Transform our terrain system into:
- **Intelligent**: Understands context, spatial relationships, compositions
- **Beautiful**: Ray-traced shadows, volumetric effects, dynamic lighting
- **Professional**: USD-inspired architecture, non-destructive editing
- **Extensible**: MCP tool registry, easy to add features
- **Performant**: GPU-optimized, 60 FPS, scalable quality

---

## Conclusion

We're building something truly special:

1. **Industry-standard architecture** (USD + MCP + Neural Scene Graphs)
2. **Cutting-edge graphics** (ray-traced shadows, volumetric AO)
3. **Natural interaction** (LLM with full semantic understanding)
4. **Professional workflow** (non-destructive, collaborative, extensible)

This isn't just a terrain editor - it's a **semantic 3D scene composition system** that happens to be optimized for terrain!

**Ready to start implementation?** Let's begin with Phase 1: MCP Tool Registry!

