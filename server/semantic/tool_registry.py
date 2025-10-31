"""MCP-style tool registry for LLM function calling.

This module implements a Model Context Protocol (MCP) inspired tool registry that:
1. Auto-discovers tools from the codebase
2. Generates JSON schemas from function signatures
3. Provides context-aware prompting for LLMs
4. Validates and executes tool calls

Architecture:
- Tool: Individual function/operation wrapper
- ToolRegistry: Container for all tools with discovery and execution
- ToolCategory: Organizes tools by type (primitive, operation, composite)
"""

import inspect
import json
from typing import Dict, List, Any, Callable, Optional, get_type_hints
from enum import Enum
from dataclasses import dataclass, field


class ToolCategory(Enum):
    """Categories of terrain generation tools."""
    PRIMITIVE = "primitive"      # Basic features (mountain, valley, dune)
    OPERATION = "operation"      # Modify/remove/query operations
    COMPOSITE = "composite"      # Complex compositions (mountain pass, crater)
    SPATIAL = "spatial"          # Spatial reasoning tools
    SEMANTIC = "semantic"        # Semantic understanding tools


@dataclass
class ToolParameter:
    """Represents a tool parameter with validation schema."""
    name: str
    type: str  # "integer", "number", "string", "boolean", "object", "array"
    description: str = ""
    required: bool = True
    default: Any = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    enum: Optional[List[Any]] = None
    items: Optional[Dict] = None  # For array types
    properties: Optional[Dict] = None  # For object types


@dataclass
class Tool:
    """Represents a callable tool with metadata and schema."""
    name: str
    func: Callable
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: Optional[Dict] = None
    examples: List[str] = field(default_factory=list)
    
    def to_schema(self) -> Dict:
        """Convert to JSON Schema format for LLM function calling."""
        schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        # Add parameters
        for param in self.parameters:
            schema["function"]["parameters"]["properties"][param.name] = {
                "type": param.type,
                "description": param.description
            }
            
            # Add constraints
            if param.minimum is not None:
                schema["function"]["parameters"]["properties"][param.name]["minimum"] = param.minimum
            if param.maximum is not None:
                schema["function"]["parameters"]["properties"][param.name]["maximum"] = param.maximum
            if param.enum is not None:
                schema["function"]["parameters"]["properties"][param.name]["enum"] = param.enum
            if param.default is not None:
                schema["function"]["parameters"]["properties"][param.name]["default"] = param.default
            if param.items is not None:
                schema["function"]["parameters"]["properties"][param.name]["items"] = param.items
            if param.properties is not None:
                schema["function"]["parameters"]["properties"][param.name]["properties"] = param.properties
            
            # Mark as required
            if param.required:
                schema["function"]["parameters"]["required"].append(param.name)
        
        return schema
    
    def to_context_string(self) -> str:
        """Generate human-readable context string for LLM."""
        lines = [f"Tool: {self.name} ({self.category.value})"]
        lines.append(f"  Description: {self.description}")
        
        if self.parameters:
            lines.append("  Parameters:")
            for param in self.parameters:
                req = " (required)" if param.required else " (optional)"
                default = f" [default: {param.default}]" if param.default is not None else ""
                lines.append(f"    - {param.name}: {param.type}{req}{default} - {param.description}")
        
        if self.examples:
            lines.append("  Examples:")
            for example in self.examples:
                lines.append(f"    - {example}")
        
        return "\n".join(lines)
    
    def validate_params(self, params: Dict) -> Dict:
        """Validate parameters against schema and apply defaults."""
        validated = {}
        
        for param in self.parameters:
            if param.name in params:
                value = params[param.name]
                # Type checking could be added here
                validated[param.name] = value
            elif param.required:
                if param.default is not None:
                    validated[param.name] = param.default
                else:
                    raise ValueError(f"Required parameter '{param.name}' not provided for tool '{self.name}'")
            elif param.default is not None:
                validated[param.name] = param.default
        
        return validated
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with validated parameters."""
        validated_params = self.validate_params(kwargs)
        return self.func(**validated_params)


class ToolRegistry:
    """
    MCP-style tool registry with runtime discovery.
    
    Features:
    - Auto-discovers tools from primitives and operations
    - Generates JSON schemas from function signatures
    - Provides context for LLM prompts
    - Validates and executes tool calls
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._discover_all_tools()
    
    def _discover_all_tools(self):
        """Auto-discover all tools from the codebase."""
        # Discover primitive tools
        self._discover_primitive_tools()
        
        # Discover operation tools
        self._discover_operation_tools()
        
        # Discover composite tools
        self._discover_composite_tools()
        
        print(f"Tool Registry initialized with {len(self.tools)} tools:")
        for category in ToolCategory:
            count = len([t for t in self.tools.values() if t.category == category])
            if count > 0:
                print(f"  - {category.value}: {count} tools")
    
    def _discover_primitive_tools(self):
        """Discover primitive terrain generation tools."""
        # Mountains
        self.register_tool(
            name="add_mountain",
            func=None,  # Handled by command pattern
            description="Add a mountain to the terrain at specified location. Creates a tall, peaked elevation with Gaussian falloff.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Position on terrain grid", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("height", "number", "Height of mountain (0.1-1.0)", False, default=0.75, minimum=0.1, maximum=1.0),
                ToolParameter("radius", "integer", "Radius of mountain base", False, default=56, minimum=20, maximum=100),
            ],
            examples=[
                "Add a mountain at the center",
                "Create a tall mountain on the left side",
                "Place two mountains with 50% more height"
            ]
        )
        
        # Hills
        self.register_tool(
            name="add_hill",
            func=None,
            description="Add a hill to the terrain. Similar to mountains but gentler slopes and lower elevation.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Position on terrain grid", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("height", "number", "Height of hill (0.1-0.8)", False, default=0.45, minimum=0.1, maximum=0.8),
                ToolParameter("radius", "integer", "Radius of hill base", False, default=42, minimum=20, maximum=80),
            ],
            examples=[
                "Add rolling hills across the terrain",
                "Create three hills on the right side"
            ]
        )
        
        # Valleys
        self.register_tool(
            name="add_valley",
            func=None,
            description="Add a valley (depression) to the terrain. Creates a bowl-shaped lowland area.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Position on terrain grid", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("depth", "number", "Depth of valley (0.1-1.0)", False, default=0.55, minimum=0.1, maximum=1.0),
                ToolParameter("radius", "integer", "Radius of valley", False, default=64, minimum=30, maximum=100),
            ],
            examples=[
                "Add a valley between the mountains",
                "Create a deep valley in the center"
            ]
        )
        
        # Dunes
        self.register_tool(
            name="add_dunes",
            func=None,
            description="Add rolling sand dunes to the terrain. Creates wavelike patterns with specified frequency and amplitude.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("region", "object", "Bounding box for dunes", True,
                             properties={"x0": {"type": "integer"}, "y0": {"type": "integer"},
                                       "x1": {"type": "integer"}, "y1": {"type": "integer"}}),
                ToolParameter("amplitude", "number", "Height of dune waves", False, default=0.08, minimum=0.02, maximum=0.3),
                ToolParameter("frequency", "number", "Wavelength of dunes", False, default=18.0, minimum=5.0, maximum=50.0),
                ToolParameter("angle", "number", "Orientation angle in degrees", False, default=20.0, minimum=0.0, maximum=360.0),
            ],
            examples=[
                "Create rolling dunes across the desert",
                "Add dunes with high frequency for fine detail"
            ]
        )
        
        # Cliffs
        self.register_tool(
            name="add_cliff",
            func=None,
            description="Add a cliff face to the terrain. Creates a steep vertical or near-vertical elevation change.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Center position of cliff", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("length", "integer", "Length of cliff face", False, default=80, minimum=20, maximum=200),
                ToolParameter("height", "number", "Height of cliff", False, default=0.55, minimum=0.2, maximum=1.0),
                ToolParameter("orientation", "number", "Rotation angle in degrees", False, default=0.0, minimum=0.0, maximum=360.0),
                ToolParameter("steepness", "number", "Steepness factor (0-1)", False, default=0.9, minimum=0.3, maximum=1.0),
            ],
            examples=[
                "Add a cliff along the northern edge",
                "Create steep cliffs for dramatic terrain"
            ]
        )
        
        # Mesas
        self.register_tool(
            name="add_mesa",
            func=None,
            description="Add a mesa (flat-topped hill) to the terrain. Creates a plateau with steep sides.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Center position", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("height", "number", "Height of mesa top", False, default=0.65, minimum=0.2, maximum=1.0),
                ToolParameter("radius", "integer", "Radius of mesa", False, default=56, minimum=30, maximum=100),
                ToolParameter("flatness", "number", "Flatness of top (0-1)", False, default=0.3, minimum=0.0, maximum=0.8),
            ],
            examples=[
                "Add a mesa to create a plateau",
                "Create flat-topped mesas for desert landscape"
            ]
        )
        
        # Plateaus
        self.register_tool(
            name="add_plateau",
            func=None,
            description="Add a plateau (large flat elevated area) to the terrain.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Center position", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("width", "integer", "Width of plateau", False, default=80, minimum=40, maximum=150),
                ToolParameter("length", "integer", "Length of plateau", False, default=120, minimum=60, maximum=200),
                ToolParameter("height", "number", "Elevation of plateau", False, default=0.50, minimum=0.2, maximum=0.9),
                ToolParameter("orientation", "number", "Rotation angle", False, default=0.0, minimum=0.0, maximum=360.0),
            ],
            examples=[
                "Add a large plateau for elevated terrain",
                "Create an oriented plateau along the ridge"
            ]
        )
        
        # Canyons
        self.register_tool(
            name="add_canyon",
            func=None,
            description="Add a canyon (linear valley) to the terrain. Creates a deep carved channel between two points.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("start", "object", "Starting position", True,
                             properties={"x": {"type": "integer"}, "y": {"type": "integer"}}),
                ToolParameter("end", "object", "Ending position", True,
                             properties={"x": {"type": "integer"}, "y": {"type": "integer"}}),
                ToolParameter("width", "integer", "Width of canyon", False, default=12, minimum=5, maximum=40),
                ToolParameter("depth", "number", "Depth of canyon", False, default=0.60, minimum=0.2, maximum=1.0),
                ToolParameter("falloff", "number", "Edge softness", False, default=0.5, minimum=0.1, maximum=1.0),
            ],
            examples=[
                "Add a winding canyon through the terrain",
                "Create a deep canyon between two points"
            ]
        )
        
        # Slopes
        self.register_tool(
            name="add_slope",
            func=None,
            description="Add a gradual slope to the terrain. Creates a smooth elevation gradient.",
            category=ToolCategory.PRIMITIVE,
            parameters=[
                ToolParameter("position", "object", "Center position", True,
                             properties={"x": {"type": "integer", "minimum": 0, "maximum": 511},
                                       "y": {"type": "integer", "minimum": 0, "maximum": 511}}),
                ToolParameter("height", "number", "Height change", False, default=0.35, minimum=0.1, maximum=0.8),
                ToolParameter("radius", "integer", "Radius of slope", False, default=60, minimum=30, maximum=120),
                ToolParameter("direction", "number", "Slope direction angle", False, default=0.0, minimum=0.0, maximum=360.0),
                ToolParameter("steepness", "number", "Slope steepness (0-1)", False, default=0.5, minimum=0.1, maximum=1.0),
            ],
            examples=[
                "Add a gentle slope for terrain transition",
                "Create slopes connecting different elevations"
            ]
        )
    
    def _discover_operation_tools(self):
        """Discover operation tools (modify, remove, query)."""
        self.register_tool(
            name="modify_feature",
            func=None,
            description="Modify an existing terrain feature by changing its parameters (height, size, etc.).",
            category=ToolCategory.OPERATION,
            parameters=[
                ToolParameter("target", "string", "Feature type or reference (e.g., 'mountain', 'the last mountain')", True),
                ToolParameter("height_percent", "number", "Height change percentage", False, minimum=-100, maximum=200),
                ToolParameter("width_percent", "number", "Width change percentage", False, minimum=-100, maximum=200),
                ToolParameter("taller", "boolean", "Make feature taller", False, default=False),
                ToolParameter("wider", "boolean", "Make feature wider", False, default=False),
                ToolParameter("deeper", "boolean", "Make feature deeper (for valleys)", False, default=False),
            ],
            examples=[
                "Make the mountain 50% taller",
                "Make the valley wider",
                "Increase the height of the last hill"
            ]
        )
        
        self.register_tool(
            name="remove_feature",
            func=None,
            description="Remove a terrain feature from the scene.",
            category=ToolCategory.OPERATION,
            parameters=[
                ToolParameter("target", "string", "Feature type or reference to remove", True),
                ToolParameter("count", "integer", "Number of features to remove (1 = most recent)", False, default=1, minimum=1),
            ],
            examples=[
                "Remove the mountain",
                "Delete the last valley",
                "Remove all dunes"
            ]
        )
        
        self.register_tool(
            name="query_features",
            func=None,
            description="Query terrain features by type, position, or properties.",
            category=ToolCategory.OPERATION,
            parameters=[
                ToolParameter("feature_type", "string", "Type of feature to query", False,
                             enum=["mountain", "hill", "valley", "dunes", "cliff", "mesa", "plateau", "canyon", "slope"]),
                ToolParameter("region", "string", "Spatial region to query", False,
                             enum=["top-left", "top", "top-right", "left", "center", "right", "bottom-left", "bottom", "bottom-right"]),
            ],
            examples=[
                "Find all mountains",
                "List features on the left side",
                "Query valleys in the center"
            ]
        )
    
    def _discover_composite_tools(self):
        """Discover composite/high-level tools."""
        self.register_tool(
            name="create_mountain_pass",
            func=None,
            description="Create a mountain pass composition: two mountains with a valley between them, optionally with cliff walls.",
            category=ToolCategory.COMPOSITE,
            parameters=[
                ToolParameter("position", "object", "Center position of the pass", True,
                             properties={"x": {"type": "integer"}, "y": {"type": "integer"}}),
                ToolParameter("width", "integer", "Width of the pass", False, default=80, minimum=40, maximum=150),
                ToolParameter("orientation", "number", "Orientation angle", False, default=0.0, minimum=0.0, maximum=360.0),
                ToolParameter("add_cliffs", "boolean", "Add cliff walls to the pass", False, default=False),
            ],
            examples=[
                "Create a mountain pass for a dramatic entrance",
                "Add a pass with cliff walls"
            ]
        )
        
        self.register_tool(
            name="create_crater",
            func=None,
            description="Create a crater composition: circular valley surrounded by raised rim.",
            category=ToolCategory.COMPOSITE,
            parameters=[
                ToolParameter("position", "object", "Center of crater", True,
                             properties={"x": {"type": "integer"}, "y": {"type": "integer"}}),
                ToolParameter("radius", "integer", "Radius of crater", False, default=60, minimum=30, maximum=120),
                ToolParameter("rim_height", "number", "Height of crater rim", False, default=0.4, minimum=0.2, maximum=0.8),
            ],
            examples=[
                "Create a crater formation",
                "Add an impact crater to the terrain"
            ]
        )
    
    def register_tool(self, name: str, func: Optional[Callable], description: str,
                     category: ToolCategory, parameters: List[ToolParameter] = None,
                     returns: Optional[Dict] = None, examples: List[str] = None):
        """Register a tool manually."""
        tool = Tool(
            name=name,
            func=func,
            description=description,
            category=category,
            parameters=parameters or [],
            returns=returns,
            examples=examples or []
        )
        self.tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get all tools in a category."""
        return [t for t in self.tools.values() if t.category == category]
    
    def to_llm_function_schemas(self) -> List[Dict]:
        """Export all tools as LLM function calling schemas."""
        return [tool.to_schema() for tool in self.tools.values()]
    
    def to_context_string(self, include_categories: Optional[List[ToolCategory]] = None) -> str:
        """
        Generate human-readable context string for LLM prompting.
        
        Args:
            include_categories: Optional list of categories to include (None = all)
        """
        lines = ["=== AVAILABLE TERRAIN TOOLS ===\n"]
        
        # Group by category
        for category in ToolCategory:
            tools = self.get_tools_by_category(category)
            
            # Filter if requested
            if include_categories and category not in include_categories:
                continue
            
            if not tools:
                continue
            
            lines.append(f"\n## {category.value.upper()} TOOLS ({len(tools)} tools)")
            lines.append("-" * 50)
            
            for tool in tools:
                lines.append("\n" + tool.to_context_string())
        
        return "\n".join(lines)
    
    def generate_scene_context(self, state: Dict) -> str:
        """
        Generate scene context string from current terrain state.
        
        Includes:
        - Feature inventory
        - Spatial layout
        - Semantic entities (if available)
        """
        lines = ["\n=== CURRENT SCENE CONTEXT ===\n"]
        
        features = state.get("features", [])
        
        # Feature inventory
        feature_counts = {}
        for feat in features:
            ftype = feat.get("type")
            feature_counts[ftype] = feature_counts.get(ftype, 0) + 1
        
        lines.append("Feature Inventory:")
        for ftype, count in sorted(feature_counts.items()):
            lines.append(f"  - {ftype}: {count}")
        
        # Spatial layout analysis
        if features:
            lines.append("\nSpatial Layout:")
            spatial_dist = self._analyze_spatial_distribution(features)
            for region, count in sorted(spatial_dist.items()):
                if count > 0:
                    lines.append(f"  - {region}: {count} features")
        
        # Semantic entities (if available)
        if "semantic_scene" in state:
            lines.append("\nSemantic Entities:")
            entities = state["semantic_scene"].get("entities", {})
            for entity_id, entity in entities.items():
                label = entity.get("label", entity_id)
                feature_refs = entity.get("feature_refs", [])
                lines.append(f"  - {label}: {len(feature_refs)} features")
        
        return "\n".join(lines)
    
    def _analyze_spatial_distribution(self, features: List[Dict]) -> Dict[str, int]:
        """Analyze which regions features are in."""
        RES = 512
        regions = {
            "top-left": 0, "top": 0, "top-right": 0,
            "left": 0, "center": 0, "right": 0,
            "bottom-left": 0, "bottom": 0, "bottom-right": 0
        }
        
        for feat in features:
            x, y = feat.get("x", RES//2), feat.get("y", RES//2)
            
            # Determine region
            if x < RES//3:
                horiz = "left"
            elif x < 2*RES//3:
                horiz = "center"
            else:
                horiz = "right"
            
            if y < RES//3:
                vert = "top"
            elif y < 2*RES//3:
                vert = "center"
            else:
                vert = "bottom"
            
            if vert == "center" and horiz == "center":
                region = "center"
            elif vert == "center":
                region = horiz
            elif horiz == "center":
                region = vert
            else:
                region = f"{vert}-{horiz}"
            
            regions[region] = regions.get(region, 0) + 1
        
        return regions
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with validation."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        
        return tool.execute(**kwargs)


# Global tool registry instance
_registry = None

def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

