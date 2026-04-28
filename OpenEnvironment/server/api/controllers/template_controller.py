"""Template management controller."""
import logging
from fastapi import HTTPException
from typing import Dict, Optional
from ...services.template_service import TemplateService
from ...services.asset_service import AssetService
from ..models import Command

logger = logging.getLogger(__name__)


class TemplateController:
    """Controller for template endpoints."""
    
    def __init__(self, template_service: TemplateService, asset_service: AssetService):
        """
        Initialize template controller.
        
        Args:
            template_service: TemplateService instance
            asset_service: AssetService instance
        """
        self.template_service = template_service
        self.asset_service = asset_service
    
    def list_templates(self, category: Optional[str] = None, tag: Optional[str] = None) -> Dict:
        """
        List available templates.
        
        Args:
            category: Optional category filter
            tag: Optional tag filter
            
        Returns:
            Templates response dictionary
        """
        try:
            result = self.template_service.list_templates(category, tag)
            return {
                "ok": True,
                **result
            }
        except Exception as e:
            error_msg = f"Failed to list templates: {str(e)}"
            logger.error(f"ERROR in TemplateController.list_templates: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def get_template(self, template_id: str) -> Dict:
        """
        Get template details.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template response dictionary
        """
        try:
            template = self.template_service.get_template(template_id)
            if not template:
                raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
            
            return {
                "ok": True,
                "template": template
            }
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Failed to get template: {str(e)}"
            logger.error(f"ERROR in TemplateController.get_template: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def apply_template(self, template_id: str, cmd: Command) -> Dict:
        """
        Apply a template.
        
        Args:
            template_id: Template identifier
            cmd: Command model (seed and biome optional)
            
        Returns:
            Response dictionary with state and assets
        """
        try:
            seed = cmd.seed if cmd.seed is not None else -1
            biome = cmd.biome if cmd.biome else "desert"
            
            heightmap, state, splatmap = self.template_service.apply_template(
                template_id, seed, biome
            )
            
            # Get template name for response
            template = self.template_service.get_template(template_id)
            template_name = template["name"] if template else template_id
            
            # Save outputs
            import time
            tag = str(int(time.time()))
            urls = self.asset_service.save_terrain_outputs(heightmap, splatmap, tag=tag)
            
            return {
                "ok": True,
                "template_id": template_id,
                "template_name": template_name,
                "state": state,
                "assets": urls
            }
        
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Failed to apply template: {str(e)}"
            logger.error(f"ERROR in TemplateController.apply_template: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)


