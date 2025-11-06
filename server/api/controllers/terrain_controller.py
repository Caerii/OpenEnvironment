"""Terrain generation controller."""
import logging
from fastapi import HTTPException
from typing import Dict
from ...services.terrain_service import TerrainService
from ...services.asset_service import AssetService
from ..models import Command

logger = logging.getLogger(__name__)


class TerrainController:
    """Controller for terrain generation endpoints."""
    
    def __init__(self, terrain_service: TerrainService, asset_service: AssetService):
        """
        Initialize terrain controller.
        
        Args:
            terrain_service: TerrainService instance
            asset_service: AssetService instance
        """
        self.terrain_service = terrain_service
        self.asset_service = asset_service
    
    def generate(self, cmd: Command) -> Dict:
        """
        Generate terrain from command.
        
        Args:
            cmd: Command model
            
        Returns:
            Response dictionary with state and assets
        """
        try:
            heightmap, state, splatmap = self.terrain_service.generate_terrain(
                command_text=cmd.text,
                actions=cmd.actions,
                seed=cmd.seed,
                biome=cmd.biome,
                voxel_mode=cmd.voxel,
                voxel_resolution=cmd.voxel_resolution
            )
            
            # Save outputs
            import time
            tag = str(int(time.time()))
            urls = self.asset_service.save_terrain_outputs(
                heightmap, splatmap, tag=tag,
                voxel_mode=cmd.voxel,
                voxel_resolution=cmd.voxel_resolution
            )
            
            return {"ok": True, "state": state, "assets": urls}
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            logger.error(f"ERROR in TerrainController.generate: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def modify(self, cmd: Command) -> Dict:
        """
        Modify terrain (alias for generate).
        
        Args:
            cmd: Command model
            
        Returns:
            Response dictionary with state and assets
        """
        return self.generate(cmd)
    
    def reset(self, cmd: Command) -> Dict:
        """
        Reset terrain to base state.
        
        Args:
            cmd: Command model (seed and biome optional)
            
        Returns:
            Response dictionary with state and assets
        """
        try:
            seed = cmd.seed if cmd.seed is not None else -1
            biome = cmd.biome if cmd.biome else "flat"
            
            heightmap, state, splatmap = self.terrain_service.reset_terrain(seed, biome)
            
            # Save outputs
            import time
            tag = str(int(time.time()))
            urls = self.asset_service.save_terrain_outputs(heightmap, splatmap, tag=tag)
            
            return {"ok": True, "state": state, "assets": urls}
        
        except Exception as e:
            error_msg = f"Reset failed: {str(e)}"
            logger.error(f"ERROR in TerrainController.reset: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def regenerate(self, cmd: Command) -> Dict:
        """
        Regenerate terrain from current state.
        
        Args:
            cmd: Command model (voxel settings)
            
        Returns:
            Response dictionary with state and assets
        """
        try:
            heightmap, state, splatmap = self.terrain_service.regenerate_terrain(
                voxel_mode=cmd.voxel,
                voxel_resolution=cmd.voxel_resolution
            )
            
            # Save outputs
            import time
            tag = str(int(time.time()))
            urls = self.asset_service.save_terrain_outputs(
                heightmap, splatmap, tag=tag,
                voxel_mode=cmd.voxel,
                voxel_resolution=cmd.voxel_resolution
            )
            
            return {"ok": True, "state": state, "assets": urls}
        
        except Exception as e:
            error_msg = f"Regeneration failed: {str(e)}"
            logger.error(f"ERROR in TerrainController.regenerate: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)


