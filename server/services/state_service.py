"""State management service."""
import os
import logging
from typing import Dict, Optional
from ..engine.state_lock import atomic_read_state, atomic_write_state

logger = logging.getLogger(__name__)


class StateService:
    """Service for managing terrain state."""
    
    def __init__(self, state_path: str):
        """
        Initialize state service.
        
        Args:
            state_path: Path to terrain state JSON file
        """
        self.state_path = state_path
        self._ensure_initialized()
    
    def _ensure_initialized(self):
        """Ensure state file exists with initial state."""
        if not os.path.exists(self.state_path):
            atomic_write_state({"features": [], "seed": 0}, self.state_path, backup=False)
    
    def get_state(self) -> Dict:
        """
        Get current terrain state.
        
        Returns:
            Current terrain state dictionary
        """
        return atomic_read_state(self.state_path)
    
    def save_state(self, state: Dict):
        """
        Save terrain state atomically.
        
        Args:
            state: State dictionary to save
        """
        atomic_write_state(state, self.state_path)
    
    def reset_state(self, seed: int = -1) -> Dict:
        """
        Reset state to initial empty state.
        
        Args:
            seed: Initial seed value (-1 = auto-generate random seed)
            
        Returns:
            New state dictionary
        """
        import random
        
        # Auto-generate random seed if seed is -1
        if seed == -1:
            seed = random.randint(0, 2**31 - 1)
        
        state = {"features": [], "seed": seed}
        
        # Create fresh scene graph
        try:
            from ..semantic.scene import TerrainSceneGraph, SceneGraphSerializer
            scene_graph = TerrainSceneGraph()
            state["semantic_scene"] = SceneGraphSerializer.to_dict(scene_graph)
        except Exception as e:
            logger.warning(f"Failed to initialize scene graph: {e}")
            state["semantic_scene"] = {}
        
        self.save_state(state)
        return state
    
    def update_seed(self, seed: int):
        """
        Update seed in current state.
        
        Args:
            seed: New seed value
        """
        state = self.get_state()
        state["seed"] = seed
        self.save_state(state)


