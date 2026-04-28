"""TerrainBuilder - Builder pattern for terrain construction."""
import numpy as np
from typing import Callable, Optional, Dict, Tuple
from .stamping import stamp_primitive, BlendingMode, apply_smoothing
from .stamping_optimized import apply_adaptive_smoothing_fast
from .splatmap_optimized import generate_splatmap_fast
from .erosion import apply_edge_erosion
from .config import get_config
from ..utils import normalize01


class TerrainBuilder:
    """
    Builder pattern for constructing terrain heightmaps.
    
    Eliminates double rebuild by building terrain in a single pass.
    """
    
    def __init__(self, base_biome_fn: Callable[[int], np.ndarray], seed: int = -1):
        """
        Initialize terrain builder.
        
        Args:
            base_biome_fn: Function to generate base biome (signature: (seed: int) -> np.ndarray)
            seed: Random seed for terrain generation (-1 = auto-generate random seed)
        """
        import random
        
        # Auto-generate random seed if seed is -1
        if seed == -1:
            seed = random.randint(0, 2**31 - 1)
        
        self.config = get_config()
        self.base_biome_fn = base_biome_fn
        self.seed = seed
        
        # Build base terrain
        self.heightmap = base_biome_fn(seed)
        self.dune_mask = np.zeros_like(self.heightmap)
        self.cliff_mask = np.zeros_like(self.heightmap)
        
        # Track applied features for validation
        self.applied_features = []
        
        # Walkability constraint system (encapsulated)
        self._walkability_constraints = None
        
        # Cache for slope/gradient (reused between adaptive smoothing and splatmap)
        self._slope_cache = None
        self._gradient_cache = None
    
    def apply_feature(self, feature_stamp: np.ndarray, blending_mode: str,
                     dune_mask_slice: Optional[np.ndarray] = None,
                     mask_bounds: Optional[tuple] = None,
                     cliff_mask_slice: Optional[np.ndarray] = None,
                     cliff_bounds: Optional[tuple] = None,
                     feature_type: Optional[str] = None,
                     feature_params: Optional[Dict] = None):
        """
        Apply a feature stamp to the terrain.
        
        Args:
            feature_stamp: Heightmap stamp to apply
            blending_mode: How to blend the stamp (string constant from BlendingMode)
            dune_mask_slice: Optional dune mask for this feature
            mask_bounds: Optional (x0, y0, x1, x1) bounds for dune mask
            cliff_mask_slice: Optional cliff mask for this feature
            cliff_bounds: Optional (x0, y0, x1, y1) bounds for cliff mask
            feature_type: Optional feature type (for constraint tracking)
            feature_params: Optional feature parameters (for constraint tracking)
        """
        # Apply heightmap stamp
        stamp_primitive(self.heightmap, feature_stamp, blending_mode)
        
        # Track walkability zones in constraint system
        if feature_type in ["flat_zone", "path", "clearing"] and feature_params:
            self._track_walkability_zone(feature_type, feature_params)
        
        # Apply dune mask if provided
        if dune_mask_slice is not None and mask_bounds is not None:
            x0, y0, x1, y1 = mask_bounds
            self.dune_mask[y0:y1, x0:x1] = np.maximum(
                self.dune_mask[y0:y1, x0:x1],
                dune_mask_slice[y0:y1, x0:x1]
            )
        
        # Apply cliff mask if provided
        if cliff_mask_slice is not None and cliff_bounds is not None:
            x0, y0, x1, y1 = cliff_bounds
            self.cliff_mask[y0:y1, x0:x1] = np.maximum(
                self.cliff_mask[y0:y1, x0:x1],
                cliff_mask_slice[y0:y1, x0:x1]
            )
    
    def finalize(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Finalize terrain generation with post-processing.
        
        Returns:
            (heightmap, dune_mask, cliff_mask) tuple
        """
        # Post-processing: feature-aware adaptive smoothing (optimized version)
        # Preserves sharp features (cliffs) while smoothing flat areas
        # Optimized version uses separable filters and simplified edge detection
        from ..utils import sobel_slope
        slope_cache = sobel_slope(self.heightmap)  # Calculate once for reuse
        
        apply_adaptive_smoothing_fast(self.heightmap, 
                                     base_sigma=self.config.smoothing_sigma,
                                     preserve_edges=True,
                                     slope_cache=slope_cache)
        
        # Store slope_cache for splatmap generation (eliminates duplicate calculation)
        self._slope_cache = slope_cache
        
        # Apply subtle edge erosion for natural weathering
        apply_edge_erosion(self.heightmap, erosion_strength=0.12, erosion_radius=2)
        
        # Normalize heightmap with depth preservation for dramatic valleys
        # This allows terrain to have deep valleys below the "sea level"
        self.heightmap = normalize01(self.heightmap, allow_depth=True)
        
        return self.heightmap, self.dune_mask, self.cliff_mask
    
    def build_splatmap(self) -> np.ndarray:
        """
        Generate splatmap from finalized heightmap (optimized version).
        
        Reuses slope and gradient calculations from adaptive smoothing to eliminate
        duplicate computation.
        
        Returns:
            4-channel RGBA splatmap
        """
        # Reuse slope from adaptive smoothing if available
        slope_cache = getattr(self, '_slope_cache', None)
        
        # Calculate gradient for splatmap (needed for aspect calculation)
        # This is separate from slope calculation, so we calculate it here
        gy, gx = np.gradient(self.heightmap.astype(np.float32))
        gradient_cache = (gy, gx)
        
        return generate_splatmap_fast(
            self.heightmap, 
            self.dune_mask, 
            self.cliff_mask,
            slope_cache=slope_cache,
            gradient_cache=gradient_cache
        )
    
    def get_heightmap(self) -> np.ndarray:
        """Get current heightmap (before finalization)."""
        return self.heightmap.copy()
    
    def calculate_walkability(self, config=None):
        """
        Calculate walkability cost map and mask from finalized terrain.
        
        Args:
            config: Optional WalkabilityConfig (defaults to DEFAULT_CONFIG)
            
        Returns:
            Tuple of (cost_map, walkable_mask) where:
            - cost_map: 512x512 cost map (higher = harder to traverse)
            - walkable_mask: 512x512 boolean mask (True = walkable)
        """
        from .walkability import (
            calculate_walkability_cost,
            calculate_walkability_mask,
            DEFAULT_CONFIG
        )
        
        if config is None:
            config = DEFAULT_CONFIG
        
        # Finalize if not already done
        heightmap, dune_mask, cliff_mask = self.finalize()
        splatmap = self.build_splatmap()
        
        cost_map = calculate_walkability_cost(
            heightmap,
            splatmap=splatmap,
            cliff_mask=cliff_mask,
            dune_mask=dune_mask,
            config=config
        )
        
        walkable_mask = calculate_walkability_mask(
            heightmap,
            splatmap=splatmap,
            cliff_mask=cliff_mask,
            config=config
        )
        
        return cost_map, walkable_mask
    
    def _get_walkability_constraints(self):
        """Get walkability constraint system (lazy initialization)."""
        if self._walkability_constraints is None:
            from .walkability_constraints import WalkabilityConstraint
            self._walkability_constraints = WalkabilityConstraint()
        return self._walkability_constraints
    
    def _track_walkability_zone(self, zone_type: str, params: Dict):
        """Track walkability zone in constraint system (internal)."""
        constraints = self._get_walkability_constraints()
        # Determine priority based on zone type
        priority = "high" if zone_type == "path" else ("medium" if zone_type == "clearing" else "high")
        constraints.add_zone(zone_type, params, priority)
    
    def can_place_feature(self, feature_type: str, position: Tuple[int, int], 
                         radius: int) -> Tuple[bool, Optional[str]]:
        """
        Check if a feature can be placed at position (public API for constraint checking).
        
        Args:
            feature_type: Type of feature (e.g., "mountain", "hill")
            position: (x, y) position
            radius: Feature radius
            
        Returns:
            (can_place, reason) tuple
        """
        constraints = self._get_walkability_constraints()
        if not constraints.has_zones():
            return True, None
        return constraints.can_place_feature(feature_type, position, radius)
    
    def find_placement_away_from_zones(self, feature_type: str,
                                      preferred_pos: Tuple[int, int],
                                      radius: int,
                                      search_radius: int = 100) -> Tuple[int, int]:
        """
        Find a valid placement position away from walkability zones (public API).
        
        Args:
            feature_type: Type of feature
            preferred_pos: Preferred (x, y) position
            radius: Feature radius
            search_radius: Maximum distance to search
            
        Returns:
            (x, y) position that doesn't violate constraints
        """
        constraints = self._get_walkability_constraints()
        if not constraints.has_zones():
            return preferred_pos
        return constraints.find_placement_away_from_zones(
            feature_type, preferred_pos, radius, search_radius
        )

