"""Feature Registry - Composable primitive system.

CORE PRIMITIVES (6 Essential):
1. Mountain - Hero elevation (rock + snow)
2. Valley - Hero depression (grass + balance)
3. Dunes - Sand texture (ONLY source via dune_mask)
4. Cliff - Vertical drama (rock via cliff_mask)
5. Plateau - Flat zones (gameplay + unique geometry)
6. Canyon - Linear exploration (optional but useful)

REFACTORING NOTES (November 2025):
- Migrating to typed Feature system (domain/models.py)
- Bridge pattern: Support BOTH dict and Feature during migration
- Preserve all existing intelligence (variation, modification, special effects)
- Commented out redundant primitives (Hill=Mountain config, Mound=tiny Mountain, etc.)
- Focus on geological storytelling through intelligent primitive use
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union
import numpy as np
from ..engine.stamping import BlendingMode

# Type-aware imports (bridge pattern)
try:
    from ..domain.models import Feature
    FEATURE_TYPE_AVAILABLE = True
except ImportError:
    FEATURE_TYPE_AVAILABLE = False
    Feature = None  # type: ignore

# Bridge type: Accept both dict and Feature during migration
if FEATURE_TYPE_AVAILABLE:
    FeatureInput = Union[Feature, Dict]
else:
    FeatureInput = Dict


class FeatureGenerator(ABC):
    """
    Base class for feature generators.
    
    MIGRATION NOTE: Now supports both dict and typed Feature during transition.
    Subclasses can override generate_stamp() to work directly with Feature,
    or use the bridge helpers (_to_dict, _to_feature) for gradual migration.
    """
    
    # Helper methods for bridge pattern
    def _to_dict(self, feature: FeatureInput) -> Dict:
        """Convert Feature → dict if needed (bridge helper)."""
        if FEATURE_TYPE_AVAILABLE and isinstance(feature, Feature):
            return feature.to_dict()
        return feature
    
    def _to_feature(self, feature_dict: Dict) -> 'Feature':
        """Convert dict → Feature if needed (bridge helper)."""
        if not FEATURE_TYPE_AVAILABLE:
            raise RuntimeError("Feature type not available - cannot convert")
        return Feature.from_dict(feature_dict)
    
    @abstractmethod
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        """
        Generate heightmap stamp for this feature.
        
        MIGRATION NOTE: Now accepts BOTH dict and typed Feature.
        Use self._to_dict(feature) to convert to dict if needed.
        
        Args:
            feature: Feature instance OR dict (legacy support during migration)
            seed: Random seed
            
        Returns:
            512x512 heightmap stamp
        """
        pass
    
    @abstractmethod
    def get_blending_mode(self) -> BlendingMode:
        """Get blending mode for this feature."""
        pass
    
    @abstractmethod
    def get_defaults(self) -> Dict:
        """
        Get default parameters for this feature.
        
        Returns:
            Dictionary of default parameter values
        """
        pass
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int):
        """
        Create feature with modifiers and variation.
        
        MIGRATION NOTE: Returns typed Feature (not dict anymore).
        Subclasses now implement _create_feature_dict() instead.
        
        Args:
            cx, cy: Center coordinates
            modifiers: User modifiers (e.g., "taller", "wider")
            seed: Random seed for variation
            
        Returns:
            Typed Feature instance (new) or dict (legacy during migration)
        """
        # Try subclass-specific logic first
        feat_dict = self._create_feature_dict(cx, cy, modifiers, seed)
        
        if feat_dict is None:
            # No custom logic - return None (terrain.py will handle it)
            return None
        
        # Ensure dict has required 'id' field for Feature.from_dict
        if "id" not in feat_dict:
            feat_dict["id"] = 0  # Temporary ID, will be assigned by state manager
        
        # Convert dict → typed Feature
        if FEATURE_TYPE_AVAILABLE:
            return self._to_feature(feat_dict)
        else:
            # Fallback if Feature type not available
            return feat_dict
    
    def _create_feature_dict(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Optional[Dict]:
        """
        Internal helper: Create feature dict with variation logic.
        
        Subclasses override this to preserve existing variation intelligence.
        Base implementation returns None (no custom logic).
        
        Returns:
            Feature dict or None (if no custom logic)
        """
        return None
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """
        Modify an existing feature's parameters.
        
        Default implementation: subclasses can override for custom logic.
        
        Args:
            feat: Existing feature dictionary (modified in-place)
            modifiers: User modifiers (e.g., "taller", "wider")
        """
        # Default: no-op
        # Subclasses override to provide custom modification logic
        pass
    
    def apply_special_effects(self, builder, feat: Dict, stamp: np.ndarray, seed: int):
        """
        Apply special effects (masks, etc.) if needed.
        
        Override in subclasses for features that need special handling
        (e.g., dunes mask, cliff mask).
        
        Args:
            builder: TerrainBuilder instance
            feat: Feature dictionary
            stamp: Generated stamp
            seed: Random seed
        """
        pass  # Default: no special effects


# ============================================================================
# Point Feature Generators (center coordinates)
# ============================================================================

class MountainGenerator(FeatureGenerator):
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        # Bridge: Convert to dict if needed (preserves existing logic)
        feat = self._to_dict(feature)
        
        from ..primitives.mountains import generate_mountain
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 56)
        height = feat.get("height", 0.75)
        use_noise = feat.get("use_noise", True)
        return generate_mountain(cx, cy, radius, height, use_noise=use_noise, seed=seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"radius": 56, "height": 0.75, "use_noise": True}
    
    def _create_feature_dict(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create mountain dict with variation (called by base create_feature)."""
        from ..engine.variation import VARIATION_CONFIG
        from ..terrain import _apply_param_modifier_or_variation
        
        cfg = VARIATION_CONFIG["mountain"]
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        height = _apply_param_modifier_or_variation(
            0.75, modifiers, "height", "taller", cfg, variation_seed
        )
        radius = _apply_param_modifier_or_variation(
            56, modifiers, "radius", "wider", cfg, variation_seed + 1, is_int=True
        )
        
        return {"type": "mountain", "x": cx, "y": cy, "radius": radius, "height": height, 
                "use_noise": True}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify mountain parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
        apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


# ============================================================================
# COMMENTED OUT: Redundant with Mountain
# ============================================================================
# Hills are just Mountain(steepness=0.7). Use Mountain with lower height instead.
# Keeping code for reference but not registering as core primitive.
#
# class HillGenerator(FeatureGenerator):
#     def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
#         from ..primitives.mountains import generate_mountain
#         cx, cy = feat["x"], feat["y"]
#         radius = feat.get("radius", 42)
#         height = feat.get("height", 0.45)
#         use_noise = feat.get("use_noise", True)
#         # Hills use gentler steepness
#         return generate_mountain(cx, cy, radius, height, steepness=0.7, use_noise=use_noise, seed=seed)
#     
#     def get_blending_mode(self) -> BlendingMode:
#         return BlendingMode.MAX
#     
#     def get_defaults(self) -> Dict:
#         return {"radius": 42, "height": 0.45, "use_noise": True}
#     
#     def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
#         """Create hill with modifiers and variation."""
#         from ..engine.variation import VARIATION_CONFIG
#         from ..terrain import _apply_param_modifier_or_variation
#         
#         cfg = VARIATION_CONFIG["hill"]
#         variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
#         
#         height = _apply_param_modifier_or_variation(
#             0.45, modifiers, "height", "taller", cfg, variation_seed
#         )
#         radius = _apply_param_modifier_or_variation(
#             42, modifiers, "radius", "wider", cfg, variation_seed + 1, is_int=True
#         )
#         
#         return {"type": "hill", "x": cx, "y": cy, "radius": radius, "height": height,
#                 "use_noise": True}
#     
#     def modify_feature(self, feat: Dict, modifiers: Dict):
#         """Modify hill parameters."""
#         from ..engine.modification import apply_modifier_to_param
#         apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
#         apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


class MesaGenerator(FeatureGenerator):
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.mountains import generate_mesa
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 56)
        height = feat.get("height", 0.65)
        flatness = feat.get("flatness", 0.3)
        return generate_mesa(cx, cy, radius, height, flatness)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"radius": 56, "height": 0.65, "flatness": 0.3}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create mesa with variation (no modifier support)."""
        from ..engine.variation import VariationEngine, VARIATION_CONFIG
        cfg = VARIATION_CONFIG.get("mesa", VARIATION_CONFIG["mountain"])
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        height = VariationEngine.apply_variation(0.65, 0.08, variation_seed, 0.50, 1.2)
        radius = VariationEngine.apply_variation_int(56, 0.12, variation_seed + 1, 40, 85)
        
        return {"type": "mesa", "x": cx, "y": cy, "radius": radius, "height": height, "flatness": 0.3}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify mesa parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
        apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


class PlateauGenerator(FeatureGenerator):
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        # Bridge: Convert to dict if needed (preserves existing logic)
        feat = self._to_dict(feature)
        
        from ..primitives.mountains import generate_plateau
        cx, cy = feat["x"], feat["y"]
        width = feat.get("width", 80)
        length = feat.get("length", 120)
        height = feat.get("height", 0.50)
        orientation = feat.get("orientation", 0.0)
        return generate_plateau(cx, cy, width, length, height, orientation)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"width": 80, "length": 120, "height": 0.50, "orientation": 0.0}
    
    def _create_feature_dict(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create plateau dict with variation (called by base create_feature)."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        height = VariationEngine.apply_variation(0.50, 0.10, variation_seed, 0.35, 0.70)
        width = VariationEngine.apply_variation_int(80, 0.15, variation_seed + 1, 60, 120)
        length = VariationEngine.apply_variation_int(120, 0.15, variation_seed + 2, 80, 160)
        
        return {"type": "plateau", "x": cx, "y": cy, "width": width, "length": length,
                "height": height, "orientation": 0.0}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify plateau parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
        apply_modifier_to_param(feat, "width", modifiers, max_value=128, is_int=True)
        apply_modifier_to_param(feat, "length", modifiers, max_value=200, is_int=True)


class ValleyGenerator(FeatureGenerator):
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        # Bridge: Convert to dict if needed (preserves existing logic)
        feat = self._to_dict(feature)
        
        from ..primitives.valleys import generate_valley
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 64)
        depth = feat.get("depth", 0.55)
        return generate_valley(cx, cy, radius, depth)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.SUBTRACT
    
    def get_defaults(self) -> Dict:
        return {"radius": 64, "depth": 0.55}
    
    def _create_feature_dict(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create valley dict with variation (called by base create_feature)."""
        from ..engine.variation import VARIATION_CONFIG
        from ..terrain import _apply_param_modifier_or_variation
        
        cfg = VARIATION_CONFIG["valley"]
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        depth = _apply_param_modifier_or_variation(
            0.55, modifiers, "depth", "deeper", cfg, variation_seed
        )
        radius = _apply_param_modifier_or_variation(
            64, modifiers, "radius", "wider", cfg, variation_seed + 1, is_int=True
        )
        
        return {"type": "valley", "x": cx, "y": cy, "radius": radius, "depth": depth}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify valley parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "depth", modifiers, max_value=1.0, modifier_keyword="deeper")
        apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


class CliffGenerator(FeatureGenerator):
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        # Bridge: Convert to dict if needed (preserves existing logic)
        feat = self._to_dict(feature)
        
        from ..primitives.cliffs import generate_cliff
        cx, cy = feat["x"], feat["y"]
        length = feat.get("length", 80)
        height = feat.get("height", 0.55)
        orientation = feat.get("orientation", 0.0)
        steepness = feat.get("steepness", 0.9)
        return generate_cliff(cx, cy, length, height, orientation, steepness)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"length": 80, "height": 0.55, "orientation": 0.0, "steepness": 0.9}
    
    def _create_feature_dict(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create cliff dict with variation (called by base create_feature)."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        length = VariationEngine.apply_variation_int(80, 0.15, variation_seed, 50, 120)
        height = VariationEngine.apply_variation(0.55, 0.10, variation_seed + 1, 0.40, 0.75)
        
        return {"type": "cliff", "x": cx, "y": cy, "length": length, "height": height,
                "orientation": 0.0, "steepness": 0.9}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify cliff parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
    
    def apply_special_effects(self, builder, feat: Dict, stamp: np.ndarray, seed: int):
        """Apply cliff mask for rock texture."""
        from ..primitives.cliffs import generate_cliff_mask
        RES = 512
        cx, cy = feat["x"], feat["y"]
        length = feat.get("length", 80)
        orientation = feat.get("orientation", 0.0)
        
        cliff_mask = generate_cliff_mask(cx, cy, length, orientation)
        x0 = max(0, cx - length // 2)
        y0 = max(0, cy - length // 2)
        x1 = min(RES, cx + length // 2)
        y1 = min(RES, cy + length // 2)
        
        builder.apply_feature(
            np.zeros_like(stamp),  # Empty stamp, just updating mask
            BlendingMode.MAX,
            cliff_mask_slice=cliff_mask,
            cliff_bounds=(x0, y0, x1, y1)
        )


class CraterGenerator(FeatureGenerator):
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.crater import generate_crater
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 64)
        depth = feat.get("depth", 0.55)
        rim_height = feat.get("rim_height", 0.1)
        steepness = feat.get("steepness", 1.0)
        return generate_crater(cx, cy, radius, depth, rim_height, steepness)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.ADD  # Has both positive (rim) and negative (center)
    
    def get_defaults(self) -> Dict:
        return {"radius": 64, "depth": 0.55, "rim_height": 0.1, "steepness": 1.0}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create crater with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        depth = VariationEngine.apply_variation(0.55, 0.10, variation_seed, 0.40, 0.70)
        radius = VariationEngine.apply_variation_int(64, 0.15, variation_seed + 1, 45, 90)
        rim_height = VariationEngine.apply_variation(0.1, 0.20, variation_seed + 2, 0.05, 0.15)
        
        return {"type": "crater", "x": cx, "y": cy, "radius": radius, "depth": depth,
                "rim_height": rim_height, "steepness": 1.0}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify crater parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "depth", modifiers, max_value=1.0, modifier_keyword="deeper")
        apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


class VolcanoGenerator(FeatureGenerator):
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.volcano import generate_volcano
        cx, cy = feat["x"], feat["y"]
        base_radius = feat.get("base_radius", 56)
        height = feat.get("height", 0.80)
        crater_radius = feat.get("crater_radius", 0.15)
        crater_depth = feat.get("crater_depth", 0.2)
        steepness = feat.get("steepness", 1.2)
        use_noise = feat.get("use_noise", True)
        return generate_volcano(cx, cy, base_radius, height, crater_radius, crater_depth, steepness, use_noise, seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"base_radius": 56, "height": 0.80, "crater_radius": 0.15, "crater_depth": 0.2, 
                "steepness": 1.2, "use_noise": True}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create volcano with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        height = VariationEngine.apply_variation(0.80, 0.10, variation_seed, 0.65, 0.95)
        base_radius = VariationEngine.apply_variation_int(56, 0.15, variation_seed + 1, 40, 75)
        
        # Random crater variation
        rng = np.random.RandomState(variation_seed + 2)
        has_crater = rng.rand() > 0.3
        crater_radius = rng.uniform(0.10, 0.25) if has_crater else 0.0
        crater_depth = rng.uniform(0.1, 0.3) if has_crater else 0.0
        
        return {"type": "volcano", "x": cx, "y": cy, "base_radius": base_radius, "height": height,
                "crater_radius": crater_radius, "crater_depth": crater_depth, "steepness": 1.2}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify volcano parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
        apply_modifier_to_param(feat, "base_radius", modifiers, max_value=128, is_int=True)


# ============================================================================
# COMMENTED OUT: Redundant with Mountain and Valley
# ============================================================================
# Mound is just Mountain(height=0.20, radius=25) - literally same gaussian code!
# Basin is just Valley(large, with flat_bottom option).
# Use Mountain/Valley with appropriate parameters instead.
#
# class MoundGenerator(FeatureGenerator):
#     def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
#         from ..primitives.mound import generate_mound
#         cx, cy = feat["x"], feat["y"]
#         radius = feat.get("radius", 25)
#         height = feat.get("height", 0.20)
#         use_noise = feat.get("use_noise", True)
#         return generate_mound(cx, cy, radius, height, use_noise, seed)
#     
#     def get_blending_mode(self) -> BlendingMode:
#         return BlendingMode.MAX
#     
#     def get_defaults(self) -> Dict:
#         return {"radius": 25, "height": 0.20, "use_noise": True}
#     
#     def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
#         """Create mound with variation."""
#         from ..engine.variation import VariationEngine
#         variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
#         
#         height = VariationEngine.apply_variation(0.20, 0.15, variation_seed, 0.12, 0.28)
#         radius = VariationEngine.apply_variation_int(25, 0.20, variation_seed + 1, 18, 35)
#         
#         return {"type": "mound", "x": cx, "y": cy, "radius": radius, "height": height}
#     
#     def modify_feature(self, feat: Dict, modifiers: Dict):
#         """Modify mound parameters."""
#         from ..engine.modification import apply_modifier_to_param
#         apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
#         apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


# class BasinGenerator(FeatureGenerator):
#     def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
#         from ..primitives.basin import generate_basin
#         cx, cy = feat["x"], feat["y"]
#         radius = feat.get("radius", 120)
#         depth = feat.get("depth", 0.50)
#         flatness = feat.get("flatness", 0.5)
#         return generate_basin(cx, cy, radius, depth, flatness)
#     
#     def get_blending_mode(self) -> BlendingMode:
#         return BlendingMode.SUBTRACT
#     
#     def get_defaults(self) -> Dict:
#         return {"radius": 120, "depth": 0.50, "flatness": 0.5}
#     
#     def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
#         """Create basin with variation."""
#         from ..engine.variation import VariationEngine
#         variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
#         
#         depth = VariationEngine.apply_variation(0.50, 0.10, variation_seed, 0.35, 0.65)
#         radius = VariationEngine.apply_variation_int(120, 0.15, variation_seed + 1, 90, 150)
#         flatness = VariationEngine.apply_variation(0.5, 0.20, variation_seed + 2, 0.3, 0.7)
#         
#         return {"type": "basin", "x": cx, "y": cy, "radius": radius, "depth": depth, "flatness": flatness}
#     
#     def modify_feature(self, feat: Dict, modifiers: Dict):
#         """Modify basin parameters."""
#         from ..engine.modification import apply_modifier_to_param
#         apply_modifier_to_param(feat, "depth", modifiers, max_value=1.0, modifier_keyword="deeper")
#         apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


# ============================================================================
# COMMENTED OUT: Redundant with Mountain
# ============================================================================
# Pinnacle is just Mountain(radius=20, height=0.90, steepness=2.0) - extreme params.
# Use Mountain with small radius and high steepness instead.
#
# class PinnacleGenerator(FeatureGenerator):
#     def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
#         from ..primitives.pinnacle import generate_pinnacle
#         cx, cy = feat["x"], feat["y"]
#         radius = feat.get("radius", 20)
#         height = feat.get("height", 0.90)
#         steepness = feat.get("steepness", 2.0)
#         use_noise = feat.get("use_noise", True)
#         return generate_pinnacle(cx, cy, radius, height, steepness, use_noise, seed)
#     
#     def get_blending_mode(self) -> BlendingMode:
#         return BlendingMode.MAX
#     
#     def get_defaults(self) -> Dict:
#         return {"radius": 20, "height": 0.90, "steepness": 2.0, "use_noise": True}
#     
#     def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
#         """Create pinnacle with variation."""
#         from ..engine.variation import VariationEngine
#         variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
#         
#         height = VariationEngine.apply_variation(0.90, 0.08, variation_seed, 0.75, 1.0)
#         radius = VariationEngine.apply_variation_int(20, 0.20, variation_seed + 1, 15, 28)
#         
#         return {"type": "pinnacle", "x": cx, "y": cy, "radius": radius, "height": height, "steepness": 2.0}
#     
#     def modify_feature(self, feat: Dict, modifiers: Dict):
#         """Modify pinnacle parameters."""
#         from ..engine.modification import apply_modifier_to_param
#         apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
#         apply_modifier_to_param(feat, "radius", modifiers, max_value=128, is_int=True)


# ============================================================================
# Linear Feature Generators (start/end coordinates)
# ============================================================================

class CanyonGenerator(FeatureGenerator):
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        # Bridge: Convert to dict if needed (preserves existing logic)
        feat = self._to_dict(feature)
        
        from ..primitives.valleys import generate_canyon
        start = (feat["x0"], feat["y0"])
        end = (feat["x1"], feat["y1"])
        width = feat.get("width", 12)
        depth = feat.get("depth", 0.60)
        falloff = feat.get("falloff", 0.5)
        return generate_canyon(start, end, width, depth, falloff)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.SUBTRACT
    
    def get_defaults(self) -> Dict:
        return {"width": 12, "depth": 0.60, "falloff": 0.5}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create canyon with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        length = VariationEngine.apply_variation_int(100, 0.20, variation_seed, 60, 150)
        width = VariationEngine.apply_variation_int(12, 0.15, variation_seed + 1, 8, 18)
        
        # Generate linear coordinates
        from ..terrain import _generate_linear_feature_coords
        start, end = _generate_linear_feature_coords(cx, cy, length, variation_seed + 2)
        
        return {"type": "canyon", "x0": start[0], "y0": start[1], "x1": end[0], "y1": end[1],
                "width": width, "depth": 0.60, "falloff": 0.5}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify canyon parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "depth", modifiers, max_value=1.0, modifier_keyword="deeper")
        apply_modifier_to_param(feat, "width", modifiers, max_value=128, is_int=True)


# ============================================================================
# COMMENTED OUT: Ridge is ugly, Ravine is redundant with Canyon
# ============================================================================
# Ridge: Too smooth (slope ~0.15-0.25) → Creates GRASS not rock. No cliff_mask.
#        Use Cliff instead for dramatic vertical features with rock texture.
# Ravine: Just Canyon(width=7, steepness=1.2) - narrow canyon config.
#         Use Canyon with small width instead.
#
# class RidgeGenerator(FeatureGenerator):
#     def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
#         from ..primitives.ridge import generate_ridge
#         start = (feat["x0"], feat["y0"])
#         end = (feat["x1"], feat["y1"])
#         width = feat.get("width", 20)
#         height = feat.get("height", 0.50)
#         steepness = feat.get("steepness", 0.8)
#         return generate_ridge(start, end, height, width, steepness)
#     
#     def get_blending_mode(self) -> BlendingMode:
#         return BlendingMode.MAX
#     
#     def get_defaults(self) -> Dict:
#         return {"width": 20, "height": 0.50, "steepness": 0.8}
#     
#     def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
#         """Create ridge with variation."""
#         from ..engine.variation import VariationEngine
#         variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
#         
#         length = VariationEngine.apply_variation_int(120, 0.20, variation_seed, 80, 180)
#         width = VariationEngine.apply_variation_int(20, 0.15, variation_seed + 1, 15, 30)
#         height = VariationEngine.apply_variation(0.50, 0.10, variation_seed + 2, 0.35, 0.65)
#         
#         from ..terrain import _generate_linear_feature_coords
#         start, end = _generate_linear_feature_coords(cx, cy, length, variation_seed + 3)
#         
#         return {"type": "ridge", "x0": start[0], "y0": start[1], "x1": end[0], "y1": end[1],
#                 "width": width, "height": height, "steepness": 0.8}
#     
#     def modify_feature(self, feat: Dict, modifiers: Dict):
#         """Modify ridge parameters."""
#         from ..engine.modification import apply_modifier_to_param
#         apply_modifier_to_param(feat, "height", modifiers, max_value=1.0)
#         apply_modifier_to_param(feat, "width", modifiers, max_value=128, is_int=True)


# class RavineGenerator(FeatureGenerator):
#     def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
#         from ..primitives.ravine import generate_ravine
#         start = (feat["x0"], feat["y0"])
#         end = (feat["x1"], feat["y1"])
#         width = feat.get("width", 7)
#         depth = feat.get("depth", 0.60)
#         steepness = feat.get("steepness", 1.2)
#         return generate_ravine(start, end, width, depth, steepness)
#     
#     def get_blending_mode(self) -> BlendingMode:
#         return BlendingMode.SUBTRACT
#     
#     def get_defaults(self) -> Dict:
#         return {"width": 7, "depth": 0.60, "steepness": 1.2}
#     
#     def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
#         """Create ravine with variation."""
#         from ..engine.variation import VariationEngine
#         variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
#         
#         length = VariationEngine.apply_variation_int(100, 0.20, variation_seed, 60, 150)
#         width = VariationEngine.apply_variation_int(7, 0.15, variation_seed + 1, 5, 10)
#         depth = VariationEngine.apply_variation(0.60, 0.10, variation_seed + 2, 0.45, 0.75)
#         
#         from ..terrain import _generate_linear_feature_coords
#         start, end = _generate_linear_feature_coords(cx, cy, length, variation_seed + 3)
#         
#         return {"type": "ravine", "x0": start[0], "y0": start[1], "x1": end[0], "y1": end[1],
#                 "width": width, "depth": depth, "steepness": 1.2}
#     
#     def modify_feature(self, feat: Dict, modifiers: Dict):
#         """Modify ravine parameters."""
#         from ..engine.modification import apply_modifier_to_param
#         apply_modifier_to_param(feat, "depth", modifiers, max_value=1.0, modifier_keyword="deeper")
#         apply_modifier_to_param(feat, "width", modifiers, max_value=128, is_int=True)


class PassGenerator(FeatureGenerator):
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.passes import generate_pass
        start = (feat["x0"], feat["y0"])
        end = (feat["x1"], feat["y1"])
        width = feat.get("width", 30)
        depth = feat.get("depth", 0.40)
        elevation = feat.get("elevation", 0.3)
        return generate_pass(start, end, width, depth, elevation)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.SUBTRACT
    
    def get_defaults(self) -> Dict:
        return {"width": 30, "depth": 0.40, "elevation": 0.3}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create pass with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        length = VariationEngine.apply_variation_int(100, 0.20, variation_seed, 60, 150)
        width = VariationEngine.apply_variation_int(30, 0.15, variation_seed + 1, 20, 45)
        depth = VariationEngine.apply_variation(0.40, 0.10, variation_seed + 2, 0.25, 0.55)
        
        from ..terrain import _generate_linear_feature_coords
        start, end = _generate_linear_feature_coords(cx, cy, length, variation_seed + 3)
        
        return {"type": "pass", "x0": start[0], "y0": start[1], "x1": end[0], "y1": end[1],
                "width": width, "depth": depth, "elevation": 0.3}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify pass parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "depth", modifiers, max_value=1.0, modifier_keyword="deeper")
        apply_modifier_to_param(feat, "width", modifiers, max_value=128, is_int=True)


class SpurGenerator(FeatureGenerator):
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.spur import generate_spur
        start = (feat["x0"], feat["y0"])
        end = (feat["x1"], feat["y1"])
        width = feat.get("width", 15)
        base_height = feat.get("base_height", 0.60)
        end_height = feat.get("end_height", 0.0)
        steepness = feat.get("steepness", 0.7)
        return generate_spur(start, end, width, base_height, end_height, steepness)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"width": 15, "base_height": 0.60, "end_height": 0.0, "steepness": 0.7}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create spur with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        length = VariationEngine.apply_variation_int(80, 0.20, variation_seed, 50, 120)
        width = VariationEngine.apply_variation_int(15, 0.15, variation_seed + 1, 10, 22)
        base_height = VariationEngine.apply_variation(0.60, 0.10, variation_seed + 2, 0.45, 0.75)
        
        from ..terrain import _generate_linear_feature_coords
        start, end = _generate_linear_feature_coords(cx, cy, length, variation_seed + 3)
        
        return {"type": "spur", "x0": start[0], "y0": start[1], "x1": end[0], "y1": end[1],
                "width": width, "base_height": base_height, "end_height": 0.0, "steepness": 0.7}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify spur parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "base_height", modifiers, max_value=1.0)
        apply_modifier_to_param(feat, "width", modifiers, max_value=128, is_int=True)


# ============================================================================
# Area Feature Generators (bounding boxes)
# ============================================================================

class DunesGenerator(FeatureGenerator):
    def generate_stamp(self, feature: FeatureInput, seed: int) -> np.ndarray:
        # Bridge: Convert to dict if needed (preserves existing logic)
        feat = self._to_dict(feature)
        
        from ..primitives.dunes import generate_dunes
        box = (feat["x0"], feat["y0"], feat["x1"], feat["y1"])
        amp = feat.get("amp", 0.08)
        freq = feat.get("freq", 18.0)
        angle = feat.get("angle", 20.0)
        return generate_dunes(box, amp, freq, angle, seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.ADD
    
    def get_defaults(self) -> Dict:
        return {"amp": 0.08, "freq": 18.0, "angle": 20.0}
    
    def _create_feature_dict(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create dunes dict with variation (called by base create_feature)."""
        from ..engine.variation import VariationEngine, VARIATION_CONFIG
        cfg = VARIATION_CONFIG["dunes"]
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        amp = VariationEngine.apply_variation(0.08, cfg["amp_variation"], variation_seed)
        freq = VariationEngine.apply_variation(18.0, cfg["freq_variation"], variation_seed + 1)
        angle = VariationEngine.apply_variation(20.0, cfg["angle_variation"], variation_seed + 2)
        radius = VariationEngine.apply_variation_int(96, cfg["radius_variation"], variation_seed + 3,
                                                      cfg["radius_min"], cfg["radius_max"])
        
        from ..terrain import _generate_bounding_box
        x0, y0, x1, y1 = _generate_bounding_box(cx, cy, radius)
        
        # Include center position (x, y) for Feature.from_dict compatibility
        return {"type": "dunes", "x": cx, "y": cy, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "amp": amp, "freq": freq, "angle": angle}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify dunes parameters."""
        # Dunes use amp as height, freq as width (inverse)
        if modifiers.get("taller") or modifiers.get("height_percent"):
            from ..engine.modification import apply_modifier_to_param
            apply_modifier_to_param(feat, "amp", modifiers, max_value=0.2)
        if modifiers.get("wider") or modifiers.get("width_percent"):
            # For dunes, wider = lower frequency (inverse relationship)
            current_freq = feat.get("freq", 18.0)
            if modifiers.get("width_percent"):
                feat["freq"] = current_freq * (1.0 - modifiers["width_percent"] / 200.0)  # Half effect
            elif modifiers.get("wider"):
                feat["freq"] = current_freq * 0.85  # Reduce frequency
    
    def apply_special_effects(self, builder, feat: Dict, stamp: np.ndarray, seed: int):
        """
        Dunes don't use this - stamp and mask are applied together.
        This is a no-op for dunes.
        """
        pass  # Dunes handled specially in _apply_feature_to_builder


class TerracesGenerator(FeatureGenerator):
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.terraces import generate_terraces
        region = (feat["x0"], feat["y0"], feat["x1"], feat["y1"])
        levels = feat.get("levels", 5)
        height_per_level = feat.get("height_per_level", 0.10)
        width_per_level = feat.get("width_per_level", 20)
        direction = feat.get("direction", 0.0)
        return generate_terraces(region, levels, height_per_level, width_per_level, direction)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"levels": 5, "height_per_level": 0.10, "width_per_level": 20, "direction": 0.0}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create terraces with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        size = VariationEngine.apply_variation_int(150, 0.20, variation_seed, 100, 200)
        levels = VariationEngine.apply_variation_int(5, 0.25, variation_seed + 1, 3, 8)
        height_per_level = VariationEngine.apply_variation(0.10, 0.15, variation_seed + 2, 0.06, 0.15)
        width_per_level = VariationEngine.apply_variation_int(20, 0.20, variation_seed + 3, 15, 30)
        rng = np.random.RandomState(variation_seed + 4)
        direction = rng.uniform(0, 360)
        
        from ..terrain import _generate_bounding_box
        x0, y0, x1, y1 = _generate_bounding_box(cx, cy, size // 2)
        
        return {"type": "terraces", "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "levels": levels, "height_per_level": height_per_level,
                "width_per_level": width_per_level, "direction": direction}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify terraces parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height_per_level", modifiers, max_value=0.3)
        apply_modifier_to_param(feat, "width_per_level", modifiers, max_value=50, is_int=True)


# ============================================================================
# Special Feature Generators
# ============================================================================

class FlatZoneGenerator(FeatureGenerator):
    """Generator for flat zones (reserved walkable areas)."""
    
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.walkability_zones import generate_flat_zone
        cx = feat.get("x", feat.get("cx", RES // 2))
        cy = feat.get("y", feat.get("cy", RES // 2))
        radius = feat.get("radius", 80)
        flatness = feat.get("flatness", 0.0)
        feather = feat.get("feather", 10)
        return generate_flat_zone(cx, cy, radius, flatness, feather)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MIN  # Ensure flatness
    
    def get_defaults(self) -> Dict:
        return {"radius": 80, "flatness": 0.0, "feather": 10}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create flat zone with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        radius = VariationEngine.apply_variation_int(80, 0.15, variation_seed, 60, 120)
        return {"type": "flat_zone", "x": cx, "y": cy, "radius": radius, "flatness": 0.0}


class PathGenerator(FeatureGenerator):
    """Generator for paths (linear walkable routes)."""
    
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.walkability_zones import generate_path
        start = feat.get("start", (0, 0))
        end = feat.get("end", (RES, RES))
        width = feat.get("width", 30)
        flatness = feat.get("flatness", 0.0)
        feather = feat.get("feather", 8)
        return generate_path(start, end, width, flatness, feather)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MIN  # Ensure flatness
    
    def get_defaults(self) -> Dict:
        return {"width": 30, "flatness": 0.0, "feather": 8}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create path - requires start/end, not center."""
        # Paths need explicit start/end, not center-based
        # This is a fallback - should be called with explicit start/end
        return None


class ClearingGenerator(FeatureGenerator):
    """Generator for clearings (large open areas)."""
    
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.walkability_zones import generate_clearing
        cx = feat.get("x", feat.get("cx", RES // 2))
        cy = feat.get("y", feat.get("cy", RES // 2))
        radius = feat.get("radius", 120)
        flatness = feat.get("flatness", 0.0)
        feather = feat.get("feather", 15)
        return generate_clearing(cx, cy, radius, flatness, feather)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MIN  # Ensure flatness
    
    def get_defaults(self) -> Dict:
        return {"radius": 120, "flatness": 0.0, "feather": 15}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create clearing with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        radius = VariationEngine.apply_variation_int(120, 0.20, variation_seed, 90, 180)
        return {"type": "clearing", "x": cx, "y": cy, "radius": radius, "flatness": 0.0}


# ============================================================================
# Forest-Specific Feature Generators
# ============================================================================

class GroveGenerator(FeatureGenerator):
    """Generator for groves (clusters of trees on gentle hills)."""
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.forest import generate_grove
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 40)
        height = feat.get("height", 0.15)
        use_noise = feat.get("use_noise", True)
        return generate_grove(cx, cy, radius, height, use_noise, seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"radius": 40, "height": 0.15, "use_noise": True}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create grove with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        height = VariationEngine.apply_variation(0.15, 0.20, variation_seed, 0.10, 0.20)
        radius = VariationEngine.apply_variation_int(40, 0.25, variation_seed + 1, 30, 50)
        
        return {"type": "grove", "x": cx, "y": cy, "radius": radius, "height": height}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify grove parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=0.3)
        apply_modifier_to_param(feat, "radius", modifiers, max_value=80, is_int=True)


class ForestHillGenerator(FeatureGenerator):
    """Generator for forest hills (larger hills suitable for trees)."""
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.forest import generate_forest_hill
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 65)
        height = feat.get("height", 0.25)
        use_noise = feat.get("use_noise", True)
        return generate_forest_hill(cx, cy, radius, height, use_noise, seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MAX
    
    def get_defaults(self) -> Dict:
        return {"radius": 65, "height": 0.25, "use_noise": True}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create forest hill with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        height = VariationEngine.apply_variation(0.25, 0.20, variation_seed, 0.20, 0.35)
        radius = VariationEngine.apply_variation_int(65, 0.25, variation_seed + 1, 50, 80)
        
        return {"type": "forest_hill", "x": cx, "y": cy, "radius": radius, "height": height}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify forest hill parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "height", modifiers, max_value=0.45)
        apply_modifier_to_param(feat, "radius", modifiers, max_value=120, is_int=True)


class ForestClearingGenerator(FeatureGenerator):
    """Generator for forest clearings (gentle depressions for meadows)."""
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.forest import generate_forest_clearing
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 55)
        depth = feat.get("depth", 0.08)
        use_noise = feat.get("use_noise", True)
        return generate_forest_clearing(cx, cy, radius, depth, use_noise, seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MIN  # Create depressions
    
    def get_defaults(self) -> Dict:
        return {"radius": 55, "depth": 0.08, "use_noise": True}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create forest clearing with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        depth = VariationEngine.apply_variation(0.08, 0.20, variation_seed, 0.05, 0.15)
        radius = VariationEngine.apply_variation_int(55, 0.25, variation_seed + 1, 40, 70)
        
        return {"type": "forest_clearing", "x": cx, "y": cy, "radius": radius, "depth": depth}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify forest clearing parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "depth", modifiers, max_value=0.20)
        apply_modifier_to_param(feat, "radius", modifiers, max_value=100, is_int=True)


class ForestValleyGenerator(FeatureGenerator):
    """Generator for forest valleys (larger depressions, often with streams)."""
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        from ..primitives.forest import generate_forest_valley
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 80)
        depth = feat.get("depth", 0.20)
        use_noise = feat.get("use_noise", True)
        return generate_forest_valley(cx, cy, radius, depth, use_noise, seed)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.MIN  # Create depressions
    
    def get_defaults(self) -> Dict:
        return {"radius": 80, "depth": 0.20, "use_noise": True}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create forest valley with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        depth = VariationEngine.apply_variation(0.20, 0.20, variation_seed, 0.15, 0.30)
        radius = VariationEngine.apply_variation_int(80, 0.25, variation_seed + 1, 60, 100)
        
        return {"type": "forest_valley", "x": cx, "y": cy, "radius": radius, "depth": depth}
    
    def modify_feature(self, feat: Dict, modifiers: Dict):
        """Modify forest valley parameters."""
        from ..engine.modification import apply_modifier_to_param
        apply_modifier_to_param(feat, "depth", modifiers, max_value=0.40)
        apply_modifier_to_param(feat, "radius", modifiers, max_value=150, is_int=True)


class SlopeGenerator(FeatureGenerator):
    """Slope can be linear or radial."""
    
    def generate_stamp(self, feat: Dict, seed: int) -> np.ndarray:
        if "start" in feat and "end" in feat:
            # Linear slope
            from ..primitives.slopes import generate_slope
            start = tuple(feat["start"])
            end = tuple(feat["end"])
            width = feat.get("width", 40)
            height = feat.get("height", 0.35)
            falloff = feat.get("falloff", 0.3)
            return generate_slope(start, end, width, height, falloff)
        else:
            # Radial slope
            from ..primitives.slopes import generate_slope_radial
            cx, cy = feat["x"], feat["y"]
            radius = feat.get("radius", 60)
            height = feat.get("height", 0.35)
            direction = feat.get("direction", 0.0)
            steepness = feat.get("steepness", 0.5)
            return generate_slope_radial(cx, cy, radius, height, direction, steepness)
    
    def get_blending_mode(self) -> BlendingMode:
        return BlendingMode.ADD
    
    def get_defaults(self) -> Dict:
        # Default to radial slope
        return {"radius": 60, "height": 0.35, "direction": 0.0, "steepness": 0.5}
    
    def create_feature(self, cx: int, cy: int, modifiers: Dict, seed: int) -> Dict:
        """Create radial slope with variation."""
        from ..engine.variation import VariationEngine
        variation_seed = (hash(f"{cx}_{cy}_{seed}") % (2**31))
        
        radius = VariationEngine.apply_variation_int(60, 0.15, variation_seed, 40, 90)
        height = VariationEngine.apply_variation(0.35, 0.10, variation_seed + 1, 0.25, 0.50)
        rng = np.random.RandomState(variation_seed + 2)
        direction = rng.uniform(0, 360)
        
        return {"type": "slope", "x": cx, "y": cy, "radius": radius, "height": height,
                "direction": direction, "steepness": 0.5}


# ============================================================================
# Feature Registry
# ============================================================================

class FeatureRegistry:
    """
    Registry for all feature generators.
    
    Provides a composable, maintainable way to manage primitive features.
    Adding a new primitive requires only:
    1. Create a Generator class
    2. Register it with FeatureRegistry.register()
    """
    
    _generators: Dict[str, FeatureGenerator] = {}
    
    @classmethod
    def register(cls, feature_type: str, generator: FeatureGenerator):
        """Register a feature generator."""
        cls._generators[feature_type] = generator
    
    @classmethod
    def has_generator(cls, feature_type: str) -> bool:
        """Check if a generator exists for this feature type."""
        return feature_type in cls._generators
    
    @classmethod
    def generate_stamp(cls, feature_or_type, feat_or_seed=None, seed_or_none=None) -> np.ndarray:
        """
        Generate heightmap stamp for a feature.
        
        MIGRATION NOTE: Supports both old and new calling conventions:
        - Old: generate_stamp("mountain", {"x": 256, "y": 256, ...}, 42)
        - New: generate_stamp(Feature(...), 42)
        
        Args:
            feature_or_type: Either Feature instance (new) or feature_type string (old)
            feat_or_seed: Either seed (new) or feature dict (old)
            seed_or_none: Either seed (old) or None (new)
            
        Returns:
            512x512 heightmap stamp
            
        Raises:
            ValueError: If feature type is not registered
        """
        # Determine calling convention
        if FEATURE_TYPE_AVAILABLE and isinstance(feature_or_type, Feature):
            # New convention: generate_stamp(Feature(...), seed)
            feature = feature_or_type
            seed = feat_or_seed
            feature_type = feature.type
        else:
            # Old convention: generate_stamp("mountain", {...}, seed)
            feature_type = feature_or_type
            feature = feat_or_seed
            seed = seed_or_none
        
        generator = cls._generators.get(feature_type)
        if not generator:
            raise ValueError(f"Unknown feature type: '{feature_type}'. "
                           f"Registered types: {list(cls._generators.keys())}")
        return generator.generate_stamp(feature, seed)
    
    @classmethod
    def get_blending_mode(cls, feature_type: str) -> BlendingMode:
        """Get blending mode for a feature type."""
        generator = cls._generators.get(feature_type)
        if not generator:
            raise ValueError(f"Unknown feature type: '{feature_type}'")
        return generator.get_blending_mode()
    
    @classmethod
    def get_defaults(cls, feature_type: str) -> Dict:
        """Get default parameters for a feature type."""
        generator = cls._generators.get(feature_type)
        if not generator:
            raise ValueError(f"Unknown feature type: '{feature_type}'")
        return generator.get_defaults()
    
    @classmethod
    def apply_special_effects(cls, feature_type: str, builder, feat: Dict, stamp: np.ndarray, seed: int):
        """Apply special effects (masks, etc.) if needed."""
        generator = cls._generators.get(feature_type)
        if not generator:
            raise ValueError(f"Unknown feature type: '{feature_type}'")
        generator.apply_special_effects(builder, feat, stamp, seed)
    
    @classmethod
    def get_registered_types(cls) -> list:
        """Get list of all registered feature types."""
        return list(cls._generators.keys())
    
    @classmethod
    def create_feature(cls, feature_type: str, cx: int, cy: int, modifiers: Dict, seed: int) -> Optional[Dict]:
        """
        Create a feature dictionary using the generator's create_feature() method.
        
        Returns None if the generator doesn't implement create_feature() yet,
        indicating the caller should use the fallback implementation.
        
        Args:
            feature_type: Type of feature (e.g., "mountain", "ridge")
            cx, cy: Center coordinates
            modifiers: User modifiers (e.g., {"taller": True})
            seed: Random seed for variation
            
        Returns:
            Feature dictionary, or None if not implemented in generator
        """
        generator = cls._generators.get(feature_type)
        if not generator:
            raise ValueError(f"Unknown feature type: '{feature_type}'. "
                           f"Registered types: {list(cls._generators.keys())}")
        
        # Try to create using generator
        feat = generator.create_feature(cx, cy, modifiers, seed)
        return feat  # Returns None if not implemented, which is OK
    
    @classmethod
    def modify_feature(cls, feature_type: str, feat: Dict, modifiers: Dict):
        """
        Modify an existing feature using the generator's modify_feature() method.
        
        Args:
            feature_type: Type of feature (e.g., "mountain", "ridge")
            feat: Existing feature dictionary (modified in-place)
            modifiers: User modifiers (e.g., {"taller": True, "height_percent": 20})
        """
        generator = cls._generators.get(feature_type)
        if not generator:
            logger.warning(f"Unknown feature type for modification: '{feature_type}'")
            return
        
        # Call generator's modify method
        generator.modify_feature(feat, modifiers)


# ============================================================================
# Auto-register all generators
# ============================================================================

def _register_all_generators():
    """
    Register feature generators.
    
    CORE 6 PRIMITIVES (Focus for geological narratives):
    - Mountain, Valley, Dunes, Cliff, Plateau, Canyon
    
    REFACTORING NOTES:
    - Commented out redundant primitives (Hill, Mound, Pinnacle = Mountain configs)
    - Commented out ugly primitives (Ridge = too smooth, no cliff_mask)
    - Keeping specialized primitives for specific use cases but not promoting to core
    """
    
    # ========== CORE 6 PRIMITIVES (Essential for geological storytelling) ==========
    FeatureRegistry.register("mountain", MountainGenerator())  # Hero elevation (rock + snow)
    FeatureRegistry.register("valley", ValleyGenerator())      # Hero depression (grass + balance)
    FeatureRegistry.register("dunes", DunesGenerator())        # Sand texture (ONLY source via dune_mask)
    FeatureRegistry.register("cliff", CliffGenerator())        # Vertical drama (rock via cliff_mask)
    FeatureRegistry.register("plateau", PlateauGenerator())    # Flat zones (gameplay + unique geometry)
    FeatureRegistry.register("canyon", CanyonGenerator())      # Linear exploration (water stories)
    
    # ========== COMMENTED OUT: Redundant Primitives ==========
    # Use Mountain/Valley/Canyon with appropriate parameters instead
    # FeatureRegistry.register("hill", HillGenerator())        # ❌ Just Mountain(steepness=0.7)
    # FeatureRegistry.register("mound", MoundGenerator())      # ❌ Just Mountain(height=0.20, radius=25)
    # FeatureRegistry.register("pinnacle", PinnacleGenerator())  # ❌ Just Mountain(radius=20, steepness=2.0)
    # FeatureRegistry.register("basin", BasinGenerator())      # ❌ Just Valley(large, flat_bottom)
    # FeatureRegistry.register("ravine", RavineGenerator())    # ❌ Just Canyon(narrow)
    # FeatureRegistry.register("ridge", RidgeGenerator())      # ❌ Ugly (too smooth, no rock), use Cliff
    
    # ========== SPECIALIZED PRIMITIVES (Kept for specific use cases) ==========
    # These are more niche but can be useful for specific narratives
    FeatureRegistry.register("mesa", MesaGenerator())          # Flat-top mountain variant
    FeatureRegistry.register("crater", CraterGenerator())      # Composite (rim + depression)
    FeatureRegistry.register("volcano", VolcanoGenerator())    # Mountain + crater combo
    FeatureRegistry.register("slope", SlopeGenerator())        # Utility: gradual inclines
    FeatureRegistry.register("pass", PassGenerator())          # Utility: mountain passages
    FeatureRegistry.register("spur", SpurGenerator())          # Utility: mountain extensions
    FeatureRegistry.register("terraces", TerracesGenerator())  # Specialized: stepped levels
    
    # ========== WALKABILITY ZONES (Gameplay/utility features) ==========
    FeatureRegistry.register("flat_zone", FlatZoneGenerator())
    FeatureRegistry.register("path", PathGenerator())
    FeatureRegistry.register("clearing", ClearingGenerator())
    
    # ========== FOREST-SPECIFIC (Biome-specific features) ==========
    FeatureRegistry.register("grove", GroveGenerator())
    FeatureRegistry.register("forest_hill", ForestHillGenerator())
    FeatureRegistry.register("forest_clearing", ForestClearingGenerator())
    FeatureRegistry.register("forest_valley", ForestValleyGenerator())


# Auto-register on import
_register_all_generators()

