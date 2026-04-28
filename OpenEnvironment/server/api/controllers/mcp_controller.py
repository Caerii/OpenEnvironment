"""MCP (Model Context Protocol) controller."""
import logging
from fastapi import HTTPException
from typing import Dict, Optional
from ...services.mcp_service import MCPService

logger = logging.getLogger(__name__)


class MCPController:
    """Controller for MCP endpoints."""
    
    def __init__(self, mcp_service: MCPService):
        """
        Initialize MCP controller.
        
        Args:
            mcp_service: MCPService instance
        """
        self.mcp_service = mcp_service
    
    def get_info(self) -> Dict:
        """
        Get MCP server information.
        
        Returns:
            Server info dictionary
        """
        try:
            info = self.mcp_service.get_server_info()
            return {"ok": True, **info}
        except Exception as e:
            error_msg = f"Failed to get MCP info: {str(e)}"
            logger.error(f"ERROR in MCPController.get_info: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def list_tools(self, category: Optional[str] = None) -> Dict:
        """
        List MCP tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            Tools response dictionary
        """
        try:
            result = self.mcp_service.list_tools(category)
            return {"ok": True, **result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            error_msg = f"Failed to list MCP tools: {str(e)}"
            logger.error(f"ERROR in MCPController.list_tools: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def get_tool(self, tool_name: str) -> Dict:
        """
        Get tool schema.
        
        Args:
            tool_name: Tool identifier
            
        Returns:
            Tool response dictionary
        """
        try:
            result = self.mcp_service.get_tool(tool_name)
            return {"ok": True, **result}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            error_msg = f"Failed to get MCP tool: {str(e)}"
            logger.error(f"ERROR in MCPController.get_tool: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Execute an MCP tool.
        
        Args:
            tool_name: Tool identifier
            arguments: Tool arguments
            
        Returns:
            Execution result dictionary
        """
        try:
            result = self.mcp_service.call_tool(tool_name, arguments)
            return {"ok": True, **result}
        except ValueError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            error_msg = f"Failed to execute MCP tool: {str(e)}"
            logger.error(f"ERROR in MCPController.call_tool: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def list_resources(self) -> Dict:
        """
        List MCP resources.
        
        Returns:
            Resources response dictionary
        """
        try:
            result = self.mcp_service.list_resources()
            return {"ok": True, **result}
        except Exception as e:
            error_msg = f"Failed to list MCP resources: {str(e)}"
            logger.error(f"ERROR in MCPController.list_resources: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def get_resource(self, resource_uri: str) -> Dict:
        """
        Get MCP resource.
        
        Args:
            resource_uri: Resource URI
            
        Returns:
            Resource response dictionary
        """
        try:
            result = self.mcp_service.get_resource(resource_uri)
            return {"ok": True, **result}
        except ValueError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            error_msg = f"Failed to get MCP resource: {str(e)}"
            logger.error(f"ERROR in MCPController.get_resource: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def list_prompts(self) -> Dict:
        """
        List MCP prompts.
        
        Returns:
            Prompts response dictionary
        """
        try:
            result = self.mcp_service.list_prompts()
            return {"ok": True, **result}
        except Exception as e:
            error_msg = f"Failed to list MCP prompts: {str(e)}"
            logger.error(f"ERROR in MCPController.list_prompts: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def get_prompt(self, prompt_name: str) -> Dict:
        """
        Get MCP prompt.
        
        Args:
            prompt_name: Prompt identifier
            
        Returns:
            Prompt response dictionary
        """
        try:
            result = self.mcp_service.get_prompt(prompt_name)
            return {"ok": True, **result}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            error_msg = f"Failed to get MCP prompt: {str(e)}"
            logger.error(f"ERROR in MCPController.get_prompt: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)


