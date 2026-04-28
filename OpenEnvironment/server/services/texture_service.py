"""Texture management service."""
import os
import logging
from PIL import Image
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class TextureService:
    """Service for managing texture files."""
    
    def __init__(self, textures_dir: str):
        """
        Initialize texture service.
        
        Args:
            textures_dir: Directory for texture files
        """
        self.textures_dir = textures_dir
        os.makedirs(textures_dir, exist_ok=True)
        self._ensure_placeholder_textures()
    
    def _ensure_placeholder_textures(self):
        """Ensure all required placeholder textures exist."""
        textures = {
            "grass": (76, 175, 80),      # #4CAF50 - bright green
            "rock": (128, 128, 128),      # #808080 - gray
            "sand": (210, 180, 140),      # #D2B48C - tan/beige
            "snow": (255, 255, 255),      # #FFFFFF - white
        }
        for name, color in textures.items():
            self.create_placeholder_texture(name, color)
    
    def create_placeholder_texture(self, name: str, color: Tuple[int, int, int]):
        """
        Create a solid color placeholder texture (512x512).
        
        Args:
            name: Texture name (e.g., "grass", "rock")
            color: RGB color tuple
        """
        path = os.path.join(self.textures_dir, f"{name}.jpg")
        if not os.path.exists(path):
            img = Image.new('RGB', (512, 512), color)
            img.save(path, 'JPEG', quality=85)
            logger.info(f"Created placeholder texture: {path}")


