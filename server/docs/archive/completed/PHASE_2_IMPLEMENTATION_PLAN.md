# Phase 2: Semantic Scene Graph - Implementation Plan

**Status:** Ready to Start  
**Priority:** High (Unlocks context-aware operations)  
**Time Estimate:** 3-4 days  
**Dependencies:** Phase 1 (MCP Tool Registry) ✅ Complete

---

## 🎯 Phase 2 Goals

**Transform from geometric shapes to intelligent scene understanding**

**Key Achievement:** Enable natural language references like:
- ✅ "make the dunes taller" → Resolves "the dunes" to specific features
- ✅ "add a valley between the mountains" → Spatial reasoning
- ✅ "the last mountain" → Reference resolution

---

## 📋 Implementation Tasks

### **Task 1: Core Scene Graph Infrastructure** (Day 1)

#### 1.1 Create `SceneNode` Class
**File:** `server/semantic/scene_graph.py`

**Purpose:** Basic building block for hierarchical scene structure

**Features:**
- Parent/child relationships
- Path-based addressing (USD-style: `/World/Features/Mountains/Mountain_001`)
- Metadata storage
- Feature ID tracking

**Structure:**
```python
class SceneNode:
    def __init__(self, path: str, parent: Optional['SceneNode'] = None):
        self.path = path  # e.g., "/World/Features/Mountains/Mountain_001"
        self.name = path.split('/')[-1]  # "Mountain_001"
        self.parent = parent
        self.children: Dict[str, 'SceneNode'] = {}
        self.data: Dict = {}  # Feature data, metadata, etc.
        self.feature_ids: List[int] = []  # Links to actual features
    
    def add_child(self, name: str) -> 'SceneNode':
        """Add child node and return it."""
        child_path = f"{self.path}/{name}" if self.path != "/" else f"/{name}"
        child = SceneNode(child_path, parent=self)
        self.children[name] = child
        return child
    
    def get_child(self, path: str) -> Optional['SceneNode']:
        """Get child by path (supports relative and absolute)."""
        # Implementation...
    
    def traverse(self) -> Iterator['SceneNode']:
        """Depth-first traversal of subtree."""
        yield self
        for child in self.children.values():
            yield from child.traverse()
```

#### 1.2 Create `TerrainSceneGraph` Class
**File:** `server/semantic/scene_graph.py`

**Purpose:** Main scene graph manager with USD-inspired structure

**Structure:**
```python
class TerrainSceneGraph:
    def __init__(self):
        self.root = SceneNode("/World")
        self.features_root = self.root.add_child("Features")
        self.semantics_root = self.root.add_child("Semantics")
        
    def add_feature_group(self, name: str, semantic_label: str = None) -> SceneNode:
        """Add a group of related features."""
        group = self.features_root.add_child(name)
        if semantic_label:
            group.data["semantic_label"] = semantic_label
        return group
    
    def add_feature(self, feature_data: Dict, group_path: str = None) -> SceneNode:
        """Add a feature to the scene graph."""
        # Implementation...
    
    def query(self, path_pattern: str) -> List[SceneNode]:
        """Query nodes by USD-style path pattern."""
        # "/Features/Mountain_Group/*" → all children
        # "/Features/*/Mountain_*" → pattern matching
        # Implementation...
    
    def to_dict(self) -> Dict:
        """Export scene graph to dictionary (for JSON serialization)."""
        # Implementation...
    
    def from_dict(self, data: Dict):
        """Load scene graph from dictionary."""
        # Implementation...
```

**Estimated Time:** 4-6 hours

---

### **Task 2: Semantic Entity Tracking** (Day 1-2)

#### 2.1 Create `SemanticEntity` Class
**File:** `server/semantic/scene_graph.py`

**Purpose:** Track semantic meaning of features

**Structure:**
```python
class SemanticEntity:
    def __init__(self, entity_id: str, entity_type: str, label: str):
        self.id = entity_id  # e.g., "desert_1", "mountain_group_1"
        self.type = entity_type  # "scene", "group", "composition", "feature"
        self.label = label  # User's words: "the desert", "two mountains"
        self.keywords: List[str] = []  # ["desert", "sandy", "arid"]
        self.description: str = ""  # Natural language description
        self.feature_refs: List[int] = []  # Feature IDs [1, 2, 3]
        self.metadata: Dict = {}
        self.created_at: float = time.time()
        self.user_intent: str = ""  # Original command
    
    def to_dict(self) -> Dict:
        """Export to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "keywords": self.keywords,
            "description": self.description,
            "feature_refs": self.feature_refs,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "user_intent": self.user_intent
        }
```

#### 2.2 Add Entity Management to Scene Graph
**File:** `server/semantic/scene_graph.py`

**Features:**
- Store entities in `semantics_root`
- Link entities to feature nodes
- Support querying by semantic label

**Methods:**
```python
class TerrainSceneGraph:
    def add_entity(self, entity: SemanticEntity):
        """Add semantic entity to scene graph."""
        entity_node = self.semantics_root.add_child(entity.id)
        entity_node.data = entity.to_dict()
        
        # Link to feature nodes
        for feature_id in entity.feature_refs:
            feature_node = self.find_feature_by_id(feature_id)
            if feature_node:
                feature_node.data["semantic_refs"] = feature_node.data.get("semantic_refs", [])
                feature_node.data["semantic_refs"].append(entity.id)
    
    def find_entity_by_label(self, label: str) -> Optional[SemanticEntity]:
        """Find entity by semantic label (e.g., "the dunes")."""
        # Implementation...
    
    def resolve_reference(self, text: str) -> List[int]:
        """Resolve natural language reference to feature IDs."""
        # "the dunes" → [1, 2, 3]
        # Implementation...
```

**Estimated Time:** 3-4 hours

---

### **Task 3: Reference Resolution** (Day 2)

#### 3.1 Implement Reference Resolution Logic
**File:** `server/semantic/scene_graph.py`

**Purpose:** Convert natural language to feature IDs

**Implementation:**
```python
class TerrainSceneGraph:
    def resolve_reference(self, text: str) -> List[int]:
        """
        Resolve natural language reference to feature IDs.
        
        Examples:
        - "the dunes" → finds entity with label "dunes" → returns feature_refs
        - "the mountains" → finds all mountain entities → aggregates feature_refs
        - "the last mountain" → finds most recent mountain → returns its feature_refs
        """
        text_lower = text.lower().strip()
        
        # Try direct entity label match
        for entity_node in self.semantics_root.traverse():
            if entity_node == self.semantics_root:
                continue
            entity_data = entity_node.data
            label = entity_data.get("label", "").lower()
            
            # Check if text matches label
            if text_lower in label or label in text_lower:
                return entity_data.get("feature_refs", [])
            
            # Check keywords
            keywords = entity_data.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return entity_data.get("feature_refs", [])
        
        # Try feature type matching
        if "mountain" in text_lower:
            return self._find_features_by_type("mountain")
        elif "dune" in text_lower:
            return self._find_features_by_type("dunes")
        # ... etc
        
        # Try "last" or "most recent"
        if "last" in text_lower or "most recent" in text_lower:
            return self._find_most_recent_by_type(text_lower)
        
        return []
    
    def _find_features_by_type(self, feature_type: str) -> List[int]:
        """Find all features of a given type."""
        feature_ids = []
        for node in self.features_root.traverse():
            if node == self.features_root:
                continue
            if node.data.get("type") == feature_type:
                feature_ids.extend(node.feature_ids)
        return feature_ids
```

**Estimated Time:** 2-3 hours

---

### **Task 4: Integration with Terrain System** (Day 2-3)

#### 4.1 Update `apply_actions()` to Use Scene Graph
**File:** `server/terrain.py`

**Changes:**
```python
def apply_actions(cmd: str, state: Dict, base_biome_fn=None, direct_actions: List[Dict] = None) -> Tuple:
    """
    Enhanced apply_actions with semantic scene graph tracking.
    """
    # Load or create scene graph
    from .semantic.scene_graph import TerrainSceneGraph
    scene_graph = TerrainSceneGraph()
    if "semantic_scene" in state:
        scene_graph.from_dict(state["semantic_scene"])
    
    # ... existing parsing logic ...
    
    # Execute actions and track semantics
    for action in add_actions:
        command = create_command_from_dict(action)
        feature_ids = command.execute(builder, feature_state, seed)
        
        # Create semantic entity for this action
        entity_id = f"{action.get('type', 'unknown')}_{len(scene_graph.semantics_root.children)}"
        entity = SemanticEntity(
            entity_id=entity_id,
            entity_type="group" if action.get("count", 1) > 1 else "feature",
            label=_extract_label_from_command(cmd, action)
        )
        entity.feature_refs = feature_ids
        entity.keywords = _extract_keywords(cmd, action)
        entity.user_intent = cmd
        
        scene_graph.add_entity(entity)
        
        # Update feature nodes
        for feature_id in feature_ids:
            feat = feature_state.find_feature(feature_id=feature_id)
            if feat:
                group_name = _determine_group_name(action)
                group = scene_graph.add_feature_group(group_name, entity.label)
                feature_node = group.add_child(f"feature_{feature_id}")
                feature_node.feature_ids = [feature_id]
                feature_node.data = feat.copy()
    
    # Save scene graph to state
    state["semantic_scene"] = scene_graph.to_dict()
    
    return h, feature_state.to_dict(), splat
```

**Estimated Time:** 3-4 hours

---

### **Task 5: Update Semantic Parser** (Day 3)

#### 5.1 Use Scene Graph for Reference Resolution
**File:** `server/semantic/parser.py`

**Changes:**
```python
def parse(self, command: str, scene_state: Optional[Dict] = None) -> Dict:
    """Parse command with scene graph context."""
    # Load scene graph if available
    scene_graph = None
    if scene_state and "semantic_scene" in scene_state:
        from .scene_graph import TerrainSceneGraph
        scene_graph = TerrainSceneGraph()
        scene_graph.from_dict(scene_state["semantic_scene"])
    
    # Build enhanced prompt with scene graph context
    system_prompt = self._build_system_prompt(scene_state, scene_graph)
    
    # ... rest of parsing ...
```

**Enhanced Prompt:**
```python
def _build_system_prompt(self, scene_state: Optional[Dict], scene_graph: Optional[TerrainSceneGraph] = None) -> str:
    """Build prompt with scene graph context."""
    prompt_parts = []
    
    # ... existing tool context ...
    
    # Add scene graph context
    if scene_graph:
        prompt_parts.append("\n=== SEMANTIC SCENE CONTEXT ===\n")
        
        # List all entities
        for entity_node in scene_graph.semantics_root.traverse():
            if entity_node == scene_graph.semantics_root:
                continue
            entity_data = entity_node.data
            prompt_parts.append(
                f"- {entity_data.get('label')}: {len(entity_data.get('feature_refs', []))} features"
            )
        
        prompt_parts.append("\nWhen user says 'the dunes' or 'the mountains', "
                          "use the scene graph to resolve which features they refer to.")
    
    return "\n\n".join(prompt_parts)
```

**Estimated Time:** 2-3 hours

---

### **Task 6: Testing & Validation** (Day 3-4)

#### 6.1 Create Test Suite
**File:** `server/test_scene_graph.py`

**Test Cases:**
```python
def test_scene_graph_basic():
    """Test basic scene graph operations."""
    graph = TerrainSceneGraph()
    
    # Add feature group
    group = graph.add_feature_group("Mountains", "the mountains")
    assert group.path == "/World/Features/Mountains"
    
    # Add feature
    feat_data = {"id": 1, "type": "mountain", "x": 128, "y": 256}
    feature_node = graph.add_feature(feat_data, "/World/Features/Mountains")
    assert feature_node.feature_ids == [1]
    
    # Query
    mountains = graph.query("/World/Features/Mountains/*")
    assert len(mountains) == 1

def test_reference_resolution():
    """Test natural language reference resolution."""
    graph = TerrainSceneGraph()
    
    # Add semantic entity
    entity = SemanticEntity("dunes_1", "group", "the dunes")
    entity.feature_refs = [1, 2, 3]
    graph.add_entity(entity)
    
    # Resolve reference
    feature_ids = graph.resolve_reference("the dunes")
    assert feature_ids == [1, 2, 3]
    
    # Resolve "the mountains"
    entity2 = SemanticEntity("mountains_1", "group", "two mountains")
    entity2.feature_refs = [4, 5]
    graph.add_entity(entity2)
    
    feature_ids = graph.resolve_reference("the mountains")
    assert feature_ids == [4, 5]

def test_integration():
    """Test integration with terrain system."""
    # Create terrain with command
    state = {"features": [], "seed": 0}
    h, state, splat = apply_actions("create a desert with rolling dunes", state)
    
    # Check scene graph was created
    assert "semantic_scene" in state
    scene_graph = TerrainSceneGraph()
    scene_graph.from_dict(state["semantic_scene"])
    
    # Resolve reference
    feature_ids = scene_graph.resolve_reference("the dunes")
    assert len(feature_ids) > 0
```

**Estimated Time:** 2-3 hours

---

## 📊 Implementation Checklist

### Day 1: Core Infrastructure
- [ ] Create `SceneNode` class
- [ ] Create `TerrainSceneGraph` class
- [ ] Implement hierarchical structure
- [ ] Add path-based querying
- [ ] Create `SemanticEntity` class
- [ ] Add entity management to scene graph

### Day 2: Reference Resolution
- [ ] Implement `resolve_reference()` method
- [ ] Add feature type matching
- [ ] Add "last" / "most recent" resolution
- [ ] Create helper methods for entity lookup

### Day 3: Integration
- [ ] Update `apply_actions()` to track semantics
- [ ] Create entities when features are added
- [ ] Link entities to feature nodes
- [ ] Update semantic parser to use scene graph
- [ ] Add scene graph context to LLM prompts

### Day 4: Testing & Polish
- [ ] Write comprehensive test suite
- [ ] Test reference resolution ("the dunes", "the mountains")
- [ ] Test integration with terrain generation
- [ ] Performance profiling
- [ ] Documentation

---

## 🎯 Success Criteria

### Phase 2 Complete When:

✅ **Scene Graph Infrastructure**
- [x] `SceneNode` and `TerrainSceneGraph` classes created
- [x] Hierarchical structure working (`/World/Features/...`)
- [x] Path-based querying functional

✅ **Semantic Entity Tracking**
- [x] Entities can be created and stored
- [x] Entities link to feature IDs
- [x] Entities have labels, keywords, descriptions

✅ **Reference Resolution**
- [x] `resolve_reference("the dunes")` returns correct feature IDs
- [x] Supports entity labels, keywords, and feature types
- [x] "last" / "most recent" resolution works

✅ **Integration**
- [x] `apply_actions()` automatically creates semantic entities
- [x] Scene graph saved to state
- [x] Semantic parser uses scene graph context

✅ **Testing**
- [x] All tests passing
- [x] Manual testing successful
- [x] Performance acceptable (<5ms overhead)

---

## 🚀 Starting Phase 2

**Ready to begin?** Let's start with **Task 1: Core Scene Graph Infrastructure**

I'll create:
1. `server/semantic/scene_graph.py` with `SceneNode` and `TerrainSceneGraph`
2. Basic hierarchical structure
3. Path-based querying

**Should I proceed with Task 1?** 🎯

