"""TerrainBuilder - Builder pattern for terrain construction."""
import numpy as np
from typing import Callable, Optional, Dict
from .stamping import stamp_primitive, BlendingMode, apply_smoothing, apply_adaptive_smoothing
from .splatmap import generate_splatmap
from .erosion import apply_edge_erosion
from .config import get_config
from ..utils import normalize01


class TerrainBuilder:
    """
    Builder pattern for constructing terrain heightmaps.
    
    Eliminates double rebuild by building terrain in a single pass.
    """
    
    def __init__(self, base_biome_fn: Callable[[int], np.ndarray], seed: int = 0):
        """
        Initialize terrain builder.
        
        Args:
            base_biome_fn: Function to generate base biome (signature: (seed: int) -> np.ndarray)
            seed: Random seed for terrain generation
        """
        self.config = get_config()
        self.base_biome_fn = base_biome_fn
        self.seed = seed
        
        # Build base terrain
        self.heightmap = base_biome_fn(seed)
        self.dune_mask = np.zeros_like(self.heightmap)
        self.cliff_mask = np.zeros_like(self.heightmap)
        
        # Track applied features for validation
        self.applied_features = []
    
    def apply_feature(self, feature_stamp: np.ndarray, blending_mode: str,
                     dune_mask_slice: Optional[np.ndarray] = None,
                     mask_bounds: Optional[tuple] = None,
                     cliff_mask_slice: Optional[np.ndarray] = None,
                     cliff_bounds: Optional[tuple] = None):
        """
        Apply a feature stamp to the terrain.
        
        Args:
            feature_stamp: Heightmap stamp to apply
            blending_mode: How to blend the stamp (string constant from BlendingMode)
            dune_mask_slice: Optional dune mask for this feature
            mask_bounds: Optional (x0, y0, x1, y1) bounds for dune mask
            cliff_mask_slice: Optional cliff mask for this feature
            cliff_bounds: Optional (x0, y0, x1, y1) bounds for cliff mask
        """
        # Apply heightmap stamp
        stamp_primitive(self.heightmap, feature_stamp, blending_mode)
        
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
        # Post-processing: feature-aware adaptive smoothing
        # Preserves sharp features (cliffs) while smoothing flat areas
        apply_adaptive_smoothing(self.heightmap, 
                                base_sigma=self.config.smoothing_sigma,
                                preserve_edges=True)
        
        # Apply subtle edge erosion for natural weathering
        apply_edge_erosion(self.heightmap, erosion_strength=0.12, erosion_radius=2)
        
        # Normalize heightmap with depth preservation for dramatic valleys
        # This allows terrain to have deep valleys below the "sea level"
        self.heightmap = normalize01(self.heightmap, allow_depth=True)
        
        return self.heightmap, self.dune_mask, self.cliff_mask
    
    def build_splatmap(self) -> np.ndarray:
        """
        Generate splatmap from finalized heightmap.
        
        Returns:
            4-channel RGBA splatmap
        """
        return generate_splatmap(self.heightmap, self.dune_mask, self.cliff_mask)
    
    def get_heightmap(self) -> np.ndarray:
        """Get current heightmap (before finalization)."""
        return self.heightmap.copy()

