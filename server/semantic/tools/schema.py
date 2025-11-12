"""
Tool schema conversion utilities.

Converts our internal tool definitions to OpenAI-compatible function schemas
for use with Cerebras SDK's tool calling feature.
"""

from typing import Dict, List, Any, Callable
import inspect


def convert_to_openai_function_schema(
    tool_name: str,
    tool_function: Callable,
    description: str,
    parameter_descriptions: Dict[str, str]
) -> Dict[str, Any]:
    """
    Convert a Python function to OpenAI function calling schema.
    
    Args:
        tool_name: Name of the tool
        tool_function: The actual function
        description: Human-readable description
        parameter_descriptions: Dict mapping parameter names to descriptions
        
    Returns:
        OpenAI-compatible function schema
    """
    # Get function signature
    sig = inspect.signature(tool_function)
    
    # Build parameters schema
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        # Skip scene_state as it's injected automatically
        if param_name == "scene_state":
            continue
        
        # Get parameter description
        param_desc = parameter_descriptions.get(param_name, f"Parameter: {param_name}")
        
        # Determine type from annotation
        param_type_info = _python_type_to_json_schema(param.annotation)
        
        param_schema = {
            **param_type_info,  # Includes type and items if array
            "description": param_desc
        }
        
        # Add default if present
        if param.default != inspect.Parameter.empty and param.default is not None:
            param_schema["default"] = param.default
        
        # Add to properties
        properties[param_name] = param_schema
        
        # Add to required if no default
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


def _python_type_to_json_schema(python_type: Any) -> Dict[str, Any]:
    """
    Convert Python type annotation to JSON Schema.
    
    Returns dict with 'type' and optionally 'items' for arrays.
    """
    if python_type == inspect.Parameter.empty:
        return {"type": "string"}
    
    # Handle type hints
    type_str = str(python_type)
    
    if "int" in type_str.lower():
        return {"type": "integer"}
    elif "float" in type_str.lower():
        return {"type": "number"}
    elif "bool" in type_str.lower():
        return {"type": "boolean"}
    elif "list" in type_str.lower() or "List" in type_str:
        # Array types MUST include 'items' schema
        return {
            "type": "array",
            "items": {"type": "integer"}  # Default to integer for feature IDs
        }
    elif "dict" in type_str.lower() or "Dict" in type_str:
        # Object types MUST include 'properties' schema
        # Cerebras requires additionalProperties: false
        return {
            "type": "object",
            "properties": {},  # Allow any properties (empty = flexible)
            "additionalProperties": False  # Required by Cerebras
        }
    else:
        return {"type": "string"}


# Define comprehensive tool schemas for all our tools
TOOL_SCHEMAS = {
    "query_entities": {
        "description": "Search for entities in the scene by label, keyword, or type. Use this to find features matching specific criteria.",
        "parameters": {
            "label": "Filter by entity label (e.g., 'the mountains')",
            "keyword": "Filter by keyword (e.g., 'tall', 'steep', 'rolling')",
            "entity_type": "Filter by entity type: 'feature' for single features or 'group' for grouped features",
            "created_after": "Unix timestamp - only return entities created after this time",
            "limit": "Maximum number of results to return (default: 10)"
        }
    },
    
    "get_feature_details": {
        "description": "Get detailed attributes of specific features including position, size, height, and other parameters.",
        "parameters": {
            "feature_ids": "List of feature IDs to query (e.g., [1, 2, 3])"
        }
    },
    
    "get_spatial_relationships": {
        "description": "Calculate spatial relationships between features such as centroids, bounding boxes, and positions for 'between', 'near', or 'around' queries.",
        "parameters": {
            "reference_ids": "List of feature IDs to use as reference points",
            "relationship_type": "Type of calculation: 'centroid' (center point), 'bounding_box', 'between_position', 'north_of', 'south_of', 'east_of', 'west_of', or 'nearby_positions' (for circular pattern)"
        }
    },
    
    "query_scene_summary": {
        "description": "Get overall scene statistics including feature counts by type, entity counts, spatial distribution, and recent activity.",
        "parameters": {}
    },
    
    "calculate_position": {
        "description": "Calculate a single position based on spatial relationships like 'near', 'between', 'north of', etc. Returns coordinates and region.",
        "parameters": {
            "reference_ids": "Optional list of feature IDs for reference point (not needed if using explicit region)",
            "relationship": "Spatial relationship: 'near', 'between', 'north_of', 'south_of', 'east_of', 'west_of'",
            "region": "Explicit region name if not using reference: 'left', 'center', 'right', 'top', 'bottom', 'top-left', 'top-right', etc.",
            "offset_distance": "Distance for directional offsets in pixels (default: 80)"
        }
    },
    
    "calculate_region_positions": {
        "description": "Generate multiple positions in a pattern (circular, scattered, line, or grid). Use for commands like 'add 5 hills around X'.",
        "parameters": {
            "count": "Number of positions to generate",
            "reference_ids": "Optional list of feature IDs for reference point",
            "pattern": "Distribution pattern: 'scattered' (random-ish), 'circular' (around center), 'line' (linear), or 'grid' (evenly spaced)",
            "radius": "Radius for pattern in pixels (default: 100)",
            "region": "Region for scattered pattern if not using reference"
        }
    },
    
    "get_region_bounds": {
        "description": "Get coordinate bounds for a named region to understand what 'left', 'center', 'top-right', etc. mean in terms of actual coordinates.",
        "parameters": {
            "region": "Region name: 'left', 'center', 'right', 'top', 'bottom', 'top-left', 'center-right', etc."
        }
    },
    
    "resolve_reference": {
        "description": "Resolve a natural language reference to feature IDs. Use this to find what 'the mountains' or 'the valley' refers to.",
        "parameters": {
            "reference": "Natural language reference (e.g., 'the mountains', 'the dunes')"
        }
    },
    
    "resolve_temporal_reference": {
        "description": "Resolve time-based references like 'recent', 'just added', 'last', etc. to feature IDs.",
        "parameters": {
            "temporal_phrase": "Temporal phrase: 'recent', 'just added', 'last', 'newest', 'oldest'"
        }
    },
    
    "resolve_attribute_filter": {
        "description": "Find entities matching attribute keywords like 'tall', 'steep', 'wide', 'gentle', etc.",
        "parameters": {
            "keyword": "Attribute keyword: 'tall', 'steep', 'wide', 'narrow', 'gentle', 'deep', etc."
        }
    },
    
    "infer_feature_parameters": {
        "description": "Suggest appropriate parameters for a feature based on user modifiers like 'tall', 'wide', 'steep'.",
        "parameters": {
            "feature_type": "Type of feature: 'mountain', 'valley', 'hill', etc.",
            "user_modifiers": "List of modifier words from user command (e.g., ['tall', 'steep'])",
            "position": "Position where feature will be placed [x, y]"
        }
    },
    
    "suggest_modification": {
        "description": "Calculate how to modify existing features based on modification type and intensity.",
        "parameters": {
            "feature_ids": "List of feature IDs to modify",
            "modification_type": "Type of modification: 'taller', 'wider', 'deeper', 'steeper', etc.",
            "intensity": "Intensity of modification: 'slightly', 'moderate', 'much' (default: 'moderate')"
        }
    },
    
    "validate_action": {
        "description": "Validate if a proposed action is valid (position in bounds, parameters in range, etc.).",
        "parameters": {
            "action": "Action dictionary to validate with kind, type, position, etc."
        }
    },
    
    "generate_narrative_composition": {
        "description": "Develop a geological narrative and convert it into terrain-building actions.",
        "parameters": {
            "command": "User's aesthetic command describing the desired terrain scene",
            "scene_state": "Current terrain state (features, seed, semantic scene). Usually passed automatically."
        }
    }
}
    

def get_all_tool_schemas(tool_functions: Dict[str, Callable]) -> List[Dict[str, Any]]:
    """Convert all registered tools to OpenAI-compatible schemas."""
    schemas: List[Dict[str, Any]] = []

    for tool_name, tool_func in tool_functions.items():
        tool_info = TOOL_SCHEMAS.get(tool_name)
        if not tool_info:
            continue

        schema = convert_to_openai_function_schema(
            tool_name=tool_name,
            tool_function=tool_func,
            description=tool_info["description"],
            parameter_descriptions=tool_info["parameters"]
        )
        schemas.append(schema)

    return schemas
    
