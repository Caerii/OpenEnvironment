"""
Tool executor for handling function calls from LLM.

Manages tool registration, execution, and result handling.
"""

from typing import Dict, Any, List, Callable, Optional
import json
import logging

from .base import ToolResult, success_result, error_result
import time

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tools called by LLM.
    
    Handles:
    - Tool registration
    - Function execution with scene_state injection
    - Error handling
    - Result formatting
    """
    
    def __init__(self):
        """Initialize tool executor."""
        self.tools: Dict[str, Callable] = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all available tools."""
        # Import tools
        from .query_tools import (
            query_entities,
            get_feature_details,
            get_spatial_relationships,
            query_scene_summary
        )
        from .spatial_tools import (
            calculate_position,
            calculate_region_positions,
            get_region_bounds
        )
        from .resolution_tools import (
            resolve_reference,
            resolve_temporal_reference,
            resolve_attribute_filter
        )
        from .inference_tools import (
            infer_feature_parameters,
            suggest_modification,
            validate_action
        )
        from .narrative_tools import (
            generate_narrative_composition
        )
        
        # Register tools
        self.tools = {
            # Query tools
            "query_entities": query_entities,
            "get_feature_details": get_feature_details,
            "get_spatial_relationships": get_spatial_relationships,
            "query_scene_summary": query_scene_summary,
            
            # Spatial tools
            "calculate_position": calculate_position,
            "calculate_region_positions": calculate_region_positions,
            "get_region_bounds": get_region_bounds,
            
            # Resolution tools
            "resolve_reference": resolve_reference,
            "resolve_temporal_reference": resolve_temporal_reference,
            "resolve_attribute_filter": resolve_attribute_filter,
            
            # Inference tools
            "infer_feature_parameters": infer_feature_parameters,
            "suggest_modification": suggest_modification,
            "validate_action": validate_action,
            
            # Narrative tools (NEW!)
            "generate_narrative_composition": generate_narrative_composition
        }
        
        logger.info(f"Registered {len(self.tools)} tools (including narrative generation)")
    
    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        scene_state: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from LLM
            scene_state: Current scene state (injected automatically)
            
        Returns:
            Standardized tool result
        """
        start_time = time.time()
        
        # Check if tool exists
        if tool_name not in self.tools:
            return error_result(
                f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}",
                tool_name,
                start_time
            )
        
        try:
            # Get tool function
            tool_func = self.tools[tool_name]
            
            # Execute with scene_state injected
            logger.info(f"Executing tool: {tool_name} with args: {list(arguments.keys())}")
            result = tool_func(scene_state, **arguments)
            
            # If result is already in standard format, return as-is
            if isinstance(result, dict) and "success" in result:
                return result
            
            # Otherwise wrap it
            return success_result(result, tool_name, start_time)
            
        except TypeError as e:
            # Handle parameter mismatch
            return error_result(
                f"Parameter error: {str(e)}",
                tool_name,
                start_time
            )
        except Exception as e:
            # Handle other errors
            logger.error(f"Tool '{tool_name}' failed: {e}", exc_info=True)
            return error_result(str(e), tool_name, start_time)
    
    def execute_tool_calls(
        self,
        tool_calls: List[Any],
        scene_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls from LLM response.
        
        Args:
            tool_calls: List of tool_call objects from LLM response
            scene_state: Current scene state
            
        Returns:
            List of tool results in OpenAI format for conversation history
        """
        results = []
        
        for tool_call in tool_calls:
            # Parse tool call
            tool_name = tool_call.function.name
            arguments_str = tool_call.function.arguments
            
            # Parse arguments JSON
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments: {arguments_str}")
                result = error_result(
                    f"Invalid JSON arguments: {str(e)}",
                    tool_name,
                    time.time()
                )
                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(result)
                })
                continue
            
            # Execute tool
            result = self.execute_tool(tool_name, arguments, scene_state)
            
            # Format for conversation history
            results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result)
            })
            
            # Log execution
            if result["success"]:
                logger.info(
                    f"Tool '{tool_name}' succeeded in {result['metadata']['execution_time_ms']}ms"
                )
            else:
                logger.warning(f"Tool '{tool_name}' failed: {result['error']}")
        
        return results
    
    def get_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def get_tool_functions(self) -> Dict[str, Callable]:
        """Get dict of tool functions for schema generation."""
        return self.tools

