"""Asset management service."""
import os
import logging
import time
from typing import Dict, Optional
import numpy as np
from ..terrain import to_png_16bit_gray, to_png_8bit_gray, to_png_rgba
from ..engine.voxel import heightmap_to_voxels, export_voxels_mesh, export_voxels_binary
from ..engine.cleanup import cleanup_old_assets, cleanup_temp_files

logger = logging.getLogger(__name__)


class AssetService:
    """Service for managing generated terrain assets."""
    
    def __init__(self, output_dir: str):
        """
        Initialize asset service.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def save_terrain_outputs(
        self,
        heightmap: np.ndarray,
        splatmap: np.ndarray,
        tag: Optional[str] = None,
        voxel_mode: bool = False,
        voxel_resolution: int = 256
    ) -> Dict[str, str]:
        """
        Save terrain outputs (heightmaps, splatmap, optional voxels).
        
        Args:
            heightmap: Heightmap array (512x512)
            splatmap: Splatmap array (512x512x4 RGBA)
            tag: Optional tag for filenames (defaults to timestamp)
            voxel_mode: Whether to generate voxel data
            voxel_resolution: Voxel grid resolution (128-2048)
            
        Returns:
            Dictionary of asset URLs
        """
        if tag is None:
            tag = str(int(time.time()))
        
        try:
            # Save heightmaps (16-bit for Unity, 8-bit for web)
            path_h16 = os.path.join(self.output_dir, f"height_{tag}_16.png")
            path_h8 = os.path.join(self.output_dir, f"height_{tag}_8.png")
            path_s = os.path.join(self.output_dir, f"splat_{tag}.png")
            
            to_png_16bit_gray(heightmap, path_h16)
            to_png_8bit_gray(heightmap, path_h8)
            to_png_rgba(splatmap, path_s)
            
            urls = {
                "height16": f"/assets/height_{tag}_16.png",
                "height8": f"/assets/height_{tag}_8.png",
                "splat": f"/assets/splat_{tag}.png"
            }
            
            # Generate voxel data if requested
            if voxel_mode:
                logger.info(f"Generating voxel grid with resolution: {voxel_resolution}³ ({voxel_resolution**3:,} voxels)")
                voxel_grid = heightmap_to_voxels(heightmap, resolution=voxel_resolution, height_scale=50.0)
                voxel_obj_path = os.path.join(self.output_dir, f"voxel_{tag}.obj")
                voxel_bin_path = os.path.join(self.output_dir, f"voxel_{tag}.bin")
                
                export_voxels_mesh(voxel_grid, voxel_obj_path)
                export_voxels_binary(voxel_grid, voxel_bin_path)
                
                urls["voxel_obj"] = f"/assets/voxel_{tag}.obj"
                urls["voxel_bin"] = f"/assets/voxel_{tag}.bin"
            
            return urls
            
        except (OSError, IOError, ValueError) as e:
            error_msg = f"Failed to save outputs: {str(e)}"
            logger.error(f"ERROR in save_terrain_outputs: {error_msg}", exc_info=True)
            raise IOError(error_msg) from e
    
    def cleanup_old_assets(self, probability: float = 0.1):
        """
        Periodically clean up old assets (probabilistic to avoid overhead).
        
        Args:
            probability: Probability of running cleanup (0.0-1.0)
        """
        import random
        if random.random() < probability:
            cleanup_old_assets(self.output_dir)
            cleanup_temp_files(self.output_dir)
    
    def list_assets(self) -> list:
        """
        List all available asset files.
        
        Returns:
            List of asset metadata dictionaries
        """
        assets = []
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                if filename.endswith(('.png', '.obj', '.bin')):
                    filepath = os.path.join(self.output_dir, filename)
                    stat = os.stat(filepath)
                    assets.append({
                        "uri": f"asset://{filename}",
                        "name": filename,
                        "type": "asset",
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
        return assets


