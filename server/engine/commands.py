"""Command pattern for terrain actions."""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import numpy as np
from ..semantic.state_manager import FeatureState
from ..engine.builder import TerrainBuilder


class ActionCommand(ABC):
    """Base class for terrain action commands."""
    
    @abstractmethod
    def execute(self, builder: Optional[TerrainBuilder], feature_state: FeatureState, seed: int):
        """
        Execute this action.
        
        Args:
            builder: TerrainBuilder instance (may be None for state-only operations)
            feature_state: FeatureState manager
            seed: Random seed
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """Serialize action to dictionary."""
        pass


class AddFeatureCommand(ActionCommand):
    """Command to add a new feature."""
    
    def __init__(self, feature_type: str, position: Dict, modifiers: Dict, count: int = 1):
        self.feature_type = feature_type
        self.position = position
        self.modifiers = modifiers
        self.count = count
    
    def execute(self, builder: Optional[TerrainBuilder], feature_state: FeatureState, seed: int):
        """Execute add feature action."""
        if builder is None:
            raise ValueError("Builder required for add feature action")
        
        from ..terrain import _create_feature
        from ..semantic.spatial_resolver import resolve_position, resolve_multiple_positions
        
        # Validate count
        if self.count < 1:
            print(f"Warning: Invalid count {self.count} for {self.feature_type}, using 1")
            self.count = 1
        
        existing_features = feature_state.list_features()
        
        # Resolve positions with deterministic seed
        position_seed = (seed + len(existing_features) * 31) % (2**31)
        if self.count > 1:
            positions = resolve_multiple_positions(
                self.position, self.count, existing_features, seed=position_seed
            )
            print(f"Adding {len(positions)} {self.feature_type}(s) (requested: {self.count})")
        else:
            pos = resolve_position(self.position, existing_features, seed=position_seed)
            positions = [pos]
        
        # Ensure we have the correct number of positions
        if len(positions) != self.count:
            print(f"Warning: Generated {len(positions)} positions but count is {self.count}")
        
        # Create and add features
        for idx, (cx, cy) in enumerate(positions):
            feature_seed = (position_seed + idx * 17) % (2**31)
            feat = _create_feature(self.feature_type, cx, cy, self.modifiers, feature_seed)
            if feat:
                feature_state.add_feature(feat)
                # Apply feature immediately to builder
                _apply_feature_to_builder(builder, feat, feature_seed)
    
    def to_dict(self) -> Dict:
        return {
            "kind": "add",
            "type": self.feature_type,
            "position": self.position,
            "modifiers": self.modifiers,
            "count": self.count
        }


class RemoveFeatureCommand(ActionCommand):
    """Command to remove a feature."""
    
    def __init__(self, feature_type: Optional[str] = None, ordinal: Optional[int] = None):
        self.feature_type = feature_type
        self.ordinal = ordinal
    
    def execute(self, builder: Optional[TerrainBuilder], feature_state: FeatureState, seed: int):
        """Execute remove feature action."""
        feature_state.remove_feature(
            feature_type=self.feature_type,
            ordinal=self.ordinal
        )
        # Note: Removal requires rebuild, so builder may be None
        # The caller handles rebuilding the terrain
    
    def to_dict(self) -> Dict:
        return {
            "kind": "remove",
            "type": self.feature_type,
            "ordinal": self.ordinal
        }


class ModifyFeatureCommand(ActionCommand):
    """Command to modify an existing feature."""
    
    def __init__(self, feature_type: Optional[str] = None, ordinal: Optional[int] = None,
                 modifiers: Optional[Dict] = None):
        self.feature_type = feature_type
        self.ordinal = ordinal
        self.modifiers = modifiers or {}
    
    def execute(self, builder: Optional[TerrainBuilder], feature_state: FeatureState, seed: int):
        """Execute modify feature action."""
        from ..terrain import _modify_feature
        
        feat = feature_state.find_feature(
            feature_type=self.feature_type,
            ordinal=self.ordinal
        )
        if feat:
            _modify_feature(feat, self.modifiers)
            # Modification requires rebuild - handled by caller
    
    def to_dict(self) -> Dict:
        return {
            "kind": "modify",
            "type": self.feature_type,
            "ordinal": self.ordinal,
            "modifiers": self.modifiers
        }


def create_command_from_dict(action_dict: Dict) -> ActionCommand:
    """Factory function to create command from action dictionary."""
    kind = action_dict.get("kind", "add")
    
    if kind == "add":
        return AddFeatureCommand(
            feature_type=action_dict.get("type") or "hill",
            position=action_dict.get("position", {}),
            modifiers=action_dict.get("modifiers", {}),
            count=action_dict.get("count", 1)
        )
    elif kind == "remove":
        return RemoveFeatureCommand(
            feature_type=action_dict.get("type"),
            ordinal=action_dict.get("ordinal")
        )
    elif kind == "modify":
        return ModifyFeatureCommand(
            feature_type=action_dict.get("type"),
            ordinal=action_dict.get("ordinal"),
            modifiers=action_dict.get("modifiers", {})
        )
    else:
        raise ValueError(f"Unknown action kind: {kind}")


def _apply_feature_to_builder(builder: TerrainBuilder, feat: Dict, seed: int):
    """Helper to apply a feature dictionary to builder."""
    from ..primitives.mountains import generate_mountain, generate_hill, generate_mesa, generate_plateau
    from ..primitives.valleys import generate_valley, generate_canyon
    from ..primitives.dunes import generate_dunes, generate_dune_mask
    from ..primitives.cliffs import generate_cliff, generate_cliff_mask
    from ..primitives.slopes import generate_slope, generate_slope_radial
    from ..engine.stamping import BlendingMode
    
    RES = 512  # Terrain resolution
    ftype = feat.get("type")
    
    if ftype in ("mountain", "hill"):
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 56 if ftype == "mountain" else 42)
        height = feat.get("height", 0.75 if ftype == "mountain" else 0.45)
        use_noise = feat.get("use_noise", True)  # Default to using noise
        
        if ftype == "mountain":
            stamp = generate_mountain(cx, cy, radius, height, use_noise=use_noise, seed=seed)
        else:
            # Hills use gentler steepness, but can also use noise
            stamp = generate_mountain(cx, cy, radius, height, steepness=0.7, use_noise=use_noise, seed=seed)
        
        builder.apply_feature(stamp, BlendingMode.MAX)
    
    elif ftype == "mesa":
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 56)
        height = feat.get("height", 0.65)
        flatness = feat.get("flatness", 0.3)
        stamp = generate_mesa(cx, cy, radius, height, flatness)
        builder.apply_feature(stamp, BlendingMode.MAX)
    
    elif ftype == "plateau":
        cx, cy = feat["x"], feat["y"]
        width = feat.get("width", 80)
        length = feat.get("length", 120)
        height = feat.get("height", 0.50)
        orientation = feat.get("orientation", 0.0)
        stamp = generate_plateau(cx, cy, width, length, height, orientation)
        builder.apply_feature(stamp, BlendingMode.MAX)
    
    elif ftype == "valley":
        cx, cy = feat["x"], feat["y"]
        radius = feat.get("radius", 64)
        depth = feat.get("depth", 0.55)
        stamp = generate_valley(cx, cy, radius, depth)
        builder.apply_feature(stamp, BlendingMode.SUBTRACT)
    
    elif ftype == "canyon":
        start = (feat["x0"], feat["y0"])
        end = (feat["x1"], feat["y1"])
        width = feat.get("width", 12)
        depth = feat.get("depth", 0.60)
        falloff = feat.get("falloff", 0.5)
        stamp = generate_canyon(start, end, width, depth, falloff)
        builder.apply_feature(stamp, BlendingMode.SUBTRACT)
    
    elif ftype == "cliff":
        cx, cy = feat["x"], feat["y"]
        length = feat.get("length", 80)
        height = feat.get("height", 0.55)
        orientation = feat.get("orientation", 0.0)
        steepness = feat.get("steepness", 0.9)
        stamp = generate_cliff(cx, cy, length, height, orientation, steepness)
        builder.apply_feature(stamp, BlendingMode.MAX)
        
        # Add cliff mask for rock texture
        RES = 512
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
    
    elif ftype == "slope":
        if "start" in feat and "end" in feat:
            # Linear slope
            start = tuple(feat["start"])
            end = tuple(feat["end"])
            width = feat.get("width", 40)
            height = feat.get("height", 0.35)
            falloff = feat.get("falloff", 0.3)
            stamp = generate_slope(start, end, width, height, falloff)
        else:
            # Radial slope
            cx, cy = feat["x"], feat["y"]
            radius = feat.get("radius", 60)
            height = feat.get("height", 0.35)
            direction = feat.get("direction", 0.0)
            steepness = feat.get("steepness", 0.5)
            stamp = generate_slope_radial(cx, cy, radius, height, direction, steepness)
        builder.apply_feature(stamp, BlendingMode.ADD)
    
    elif ftype == "dunes":
        box = (feat["x0"], feat["y0"], feat["x1"], feat["y1"])
        amp = feat.get("amp", 0.08)
        freq = feat.get("freq", 18.0)
        angle = feat.get("angle", 20.0)
        stamp = generate_dunes(box, amp, freq, angle, seed)
        dune_mask = generate_dune_mask(box)
        builder.apply_feature(stamp, BlendingMode.ADD, dune_mask, box)

