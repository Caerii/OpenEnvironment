# Type System & Abstraction Hierarchy Analysis

## 🎯 **Goal: Clean, Type-Safe, Maintainable Architecture**

We need:
1. **Type safety** - Catch errors at development time, not runtime
2. **Clear abstractions** - Each layer has well-defined responsibilities
3. **Composability** - Components work together cleanly
4. **Testability** - Easy to unit test each layer
5. **Extensibility** - Easy to add new archetypes, features, metrics

---

## 📊 **Current Type System Issues**

### **Issue #1: Loose Typing in scene_state**
```python
# Current (from terrain.py):
scene_state: Dict[str, Any] = {
    "features": [...],  # List of dicts, no validation
    "semantic_scene": {...},  # Nested dicts
    "seed": 12345,
    "biome": "desert"
}

# Problem: No validation, runtime errors possible
feature = scene_state["features"][0]
radius = feature["radius"]  # KeyError if missing!
```

### **Issue #2: Mixed Concerns in Feature Dict**
```python
# Current feature representation:
{
    "id": 1,              # Identity
    "type": "mountain",   # Type
    "x": 100, "y": 200,   # Position
    "radius": 50,         # Geometry
    "height": 0.8,        # Appearance
    "use_noise": True,    # Rendering
    "label": "the peak"   # Semantics
}

# Problem: Everything mixed together, no clear separation
```

### **Issue #3: No Abstract Base Classes**
```python
# All features are just dicts
# No common interface, no polymorphism
# Hard to add feature-specific logic

# Compare to:
class Feature(ABC):
    @abstractmethod
    def get_stamp(self) -> np.ndarray:
        pass
    
    @abstractmethod
    def get_blending_mode(self) -> BlendingMode:
        pass
```

### **Issue #4: Narrative Types Are Disconnected**
```python
# We created TerrainNarrative, but it's not integrated with:
# - TerrainBuilder (still takes raw feature dicts)
# - FeatureRegistry (still returns dicts)
# - scene_state (still a Dict[str, Any])

# Need to bridge the gap!
```

---

## 🏗️ **Proposed Type Hierarchy**

### **Layer 1: Primitives (Foundation)**

These are the basic building blocks:

```python
# geometry.py
@dataclass(frozen=True)
class Position:
    """2D position on terrain grid."""
    x: int  # 0-512
    y: int  # 0-512
    
    def __post_init__(self):
        assert 0 <= self.x <= 512, f"x out of bounds: {self.x}"
        assert 0 <= self.y <= 512, f"y out of bounds: {self.y}"
    
    def distance_to(self, other: 'Position') -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx*dx + dy*dy)
    
    def offset(self, dx: int, dy: int) -> 'Position':
        return Position(self.x + dx, self.y + dy)


@dataclass(frozen=True)
class Region:
    """Rectangular region on terrain."""
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    
    def __post_init__(self):
        assert self.x_min < self.x_max
        assert self.y_min < self.y_max
    
    def contains(self, pos: Position) -> bool:
        return (self.x_min <= pos.x <= self.x_max and
                self.y_min <= pos.y <= self.y_max)
    
    def area(self) -> int:
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    def center(self) -> Position:
        return Position(
            (self.x_min + self.x_max) // 2,
            (self.y_min + self.y_max) // 2
        )


@dataclass(frozen=True)
class Circle:
    """Circular region on terrain."""
    center: Position
    radius: int
    
    def contains(self, pos: Position) -> bool:
        return self.center.distance_to(pos) <= self.radius
    
    def area(self) -> float:
        return math.pi * self.radius ** 2
```

**Benefits:**
- Type-safe geometry operations
- Validation on construction
- Immutable (frozen) for safety
- Rich methods for common operations

---

### **Layer 2: Features (Domain Objects)**

Features are the entities we place on terrain:

```python
# features/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class FeatureType(Enum):
    """Enumeration of feature types (6 core primitives)."""
    MOUNTAIN = "mountain"
    VALLEY = "valley"
    DUNES = "dunes"
    CLIFF = "cliff"
    PLATEAU = "plateau"
    CANYON = "canyon"


@dataclass
class FeatureIdentity:
    """Identity and metadata for a feature."""
    id: int
    type: FeatureType
    label: Optional[str] = None  # Semantic label ("the peak")
    created_at: float = field(default_factory=time.time)


@dataclass
class FeatureGeometry:
    """Geometric properties common to all features."""
    position: Position
    bounding_radius: int  # Approximate spatial extent


@dataclass
class FeatureAppearance:
    """Appearance properties (affect rendering)."""
    height: float  # 0.0-1.0
    use_noise: bool = True


class Feature(ABC):
    """
    Abstract base class for all terrain features.
    
    Design principles:
    1. Identity: Who am I? (id, type, label)
    2. Geometry: Where am I? (position, bounds)
    3. Appearance: What do I look like? (height, style)
    4. Behavior: How do I interact? (stamping, blending)
    """
    
    def __init__(
        self,
        identity: FeatureIdentity,
        geometry: FeatureGeometry,
        appearance: FeatureAppearance
    ):
        self.identity = identity
        self.geometry = geometry
        self.appearance = appearance
    
    # === Identity ===
    @property
    def id(self) -> int:
        return self.identity.id
    
    @property
    def type(self) -> FeatureType:
        return self.identity.type
    
    @property
    def label(self) -> Optional[str]:
        return self.identity.label
    
    # === Geometry ===
    @property
    def position(self) -> Position:
        return self.geometry.position
    
    @property
    def bounds(self) -> Circle:
        return Circle(self.position, self.geometry.bounding_radius)
    
    def overlaps_with(self, other: 'Feature') -> bool:
        """Check if this feature overlaps with another."""
        distance = self.position.distance_to(other.position)
        return distance < (self.geometry.bounding_radius + other.geometry.bounding_radius)
    
    # === Appearance ===
    @property
    def height(self) -> float:
        return self.appearance.height
    
    # === Behavior (Abstract) ===
    @abstractmethod
    def get_stamp(self, seed: int) -> np.ndarray:
        """Generate 512x512 heightmap stamp for this feature."""
        pass
    
    @abstractmethod
    def get_blending_mode(self) -> BlendingMode:
        """Get blending mode for compositing this feature."""
        pass
    
    @abstractmethod
    def get_type_specific_params(self) -> Dict[str, Any]:
        """Get type-specific parameters (e.g., steepness for mountains)."""
        pass
    
    # === Serialization ===
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON serialization)."""
        return {
            "id": self.id,
            "type": self.type.value,
            "x": self.position.x,
            "y": self.position.y,
            "height": self.height,
            "use_noise": self.appearance.use_noise,
            "label": self.label,
            **self.get_type_specific_params()
        }
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feature':
        """Create feature from dictionary."""
        pass
```

**Benefits:**
- Clear separation of concerns (identity/geometry/appearance/behavior)
- Type-safe properties
- Abstract methods enforce interface
- Easy to add feature-specific logic
- Serialization built-in

---

### **Layer 2.1: Concrete Feature Types**

Now we implement each of the 6 core primitives:

```python
# features/mountain.py
@dataclass
class MountainParams:
    """Mountain-specific parameters."""
    radius: int = 56
    steepness: float = 1.0
    
    def __post_init__(self):
        assert 15 <= self.radius <= 120
        assert 0.5 <= self.steepness <= 2.5


class Mountain(Feature):
    """Mountain feature - hero elevation primitive."""
    
    def __init__(
        self,
        identity: FeatureIdentity,
        geometry: FeatureGeometry,
        appearance: FeatureAppearance,
        params: MountainParams
    ):
        super().__init__(identity, geometry, appearance)
        self.params = params
        
        # Update bounding radius based on mountain radius
        self.geometry.bounding_radius = params.radius
    
    def get_stamp(self, seed: int) -> np.ndarray:
        """Generate mountain stamp."""
        from ..primitives.mountains import generate_mountain
        return generate_mountain(
            cx=self.position.x,
            cy=self.position.y,
            radius=self.params.radius,
            height=self.height,
            steepness=self.params.steepness,
            use_noise=self.appearance.use_noise,
            seed=seed
        )
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_type_specific_params(self) -> Dict[str, Any]:
        return {
            "radius": self.params.radius,
            "steepness": self.params.steepness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mountain':
        identity = FeatureIdentity(
            id=data["id"],
            type=FeatureType.MOUNTAIN,
            label=data.get("label")
        )
        geometry = FeatureGeometry(
            position=Position(data["x"], data["y"]),
            bounding_radius=data.get("radius", 56)
        )
        appearance = FeatureAppearance(
            height=data.get("height", 0.75),
            use_noise=data.get("use_noise", True)
        )
        params = MountainParams(
            radius=data.get("radius", 56),
            steepness=data.get("steepness", 1.0)
        )
        return cls(identity, geometry, appearance, params)


# features/valley.py
@dataclass
class ValleyParams:
    """Valley-specific parameters."""
    radius: int = 80
    depth: float = 0.5
    flatness: float = 0.5
    
    def __post_init__(self):
        assert 30 <= self.radius <= 150
        assert 0.2 <= self.depth <= 0.9
        assert 0.2 <= self.flatness <= 0.8


class Valley(Feature):
    """Valley feature - hero depression primitive."""
    
    def __init__(
        self,
        identity: FeatureIdentity,
        geometry: FeatureGeometry,
        appearance: FeatureAppearance,
        params: ValleyParams
    ):
        super().__init__(identity, geometry, appearance)
        self.params = params
        self.geometry.bounding_radius = params.radius
    
    def get_stamp(self, seed: int) -> np.ndarray:
        from ..primitives.valleys import generate_valley
        return generate_valley(
            cx=self.position.x,
            cy=self.position.y,
            radius=self.params.radius,
            depth=self.params.depth,
            flatness=self.params.flatness
        )
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.SUBTRACT
    
    def get_type_specific_params(self) -> Dict[str, Any]:
        return {
            "radius": self.params.radius,
            "depth": self.params.depth,
            "flatness": self.params.flatness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Valley':
        # Similar to Mountain.from_dict()
        pass


# ... Similar for Dunes, Cliff, Plateau, Canyon
```

**Pattern:**
- Each feature has a `<FeatureType>Params` dataclass
- Params validated on construction
- Type-specific logic encapsulated
- Consistent interface via base class

---

### **Layer 3: Scene (Aggregate)**

The scene manages collections of features:

```python
# scene/terrain_scene.py
@dataclass
class TerrainScene:
    """
    Complete terrain scene.
    
    Responsibilities:
    - Manage feature collection
    - Enforce spatial constraints
    - Track scene metadata
    - Provide query interface
    """
    
    features: List[Feature] = field(default_factory=list)
    seed: int = field(default_factory=lambda: random.randint(0, 2**31))
    biome: str = "default"
    next_feature_id: int = 1
    
    # Optional: Semantic scene graph
    semantic_scene: Optional[TerrainSceneGraph] = None
    
    # === Queries ===
    def get_feature_by_id(self, feature_id: int) -> Optional[Feature]:
        """Find feature by ID."""
        for feat in self.features:
            if feat.id == feature_id:
                return feat
        return None
    
    def get_features_by_type(self, feature_type: FeatureType) -> List[Feature]:
        """Get all features of a specific type."""
        return [f for f in self.features if f.type == feature_type]
    
    def get_features_in_region(self, region: Region) -> List[Feature]:
        """Get all features within a region."""
        return [f for f in self.features if region.contains(f.position)]
    
    def get_features_near(self, position: Position, radius: int) -> List[Feature]:
        """Get features within radius of position."""
        return [
            f for f in self.features
            if f.position.distance_to(position) <= radius
        ]
    
    # === Mutations ===
    def add_feature(self, feature: Feature) -> None:
        """Add a feature to the scene."""
        # Validation
        if not self._validate_feature(feature):
            raise ValueError(f"Invalid feature: {feature}")
        
        self.features.append(feature)
    
    def remove_feature(self, feature_id: int) -> bool:
        """Remove a feature by ID."""
        for i, feat in enumerate(self.features):
            if feat.id == feature_id:
                del self.features[i]
                return True
        return False
    
    def _validate_feature(self, feature: Feature) -> bool:
        """Validate feature constraints."""
        # Check bounds
        if not (0 <= feature.position.x <= 512 and
                0 <= feature.position.y <= 512):
            return False
        
        # Check for overlaps (optional, can be relaxed)
        for existing in self.features:
            if feature.overlaps_with(existing):
                logger.warning(f"Feature {feature.id} overlaps with {existing.id}")
                # Don't fail, just warn
        
        return True
    
    # === Statistics ===
    def get_statistics(self) -> Dict[str, Any]:
        """Compute scene statistics."""
        return {
            "feature_count": len(self.features),
            "type_distribution": self._get_type_distribution(),
            "height_range": self._get_height_range(),
            "coverage": self._estimate_coverage(),
        }
    
    def _get_type_distribution(self) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(f.type.value for f in self.features))
    
    def _get_height_range(self) -> Tuple[float, float]:
        if not self.features:
            return (0.0, 0.0)
        heights = [f.height for f in self.features]
        return (min(heights), max(heights))
    
    def _estimate_coverage(self) -> float:
        """Estimate % of terrain covered by features."""
        total_area = 512 * 512
        feature_area = sum(f.bounds.area() for f in self.features)
        return min(1.0, feature_area / total_area)
    
    # === Serialization ===
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "features": [f.to_dict() for f in self.features],
            "seed": self.seed,
            "biome": self.biome,
            "next_id": self.next_feature_id,
            "semantic_scene": self.semantic_scene.to_dict() if self.semantic_scene else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerrainScene':
        """Create scene from dictionary."""
        scene = cls(
            seed=data.get("seed", random.randint(0, 2**31)),
            biome=data.get("biome", "default"),
            next_feature_id=data.get("next_id", 1)
        )
        
        # Deserialize features
        for feat_dict in data.get("features", []):
            feature = _deserialize_feature(feat_dict)
            scene.features.append(feature)
        
        return scene


def _deserialize_feature(data: Dict[str, Any]) -> Feature:
    """Factory function to deserialize features by type."""
    feature_type = FeatureType(data["type"])
    
    # Dispatch to concrete class
    if feature_type == FeatureType.MOUNTAIN:
        return Mountain.from_dict(data)
    elif feature_type == FeatureType.VALLEY:
        return Valley.from_dict(data)
    elif feature_type == FeatureType.DUNES:
        return Dunes.from_dict(data)
    elif feature_type == FeatureType.CLIFF:
        return Cliff.from_dict(data)
    elif feature_type == FeatureType.PLATEAU:
        return Plateau.from_dict(data)
    elif feature_type == FeatureType.CANYON:
        return Canyon.from_dict(data)
    else:
        raise ValueError(f"Unknown feature type: {feature_type}")
```

**Benefits:**
- Type-safe feature collection
- Rich query interface
- Validation on mutations
- Statistics computation
- Clean serialization

---

### **Layer 4: Narrative (Intelligence)**

Already defined in `narrative/types.py`, but let's ensure integration:

```python
# narrative/types.py (already created)
@dataclass
class TerrainNarrative:
    """Complete terrain narrative."""
    archetype: TerrainArchetype
    story: str
    aesthetic_goals: List[AestheticGoal]
    # ... (all the fields we defined)


# narrative/integration.py (NEW)
class NarrativeToSceneMapper:
    """
    Maps narrative descriptions to concrete scene features.
    
    Responsibilities:
    - Convert narrative → feature specifications
    - Apply aesthetic modifiers to parameters
    - Maintain narrative coherence
    """
    
    def __init__(self, narrative: TerrainNarrative):
        self.narrative = narrative
    
    def create_feature_from_spec(
        self,
        feature_type: FeatureType,
        position: Position,
        role: str,  # "hero", "supporting", "accent"
        scene: TerrainScene
    ) -> Feature:
        """
        Create a feature based on narrative guidance.
        
        Args:
            feature_type: Type of feature to create
            position: Where to place it
            role: Compositional role
            scene: Scene (for ID assignment)
        
        Returns:
            Fully configured Feature instance
        """
        # Create identity
        identity = FeatureIdentity(
            id=scene.next_feature_id,
            type=feature_type,
            label=self._generate_label(feature_type, role)
        )
        scene.next_feature_id += 1
        
        # Infer parameters from narrative
        params = self._infer_parameters(feature_type, role)
        
        # Create geometry
        geometry = FeatureGeometry(
            position=position,
            bounding_radius=params.get("radius", 50)
        )
        
        # Create appearance
        appearance = FeatureAppearance(
            height=params.get("height", 0.5),
            use_noise=self._should_use_noise()
        )
        
        # Create concrete feature
        if feature_type == FeatureType.MOUNTAIN:
            mountain_params = MountainParams(
                radius=params.get("radius", 56),
                steepness=params.get("steepness", 1.0)
            )
            return Mountain(identity, geometry, appearance, mountain_params)
        
        # ... similar for other types
    
    def _infer_parameters(self, feature_type: FeatureType, role: str) -> Dict[str, Any]:
        """Infer parameters from narrative + role."""
        # Get archetype defaults
        params = self._get_archetype_defaults(feature_type)
        
        # Apply aesthetic modifiers
        for aesthetic in self.narrative.aesthetic_goals:
            self._apply_aesthetic_modifier(params, aesthetic)
        
        # Apply role scaling
        if role == "hero":
            params["height"] = params.get("height", 0.5) * 1.2
            params["radius"] = params.get("radius", 50) * 1.1
        elif role == "supporting":
            params["height"] = params.get("height", 0.5) * 0.85
        
        return params
    
    def _get_archetype_defaults(self, feature_type: FeatureType) -> Dict[str, Any]:
        """Get default parameters for feature type from archetype."""
        archetype = self.narrative.archetype
        
        if feature_type == FeatureType.MOUNTAIN:
            return {
                "radius": int(56 * archetype.scale_bias),
                "height": (archetype.height_range[0] + archetype.height_range[1]) / 2,
                "steepness": 1.0 / archetype.smoothness_bias
            }
        
        # ... similar for other types
        
        return {}
    
    def _apply_aesthetic_modifier(self, params: Dict, aesthetic: AestheticGoal):
        """Apply aesthetic goal to parameters."""
        from ..narrative.narrative_dev import AESTHETIC_PARAMETER_MAPS
        
        modifiers = AESTHETIC_PARAMETER_MAPS.get(aesthetic, {})
        
        for param, multiplier in modifiers.items():
            if param.endswith("_multiplier"):
                base_param = param.replace("_multiplier", "")
                if base_param in params:
                    params[base_param] *= multiplier
    
    def _should_use_noise(self) -> bool:
        """Determine if noise should be enabled based on aesthetics."""
        return AestheticGoal.RUGGED in self.narrative.aesthetic_goals or \
               AestheticGoal.ORGANIC in self.narrative.aesthetic_goals
    
    def _generate_label(self, feature_type: FeatureType, role: str) -> Optional[str]:
        """Generate semantic label for feature."""
        if role == "hero":
            labels = {
                FeatureType.MOUNTAIN: "the great peak",
                FeatureType.VALLEY: "the main valley",
                FeatureType.DUNES: "the great dune",
                FeatureType.CLIFF: "the towering cliff",
                FeatureType.PLATEAU: "the high mesa",
                FeatureType.CANYON: "the deep canyon"
            }
            return labels.get(feature_type)
        return None  # Supporting/accent features get no label
```

**Benefits:**
- Clean separation: Narrative → Scene mapping
- Parameters inferred intelligently
- Type-safe feature creation
- Labels generated automatically

---

### **Layer 5: Services (Application Logic)**

High-level orchestration:

```python
# services/terrain_generation_service.py
class TerrainGenerationService:
    """
    High-level service for terrain generation.
    
    Orchestrates:
    - Narrative development
    - Scene composition
    - Heightmap generation
    - Quality evaluation
    """
    
    def __init__(self):
        self.builder = TerrainBuilder()
    
    def generate_from_command(
        self,
        command: str,
        existing_scene: Optional[TerrainScene] = None
    ) -> TerrainGenerationResult:
        """
        Generate terrain from natural language command.
        
        Full pipeline with narrative intelligence.
        """
        
        # Step 1: Develop narrative
        from ..semantic.narrative import develop_terrain_narrative
        narrative_result = develop_terrain_narrative(command, existing_scene)
        narrative = narrative_result.data["narrative_object"]
        
        # Step 2: Create or use existing scene
        scene = existing_scene or TerrainScene(biome=narrative.climate)
        
        # Step 3: Calculate spatial constraints
        from ..semantic.narrative import calculate_spatial_constraints
        constraints_result = calculate_spatial_constraints(narrative, scene)
        constraints = constraints_result.data["constraints"]
        
        # Step 4: Plan composition
        from ..semantic.narrative import plan_composition
        composition_result = plan_composition(narrative, constraints)
        composition = composition_result.data["composition"]
        
        # Step 5: Create features from composition
        mapper = NarrativeToSceneMapper(narrative)
        for feature_spec in composition.all_feature_specs():
            feature = mapper.create_feature_from_spec(
                feature_type=FeatureType(feature_spec["type"]),
                position=Position(feature_spec["x"], feature_spec["y"]),
                role=feature_spec["role"],
                scene=scene
            )
            scene.add_feature(feature)
        
        # Step 6: Generate heightmap
        self.builder.reset()
        for feature in scene.features:
            stamp = feature.get_stamp(scene.seed)
            self.builder.apply_feature(
                stamp,
                feature.get_blending_mode(),
                feature.position.x,
                feature.position.y
            )
        
        self.builder.finalize()
        heightmap = self.builder.heightmap.copy()
        
        # Step 7: Generate splatmap
        splatmap = self.builder.build_splatmap()
        
        # Step 8: Evaluate quality
        from ..semantic.narrative import evaluate_narrative_coherence
        coherence_result = evaluate_narrative_coherence(scene, narrative)
        scores = coherence_result.data["scores"]
        
        return TerrainGenerationResult(
            scene=scene,
            heightmap=heightmap,
            splatmap=splatmap,
            narrative=narrative,
            coherence_scores=scores
        )


@dataclass
class TerrainGenerationResult:
    """Result of terrain generation."""
    scene: TerrainScene
    heightmap: np.ndarray
    splatmap: np.ndarray
    narrative: TerrainNarrative
    coherence_scores: CoherenceScores
```

---

## 📊 **Complete Type Hierarchy Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 5: Services                         │
│  TerrainGenerationService                                    │
│    ↓ orchestrates                                            │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: Narrative                         │
│  TerrainNarrative → NarrativeToSceneMapper                   │
│    ↓ guides                                                  │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Scene                            │
│  TerrainScene (aggregate of Features)                        │
│    ↓ contains                                                │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Layer 2: Features                         │
│  Feature (ABC)                                               │
│    ├─ Mountain                                               │
│    ├─ Valley                                                 │
│    ├─ Dunes                                                  │
│    ├─ Cliff                                                  │
│    ├─ Plateau                                                │
│    └─ Canyon                                                 │
│                                                              │
│  Each has:                                                   │
│    - FeatureIdentity                                         │
│    - FeatureGeometry                                         │
│    - FeatureAppearance                                       │
│    - <Type>Params                                            │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: Primitives                       │
│  Position, Region, Circle                                    │
│  (immutable, validated geometry types)                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔍 **Type Safety Analysis**

### **What We Gain:**

#### **1. Compile-Time Error Detection**
```python
# Before (runtime error):
feature["radius"] = "fifty"  # No error until execution!
heightmap = builder.apply_feature(feature)  # Crash!

# After (type error caught by IDE/mypy):
feature.params.radius = "fifty"  # Type error: Expected int, got str
```

#### **2. IDE Autocomplete**
```python
# Before:
feature["r..."]  # IDE can't help, dict keys are strings

# After:
feature.params.ra<TAB>  # IDE suggests: radius (int)
```

#### **3. Validation on Construction**
```python
# Before:
feature = {"x": 1000, "radius": -50}  # Invalid but no error!

# After:
pos = Position(1000, 200)  # AssertionError: x out of bounds
params = MountainParams(radius=-50)  # AssertionError: radius invalid
```

#### **4. Refactoring Safety**
```python
# Before: Rename "radius" → "size"
# Must find all dict accesses (error-prone!)

# After: Rename MountainParams.radius → size
# IDE/refactoring tools update all references automatically
```

### **Runtime Checks vs Compile-Time Checks**

| Check | Runtime (Dict) | Compile-Time (Class) |
|-------|----------------|----------------------|
| Type mismatch | ❌ Crashes | ✅ IDE error |
| Missing key | ❌ KeyError | ✅ Type error |
| Invalid range | ⚠️ Must validate | ✅ __post_init__ |
| Misspelled name | ❌ Silent bug | ✅ AttributeError |

---

## 🎯 **Migration Strategy**

### **Phase 1: Add Type System (No Breaking Changes)**

Create new typed classes alongside existing dict-based code:

```python
# New file: features/base.py
# Define Feature, Mountain, Valley, etc.

# Existing code still works with dicts
# New code can use typed classes
```

### **Phase 2: Add Adapter Layer**

Bridge between old and new:

```python
# features/adapters.py
def feature_to_dict(feature: Feature) -> Dict[str, Any]:
    """Convert typed Feature to dict (for backward compatibility)."""
    return feature.to_dict()

def feature_from_dict(data: Dict[str, Any]) -> Feature:
    """Convert dict to typed Feature."""
    return _deserialize_feature(data)


# In TerrainBuilder:
class TerrainBuilder:
    def apply_feature_typed(self, feature: Feature, seed: int):
        """New method accepting typed features."""
        stamp = feature.get_stamp(seed)
        self.apply_feature(stamp, feature.get_blending_mode(), ...)
    
    def apply_feature(self, feat_dict: Dict, ...):
        """Old method, still works."""
        # Internally convert to typed feature
        feature = feature_from_dict(feat_dict)
        return self.apply_feature_typed(feature)
```

### **Phase 3: Gradual Adoption**

```python
# Week 2 tools: Use typed system
def plan_composition(narrative, constraints) -> FeatureComposition:
    # Returns typed composition
    pass

# Existing tools: Still use dicts
def apply_actions(actions: List[Dict], ...) -> Tuple:
    # Convert actions to typed features
    features = [feature_from_dict(action) for action in actions]
    # Use new typed API
    pass
```

### **Phase 4: Full Migration (Future)**

Eventually deprecate dict-based API:

```python
# terrain.py (future)
def apply_actions(actions: List[Feature], ...):  # Now expects typed
    pass

# All dict-based code converted
```

---

## 📐 **Design Patterns Applied**

### **1. Value Objects (Position, Region)**
- Immutable
- Equality by value
- No identity

### **2. Entity (Feature)**
- Has identity (ID)
- Mutable state
- Equality by ID

### **3. Aggregate (TerrainScene)**
- Manages collection of entities
- Enforces invariants
- Provides transactional boundary

### **4. Factory (from_dict, create_feature_from_spec)**
- Encapsulates creation logic
- Handles complex initialization
- Type-specific construction

### **5. Adapter (feature_to_dict, feature_from_dict)**
- Bridges typed and untyped worlds
- Maintains backward compatibility
- Smooth migration path

### **6. Service (TerrainGenerationService)**
- Stateless orchestration
- High-level workflows
- Composes lower-level components

---

## ✅ **Implementation Checklist**

### **Week 2 Day 1:**
- [ ] Create `features/base.py` with Feature ABC
- [ ] Create `geometry.py` with Position, Region, Circle
- [ ] Create `features/mountain.py` with Mountain class
- [ ] Create `features/valley.py` with Valley class
- [ ] Add unit tests for Position, Region validation

### **Week 2 Day 2:**
- [ ] Create remaining feature types (Dunes, Cliff, Plateau, Canyon)
- [ ] Create `scene/terrain_scene.py` with TerrainScene
- [ ] Create `features/adapters.py` for dict conversion
- [ ] Add unit tests for Feature serialization

### **Week 2 Day 3:**
- [ ] Create `narrative/integration.py` with NarrativeToSceneMapper
- [ ] Update narrative tools to return typed objects
- [ ] Add TerrainBuilder.apply_feature_typed() method
- [ ] Update tests

### **Week 2 Day 4:**
- [ ] Create `services/terrain_generation_service.py`
- [ ] Integrate all layers in service
- [ ] Add end-to-end test with typed API
- [ ] Documentation

### **Week 2 Day 5:**
- [ ] Gradually update existing code to use typed API
- [ ] Fix any issues
- [ ] Performance testing
- [ ] Final polish

---

## 🚀 **Expected Benefits**

### **Development Experience:**
- ✅ 50-70% reduction in type-related bugs
- ✅ IDE autocomplete speeds up development
- ✅ Refactoring becomes safe and easy
- ✅ Self-documenting code (types as documentation)

### **Code Quality:**
- ✅ Clear separation of concerns
- ✅ Single responsibility per class
- ✅ Easy to test each layer independently
- ✅ Easy to extend (add new feature types, archetypes)

### **Maintainability:**
- ✅ New developers onboard faster (types explain structure)
- ✅ Changes localized (modify Mountain, Valley unaffected)
- ✅ Validation centralized (in __post_init__)
- ✅ Serialization handled consistently

---

## ✨ **Summary**

**Proposed 5-Layer Architecture:**

1. **Primitives** - Position, Region, Circle (immutable geometry)
2. **Features** - Feature ABC + 6 concrete types (domain objects)
3. **Scene** - TerrainScene (aggregate, enforces invariants)
4. **Narrative** - TerrainNarrative + mapper (intelligence layer)
5. **Services** - TerrainGenerationService (orchestration)

**Key Principles:**
- Type safety (catch errors early)
- Clear abstractions (each layer has purpose)
- Composability (layers work together cleanly)
- Testability (each layer testable independently)
- Extensibility (easy to add new features/archetypes)

**Migration Path:**
- Phase 1: Add typed system (no breaking changes)
- Phase 2: Add adapters (bridge old/new)
- Phase 3: Gradual adoption (new code uses types)
- Phase 4: Full migration (deprecate dicts)

Ready to implement the type-safe architecture? 🎯

