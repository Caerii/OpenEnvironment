"""
Base classes for terrain features.

Defines the Feature ABC and supporting types (identity, geometry, appearance).
All features must implement get_stamp() and get_blending_mode().
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

import numpy as np

from server.core.geometry import Position, Circle
from server.engine.stamping import BlendingMode


class FeatureType(Enum):
    """
    Enumeration of core feature types.
    
    These are the 6 refined core primitives based on geological roles,
    splatmap contributions, and aesthetic value.
    """
    MOUNTAIN = "mountain"
    VALLEY = "valley"
    DUNES = "dunes"
    CLIFF = "cliff"
    PLATEAU = "plateau"
    CANYON = "canyon"


@dataclass
class FeatureIdentity:
    """
    Identity and metadata for a feature.
    
    Attributes:
        id: Unique identifier (assigned by scene)
        type: Feature type (mountain, valley, etc.)
        label: Optional semantic label (e.g., "the great peak")
        created_at: Unix timestamp of creation
    
    Examples:
        >>> identity = FeatureIdentity(1, FeatureType.MOUNTAIN, "the peak")
        >>> identity.id
        1
        >>> identity.label
        'the peak'
    """
    id: int
    type: FeatureType
    label: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Validate identity fields."""
        if self.id < 0:
            raise ValueError(f"Feature ID must be non-negative: {self.id}")


@dataclass
class FeatureGeometry:
    """
    Geometric properties common to all features.
    
    Attributes:
        position: Center position on terrain
        bounding_radius: Approximate spatial extent (for overlap checks)
    
    Examples:
        >>> from server.core.geometry import Position
        >>> geometry = FeatureGeometry(Position(256, 256), 50)
        >>> geometry.position.x
        256
        >>> geometry.bounds
        Circle(center=Position(x=256, y=256), radius=50)
    """
    position: Position
    bounding_radius: int
    
    def __post_init__(self):
        """Validate geometry fields."""
        if self.bounding_radius <= 0:
            raise ValueError(f"Bounding radius must be positive: {self.bounding_radius}")
    
    @property
    def bounds(self) -> Circle:
        """Get circular bounds for this feature."""
        return Circle(self.position, self.bounding_radius)


@dataclass
class FeatureAppearance:
    """
    Appearance properties affecting rendering.
    
    Attributes:
        height: Height multiplier (0.0-1.0)
        use_noise: Whether to apply procedural noise
    
    Examples:
        >>> appearance = FeatureAppearance(height=0.75, use_noise=True)
        >>> appearance.height
        0.75
    """
    height: float
    use_noise: bool = True
    
    def __post_init__(self):
        """Validate appearance fields."""
        if not (0.0 <= self.height <= 1.0):
            raise ValueError(f"Height must be in [0.0, 1.0]: {self.height}")


class Feature(ABC):
    """
    Abstract base class for all terrain features.
    
    Design principles:
    1. **Identity**: Who am I? (id, type, label)
    2. **Geometry**: Where am I? (position, bounds)
    3. **Appearance**: What do I look like? (height, style)
    4. **Behavior**: How do I interact? (stamping, blending)
    
    All concrete features (Mountain, Valley, etc.) must:
    - Implement get_stamp() to generate heightmap stamps
    - Implement get_blending_mode() to specify compositing
    - Implement get_type_specific_params() for serialization
    - Implement from_dict() for deserialization
    
    Examples:
        >>> # Concrete feature (Mountain) implementation
        >>> identity = FeatureIdentity(1, FeatureType.MOUNTAIN, "peak")
        >>> geometry = FeatureGeometry(Position(256, 256), 56)
        >>> appearance = FeatureAppearance(0.75, use_noise=True)
        >>> mountain = Mountain(identity, geometry, appearance, MountainParams())
        >>> mountain.id
        1
        >>> mountain.type
        <FeatureType.MOUNTAIN: 'mountain'>
    """
    
    def __init__(
        self,
        identity: FeatureIdentity,
        geometry: FeatureGeometry,
        appearance: FeatureAppearance
    ):
        """
        Initialize feature with identity, geometry, and appearance.
        
        Args:
            identity: Feature identity (id, type, label)
            geometry: Geometric properties (position, bounds)
            appearance: Appearance properties (height, noise)
        """
        self.identity = identity
        self.geometry = geometry
        self.appearance = appearance
    
    # === Identity Properties ===
    
    @property
    def id(self) -> int:
        """Get feature ID."""
        return self.identity.id
    
    @property
    def type(self) -> FeatureType:
        """Get feature type."""
        return self.identity.type
    
    @property
    def label(self) -> Optional[str]:
        """Get semantic label (if any)."""
        return self.identity.label
    
    @property
    def created_at(self) -> float:
        """Get creation timestamp."""
        return self.identity.created_at
    
    # === Geometry Properties ===
    
    @property
    def position(self) -> Position:
        """Get center position."""
        return self.geometry.position
    
    @property
    def bounds(self) -> Circle:
        """Get circular bounds."""
        return self.geometry.bounds
    
    def overlaps_with(self, other: 'Feature') -> bool:
        """
        Check if this feature overlaps with another.
        
        Args:
            other: Feature to check
            
        Returns:
            True if circular bounds overlap
        """
        return self.bounds.overlaps_with(other.bounds)
    
    # === Appearance Properties ===
    
    @property
    def height(self) -> float:
        """Get height multiplier."""
        return self.appearance.height
    
    @property
    def use_noise(self) -> bool:
        """Check if noise is enabled."""
        return self.appearance.use_noise
    
    # === Abstract Behavior ===
    
    @abstractmethod
    def get_stamp(self, seed: int) -> np.ndarray:
        """
        Generate 512x512 heightmap stamp for this feature.
        
        This stamp will be composited onto the terrain using the
        blending mode specified by get_blending_mode().
        
        Args:
            seed: Random seed for procedural generation
            
        Returns:
            512x512 numpy array with heightmap values
        """
        pass
    
    @abstractmethod
    def get_blending_mode(self) -> BlendingMode:
        """
        Get blending mode for compositing this feature.
        
        Returns:
            BlendingMode (MAX for mountains, SUBTRACT for valleys, etc.)
        """
        pass
    
    @abstractmethod
    def get_type_specific_params(self) -> Dict[str, Any]:
        """
        Get type-specific parameters for serialization.
        
        Returns:
            Dictionary with feature-specific params (e.g., steepness for mountains)
        """
        pass
    
    # === Serialization ===
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert feature to dictionary for JSON serialization.
        
        Returns:
            Dictionary with all feature properties
        
        Examples:
            >>> feature.to_dict()
            {
                'id': 1,
                'type': 'mountain',
                'x': 256,
                'y': 256,
                'height': 0.75,
                'use_noise': True,
                'label': 'the peak',
                'radius': 56,
                'steepness': 1.0
            }
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "x": self.position.x,
            "y": self.position.y,
            "height": self.height,
            "use_noise": self.use_noise,
            "label": self.label,
            **self.get_type_specific_params()
        }
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feature':
        """
        Create feature from dictionary.
        
        Args:
            data: Dictionary with feature properties
            
        Returns:
            Concrete Feature instance
        
        Raises:
            ValueError: If data is invalid or missing required fields
        """
        pass
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        label_str = f" '{self.label}'" if self.label else ""
        return (f"{self.__class__.__name__}(id={self.id}{label_str}, "
                f"pos=({self.position.x},{self.position.y}), "
                f"height={self.height:.2f})")

