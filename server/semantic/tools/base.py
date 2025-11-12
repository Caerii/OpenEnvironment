"""
Base utilities for semantic tools.

Provides standardized output format and error handling.
"""

from typing import Dict, Any, Optional, TypedDict
from dataclasses import dataclass
import time


class ToolResult(TypedDict):
    """Standardized tool result format."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class ToolExecutionContext:
    """Context for tool execution."""
    tool_name: str
    start_time: float
    
    @classmethod
    def create(cls, tool_name: str) -> "ToolExecutionContext":
        """Create a new execution context."""
        return cls(tool_name=tool_name, start_time=time.time())
    
    def get_execution_time_ms(self) -> int:
        """Get execution time in milliseconds."""
        return int((time.time() - self.start_time) * 1000)


def success_result(data: Dict[str, Any], tool_name: str, start_time: float) -> ToolResult:
    """
    Create a successful tool result.
    
    Args:
        data: Result data
        tool_name: Name of the tool
        start_time: When execution started
        
    Returns:
        Standardized success result
    """
    execution_time = int((time.time() - start_time) * 1000)
    
    return {
        "success": True,
        "data": data,
        "error": None,
        "metadata": {
            "tool": tool_name,
            "execution_time_ms": execution_time
        }
    }


def error_result(error_msg: str, tool_name: str, start_time: float) -> ToolResult:
    """
    Create an error tool result.
    
    Args:
        error_msg: Error message
        tool_name: Name of the tool
        start_time: When execution started
        
    Returns:
        Standardized error result
    """
    execution_time = int((time.time() - start_time) * 1000)
    
    return {
        "success": False,
        "data": {},
        "error": error_msg,
        "metadata": {
            "tool": tool_name,
            "execution_time_ms": execution_time
        }
    }


def wrap_tool(func):
    """
    Decorator to wrap tool functions with standardized output format.
    
    Usage:
        @wrap_tool
        def my_tool(scene_state, param1, param2):
            # ... do work ...
            return {"result": ...}
    """
    def wrapper(scene_state: Dict, *args, **kwargs):
        start_time = time.time()
        tool_name = func.__name__
        
        try:
            # Execute tool
            result = func(scene_state, *args, **kwargs)
            
            # If result is already in standard format, return as-is
            if isinstance(result, dict) and "success" in result:
                return result
            
            # Otherwise wrap it
            return success_result(result, tool_name, start_time)
            
        except Exception as e:
            return error_result(str(e), tool_name, start_time)
    
    # Preserve function metadata for schema generation
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__
    wrapper.__signature__ = func.__signature__ if hasattr(func, '__signature__') else None
    
    return wrapper

