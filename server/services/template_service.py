"""Template management service."""
import logging
from typing import Dict, List, Optional
from ..engine.templates import TemplateRegistry

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing terrain templates."""
    
    def __init__(self, terrain_service):
        """
        Initialize template service.
        
        Args:
            terrain_service: TerrainService instance
        """
        self.terrain_service = terrain_service
    
    def list_templates(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> Dict:
        """
        List available templates.
        
        Args:
            category: Optional category filter
            tag: Optional tag filter
            
        Returns:
            Dictionary with templates list and metadata
        """
        if category:
            templates = TemplateRegistry.get_by_category(category)
        elif tag:
            templates = TemplateRegistry.get_by_tag(tag)
        else:
            templates = TemplateRegistry.get_all()
        
        categories = TemplateRegistry.get_categories()
        
        return {
            "templates": templates,
            "categories": categories,
            "count": len(templates)
        }
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template dictionary or None if not found
        """
        template = TemplateRegistry.get_by_id(template_id)
        if not template:
            return None
        
        template_dict = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "tags": template.tags,
            "thumbnail_hint": template.thumbnail_hint,
            "format": "actions" if template.actions is not None else "commands"
        }
        
        if template.commands:
            template_dict["commands"] = template.commands
            template_dict["command_count"] = len(template.commands)
        if template.actions:
            template_dict["actions"] = template.actions
            template_dict["action_count"] = len(template.actions)
        
        return template_dict
    
    def apply_template(
        self,
        template_id: str,
        seed: Optional[int] = None,
        biome: Optional[str] = None
    ) -> tuple:
        """
        Apply a template to generate terrain.
        
        Args:
            template_id: Template identifier
            seed: Optional seed value
            biome: Optional biome type
            
        Returns:
            Tuple of (heightmap, state, splatmap)
        """
        from ..terrain import apply_actions
        
        template = TemplateRegistry.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Reset state
        seed_value = seed if seed is not None else -1
        state = self.terrain_service.state_service.reset_state(seed_value)
        
        # Get biome function
        base_biome_fn = self.terrain_service.get_biome_function(biome or "desert")
        
        # Apply template
        if template.actions:
            # Use pre-composed JSON actions
            heightmap, state, splatmap = apply_actions(
                "", state, base_biome_fn=base_biome_fn, direct_actions=template.actions
            )
        else:
            # Use natural language commands
            combined_command = ". ".join(template.commands)
            heightmap, state, splatmap = apply_actions(
                combined_command, state, base_biome_fn=base_biome_fn
            )
        
        # Save state
        self.terrain_service.state_service.save_state(state)
        
        return heightmap, state, splatmap

