"""MCP (Model Context Protocol) service."""
import logging
from typing import Dict, List, Optional
import os
import json
from ..semantic.tool_registry import get_tool_registry, ToolCategory
from ..engine.templates import TemplateRegistry

logger = logging.getLogger(__name__)


class MCPService:
    """Service for MCP protocol operations."""
    
    def __init__(self, terrain_service, asset_service, state_service):
        """
        Initialize MCP service.
        
        Args:
            terrain_service: TerrainService instance
            asset_service: AssetService instance
            state_service: StateService instance
        """
        self.terrain_service = terrain_service
        self.asset_service = asset_service
        self.state_service = state_service
        self._registry = None
    
    @property
    def registry(self):
        """Get tool registry (lazy initialization)."""
        if self._registry is None:
            self._registry = get_tool_registry()
        return self._registry
    
    def get_server_info(self) -> Dict:
        """
        Get MCP server information and capabilities.
        
        Returns:
            Server metadata dictionary
        """
        tools_by_category = {
            category.value: len(self.registry.get_tools_by_category(category))
            for category in ToolCategory
        }
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "name": "OpenEnvironment MCP Server",
            "description": "MCP-compatible tool registry for procedural environment generation",
            "capabilities": {
                "tools": True,
                "tool_listing": True,
                "tool_schemas": True,
                "tool_execution": True,
                "resources": True,
                "prompts": True,
            },
            "tool_count": len(self.registry.tools),
            "tools_by_category": tools_by_category,
            "endpoints": {
                "list_tools": "/api/mcp/tools",
                "get_tool": "/api/mcp/tools/{tool_name}",
                "call_tool": "/api/mcp/tools/{tool_name}/call",
                "list_resources": "/api/mcp/resources",
                "get_resource": "/api/mcp/resources/{resource_uri}",
                "list_prompts": "/api/mcp/prompts",
                "get_prompt": "/api/mcp/prompts/{prompt_name}"
            }
        }
    
    def list_tools(self, category: Optional[str] = None) -> Dict:
        """
        List MCP tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            Tools dictionary
        """
        if category:
            try:
                tool_category = ToolCategory[category.upper()]
                tools = self.registry.get_tools_by_category(tool_category)
            except KeyError:
                raise ValueError(f"Invalid category: {category}")
        else:
            tools = list(self.registry.tools.values())
        
        tools_schema = [tool.to_schema() for tool in tools]
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "tools": tools_schema,
            "count": len(tools_schema),
            "categories": [cat.value for cat in ToolCategory]
        }
    
    def get_tool(self, tool_name: str) -> Dict:
        """
        Get tool schema.
        
        Args:
            tool_name: Tool identifier
            
        Returns:
            Tool schema dictionary
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "tool": tool.to_schema()
        }
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Execute an MCP tool.
        
        Args:
            tool_name: Tool identifier
            arguments: Tool arguments
            
        Returns:
            Execution result
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Validate arguments
        validated_args = tool.validate_params(arguments)
        
        # Convert tool call to action format
        action_type_map = {
            "add_mountain": "mountain",
            "add_hill": "hill",
            "add_valley": "valley",
            "add_dunes": "dunes",
            "add_cliff": "cliff",
            "add_mesa": "mesa",
            "add_canyon": "canyon",
            "add_ridge": "ridge",
            "add_volcano": "volcano",
            "add_crater": "crater",
            "add_basin": "basin",
            "add_pass": "pass",
            "add_ravine": "ravine",
            "add_slope": "slope",
            "add_plateau": "plateau",
            "add_mound": "mound",
            "add_pinnacle": "pinnacle",
            "add_spur": "spur",
            "add_terraces": "terraces",
            "add_flat_zone": "flat_zone",
            "add_path": "path",
            "add_clearing": "clearing",
        }
        
        feature_type = action_type_map.get(tool_name, tool_name.replace("add_", ""))
        
        # Build action from tool arguments
        action = {
            "kind": "add",
            "type": feature_type,
            "count": 1,
            "position": {},
            "modifiers": {}
        }
        
        # Map tool parameters to action format
        if "position" in validated_args:
            pos = validated_args["position"]
            if isinstance(pos, dict):
                if "x" in pos and "y" in pos:
                    action["position"] = {"coords": [pos["x"], pos["y"]]}
                elif "region" in pos:
                    action["position"] = {"region": pos["region"]}
        
        # Map modifiers
        modifier_map = {
            "height": "height_percent",
            "depth": "depth_percent",
            "radius": "width_percent",
            "taller": lambda v: {"taller": True} if v else {},
            "deeper": lambda v: {"deeper": True} if v else {},
            "wider": lambda v: {"wider": True} if v else {},
        }
        
        for param_name, param_value in validated_args.items():
            if param_name == "position":
                continue
            if param_name in modifier_map:
                mapped = modifier_map[param_name]
                if callable(mapped):
                    action["modifiers"].update(mapped(param_value))
                else:
                    action["modifiers"][mapped] = param_value
            else:
                action["modifiers"][param_name] = param_value
        
        # Execute via terrain service
        heightmap, state, splatmap = self.terrain_service.generate_terrain(
            actions=[action]
        )
        
        # Save assets
        urls = self.asset_service.save_terrain_outputs(heightmap, splatmap)
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "tool": tool_name,
            "result": {
                "success": True,
                "state": state,
                "assets": urls
            }
        }
    
    def list_resources(self) -> Dict:
        """
        List MCP resources.
        
        Returns:
            Resources dictionary
        """
        # Get current terrain state
        state = self.state_service.get_state()
        
        # List available assets
        assets = self.asset_service.list_assets()
        
        # List templates as resources
        templates = TemplateRegistry.get_all()
        template_resources = [
            {
                "uri": f"template://{t['id']}",
                "name": t['name'],
                "type": "template",
                "category": t['category'],
                "description": t['description']
            }
            for t in templates
        ]
        
        resources = [
            {
                "uri": "state://current",
                "name": "Current Terrain State",
                "type": "state",
                "description": "Current terrain configuration with features and seed",
                "mimeType": "application/json"
            }
        ] + assets + template_resources
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "resources": resources,
            "count": len(resources)
        }
    
    def get_resource(self, resource_uri: str) -> Dict:
        """
        Get MCP resource.
        
        Args:
            resource_uri: Resource URI (state://, asset://, template://)
            
        Returns:
            Resource dictionary
        """
        if resource_uri.startswith("state://"):
            state = self.state_service.get_state()
            return {
                "protocol": "mcp",
                "version": "1.0",
                "uri": resource_uri,
                "contents": [
                    {
                        "uri": resource_uri,
                        "mimeType": "application/json",
                        "text": json.dumps(state, indent=2)
                    }
                ]
            }
        
        elif resource_uri.startswith("asset://"):
            filename = resource_uri.replace("asset://", "")
            filepath = os.path.join(self.asset_service.output_dir, filename)
            
            if not os.path.exists(filepath):
                raise ValueError(f"Asset not found: {filename}")
            
            # Determine MIME type
            mime_type = "application/octet-stream"
            if filename.endswith('.png'):
                mime_type = "image/png"
            elif filename.endswith('.obj'):
                mime_type = "model/obj"
            elif filename.endswith('.bin'):
                mime_type = "application/octet-stream"
            
            stat = os.stat(filepath)
            return {
                "protocol": "mcp",
                "version": "1.0",
                "uri": resource_uri,
                "name": filename,
                "mimeType": mime_type,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "url": f"/assets/{filename}"
            }
        
        elif resource_uri.startswith("template://"):
            template_id = resource_uri.replace("template://", "")
            template = TemplateRegistry.get_by_id(template_id)
            
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
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
            if template.actions:
                template_dict["actions"] = template.actions
            
            return {
                "protocol": "mcp",
                "version": "1.0",
                "uri": resource_uri,
                "contents": [
                    {
                        "uri": resource_uri,
                        "mimeType": "application/json",
                        "text": json.dumps(template_dict, indent=2)
                    }
                ]
            }
        
        else:
            raise ValueError(f"Invalid resource URI format: {resource_uri}")
    
    def list_prompts(self) -> Dict:
        """
        List MCP prompts.
        
        Returns:
            Prompts dictionary
        """
        templates = TemplateRegistry.get_all()
        prompts = []
        
        for template in templates:
            if template.get("commands"):
                prompts.append({
                    "name": template["id"],
                    "description": template["description"],
                    "arguments": [
                        {
                            "name": "seed",
                            "description": "Random seed for terrain generation",
                            "required": False
                        },
                        {
                            "name": "biome",
                            "description": "Base biome type (flat, desert, forest, arctic)",
                            "required": False
                        }
                    ]
                })
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "prompts": prompts,
            "count": len(prompts)
        }
    
    def get_prompt(self, prompt_name: str) -> Dict:
        """
        Get MCP prompt.
        
        Args:
            prompt_name: Prompt identifier
            
        Returns:
            Prompt dictionary
        """
        template = TemplateRegistry.get_by_id(prompt_name)
        if not template:
            raise ValueError(f"Prompt not found: {prompt_name}")
        
        if not template.commands:
            raise ValueError(f"Template {prompt_name} has no commands (prompts)")
        
        prompt_text = ". ".join(template.commands)
        
        return {
            "protocol": "mcp",
            "version": "1.0",
            "name": prompt_name,
            "description": template.description,
            "arguments": [
                {
                    "name": "seed",
                    "description": "Random seed for terrain generation",
                    "required": False
                },
                {
                    "name": "biome",
                    "description": "Base biome type (flat, desert, forest, arctic)",
                    "required": False
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_text
                    }
                }
            ]
        }


