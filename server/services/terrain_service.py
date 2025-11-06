"""Terrain generation service."""
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from ..terrain import apply_actions
from ..primitives.base import base_flat, base_desert, base_forest, base_arctic

logger = logging.getLogger(__name__)


class TerrainService:
    """Service for terrain generation operations."""
    
    def __init__(self, state_service, asset_service):
        """
        Initialize terrain service.
        
        Args:
            state_service: StateService instance
            asset_service: AssetService instance
        """
        self.state_service = state_service
        self.asset_service = asset_service
        
        # Biome function mapping
        self.biome_map = {
            "flat": base_flat,
            "desert": base_desert,
            "forest": base_forest,
            "arctic": base_arctic
        }
    
    def get_biome_function(self, biome: Optional[str]):
        """
        Get biome generation function.
        
        Args:
            biome: Biome name (flat, desert, forest, arctic) or None
            
        Returns:
            Biome generation function
        """
        if biome and biome in self.biome_map:
            return self.biome_map[biome]
        return base_desert  # Default
    
    def generate_terrain(
        self,
        command_text: str = "",
        actions: Optional[List[Dict]] = None,
        seed: Optional[int] = None,
        biome: Optional[str] = None,
        voxel_mode: bool = False,
        voxel_resolution: int = 256
    ) -> Tuple[np.ndarray, Dict, np.ndarray]:
        """
        Generate terrain from command or actions.
        
        Args:
            command_text: Natural language command (empty = rebuild from state)
            actions: Optional direct JSON actions
            seed: Optional seed override
            biome: Optional biome type
            voxel_mode: Whether to generate voxels
            voxel_resolution: Voxel grid resolution
            
        Returns:
            Tuple of (heightmap, state, splatmap)
        """
        # Get current state
        state = self.state_service.get_state()
        
        # Update seed if provided
        if seed is not None:
            state["seed"] = seed
            self.state_service.update_seed(seed)
        
        # Get biome function
        base_biome_fn = self.get_biome_function(biome)
        
        # Generate terrain
        if actions:
            # Direct JSON actions
            heightmap, state, splatmap = apply_actions(
                "", state, base_biome_fn=base_biome_fn, direct_actions=actions
            )
        else:
            # Natural language command
            heightmap, state, splatmap = apply_actions(
                command_text, state, base_biome_fn=base_biome_fn
            )
        
        # Save state
        self.state_service.save_state(state)
        
        # Periodic cleanup (probabilistic to avoid overhead)
        self.asset_service.cleanup_old_assets(probability=0.1)
        
        return heightmap, state, splatmap
    
    def reset_terrain(self, seed: int = 0, biome: str = "flat") -> Tuple[np.ndarray, Dict, np.ndarray]:
        """
        Reset terrain to base state with interesting procedural variation.
        
        Instead of just flat terrain, generates a procedurally interesting
        default terrain with varied features based on the seed.
        
        Args:
            seed: Initial seed value
            biome: Base biome type
            
        Returns:
            Tuple of (heightmap, state, splatmap)
        """
        # Reset state
        state = self.state_service.reset_state(seed)
        
        # Get biome function
        base_biome_fn = self.get_biome_function(biome)
        
        # Generate procedurally interesting default terrain
        # Use seed to deterministically generate random but cool features
        import random
        rng = random.Random(seed)
        
        # Generate 3-6 random features for interesting terrain
        num_features = rng.randint(3, 6)
        
        # Pre-composed actions for interesting default terrain
        default_actions = []
        
        # Feature types with varied parameters
        feature_types = [
            ("mountain", {"count": 1, "height_range": (0.4, 0.7), "radius_range": (40, 80)}),
            ("valley", {"count": 1, "depth_range": (0.2, 0.4), "radius_range": (50, 100)}),
            ("hill", {"count": 1, "height_range": (0.2, 0.4), "radius_range": (30, 60)}),
            ("mound", {"count": 1, "height_range": (0.15, 0.3), "radius_range": (20, 40)}),
            ("basin", {"count": 1, "depth_range": (0.15, 0.3), "radius_range": (40, 70)}),
            ("dunes", {"count": 1, "amp_range": (0.05, 0.12), "freq_range": (15.0, 25.0)}),
        ]
        
        # Select random features based on seed
        selected_features = rng.sample(feature_types, min(num_features, len(feature_types)))
        
        # Position regions (vary placement)
        regions = ["center", "top-left", "top-right", "bottom-left", "bottom-right", 
                   "top", "bottom", "left", "right"]
        
        for feature_type, params in selected_features:
            region = rng.choice(regions)
            
            if feature_type == "mountain":
                height = rng.uniform(*params["height_range"])
                radius = rng.randint(*params["radius_range"])
                default_actions.append({
                    "kind": "add",
                    "type": "mountain",
                    "count": params["count"],
                    "position": {"region": region},
                    "modifiers": {
                        "height": height,
                        "radius": radius,
                        "steepness": rng.uniform(0.8, 1.5)
                    }
                })
            elif feature_type == "valley":
                depth = rng.uniform(*params["depth_range"])
                radius = rng.randint(*params["radius_range"])
                default_actions.append({
                    "kind": "add",
                    "type": "valley",
                    "count": params["count"],
                    "position": {"region": region},
                    "modifiers": {
                        "depth": depth,
                        "radius": radius
                    }
                })
            elif feature_type == "hill":
                height = rng.uniform(*params["height_range"])
                radius = rng.randint(*params["radius_range"])
                default_actions.append({
                    "kind": "add",
                    "type": "hill",
                    "count": params["count"],
                    "position": {"region": region},
                    "modifiers": {
                        "height": height,
                        "radius": radius
                    }
                })
            elif feature_type == "mound":
                height = rng.uniform(*params["height_range"])
                radius = rng.randint(*params["radius_range"])
                default_actions.append({
                    "kind": "add",
                    "type": "mound",
                    "count": params["count"],
                    "position": {"region": region},
                    "modifiers": {
                        "height": height,
                        "radius": radius
                    }
                })
            elif feature_type == "basin":
                depth = rng.uniform(*params["depth_range"])
                radius = rng.randint(*params["radius_range"])
                default_actions.append({
                    "kind": "add",
                    "type": "basin",
                    "count": params["count"],
                    "position": {"region": region},
                    "modifiers": {
                        "depth": depth,
                        "radius": radius
                    }
                })
            elif feature_type == "dunes":
                amp = rng.uniform(*params["amp_range"])
                freq = rng.uniform(*params["freq_range"])
                default_actions.append({
                    "kind": "add",
                    "type": "dunes",
                    "count": params["count"],
                    "position": {"region": region},
                    "modifiers": {
                        "amplitude": amp,
                        "frequency": freq,
                        "angle": rng.uniform(0, 360)
                    }
                })
        
        # Generate terrain with interesting default features
        heightmap, state, splatmap = apply_actions(
            "", state, base_biome_fn=base_biome_fn, seed=seed, direct_actions=default_actions
        )
        
        # Save state
        self.state_service.save_state(state)
        
        return heightmap, state, splatmap
    
    def regenerate_terrain(
        self,
        voxel_mode: bool = False,
        voxel_resolution: int = 256
    ) -> Tuple[np.ndarray, Dict, np.ndarray]:
        """
        Regenerate terrain from current state.
        
        Args:
            voxel_mode: Whether to generate voxels
            voxel_resolution: Voxel grid resolution
            
        Returns:
            Tuple of (heightmap, state, splatmap)
        """
        # Get current state
        state = self.state_service.get_state()
        
        # Regenerate from state (empty command = rebuild)
        heightmap, state, splatmap = apply_actions("", state)
        
        # Save state (may have been updated)
        self.state_service.save_state(state)
        
        return heightmap, state, splatmap


