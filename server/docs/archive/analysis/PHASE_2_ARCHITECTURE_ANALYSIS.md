# Phase 2: Deep Architecture Analysis & Reorganization Plan

**Date:** October 31, 2025  
**Goal:** Design a well-organized, modular semantic scene graph system

---

## 📊 Current Architecture Analysis

### Existing Structure

```
server/
├── semantic/                    # Semantic understanding layer
│   ├── parser.py               # LLM parsing (✅ Phase 1)
│   ├── tool_registry.py        # MCP tool registry (✅ Phase 1)
│   ├── spatial_resolver.py     # Position resolution
│   └── state_manager.py        # Feature state (ID tracking)
│
├── engine/                      # Terrain generation engine
│   ├── builder.py              # TerrainBuilder (single-pass construction)
│   ├── commands.py             # Command pattern (Add/Remove/Modify)
│   ├── spatial.py              # Spatial utilities (regions, boxes)
│   ├── splatmap.py             # Texture blending
│   └── ...
│
└── primitives/                  # Terrain generation primitives
    ├── mountains.py
    ├── valleys.py
    └── ...
```

### Current Concerns Separation

**✅ Good Separation:**
- `semantic/` vs `engine/` vs `primitives/` - Clear layers
- `state_manager.py` handles feature IDs
- `spatial_resolver.py` handles position logic
- `tool_registry.py` handles tool discovery

**⚠️ Potential Issues:**
- `state_manager.py` mixes feature storage with ID management
- No semantic entity tracking (Phase 2 adds this)
- Reference resolution not separated from parsing
- Scene graph would be a big monolithic file

---

## 🎯 Phase 2 Goals (Revisited)

### What We Need:

1. **Graph Structure** - Hierarchical nodes (USD-inspired)
2. **Entity Management** - Semantic entities (labels, keywords, descriptions)
3. **Reference Resolution** - "the dunes" → feature IDs
4. **Query System** - Path-based queries (`/Features/*/Mountain_*`)
5. **Integration** - Connect to existing terrain system
6. **Persistence** - Save/load scene graph from state

### Design Principles:

1. **Separation of Concerns** - Each module has one responsibility
2. **Extensibility** - Easy to add relationships, compositions later
3. **USD-Inspired** - Use proven patterns, but simplified
4. **Backward Compatible** - Works with existing `FeatureState`
5. **Performance** - Fast queries, efficient storage

---

## 🏗️ Proposed Reorganized Structure

### Option A: Flat Modular (Recommended)

```
server/semantic/
├── __init__.py
│
├── # Existing (Phase 1) ✅
├── parser.py                    # LLM command parsing
├── tool_registry.py            # MCP tool registry
├── spatial_resolver.py         # Position resolution
├── state_manager.py            # Feature ID management
│
├── # Phase 2: Scene Graph System
├── scene/
│   ├── __init__.py             # Public API exports
│   │
│   ├── # Core Graph Structure
│   ├── node.py                 # SceneNode class (USD prim)
│   ├── graph.py                # TerrainSceneGraph manager
│   │
│   ├── # Entity System
│   ├── entity.py               # SemanticEntity class
│   ├── entity_manager.py       # Entity CRUD operations
│   │
│   ├── # Reference Resolution
│   ├── reference_resolver.py   # "the dunes" → feature IDs
│   │
│   ├── # Query System
│   ├── query.py                # Path-based queries
│   │
│   ├── # Persistence
│   ├── serialization.py        # to_dict/from_dict
│   │
│   └── # Integration
│   └── integration.py          # Helpers for terrain.py integration
│
└── # Future: Phase 4+ (Relationships, Compositions)
    └── relationships/           # (Future: spatial relationships)
        └── ...
```

### Option B: Nested by Concern

```
server/semantic/
├── parsing/                    # Command parsing
│   ├── parser.py
│   └── tool_registry.py
│
├── graph/                      # Scene graph system
│   ├── core/                   # Core structure
│   │   ├── node.py
│   │   └── graph.py
│   ├── entities/               # Entity management
│   │   ├── entity.py
│   │   └── manager.py
│   ├── query/                  # Query system
│   │   ├── resolver.py
│   │   └── path.py
│   └── storage/                # Persistence
│       └── serialization.py
│
└── spatial/                    # Spatial operations
    ├── resolver.py
    └── state_manager.py
```

**Decision: Option A (Flat Modular)** - Easier to navigate, clearer module boundaries

---

## 📁 Detailed Module Breakdown

### 1. **Core Graph Structure**

#### `semantic/scene/node.py`
**Purpose:** Basic building block - USD-inspired prim

**Responsibilities:**
- Parent/child relationships
- Path management (`/World/Features/...`)
- Data storage (feature IDs, metadata)
- Traversal (depth-first, breadth-first)

**Public API:**
```python
class SceneNode:
    def __init__(self, path: str, parent: Optional['SceneNode'] = None)
    def add_child(self, name: str) -> 'SceneNode'
    def get_child(self, path: str) -> Optional['SceneNode']
    def traverse(self) -> Iterator['SceneNode']
    def get_path(self) -> str
    def get_name(self) -> str
```

**Size:** ~150 lines

---

#### `semantic/scene/graph.py`
**Purpose:** Main scene graph manager

**Responsibilities:**
- Initialize root structure (`/World/Features/Semantics`)
- Feature group management
- High-level operations (add_feature, find_feature)
- Delegates to specialized modules

**Public API:**
```python
class TerrainSceneGraph:
    def __init__(self)
    def add_feature_group(self, name: str, semantic_label: str = None) -> SceneNode
    def add_feature(self, feature_data: Dict, group_path: str = None) -> SceneNode
    def find_feature_by_id(self, feature_id: int) -> Optional[SceneNode]
    def get_feature_groups(self) -> List[SceneNode]
```

**Size:** ~200 lines

---

### 2. **Entity System**

#### `semantic/scene/entity.py`
**Purpose:** Semantic entity definition

**Responsibilities:**
- Entity data structure
- Validation
- Serialization

**Public API:**
```python
class SemanticEntity:
    def __init__(self, entity_id: str, entity_type: str, label: str)
    def add_keyword(self, keyword: str)
    def add_feature_ref(self, feature_id: int)
    def to_dict(self) -> Dict
    @classmethod
    def from_dict(cls, data: Dict) -> 'SemanticEntity'
```

**Size:** ~100 lines

---

#### `semantic/scene/entity_manager.py`
**Purpose:** Entity CRUD operations

**Responsibilities:**
- Create entities from actions
- Store entities in scene graph
- Link entities to feature nodes
- Query entities by label/type

**Public API:**
```python
class EntityManager:
    def __init__(self, scene_graph: TerrainSceneGraph)
    def create_entity(self, action: Dict, feature_ids: List[int], 
                     user_command: str) -> SemanticEntity
    def add_entity(self, entity: SemanticEntity)
    def find_entity_by_label(self, label: str) -> Optional[SemanticEntity]
    def find_entities_by_type(self, entity_type: str) -> List[SemanticEntity]
    def get_all_entities(self) -> List[SemanticEntity]
```

**Size:** ~150 lines

---

### 3. **Reference Resolution**

#### `semantic/scene/reference_resolver.py`
**Purpose:** Natural language → Feature IDs

**Responsibilities:**
- Parse natural language references
- Match against entity labels/keywords
- Fallback to feature type matching
- Support "last", "most recent", ordinal numbers

**Public API:**
```python
class ReferenceResolver:
    def __init__(self, scene_graph: TerrainSceneGraph)
    def resolve(self, text: str) -> List[int]
    def resolve_by_label(self, label: str) -> List[int]
    def resolve_by_type(self, feature_type: str) -> List[int]
    def resolve_most_recent(self, feature_type: str) -> List[int]
    def resolve_ordinal(self, feature_type: str, ordinal: int) -> List[int]
```

**Implementation Strategy:**
```python
def resolve(self, text: str) -> List[int]:
    """
    Multi-strategy resolution:
    1. Try exact label match ("the dunes")
    2. Try keyword match ("dunes" in keywords)
    3. Try feature type match ("mountain" → all mountains)
    4. Try ordinal ("first mountain", "last valley")
    5. Try "most recent" by type
    """
    text_lower = text.lower().strip()
    
    # Strategy 1: Entity label match
    entity = self.scene_graph.entity_manager.find_entity_by_label(text_lower)
    if entity:
        return entity.feature_refs
    
    # Strategy 2: Keyword match
    entities = self.scene_graph.entity_manager.get_all_entities()
    for entity in entities:
        if any(kw in text_lower for kw in entity.keywords):
            return entity.feature_refs
    
    # Strategy 3: Feature type match
    if "mountain" in text_lower:
        return self._find_features_by_type("mountain")
    # ... etc
    
    # Strategy 4: Ordinal ("first", "second", "last")
    if "last" in text_lower or "most recent" in text_lower:
        return self.resolve_most_recent(self._extract_type(text_lower))
    
    return []
```

**Size:** ~200 lines

---

### 4. **Query System**

#### `semantic/scene/query.py`
**Purpose:** Path-based queries (USD-style)

**Responsibilities:**
- Parse path patterns (`/Features/*/Mountain_*`)
- Pattern matching
- Query optimization

**Public API:**
```python
class QueryEngine:
    def __init__(self, scene_graph: TerrainSceneGraph)
    def query(self, path_pattern: str) -> List[SceneNode]
    def query_by_type(self, feature_type: str) -> List[SceneNode]
    def query_by_group(self, group_name: str) -> List[SceneNode]
    def query_children(self, parent_path: str) -> List[SceneNode]
```

**Pattern Examples:**
```
"/Features/Mountain_Group/*"          → All children of Mountain_Group
"/Features/*/Mountain_*"              → All nodes matching Mountain_*
"/Features/*"                         → All feature groups
"/World/Features/*/feature_*"          → All features
"/Semantics/*"                        → All entities
```

**Size:** ~150 lines

---

### 5. **Persistence**

#### `semantic/scene/serialization.py`
**Purpose:** Save/load scene graph

**Responsibilities:**
- Serialize scene graph to dict
- Deserialize from dict
- Version handling
- Migration support

**Public API:**
```python
class SceneGraphSerializer:
    @staticmethod
    def to_dict(scene_graph: TerrainSceneGraph) -> Dict
    @staticmethod
    def from_dict(data: Dict) -> TerrainSceneGraph
    @staticmethod
    def validate(data: Dict) -> bool
```

**Format:**
```python
{
    "version": 1,
    "root": {
        "path": "/World",
        "children": {
            "Features": {
                "path": "/World/Features",
                "children": {...},
                "data": {}
            },
            "Semantics": {
                "path": "/World/Semantics",
                "children": {...},
                "data": {}
            }
        },
        "data": {}
    },
    "entities": [
        {
            "id": "dunes_1",
            "type": "group",
            "label": "the dunes",
            "feature_refs": [1, 2, 3],
            ...
        }
    ]
}
```

**Size:** ~200 lines

---

### 6. **Integration Layer**

#### `semantic/scene/integration.py`
**Purpose:** Helpers for terrain.py integration

**Responsibilities:**
- Extract labels from commands
- Extract keywords from commands
- Create entities from actions
- Bridge between FeatureState and SceneGraph

**Public API:**
```python
class SceneGraphIntegrator:
    @staticmethod
    def extract_label(command: str, action: Dict) -> str
    @staticmethod
    def extract_keywords(command: str, action: Dict) -> List[str]
    @staticmethod
    def create_entity_from_action(action: Dict, feature_ids: List[int], 
                                 command: str) -> SemanticEntity
    @staticmethod
    def update_scene_graph_for_action(scene_graph: TerrainSceneGraph,
                                     action: Dict, feature_ids: List[int],
                                     command: str)
```

**Size:** ~150 lines

---

## 🔄 Integration Points

### Integration with Existing System

#### 1. **terrain.py Integration**

```python
def apply_actions(cmd: str, state: Dict, ...) -> Tuple:
    # Load scene graph
    from .semantic.scene import TerrainSceneGraph
    from .semantic.scene.integration import SceneGraphIntegrator
    
    scene_graph = TerrainSceneGraph()
    if "semantic_scene" in state:
        from .semantic.scene.serialization import SceneGraphSerializer
        scene_graph = SceneGraphSerializer.from_dict(state["semantic_scene"])
    
    # ... existing parsing ...
    
    # Execute actions and track semantics
    integrator = SceneGraphIntegrator()
    for action in add_actions:
        command = create_command_from_dict(action)
        feature_ids = command.execute(builder, feature_state, seed)
        
        # Create semantic entity
        entity = integrator.create_entity_from_action(action, feature_ids, cmd)
        scene_graph.entity_manager.add_entity(entity)
        
        # Update feature nodes
        integrator.update_scene_graph_for_action(scene_graph, action, feature_ids, cmd)
    
    # Save scene graph
    state["semantic_scene"] = SceneGraphSerializer.to_dict(scene_graph)
    
    return h, state, splat
```

---

#### 2. **parser.py Integration**

```python
def parse(self, command: str, scene_state: Optional[Dict] = None) -> Dict:
    # Load scene graph if available
    scene_graph = None
    if scene_state and "semantic_scene" in state:
        from .scene.serialization import SceneGraphSerializer
        scene_graph = SceneGraphSerializer.from_dict(state["semantic_scene"])
    
    # Use reference resolver for context
    if scene_graph:
        from .scene.reference_resolver import ReferenceResolver
        resolver = ReferenceResolver(scene_graph)
        
        # Build context with resolved references
        context = self._build_context_with_resolver(scene_graph, resolver)
    
    # ... rest of parsing ...
```

---

#### 3. **commands.py Integration**

```python
class ModifyFeatureCommand(ActionCommand):
    def execute(self, builder, feature_state, seed):
        # Use reference resolver to find target features
        if "target" in self.modifiers:
            from .scene import TerrainSceneGraph
            from .scene.reference_resolver import ReferenceResolver
            
            # Get scene graph from state (pass through builder or state)
            scene_graph = self._get_scene_graph(feature_state)
            resolver = ReferenceResolver(scene_graph)
            
            # Resolve target reference
            target_ids = resolver.resolve(self.modifiers["target"])
            
            # Modify resolved features
            for feature_id in target_ids:
                # ... modify logic ...
```

---

## 📊 Module Dependency Graph

```
┌─────────────────────────────────────────┐
│         terrain.py (Integration)          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     semantic/scene/integration.py         │
└──────────────┬──────────────────────────┘
               │
               ├──────────────────┬──────────────────┐
               ▼                  ▼                  ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   graph.py   │    │entity_manager│    │reference_    │
    │              │    │     .py      │    │resolver.py   │
    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   node.py    │    │  entity.py   │    │   query.py   │
    └──────────────┘    └──────────────┘    └──────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │  serialization.py         │
    └──────────────────────────┘
```

---

## 📈 Implementation Order

### Phase 2.1: Core Structure (Day 1 Morning)
1. `node.py` - Basic SceneNode
2. `graph.py` - TerrainSceneGraph manager
3. Basic tests

### Phase 2.2: Entity System (Day 1 Afternoon)
4. `entity.py` - SemanticEntity class
5. `entity_manager.py` - Entity CRUD
6. Integration tests

### Phase 2.3: Reference Resolution (Day 2 Morning)
7. `reference_resolver.py` - Natural language → IDs
8. Multi-strategy resolution
9. Resolution tests

### Phase 2.4: Query System (Day 2 Afternoon)
10. `query.py` - Path-based queries
11. Pattern matching
12. Query tests

### Phase 2.5: Persistence (Day 3 Morning)
13. `serialization.py` - Save/load
14. Version handling
15. Serialization tests

### Phase 2.6: Integration (Day 3 Afternoon)
16. `integration.py` - Terrain.py helpers
17. Update `terrain.py` to use scene graph
18. Update `parser.py` to use resolver
19. Integration tests

### Phase 2.7: Testing & Polish (Day 4)
20. End-to-end tests
21. Performance profiling
22. Documentation
23. Bug fixes

---

## 🎯 Success Metrics

### Code Quality:
- ✅ Each module < 250 lines
- ✅ Clear single responsibility
- ✅ Comprehensive docstrings
- ✅ Type hints throughout

### Functionality:
- ✅ Reference resolution works ("the dunes" → IDs)
- ✅ Scene graph persists correctly
- ✅ Integration doesn't break existing code
- ✅ Performance < 5ms overhead

### Testing:
- ✅ Unit tests for each module
- ✅ Integration tests
- ✅ End-to-end tests
- ✅ 90%+ code coverage

---

## 🚀 Next Steps

**Ready to implement?** Start with:

1. **Create directory structure:**
   ```
   mkdir -p server/semantic/scene
   ```

2. **Implement Phase 2.1:** Core structure (`node.py`, `graph.py`)

3. **Test incrementally** after each module

**Should I proceed with creating the directory structure and starting Phase 2.1?**

