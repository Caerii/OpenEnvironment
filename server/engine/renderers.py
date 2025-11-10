"""
Feature renderers - Clean separation of data (Feature) from behavior (rendering).

This module replaces the dict-based FeatureRegistry with a cleaner, typed API.
Each renderer knows HOW to render a specific feature type to a heightmap stamp.

Architecture:
- FeatureRenderer (ABC): Interface for all renderers
- Concrete renderers (MountainRenderer, etc.): Type-specific rendering logic
- RendererRegistry: Central registry mapping feature types → renderers

Example usage:
    # Render a typed Feature
    stamp, mode = RendererRegistry.render(feature, seed=42)
    
    # Apply to builder
    builder.apply_feature(stamp, mode.value, feature_type=feature.type)
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import numpy as np

from ..domain.models import Feature
from .stamping import BlendingMode


logger = logging.getLogger(__name__)


class FeatureRenderer(ABC):
    """
    Abstract base class for feature renderers.
    
    Each renderer implements type-specific logic for converting a Feature
    (data) into a heightmap stamp (rendering).
    """
    
    @abstractmethod
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render feature to heightmap stamp.
        
        Args:
            feature: Typed Feature instance (from domain/models.py)
            seed: Random seed for procedural generation
            
        Returns:
            Tuple of (512x512 heightmap stamp, blending mode string)
            BlendingMode is a string constant: "max", "min", "add", "subtract", etc.
            
        Raises:
            ValueError: If feature parameters are invalid
        """
        pass


class MountainRenderer(FeatureRenderer):
    """Renderer for mountain features - hero elevation primitive."""
    
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render mountain to heightmap stamp.
        
        Parameters used:
        - position.x, position.y: Center coordinates
        - parameters.height: Height multiplier (0.0-1.0)
        - parameters.radius: Base radius
        - parameters.params["steepness"]: Steepness factor (default: 1.0)
        - parameters.params["use_noise"]: Whether to apply noise (default: True)
        """
        from ..primitives.mountains import generate_mountain
        
        # Extract parameters with defaults
        x = feature.position.x or 256
        y = feature.position.y or 256
        height = feature.parameters.height or 0.75
        radius = feature.parameters.radius or 56
        steepness = feature.parameters.params.get("steepness", 1.0)
        use_noise = feature.parameters.params.get("use_noise", True)
        
        # Generate stamp using primitive function
        stamp = generate_mountain(
            cx=x,
            cy=y,
            radius=radius,
            height=height,
            steepness=steepness,
            use_noise=use_noise,
            seed=seed
        )
        
        return stamp, BlendingMode.MAX


class ValleyRenderer(FeatureRenderer):
    """Renderer for valley features - hero depression primitive."""
    
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render valley to heightmap stamp.
        
        Parameters used:
        - position.x, position.y: Center coordinates
        - parameters.depth: Depth multiplier (0.0-1.0)
        - parameters.radius: Basin radius
        
        Note: generate_valley signature is (cx, cy, radius, depth)
        """
        from ..primitives.valleys import generate_valley
        
        x = feature.position.x or 256
        y = feature.position.y or 256
        radius = feature.parameters.radius or 80
        depth = feature.parameters.depth or 0.5
        
        stamp = generate_valley(
            cx=x,
            cy=y,
            radius=radius,
            depth=depth
        )
        
        return stamp, BlendingMode.SUBTRACT


class DunesRenderer(FeatureRenderer):
    """Renderer for dunes features - sand texture primitive."""
    
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render dunes to heightmap stamp.
        
        Note: Dunes require special handling for dune_mask.
        The caller (builder) must apply the mask separately.
        
        Parameters used:
        - parameters.params["x0"], ["y0"], ["x1"], ["y1"]: Bounding box (region tuple)
        - parameters.params["amp"]: Amplitude (default: 0.08)
        - parameters.params["angle_deg"]: Angle in degrees (default: 20.0)
        
        Note: generate_dunes signature is (region, amp, freq, angle_deg, seed)
        """
        from ..primitives.dunes import generate_dunes
        
        # Dunes use bounding box (region tuple)
        x0 = feature.parameters.params.get("x0", 50)
        y0 = feature.parameters.params.get("y0", 50)
        x1 = feature.parameters.params.get("x1", 450)
        y1 = feature.parameters.params.get("y1", 450)
        region = (x0, y0, x1, y1)
        
        amp = feature.parameters.params.get("amp", 0.08)
        angle_deg = feature.parameters.params.get("angle_deg", 20.0)
        
        stamp = generate_dunes(
            region=region,
            amp=amp,
            angle_deg=angle_deg,
            seed=seed
        )
        
        return stamp, BlendingMode.MAX


class CliffRenderer(FeatureRenderer):
    """Renderer for cliff features - vertical drama primitive."""
    
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render cliff to heightmap stamp.
        
        Note: Cliffs require special handling for cliff_mask.
        The caller (builder) must apply the mask separately.
        
        Parameters used:
        - position.x, position.y: Center coordinates
        - parameters.height: Cliff height (default: 0.7)
        - parameters.params["length"]: Cliff length (default: 150)
        - parameters.params["orientation"]: Rotation angle in degrees (default: 0.0)
        - parameters.params["steepness"]: Steepness factor (default: 0.9)
        
        Note: generate_cliff signature is (cx, cy, length, height, orientation, steepness)
        """
        from ..primitives.cliffs import generate_cliff
        
        x = feature.position.x or 256
        y = feature.position.y or 256
        height = feature.parameters.height or 0.7
        length = feature.parameters.params.get("length", 150)
        orientation = feature.parameters.params.get("orientation", 0.0)
        steepness = feature.parameters.params.get("steepness", 0.9)
        
        stamp = generate_cliff(
            cx=x,
            cy=y,
            length=length,
            height=height,
            orientation=orientation,
            steepness=steepness
        )
        
        return stamp, BlendingMode.MAX


class PlateauRenderer(FeatureRenderer):
    """Renderer for plateau features - flat elevated zones."""
    
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render plateau to heightmap stamp.
        
        Parameters used:
        - position.x, position.y: Center coordinates
        - parameters.height: Plateau height (default: 0.6)
        - parameters.width: Plateau width (default: 80)
        - parameters.params["length"]: Plateau length (default: 80)
        - parameters.params["orientation"]: Rotation angle in degrees (default: 0.0)
        
        Note: generate_plateau signature is (cx, cy, width, length, height, orientation)
        """
        from ..primitives.mountains import generate_plateau
        
        x = feature.position.x or 256
        y = feature.position.y or 256
        width = feature.parameters.width or 80
        length = feature.parameters.params.get("length", 80)
        height = feature.parameters.height or 0.6
        orientation = feature.parameters.params.get("orientation", 0.0)
        
        stamp = generate_plateau(
            cx=x,
            cy=y,
            width=width,
            length=length,
            height=height,
            orientation=orientation
        )
        
        return stamp, BlendingMode.MAX


class CanyonRenderer(FeatureRenderer):
    """Renderer for canyon features - linear exploration primitive."""
    
    def render(self, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render canyon to heightmap stamp.
        
        Parameters used:
        - position.x, position.y: Start coordinates
        - parameters.params["end_x"], ["end_y"]: End coordinates
        - parameters.depth: Canyon depth (default: 0.6)
        - parameters.width: Canyon width (default: 40)
        """
        from ..primitives.valleys import generate_canyon
        
        x = feature.position.x or 100
        y = feature.position.y or 100
        end_x = feature.parameters.params.get("end_x", 400)
        end_y = feature.parameters.params.get("end_y", 400)
        depth = feature.parameters.depth or 0.6
        width = feature.parameters.width or 40
        
        stamp = generate_canyon(
            start=(x, y),
            end=(end_x, end_y),
            width=width,
            depth=depth
        )
        
        return stamp, BlendingMode.SUBTRACT


class RendererRegistry:
    """
    Central registry of feature renderers.
    
    This replaces the old dict-based FeatureRegistry with a cleaner,
    typed API that works with domain/models.Feature.
    
    Usage:
        # Render a feature
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        # Check if a type is supported
        if RendererRegistry.has_renderer("mountain"):
            ...
        
        # Get list of supported types
        types = RendererRegistry.get_supported_types()
    """
    
    _renderers: Dict[str, FeatureRenderer] = {}
    
    @classmethod
    def register(cls, feature_type: str, renderer: FeatureRenderer):
        """
        Register a renderer for a feature type.
        
        Args:
            feature_type: Feature type string (e.g., "mountain")
            renderer: FeatureRenderer instance
        """
        cls._renderers[feature_type] = renderer
        logger.debug(f"Registered renderer for feature type: {feature_type}")
    
    @classmethod
    def render(cls, feature: Feature, seed: int) -> Tuple[np.ndarray, str]:
        """
        Render a typed Feature to heightmap stamp.
        
        Args:
            feature: Typed Feature instance (domain/models.Feature)
            seed: Random seed for procedural generation
            
        Returns:
            Tuple of (512x512 heightmap stamp, blending mode string)
            
        Raises:
            ValueError: If feature type has no registered renderer
        """
        renderer = cls._renderers.get(feature.type)
        if not renderer:
            raise ValueError(
                f"No renderer registered for feature type: '{feature.type}'. "
                f"Supported types: {list(cls._renderers.keys())}"
            )
        
        return renderer.render(feature, seed)
    
    @classmethod
    def has_renderer(cls, feature_type: str) -> bool:
        """Check if a feature type has a registered renderer."""
        return feature_type in cls._renderers
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of all supported feature types."""
        return list(cls._renderers.keys())


# ==============================================================================
# Auto-register Core Renderers
# ==============================================================================

# Register the 6 core primitives
RendererRegistry.register("mountain", MountainRenderer())
RendererRegistry.register("valley", ValleyRenderer())
RendererRegistry.register("dunes", DunesRenderer())
RendererRegistry.register("cliff", CliffRenderer())
RendererRegistry.register("plateau", PlateauRenderer())
RendererRegistry.register("canyon", CanyonRenderer())

logger.info(f"Registered {len(RendererRegistry.get_supported_types())} core feature renderers")

