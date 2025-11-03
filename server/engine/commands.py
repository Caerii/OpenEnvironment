"""Command pattern for terrain actions."""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import logging
import numpy as np
from ..semantic.state_manager import FeatureState
from ..engine.builder import TerrainBuilder

logger = logging.getLogger(__name__)


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
            logger.warning(f"Invalid count {self.count} for {self.feature_type}, using 1")
            self.count = 1
        
        existing_features = feature_state.list_features()
        
        # Resolve positions with deterministic seed
        position_seed = (seed + len(existing_features) * 31) % (2**31)
        if self.count > 1:
            positions = resolve_multiple_positions(
                self.position, self.count, existing_features, seed=position_seed
            )
            logger.info(f"Adding {len(positions)} {self.feature_type}(s) (requested: {self.count})")
        else:
            pos = resolve_position(self.position, existing_features, seed=position_seed)
            positions = [pos]
        
        # Ensure we have the correct number of positions
        if len(positions) != self.count:
            logger.warning(f"Generated {len(positions)} positions but count is {self.count}")
        
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
    
    def __init__(self, feature_type: Optional[str] = None, ordinal: Optional[int] = None,
                 target_feature_ids: Optional[List[int]] = None):
        self.feature_type = feature_type
        self.ordinal = ordinal
        self.target_feature_ids = target_feature_ids
    
    def execute(self, builder: Optional[TerrainBuilder], feature_state: FeatureState, seed: int):
        """Execute remove feature action."""
        # If target_feature_ids provided, remove those specific features
        if self.target_feature_ids:
            for feature_id in self.target_feature_ids:
                feature_state.remove_feature(feature_id=feature_id)
        else:
            # Fall back to type/ordinal resolution
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
            "ordinal": self.ordinal,
            "target_feature_ids": self.target_feature_ids
        }


class ModifyFeatureCommand(ActionCommand):
    """Command to modify an existing feature."""
    
    def __init__(self, feature_type: Optional[str] = None, ordinal: Optional[int] = None,
                 modifiers: Optional[Dict] = None, target_feature_ids: Optional[List[int]] = None):
        self.feature_type = feature_type
        self.ordinal = ordinal
        self.modifiers = modifiers or {}
        self.target_feature_ids = target_feature_ids
    
    def execute(self, builder: Optional[TerrainBuilder], feature_state: FeatureState, seed: int):
        """Execute modify feature action."""
        from ..terrain import _modify_feature
        
        # If target_feature_ids provided, modify those specific features
        if self.target_feature_ids:
            for feature_id in self.target_feature_ids:
                feat = feature_state.find_feature(feature_id=feature_id)
                if feat:
                    _modify_feature(feat, self.modifiers)
        else:
            # Fall back to type/ordinal resolution
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
            "modifiers": self.modifiers,
            "target_feature_ids": self.target_feature_ids
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
            ordinal=action_dict.get("ordinal"),
            target_feature_ids=action_dict.get("target_feature_ids")
        )
    elif kind == "modify":
        return ModifyFeatureCommand(
            feature_type=action_dict.get("type"),
            ordinal=action_dict.get("ordinal"),
            modifiers=action_dict.get("modifiers", {}),
            target_feature_ids=action_dict.get("target_feature_ids")
        )
    else:
        raise ValueError(f"Unknown action kind: {kind}")


def _apply_feature_to_builder(builder: TerrainBuilder, feat: Dict, seed: int):
    """
    Helper to apply a feature dictionary to builder.
    
    Uses FeatureRegistry for composable, maintainable primitive handling.
    All 19 primitives are automatically handled through the registry.
    """
    from ..engine.feature_registry import FeatureRegistry
    
    ftype = feat.get("type")
    
    if not ftype:
        logger.warning(f"Feature missing type field: {feat}")
        return
    
    if not FeatureRegistry.has_generator(ftype):
        logger.warning(f"Unknown feature type '{ftype}', skipping. Registered types: {FeatureRegistry.get_registered_types()}")
        return
    
    # Generate stamp using registry
    try:
        stamp = FeatureRegistry.generate_stamp(ftype, feat, seed)
        mode = FeatureRegistry.get_blending_mode(ftype)
        
        # Special handling for dunes (need stamp + mask together)
        if ftype == "dunes":
            from ..primitives.dunes import generate_dune_mask
            box = (feat["x0"], feat["y0"], feat["x1"], feat["y1"])
            dune_mask = generate_dune_mask(box)
            builder.apply_feature(stamp, mode, dune_mask_slice=dune_mask, mask_bounds=box)
        else:
            # Apply stamp
            builder.apply_feature(stamp, mode)
            
            # Apply special effects (masks, etc.) if needed
            FeatureRegistry.apply_special_effects(ftype, builder, feat, stamp, seed)
        
    except Exception as e:
        logger.error(f"Error applying feature '{ftype}': {e}", exc_info=True)

