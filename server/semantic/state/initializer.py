"""
Centralized state initialization and validation.

Ensures consistent state structure across the codebase.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StateInitializer:
    """Initialize and validate terrain state."""
    
    # Required keys for FeatureState
    REQUIRED_KEYS = ["features", "seed", "next_id"]
    
    # Default values for state initialization
    DEFAULT_VALUES: Dict[str, Any] = {
        "features": [],
        "seed": 42,
        "next_id": 1,
        "semantic_scene": {},
        "base_biome_fn": None,
    }
    
    @staticmethod
    def initialize(scene_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initialize state with defaults.
        
        Args:
            scene_state: Optional existing state to merge
        
        Returns:
            Initialized state dictionary with all required keys
        """
        if scene_state is None:
            scene_state = {}
        
        # Start with defaults
        state = StateInitializer.DEFAULT_VALUES.copy()
        
        # Merge with provided state
        state.update(scene_state)
        
        # Ensure required keys exist (override None values)
        for key, default_value in StateInitializer.DEFAULT_VALUES.items():
            if key not in state or state[key] is None:
                state[key] = default_value
        
        return state
    
    @staticmethod
    def validate(state: Dict[str, Any]) -> bool:
        """
        Validate state has required keys.
        
        Args:
            state: State dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        missing_keys = [
            key for key in StateInitializer.REQUIRED_KEYS
            if key not in state
        ]
        
        if missing_keys:
            logger.warning(f"State missing required keys: {missing_keys}")
            return False
        
        return True
    
    @staticmethod
    def ensure_features_key(state: Dict[str, Any]) -> None:
        """Ensure 'features' key exists in state."""
        if "features" not in state:
            state["features"] = []
    
    @staticmethod
    def ensure_seed(state: Dict[str, Any], default: int = 42) -> None:
        """Ensure 'seed' key exists in state."""
        if "seed" not in state:
            state["seed"] = default
    
    @staticmethod
    def ensure_next_id(state: Dict[str, Any]) -> None:
        """Ensure 'next_id' key exists in state."""
        if "next_id" not in state:
            # Calculate from existing features
            max_id = 0
            for feat in state.get("features", []):
                if isinstance(feat, dict) and "id" in feat:
                    max_id = max(max_id, feat["id"])
            state["next_id"] = max_id + 1

