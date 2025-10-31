import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
from .tool_registry import get_tool_registry, ToolCategory

# Load environment variables
load_dotenv()

class SemanticParser:
    """
    MCP-enhanced semantic command parser for terrain generation.
    
    Features:
    - Context-aware parsing with tool registry
    - Scene state understanding
    - Spatial relationship reasoning
    """
    
    def __init__(self):
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not found in environment variables")
        
        self.client = Cerebras(api_key=api_key)
        self.model = "qwen-3-235b-a22b-instruct-2507"
        self.tool_registry = get_tool_registry()
        
    def parse(self, command: str, scene_state: Optional[Dict] = None) -> Dict:
        """
        Parse a natural language command into structured terrain generation actions.
        
        Args:
            command: Natural language command from user
            scene_state: Optional current terrain state for context
        
        Returns:
            Dictionary with:
            - actions: List of action dictionaries
            - Each action has: kind, type, count, position, modifiers
        """
        # Build context-aware system prompt
        system_prompt = self._build_system_prompt(scene_state)
        
        user_message = f"""Parse this terrain generation command:

"{command}"

Output only valid JSON, no additional text."""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model=self.model,
                stream=False,
                max_completion_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent parsing
                top_p=0.8,
                response_format={"type": "json_object"}
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            import json
            parsed = json.loads(content)
            
            # Validate and normalize the structure
            return self._normalize_response(parsed)
            
        except Exception as e:
            # Fallback to simple parsing on error
            print(f"LLM parsing failed: {e}, falling back to regex parser")
            return self._fallback_parse(command)
    
    def _build_system_prompt(self, scene_state: Optional[Dict] = None) -> str:
        """
        Build context-aware system prompt with tool registry and scene state.
        
        This is the MCP magic - the LLM sees all available tools and current scene.
        """
        prompt_parts = []
        
        # Base instruction
        prompt_parts.append("""You are a terrain generation command parser with full knowledge of available tools and current scene state.

Convert natural language commands into structured JSON using the tools described below.

CRITICAL: Extract EXACT numerical quantities for each feature type. Do NOT ignore or approximate counts.

Output format (JSON):
{
  "actions": [
    {
      "kind": "add" | "remove" | "modify",
      "type": "mountain" | "hill" | "valley" | "dunes" | "mesa" | "plateau" | "cliff" | "canyon" | "slope" | null,
      "count": number (REQUIRED - extract exact count for each feature, default 1 if not specified),
      "position": {
        "region": "top-left" | "top" | "top-right" | "left" | "center" | "right" | "bottom-left" | "bottom" | "bottom-right" | null,
        "coords": [x, y] | null (0-511, use explicit coordinates when user specifies precise locations)
      },
      "modifiers": {
        "taller": boolean,
        "deeper": boolean,
        "wider": boolean,
        "height_percent": number | null,
        "depth_percent": number | null,
        "width_percent": number | null
      }
    }
  ]
}
""")
        
        # Add scene context if available
        if scene_state:
            scene_context = self.tool_registry.generate_scene_context(scene_state)
            prompt_parts.append(scene_context)
        
        # Add tool context (what tools are available)
        tool_context = self._generate_compact_tool_context()
        prompt_parts.append(tool_context)
        
        # Add parsing rules
        prompt_parts.append("""
COMPOSITIONAL SUPPORT:
- When user provides explicit coordinates (e.g., "mountain at (100, 200)"), use "coords": [100, 200]
- When user specifies multiple features with different positions, create separate actions for each
- Support multiple actions in one call for complex compositions
- Example: "mountain at (100, 100), valley at (300, 300), hill at (200, 200)" → 3 separate actions with explicit coords

COUNT EXTRACTION RULES (CRITICAL):
- Extract numbers in ALL forms: words ("one", "two", "three"), digits ("1", "2", "3"), written ("a", "an" = 1, "several" = 3-5)
- Associate count with the IMMEDIATELY following feature type
- "two mountains" → count: 2, type: "mountain"
- "three hills" → count: 3, type: "hill"
- "a valley" → count: 1, type: "valley"
- "two mountains and three hills" → 2 actions: [count:2, type:"mountain"], [count:3, type:"hill"]
- If no count specified, default to 1
- NEVER create multiple actions with count=1 when user specified a number

NUMERICAL QUANTITY PATTERNS:
- "one/two/three/four/five/six/seven/eight/nine/ten" → 1-10
- "1/2/3/4/5/6/7/8/9/10" → digits
- "a/an" → 1
- "several" → 3-5
- "many" → 5-8
- "few" → 2-3
- "couple" → 2
- "pair" → 2
- "dozen" → 12

Other Rules:
- Extract ALL actions from the command
- If multiple features mentioned, create separate actions for each WITH CORRECT COUNT
- Default to "add" if action unclear
- Default to "center" if position unclear and no scene context
- Extract numeric percentages if given (e.g., "50% taller" → height_percent: 50)
- Coordinates are optional, use region if no coordinates specified
- For "remove" or "modify", type can be null to target the most recent feature
- Use scene context to resolve spatial references ("between the mountains", "near the valley")

Examples (COUNT IS CRITICAL):
- "create a desert with rolling dunes and two mountains on the left" → 2 actions:
  [kind:"add", type:"dunes", count:1, position:{region:"center"}],
  [kind:"add", type:"mountain", count:2, position:{region:"left"}]
- "add a valley in the center" → 1 action: [kind:"add", type:"valley", count:1, position:{region:"center"}]
- "add three hills on the right" → 1 action: [kind:"add", type:"hill", count:3, position:{region:"right"}]
- "add two mountains and three valleys" → 2 actions:
  [kind:"add", type:"mountain", count:2, position:{region:"center"}],
  [kind:"add", type:"valley", count:3, position:{region:"center"}]
- "create five mountains scattered" → 1 action: [kind:"add", type:"mountain", count:5, position:{distribution:"scattered"}]
- "make the mountain 50% taller" → 1 action: [kind:"modify", type:"mountain", count:1, modifiers:{height_percent:50}]
- "remove the valley" → 1 action: [kind:"remove", type:"valley", count:1]""")
        
        return "\n\n".join(prompt_parts)
    
    def _generate_compact_tool_context(self) -> str:
        """Generate compact tool context for the system prompt."""
        lines = ["\n=== AVAILABLE TOOLS (MCP Registry) ===\n"]
        lines.append("You have access to the following terrain generation tools:\n")
        
        # List primitive tools compactly
        primitives = self.tool_registry.get_tools_by_category(ToolCategory.PRIMITIVE)
        lines.append("PRIMITIVE FEATURES:")
        for tool in primitives:
            lines.append(f"  - {tool.name}: {tool.description[:80]}...")
        
        # List operation tools
        operations = self.tool_registry.get_tools_by_category(ToolCategory.OPERATION)
        if operations:
            lines.append("\nOPERATIONS:")
            for tool in operations:
                lines.append(f"  - {tool.name}: {tool.description[:80]}...")
        
        # List composite tools
        composites = self.tool_registry.get_tools_by_category(ToolCategory.COMPOSITE)
        if composites:
            lines.append("\nCOMPOSITE FEATURES:")
            for tool in composites:
                lines.append(f"  - {tool.name}: {tool.description[:80]}...")
        
        lines.append("\nAll tools support spatial placement (coordinates or regions) and parameter customization.")
        
        return "\n".join(lines)
    
    def _normalize_response(self, parsed: Dict) -> Dict:
        """Normalize LLM response to expected format."""
        if "actions" not in parsed:
            parsed["actions"] = []
        
        # Ensure each action has required fields
        for action in parsed["actions"]:
            if "kind" not in action:
                action["kind"] = "add"
            if "type" not in action:
                action["type"] = None
            if "count" not in action or not isinstance(action["count"], (int, float)):
                # Try to extract count if missing
                action["count"] = 1
                print(f"Warning: Missing or invalid count in action, defaulting to 1. Action: {action}")
            else:
                # Ensure count is an integer
                action["count"] = int(action["count"])
                if action["count"] < 1:
                    print(f"Warning: Invalid count {action['count']}, clamping to 1. Action: {action}")
                    action["count"] = 1
            
            if "position" not in action:
                action["position"] = {"region": None, "coords": None}
            if "modifiers" not in action:
                action["modifiers"] = {"taller": False, "deeper": False, "wider": False}
            
            # Convert position dict to flat format for compatibility
            if isinstance(action["position"], dict):
                poskey = action["position"].get("region")
                coord = action["position"].get("coords")
                action["poskey"] = poskey
                action["coord"] = tuple(coord) if coord else None
            else:
                action["poskey"] = None
                action["coord"] = None
            
            # Log extracted count for debugging
            if action.get("count", 1) > 1:
                print(f"Extracted count: {action['count']} for type: {action.get('type')}")
        
        return parsed
    
    def _fallback_parse(self, command: str) -> Dict:
        """Fallback to regex-based parsing if LLM fails."""
        # Import the old parser as fallback
        from ..terrain import parse_command
        return parse_command(command)

