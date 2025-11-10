"""Core domain models for terrain generation.

This module defines the fundamental domain concepts with proper typing,
replacing the Dict-based approach with structured dataclasses.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class RegionType(Enum):
    """Named regions of the terrain."""
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    RANDOM = "random"
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass
class Position:
    """
    Position specification for feature placement.
    
    Supports three modes:
    1. Absolute coordinates: x, y specified
    2. Named region: region specified (e.g., "center", "left")
    3. Relative to feature: relative_to specified with offset
    
    Attributes:
        x: Absolute X coordinate (0-511), mutually exclusive with region
        y: Absolute Y coordinate (0-511), mutually exclusive with region
        region: Named region for placement, mutually exclusive with x/y
        relative_to: Reference to another feature for relative positioning
        offset_x: X offset when using relative positioning
        offset_y: Y offset when using relative positioning
    """
    x: Optional[int] = None
    y: Optional[int] = None
    region: Optional[str] = None
    relative_to: Optional[str] = None
    offset_x: int = 0
    offset_y: int = 0
    
    def is_absolute(self) -> bool:
        """Check if this is an absolute coordinate position."""
        return self.x is not None and self.y is not None
    
    def is_region(self) -> bool:
        """Check if this is a region-based position."""
        return self.region is not None
    
    def is_relative(self) -> bool:
        """Check if this is a relative position."""
        return self.relative_to is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation (for serialization)."""
        result = {}
        if self.x is not None:
            result["coords"] = [self.x, self.y]
        if self.region is not None:
            result["region"] = self.region
        if self.relative_to is not None:
            result["relative_to"] = self.relative_to
            if self.offset_x != 0 or self.offset_y != 0:
                result["offset"] = [self.offset_x, self.offset_y]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        """Create Position from dictionary (for deserialization)."""
        x, y = None, None
        if "coords" in data:
            coords = data["coords"]
            x, y = coords[0], coords[1]
        
        region = data.get("region")
        relative_to = data.get("relative_to")
        
        offset_x, offset_y = 0, 0
        if "offset" in data:
            offset = data["offset"]
            offset_x, offset_y = offset[0], offset[1]
        
        return cls(
            x=x, y=y, region=region,
            relative_to=relative_to, 
            offset_x=offset_x, offset_y=offset_y
        )


@dataclass
class Modifier:
    """
    Feature modifier specification.
    
    Modifiers adjust feature parameters like "taller", "wider", etc.
    
    Attributes:
        height_percent: Percentage adjustment to height (e.g., 20 = 120% of base)
        depth_percent: Percentage adjustment to depth
        width_percent: Percentage adjustment to width/radius
        taller: Boolean flag for "taller" keyword modifier
        deeper: Boolean flag for "deeper" keyword modifier  
        wider: Boolean flag for "wider" keyword modifier
        custom: Additional custom modifiers as key-value pairs
    """
    height_percent: Optional[float] = None
    depth_percent: Optional[float] = None
    width_percent: Optional[float] = None
    taller: bool = False
    deeper: bool = False
    wider: bool = False
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {}
        if self.height_percent is not None:
            result["height_percent"] = self.height_percent
        if self.depth_percent is not None:
            result["depth_percent"] = self.depth_percent
        if self.width_percent is not None:
            result["width_percent"] = self.width_percent
        if self.taller:
            result["taller"] = True
        if self.deeper:
            result["deeper"] = True
        if self.wider:
            result["wider"] = True
        result.update(self.custom)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Modifier":
        """Create Modifier from dictionary."""
        return cls(
            height_percent=data.get("height_percent"),
            depth_percent=data.get("depth_percent"),
            width_percent=data.get("width_percent"),
            taller=data.get("taller", False),
            deeper=data.get("deeper", False),
            wider=data.get("wider", False),
            custom={k: v for k, v in data.items() 
                   if k not in {"height_percent", "depth_percent", "width_percent", 
                               "taller", "deeper", "wider"}}
        )


@dataclass
class FeatureParameters:
    """
    Feature-specific parameters.
    
    This is intentionally flexible to accommodate different feature types
    while providing common structure. Type-specific parameters are stored
    in the params dict.
    
    Common parameters:
        height: Height/amplitude of feature (normalized 0-1)
        depth: Depth of feature (for valleys, canyons)
        radius: Radius for circular features
        width: Width for linear/rectangular features
        params: Additional type-specific parameters
    """
    height: Optional[float] = None
    depth: Optional[float] = None
    radius: Optional[int] = None
    width: Optional[int] = None
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {}
        if self.height is not None:
            result["height"] = self.height
        if self.depth is not None:
            result["depth"] = self.depth
        if self.radius is not None:
            result["radius"] = self.radius
        if self.width is not None:
            result["width"] = self.width
        result.update(self.params)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureParameters":
        """Create FeatureParameters from dictionary."""
        return cls(
            height=data.get("height"),
            depth=data.get("depth"),
            radius=data.get("radius"),
            width=data.get("width"),
            params={k: v for k, v in data.items() 
                   if k not in {"height", "depth", "radius", "width"}}
        )


@dataclass
class Feature:
    """
    A terrain feature instance.
    
    Represents a single feature placed on the terrain (e.g., one mountain).
    
    Attributes:
        id: Unique feature identifier (assigned by FeatureState)
        type: Feature type (e.g., "mountain", "valley", "dunes")
        position: Feature position (x, y coordinates)
        parameters: Feature-specific parameters (height, radius, etc.)
        metadata: Additional metadata (creation time, user intent, etc.)
    """
    id: int
    type: str
    position: Position
    parameters: FeatureParameters
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation for serialization.
        
        This maintains backward compatibility with the Dict-based system.
        """
        result = {
            "id": self.id,
            "type": self.type,
            "x": self.position.x,
            "y": self.position.y,
        }
        
        # Merge parameters into flat dict (backward compatibility)
        result.update(self.parameters.to_dict())
        
        # Add metadata
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        """
        Create Feature from dictionary representation.
        
        Handles both new structured format and legacy Dict format.
        """
        feature_id = data["id"]
        feature_type = data["type"]
        
        # Extract position
        x = data.get("x")
        y = data.get("y")
        position = Position(x=x, y=y)
        
        # Extract parameters (everything except known keys)
        known_keys = {"id", "type", "x", "y", "metadata"}
        params_data = {k: v for k, v in data.items() if k not in known_keys}
        parameters = FeatureParameters.from_dict(params_data)
        
        # Extract metadata
        metadata = data.get("metadata", {})
        
        return cls(
            id=feature_id,
            type=feature_type,
            position=position,
            parameters=parameters,
            metadata=metadata
        )


@dataclass
class TerrainState:
    """
    Complete terrain state.
    
    Represents the entire state of the terrain including all features,
    configuration, and semantic information.
    
    Attributes:
        features: List of all terrain features
        seed: Random seed for deterministic generation
        biome: Biome name (e.g., "desert", "mountains", "default")
        next_id: Next available feature ID
        semantic_scene: Serialized scene graph (optional)
        metadata: Additional state metadata
    """
    features: List[Feature] = field(default_factory=list)
    seed: int = 0
    biome: str = "default"
    next_id: int = 1
    semantic_scene: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for JSON serialization."""
        result = {
            "features": [f.to_dict() for f in self.features],
            "seed": self.seed,
            "biome": self.biome,
            "next_id": self.next_id,
        }
        if self.semantic_scene is not None:
            result["semantic_scene"] = self.semantic_scene
        if self.metadata:
            result.update(self.metadata)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerrainState":
        """Create TerrainState from dictionary representation."""
        features = [Feature.from_dict(f) for f in data.get("features", [])]
        seed = data.get("seed", 0)
        biome = data.get("biome", "default")
        next_id = data.get("next_id", 1)
        semantic_scene = data.get("semantic_scene")
        
        # Extract metadata (everything except known keys)
        known_keys = {"features", "seed", "biome", "next_id", "semantic_scene"}
        metadata = {k: v for k, v in data.items() if k not in known_keys}
        
        return cls(
            features=features,
            seed=seed,
            biome=biome,
            next_id=next_id,
            semantic_scene=semantic_scene,
            metadata=metadata
        )
    
    def add_feature(self, feature: Feature) -> int:
        """
        Add a feature to the state.
        
        Automatically assigns an ID if not set.
        
        Returns:
            Assigned feature ID
        """
        if feature.id == 0 or feature.id is None:
            feature.id = self.next_id
            self.next_id += 1
        else:
            # Ensure next_id is beyond this ID
            self.next_id = max(self.next_id, feature.id + 1)
        
        self.features.append(feature)
        return feature.id
    
    def remove_feature(self, feature_id: int) -> bool:
        """
        Remove a feature by ID.
        
        Returns:
            True if feature was removed, False if not found
        """
        for i, feature in enumerate(self.features):
            if feature.id == feature_id:
                del self.features[i]
                return True
        return False
    
    def find_feature(self, feature_id: int) -> Optional[Feature]:
        """Find a feature by ID."""
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        return None
    
    def list_features_by_type(self, feature_type: str) -> List[Feature]:
        """List all features of a specific type."""
        return [f for f in self.features if f.type == feature_type]

