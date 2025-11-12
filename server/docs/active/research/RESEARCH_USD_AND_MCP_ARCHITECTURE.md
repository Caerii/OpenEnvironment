# Research: USD, Neural Scene Graphs, and MCP Architecture

## Overview

Analysis of industry-leading scene representation systems and how to apply them to our semantic terrain system.

---

## 1. Universal Scene Description (USD) - Pixar

### Core Concepts

#### **Prims (Primitives)**
The fundamental building blocks of a USD scene:
```python
# USD Structure
/World
  /Desert
    /Dunes_Group
      /Dune_001 (Xform + Mesh)
      /Dune_002 (Xform + Mesh)
    /Mountains_Group
      /Mountain_Left (Xform + Mesh)
      /Mountain_Right (Xform + Mesh)
```

**Key Features:**
- **Hierarchy**: Tree structure with parent/child relationships
- **Typed Prims**: Each prim has a type (Xform, Mesh, Material, etc.)
- **Properties**: Attributes, relationships, metadata
- **Namespacing**: Path-based addressing

#### **Composition Arcs**
Non-destructive editing through layering:

1. **References**: Include external USD files
   ```python
   /World/Desert [references -> desert_template.usd]
   ```

2. **Variants**: Multiple configurations of same object
   ```python
   /Mountain {
     variantSet "height" = {
       "tall": height=100,
       "medium": height=50
     }
   }
   ```

3. **Layers**: Non-destructive overrides
   ```python
   # Base layer
   /Mountain.height = 50
   
   # Override layer
   /Mountain.height = 75  # Non-destructively overrides base
   ```

4. **Inherits**: Class-based composition
   ```python
   /MountainClass [defines properties]
   /Mountain_001 [inherits MountainClass]
   ```

#### **Schemas**
Structured data definitions:
```python
class TerrainFeature:
    """USD Schema for terrain features."""
    type: str
    position: Vec3
    parameters: Dict
    semantic_tags: List[str]
    relationships: List[Relationship]
```

### What USD Teaches Us

1. **Hierarchical Organization**:
   - Scenes are trees, not flat lists
   - Grouping is fundamental
   - Paths enable precise addressing

2. **Non-Destructive Editing**:
   - Layers allow modifications without destroying original
   - Multiple artists can work simultaneously
   - Easy to revert/compare versions

3. **Composition Over Modification**:
   - Build complex scenes from simple parts
   - Reference and reuse, don't duplicate
   - Variants for configurability

4. **Strong Opinions, Weak Opinions**:
   - Strong opinions (base layer) define defaults
   - Weak opinions (user layer) override when needed
   - Clear precedence rules

---

## 2. NVIDIA Neural Scene Graphs

### Core Concepts

#### **Modular Scene Representation**
```python
SceneGraph {
  nodes: [
    NeuralNode(type="terrain", learned_features=...),
    ClassicalNode(type="geometry", mesh=...),
    MaterialNode(type="pbr", albedo=..., roughness=...)
  ],
  edges: [
    (terrain) --contains--> (geometry),
    (geometry) --uses--> (material)
  ]
}
```

**Key Features:**
- **Hybrid Representation**: Neural + classical
- **Modularity**: Each node is independent
- **Controllability**: Artists can manipulate individual components
- **Composability**: Nodes can be mixed and matched

#### **Semantic Segmentation**
NVIDIA's GSNeRF approach:
```python
{
  "geometric_features": [...],  # 3D structure
  "semantic_features": [...],   # What things are (mountain, valley, etc.)
  "rendering_features": [...],  # How things look
}
```

**Enables:**
- Query by semantics: "Find all mountains"
- Semantic-aware operations: "Make mountains steeper"
- Transfer learning: Apply styles across scenes

### What NVIDIA Teaches Us

1. **Separation of Concerns**:
   - Geometry ≠ Semantics ≠ Appearance
   - Each can be modified independently
   - Enables powerful operations

2. **Neural + Classical Hybrid**:
   - Don't abandon traditional graphics
   - Use neural nets for intelligence
   - Keep classical for control

3. **Semantic-Driven Operations**:
   - Operations understand *what* they're operating on
   - Context-aware modifications
   - Intelligent defaults

---

## 3. Model Context Protocol (MCP) - Tool Calling Architecture

### Core Concepts

#### **Tool Registry System**
```python
{
  "tools": [
    {
      "name": "add_mountain",
      "description": "Add a mountain to the terrain at specified location",
      "parameters": {
        "type": "object",
        "properties": {
          "position": {
            "type": "object",
            "properties": {
              "x": {"type": "integer", "minimum": 0, "maximum": 511},
              "y": {"type": "integer", "minimum": 0, "maximum": 511}
            },
            "required": ["x", "y"]
          },
          "height": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 1.0,
            "default": 0.75,
            "description": "Height of the mountain (0-1 range)"
          },
          "radius": {
            "type": "integer",
            "minimum": 20,
            "maximum": 100,
            "default": 56,
            "description": "Radius of the mountain base in pixels"
          }
        },
        "required": ["position"]
      },
      "returns": {
        "type": "object",
        "properties": {
          "feature_id": {"type": "integer"},
          "success": {"type": "boolean"}
        }
      }
    }
  ]
}
```

#### **Tool Discovery**
```python
class ToolRegistry:
    """Runtime-loaded tool registry for LLM function calling."""
    
    def __init__(self):
        self.tools = {}
        self._discover_tools()
    
    def _discover_tools(self):
        """Auto-discover tools from primitives and engine modules."""
        # Scan primitives
        for module in [mountains, valleys, dunes, cliffs]:
            self._register_module_tools(module)
        
        # Scan engine operations
        for op in [modify, remove, query]:
            self._register_operation_tools(op)
    
    def to_mcp_schema(self) -> Dict:
        """Export tools in MCP-compatible format."""
        return {
            "tools": [tool.to_schema() for tool in self.tools.values()]
        }
```

#### **Context Passing**
```python
{
  "conversation_context": {
    "scene_state": {
      "features": [...],
      "semantic_entities": {...}
    },
    "recent_actions": [
      "Added two mountains on left",
      "Created desert with dunes"
    ],
    "spatial_context": {
      "occupied_regions": ["left", "center"],
      "available_space": ["right", "top-right", "bottom"]
    }
  },
  "tool_context": {
    "available_tools": [...],
    "recently_used": ["add_mountain", "add_dunes"],
    "suggested_next": ["add_valley", "add_vegetation"]
  }
}
```

### What MCP Teaches Us

1. **Structured Tool Definitions**:
   - Schema-driven (JSON Schema or similar)
   - Self-documenting
   - Validation built-in

2. **Runtime Discovery**:
   - Tools loaded dynamically
   - Easy to extend
   - No hard-coded tool lists

3. **Rich Context**:
   - Tools understand current state
   - History-aware
   - Spatially-aware

4. **Composable Operations**:
   - Tools can call other tools
   - Multi-step operations
   - Transactions/rollback

---

## 4. Application to Our Terrain System

### Hybrid Architecture: USD + Neural Scene Graphs + MCP

```python
TerrainScene {
  # USD-inspired hierarchical structure
  hierarchy: {
    /World
      /TerrainBase
      /Features
        /Dunes_Group [semantic entity]
          /Dune_001 [geometric feature]
          /Dune_002 [geometric feature]
        /Mountain_Group [semantic entity]
          /Mountain_Left [geometric feature]
          /Mountain_Right [geometric feature]
      /Semantics
        /desert_scene [scene entity]
        /mountain_pass [compositional entity]
  },
  
  # Neural Scene Graph-inspired separation
  layers: {
    geometry: {features: [...]},      # Physical terrain data
    semantics: {entities: {...}},     # What things mean
    appearance: {splatmap: ...},      # How things look
    relationships: {spatial: [...]}    # How things relate
  },
  
  # MCP-inspired tool system
  tools: ToolRegistry {
    primitives: [add_mountain, add_valley, ...],
    operations: [modify, remove, query, ...],
    composites: [create_mountain_pass, create_crater, ...]
  }
}
```

### Concrete Implementation

#### **1. Hierarchical Scene Structure**
```python
class TerrainSceneGraph:
    """USD-inspired hierarchical scene representation."""
    
    def __init__(self):
        self.root = SceneNode("/World")
        self.features = self.root.add_child("/Features")
        self.semantics = self.root.add_child("/Semantics")
    
    def add_feature_group(self, name: str, parent_path: str = "/Features"):
        """Add a feature group (like USD Xform)."""
        parent = self.get_node(parent_path)
        group = parent.add_child(name)
        group.type = "group"
        return group
    
    def add_feature(self, feature_data: Dict, group_path: str):
        """Add a feature to a group."""
        group = self.get_node(group_path)
        feature = group.add_child(f"/{feature_data['type']}_{feature_data['id']}")
        feature.data = feature_data
        feature.type = "feature"
        return feature
    
    def query(self, path_pattern: str) -> List[SceneNode]:
        """Query nodes by path pattern (USD-style)."""
        # /Features/Mountain_Group/* -> all mountains in group
        # /Features/*/Dune_* -> all dunes in any group
        return self._pattern_match(path_pattern)
```

#### **2. Layered Composition**
```python
class LayeredTerrain:
    """USD-inspired layered composition."""
    
    def __init__(self):
        self.layers = {
            "base": Layer(strength="strong"),      # Default values
            "user": Layer(strength="weak"),        # User modifications
            "semantic": Layer(strength="metadata") # Semantic annotations
        }
    
    def set_property(self, path: str, property: str, value: Any, layer: str = "user"):
        """Set property with layer override."""
        self.layers[layer].set(path, property, value)
    
    def get_property(self, path: str, property: str) -> Any:
        """Get property with layer composition."""
        # Weak opinions override strong opinions
        for layer in ["user", "base"]:
            if self.layers[layer].has(path, property):
                return self.layers[layer].get(path, property)
        return None
    
    def create_variant(self, path: str, variant_name: str, variant_data: Dict):
        """Create a variant set (USD-style configurability)."""
        node = self.get_node(path)
        node.variants[variant_name] = variant_data
```

#### **3. MCP Tool Registry**
```python
class TerrainToolRegistry:
    """MCP-style tool registry with runtime discovery."""
    
    def __init__(self):
        self.tools = {}
        self._discover_tools()
    
    def _discover_tools(self):
        """Auto-discover tools from code."""
        # Primitive tools
        self.register_tool(
            name="add_mountain",
            func=primitives.mountains.generate_mountain,
            schema=self._introspect_function(primitives.mountains.generate_mountain),
            category="primitive",
            description="Create a mountain feature at specified location"
        )
        
        # Operation tools
        self.register_tool(
            name="modify_height",
            func=operations.modify_feature_height,
            schema=self._introspect_function(operations.modify_feature_height),
            category="operation",
            description="Modify the height of an existing feature"
        )
        
        # Composite tools
        self.register_tool(
            name="create_mountain_pass",
            func=composites.create_mountain_pass,
            schema={
                "parameters": {
                    "width": {"type": "integer", "default": 80},
                    "orientation": {"type": "number", "default": 0.0}
                }
            },
            category="composite",
            description="Create a mountain pass (2 mountains + valley + cliffs)"
        )
    
    def to_llm_tools(self) -> List[Dict]:
        """Export tools in LLM function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.schema
                }
            }
            for tool in self.tools.values()
        ]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """Execute a tool with validation."""
        tool = self.tools[tool_name]
        # Validate parameters against schema
        validated_params = self._validate_params(kwargs, tool.schema)
        # Execute
        result = tool.func(**validated_params)
        return {"success": True, "result": result}
```

---

## 5. Benefits of This Architecture

### From USD:
- ✅ **Hierarchical organization**: Clear structure, easy navigation
- ✅ **Path-based addressing**: Precise queries ("/Features/Mountains/*")
- ✅ **Layered composition**: Non-destructive editing
- ✅ **Variants**: Multiple configurations without duplication

### From NVIDIA Neural Scene Graphs:
- ✅ **Separation of concerns**: Geometry, semantics, appearance separate
- ✅ **Hybrid classical+neural**: Best of both worlds
- ✅ **Semantic operations**: Context-aware modifications
- ✅ **Modular**: Independent components, easy to extend

### From MCP:
- ✅ **Self-documenting**: Tools describe themselves
- ✅ **Runtime discovery**: Easy to add new tools
- ✅ **Type-safe**: Schema validation built-in
- ✅ **Rich context**: Tools understand scene state

### Combined Benefits:
- ✅ **Scalability**: Handles complex scenes efficiently
- ✅ **Maintainability**: Clear structure, easy to understand
- ✅ **Extensibility**: Add features without breaking existing code
- ✅ **Intelligence**: LLM has full access to capabilities and context
- ✅ **Collaboration**: Multiple users, non-destructive edits
- ✅ **Reproducibility**: Clear history, can replay actions

---

## 6. Implementation Roadmap

### Phase 1: Hierarchical Scene Graph (USD-inspired)
- SceneNode class with parent/child relationships
- Path-based querying
- Feature grouping

### Phase 2: Layered Composition
- Layer system (base, user, semantic)
- Property override mechanics
- Variant sets

### Phase 3: MCP Tool Registry
- Tool discovery from code
- Schema generation from function signatures
- LLM function-calling integration

### Phase 4: Semantic Integration
- Attach semantic entities to scene nodes
- Neural Scene Graph-style separation
- Context-aware operations

### Phase 5: Advanced Features
- References (include external terrains)
- Transactions (undo/redo)
- Multi-user collaboration
- Scene templates

---

## Conclusion

By combining USD's hierarchical composition, NVIDIA's semantic separation, and MCP's tool architecture, we create a system that is:

1. **Organized** (USD hierarchy)
2. **Intelligent** (Neural semantic understanding)
3. **Extensible** (MCP tool registry)
4. **Powerful** (Compositional operations)
5. **Maintainable** (Clear architecture)

This architecture transforms our terrain system from a simple feature list into a professional-grade scene representation system capable of handling complex workflows, multi-user collaboration, and intelligent LLM-driven operations.

