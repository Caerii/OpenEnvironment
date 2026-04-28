"""
Mountain feature implementation.

The Mountain is the hero elevation primitive - tall, dramatic peaks with
configurable steepness and radius.
"""

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np

from server.features.base import (
    Feature,
    FeatureType,
    FeatureIdentity,
    FeatureGeometry,
    FeatureAppearance,
)
from server.core.geometry import Position
from server.engine.stamping import BlendingMode


@dataclass
class MountainParams:
    """
    Mountain-specific parameters.
    
    Attributes:
        radius: Base radius of mountain (15-120)
        steepness: Steepness factor (0.5-2.5, default 1.0)
    
    Examples:
        >>> params = MountainParams(radius=56, steepness=1.0)
        >>> params.radius
        56
        >>> params.steepness
        1.0
    """
    radius: int = 56
    steepness: float = 1.0
    
    def __post_init__(self):
        """Validate parameter ranges."""
        if not (15 <= self.radius <= 120):
            raise ValueError(f"Mountain radius must be in [15, 120]: {self.radius}")
        if not (0.5 <= self.steepness <= 2.5):
            raise ValueError(f"Mountain steepness must be in [0.5, 2.5]: {self.steepness}")


class Mountain(Feature):
    """
    Mountain feature - hero elevation primitive.
    
    Mountains are tall, dramatic peaks that serve as focal points. They use
    MAX blending mode and generate rock splatmap contribution via slope.
    
    Key characteristics:
    - Blending: MAX (tallest wins)
    - Splatmap: High slope → rock channel
    - Typical height: 0.65-0.95
    - Typical radius: 40-80
    
    Examples:
        >>> identity = FeatureIdentity(1, FeatureType.MOUNTAIN, "the peak")
        >>> geometry = FeatureGeometry(Position(256, 256), 56)
        >>> appearance = FeatureAppearance(0.75, use_noise=True)
        >>> params = MountainParams(radius=56, steepness=1.2)
        >>> mountain = Mountain(identity, geometry, appearance, params)
        >>> mountain.type
        <FeatureType.MOUNTAIN: 'mountain'>
        >>> mountain.get_blending_mode()
        <BlendingMode.MAX: 'max'>
    """
    
    def __init__(
        self,
        identity: FeatureIdentity,
        geometry: FeatureGeometry,
        appearance: FeatureAppearance,
        params: MountainParams
    ):
        """
        Initialize mountain feature.
        
        Args:
            identity: Feature identity (id, type, label)
            geometry: Geometric properties (position, bounds)
            appearance: Appearance properties (height, noise)
            params: Mountain-specific parameters (radius, steepness)
        """
        super().__init__(identity, geometry, appearance)
        self.params = params
        
        # Update bounding radius to match mountain radius
        self.geometry.bounding_radius = params.radius
    
    def get_stamp(self, seed: int) -> np.ndarray:
        """
        Generate mountain heightmap stamp.
        
        Args:
            seed: Random seed for procedural generation
            
        Returns:
            512x512 heightmap array with mountain shape
        """
        from server.primitives.mountains import generate_mountain
        
        return generate_mountain(
            cx=self.position.x,
            cy=self.position.y,
            radius=self.params.radius,
            height=self.height,
            steepness=self.params.steepness,
            use_noise=self.use_noise,
            seed=seed
        )
    
    def get_blending_mode(self) -> BlendingMode:
        """Mountains use MAX blending (tallest wins)."""
        return BlendingMode.MAX
    
    def get_type_specific_params(self) -> Dict[str, Any]:
        """Get mountain-specific parameters for serialization."""
        return {
            "radius": self.params.radius,
            "steepness": self.params.steepness
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mountain':
        """
        Create Mountain from dictionary.
        
        Args:
            data: Dictionary with mountain properties
            
        Returns:
            Mountain instance
            
        Examples:
            >>> data = {
            ...     "id": 1,
            ...     "type": "mountain",
            ...     "x": 256,
            ...     "y": 256,
            ...     "height": 0.75,
            ...     "radius": 56,
            ...     "steepness": 1.2
            ... }
            >>> mountain = Mountain.from_dict(data)
            >>> mountain.params.radius
            56
        """
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

