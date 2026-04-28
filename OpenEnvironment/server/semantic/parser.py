import os
import re
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

from .tool_registry import get_tool_registry, ToolCategory
from ..core.spatial_queries import handle_spatial_query
from .narrative.utils import run_narrative_pipeline
from .llm import create_llm_client, LLMClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SemanticParser:
    """
    MCP-enhanced semantic command parser for terrain generation.
    
    Features:
    - Context-aware parsing with tool registry
    - Scene state understanding
    - Spatial relationship reasoning
    """
    
    def __init__(self):
        self.llm_client: Optional[LLMClient] = create_llm_client()
        self.llm_available = self.llm_client is not None
        
        # Load tool registry (always available, even without API key)
        try:
            self.tool_registry = get_tool_registry()
        except Exception as e:
            logger.warning(f"Tool registry unavailable: {e}")
            self.tool_registry = None
        
        # OLD IMPLEMENTATION (kept for reference):
        # api_key = os.environ.get("CEREBRAS_API_KEY")
        # if not api_key:
        #     raise ValueError("CEREBRAS_API_KEY not found in environment variables")
        # self.client = Cerebras(api_key=api_key)
        # self.model = "llama3.1-8b"
        # self.tool_registry = get_tool_registry()
        
    def parse(self, command: str, scene_state: Optional[Dict] = None, use_react: bool = True) -> Dict:
        """
        Parse a natural language command into structured terrain generation actions.
        
        Supports spatial queries like "find features near the dunes".
        
        Args:
            command: Natural language command from user
            scene_state: Optional current terrain state for context
        
        Returns:
            Dictionary with:
            - actions: List of action dictionaries
            - queries: Optional list of spatial queries (for query commands)
            - Each action has: kind, type, count, position, modifiers
        """
        # Check if this is a spatial query command
        query_result = handle_spatial_query(command, scene_state)
        if query_result:
            return query_result
        
        try:
            actions, metadata = run_narrative_pipeline(command, scene_state)
            if actions:
                logger.info(
                    "Narrative pipeline produced %d actions for command '%s'",
                    len(actions), command[:60]
                )
                if isinstance(scene_state, dict):
                    scene_state["_last_narrative_meta"] = metadata
                return {"actions": actions}
        except Exception as narrative_exc:
            logger.warning(
                "Narrative pipeline exception: %s", narrative_exc,
                exc_info=True
            )

        # Build context-aware system prompt
        system_prompt = self._build_system_prompt(scene_state)
        
        user_message = f"""Parse this terrain generation command:

"{command}"

Output only valid JSON, no additional text."""

        # FIX: Check if LLM is available before trying to call it
        if not self.llm_available or self.llm_client is None:
            logger.info("LLM not available, falling back to regex parser")
            return self._fallback_parse(command)

        # NEW: Use ReAct agent V2 for complex multi-turn reasoning with proper tool calling
        if use_react and scene_state:
            try:
                from .react_agent_v2 import ReActAgentV2
                prompt_profile = os.environ.get("LLM_PROMPT_PROFILE", "compact")
                agent = ReActAgentV2(self.llm_client, prompt_profile=prompt_profile)
                logger.info(f"Using ReAct agent V2 for command: {command[:50]}...")
                result = agent.solve(command, scene_state)
                
                if result.get("success") and result.get("actions"):
                    logger.info(
                        f"ReAct agent completed in {result['iterations']} iterations "
                        f"with {result['total_tool_calls']} tool calls"
                    )
                    return {"actions": result["actions"]}
                else:
                    logger.warning(f"ReAct agent failed: {result.get('error', 'no actions')}, falling back")
            except Exception as e:
                logger.warning(f"ReAct agent V2 failed: {e}, falling back to single-turn parsing")

        # Fallback to single-turn parsing
        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                top_p=0.8,
                max_completion_tokens=2000,
                response_format={"type": "json_object"},
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Validate and normalize the structure
            return self._normalize_response(parsed)
            
        except (ValueError, KeyError, ImportError, json.JSONDecodeError) as e:
            logger.warning(f"LLM parsing failed: {e}, returning no actions")
            return {"actions": []}
    
    def _handle_spatial_query(self, command: str, scene_state: Optional[Dict] = None) -> Optional[Dict]:
        """
        Handle spatial query commands like "find features near the dunes".
        
        Args:
            command: User command
            scene_state: Scene state
            
        Returns:
            Query result dictionary or None if not a query command
        """
        command_lower = command.lower().strip()
        
        # Check for query keywords
        query_keywords = ["find", "show", "list", "query", "search", "what"]
        if not any(keyword in command_lower for keyword in query_keywords):
            return None
        
        # Check if scene graph is available
        if not scene_state or "semantic_scene" not in scene_state:
            return None
        
        try:
            from .scene import TerrainSceneGraph, QueryEngine, SceneGraphSerializer, ReferenceResolver
            
            # Load scene graph
            scene_graph = SceneGraphSerializer.from_dict(scene_state["semantic_scene"])
            query_engine = QueryEngine(scene_graph)
            resolver = ReferenceResolver(scene_graph)
            
            # Parse spatial query
            # "find features near the dunes"
            # "find mountains in the left half"
            # "find features between the mountains"
            
            result = {"queries": []}
            
            # Extract spatial relationship
            if "near" in command_lower:
                # Find reference entity
                # Extract entity reference (e.g., "the dunes", "mountains")
                ref_text = self._extract_reference_from_command(command_lower)
                if ref_text:
                    ref_ids = resolver.resolve(ref_text)
                    if ref_ids:
                        # Find features near this reference
                        for ref_id in ref_ids[:1]:  # Use first reference
                            nearby = query_engine.find_near_feature(ref_id, radius=150)
                            feature_ids = query_engine.get_feature_ids(nearby)
                            result["queries"].append({
                                "type": "near",
                                "reference": ref_text,
                                "reference_feature_ids": [ref_id],
                                "results": feature_ids,
                                "count": len(feature_ids)
                            })
            
            elif "between" in command_lower:
                # Find features between entities
                ref_text = self._extract_reference_from_command(command_lower)
                if ref_text:
                    # This is complex - would need to find two anchor entities
                    # For now, return empty
                    pass
            
            elif "in" in command_lower and ("left" in command_lower or "right" in command_lower or 
                                             "half" in command_lower or "region" in command_lower):
                # Find features in region
                if "left" in command_lower:
                    region_features = query_engine.find_within_region((0, 0, 256, 512))
                elif "right" in command_lower:
                    region_features = query_engine.find_within_region((256, 0, 512, 512))
                else:
                    region_features = query_engine.find_within_region((0, 0, 512, 512))
                
                feature_ids = query_engine.get_feature_ids(region_features)
                result["queries"].append({
                    "type": "region",
                    "region": "left" if "left" in command_lower else "right" if "right" in command_lower else "all",
                    "results": feature_ids,
                    "count": len(feature_ids)
                })
            
            if result["queries"]:
                return result
            
        except (ImportError, AttributeError, KeyError, ValueError) as e:
            logger.warning(f"Spatial query handling failed: {e}")
        
        return None
    
    def _extract_reference_from_command(self, command_lower: str) -> Optional[str]:
        """Extract entity reference from command."""
        # Simple extraction - look for common patterns
        # "the dunes", "mountains", "the mountains"
        patterns = [
            r"the\s+(\w+)",  # "the dunes"
            r"(\w+)\s+on\s+the",  # "mountains on the"
            r"(\w+)\s+near",  # "mountains near"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                return match.group(1)
        
        return None
    
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
      "type": "mountain" | "hill" | "valley" | "dunes" | "mesa" | "plateau" | "cliff" | "canyon" | "slope" | "crater" | "ridge" | "ravine" | "volcano" | "pass" | "mound" | "basin" | "pinnacle" | "spur" | "terraces" | null,
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
      },
      "target_feature_ids": [number] | null (OPTIONAL - feature IDs resolved from scene graph references like "the dunes")
    }
  ]
}
""")
        
        # Add structured scene graph context if available
        if scene_state:
            scene_graph_context = self._generate_scene_graph_context(scene_state)
            if scene_graph_context:
                prompt_parts.append(scene_graph_context)
            
            # Also add basic scene context (backward compatibility)
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

REFERENCE RESOLUTION (Using Scene Graph):
- The scene graph above shows semantic entities with their labels and feature IDs
- When user says "the dunes", look up entity "the dunes" → use its Feature IDs
- When user says "make the mountains taller", find entity matching "mountains" → use its Feature IDs
- For modify/remove actions with references:
  * "the [entity]" → Use entity's feature_refs from scene graph
  * "[ordinal] [type]" → Use ordinal resolution (first=1st, last=most recent)
  * "[type]" → Use all features of that type
- When you see a reference, you can include a "target_feature_ids" field in the action:
  {
    "kind": "modify",
    "type": "mountain",
    "target_feature_ids": [4, 5],  // Optional: resolved from "the mountains"
    "modifiers": {"taller": true}
  }
- This helps the system know exactly which features to modify

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
- "remove the valley" → 1 action: [kind:"remove", type:"valley", count:1]

Examples with Scene Graph Context:
- User says "make the dunes taller" and scene graph shows entity "the dunes" with Feature IDs [1,2,3]:
  → [kind:"modify", type:"dunes", target_feature_ids:[1,2,3], modifiers:{taller:true}]
- User says "remove the mountains" and scene graph shows entity "two mountains" with Feature IDs [4,5]:
  → [kind:"remove", type:"mountain", target_feature_ids:[4,5]]
- User says "make the last mountain taller" (no entity, but scene graph shows mountains [4,5]):
  → [kind:"modify", type:"mountain", target_feature_ids:[5], modifiers:{taller:true}]
  (target_feature_ids is optional but helpful - system can resolve if not provided)""")
        
        return "\n\n".join(prompt_parts)
    
    def _generate_scene_graph_context(self, scene_state: Dict) -> Optional[str]:
        """
        Generate COMPACT scene graph context for LLM parsing.
        
        FIX: Truncated version to prevent context length exceeded errors.
        Only includes essential information needed for reference resolution.
        
        Args:
            scene_state: Current terrain state dictionary
            
        Returns:
            Formatted context string or None if no scene graph available
        """
        # Check if scene graph exists
        if "semantic_scene" not in scene_state:
            return None
        
        try:
            from .scene import TerrainSceneGraph, EntityManager, SceneGraphSerializer
            
            # Check if semantic_scene is valid
            semantic_scene = scene_state.get("semantic_scene", {})
            if not isinstance(semantic_scene, dict):
                return None
            
            # Load scene graph using serializer
            scene_graph = SceneGraphSerializer.from_dict(semantic_scene)
            
            manager = EntityManager(scene_graph)
            entities = manager.get_all_entities()
            
            if not entities:
                return None
            
            # SMART HYBRID APPROACH: Minimal context + spatial/attribute hints
            lines = ["\n=== SCENE ENTITIES ==="]
            
            # Limit to most recent 10 entities to prevent context overflow
            MAX_ENTITIES = 10
            recent_entities = entities[-MAX_ENTITIES:] if len(entities) > MAX_ENTITIES else entities
            
            if len(entities) > MAX_ENTITIES:
                lines.append(f"Showing {MAX_ENTITIES} most recent of {len(entities)} total entities:")
            
            # Get feature positions for spatial context (essential for "between", "near")
            for entity in recent_entities:
                # Get representative feature position (centroid of group)
                positions = []
                for fid in entity.feature_refs[:3]:  # Sample first 3 features
                    feature_node = scene_graph.find_feature_by_id(fid)
                    if feature_node:
                        x = feature_node.get_data("x")
                        y = feature_node.get_data("y")
                        if x is not None and y is not None:
                            positions.append((x, y))
                
                # Calculate centroid for spatial reference
                if positions:
                    avg_x = sum(p[0] for p in positions) // len(positions)
                    avg_y = sum(p[1] for p in positions) // len(positions)
                    # Determine region (left/center/right, top/center/bottom)
                    region_x = "left" if avg_x < 170 else ("center" if avg_x < 341 else "right")
                    region_y = "top" if avg_y < 170 else ("center" if avg_y < 341 else "bottom")
                    region = f"{region_y}-{region_x}" if region_y != "center" and region_x != "center" else (region_y if region_x == "center" else region_x)
                    spatial_info = f" @({avg_x},{avg_y}) {region}"
                else:
                    spatial_info = ""
                
                # Format: label → IDs (keywords) @position region
                keywords_str = f" ({', '.join(entity.keywords[:2])})" if entity.keywords else ""
                count_str = f" {len(entity.feature_refs)}×" if len(entity.feature_refs) > 1 else ""
                lines.append(f"  '{entity.label}' →{count_str} {entity.feature_refs[:5]}{keywords_str}{spatial_info}")
            
            # Summary
            type_counts = {}
            for entity in entities:
                type_counts[entity.type] = type_counts.get(entity.type, 0) + 1
            
            lines.append(f"\nTypes: {dict(type_counts)}")
            lines.append("Note: Use 'target_feature_ids' for precise targeting.\n")
            
            return "\n".join(lines)
            
        except (ImportError, AttributeError, KeyError) as e:
            logger.warning(f"Failed to generate scene graph context: {e}")
            return None
    
    def _generate_compact_tool_context(self) -> str:
        """
        Generate COMPACT tool context for LLM.
        
        FIX: Simplified version to prevent context length exceeded errors.
        Lists available feature types without detailed parameter information.
        """
        lines = ["\n=== AVAILABLE TERRAIN FEATURES ==="]
        
        # Just list feature types, no detailed parameters
        primitives = self.tool_registry.get_tools_by_category(ToolCategory.PRIMITIVE)
        feature_names = [tool.name for tool in primitives]
        lines.append(f"Types: {', '.join(feature_names)}")
        
        # Simplified parameter guidelines
        lines.append("\nQuick modifiers:")
        lines.append("  'tall/high' → height: 0.8-0.9, 'wide' → radius: 60-80")
        lines.append("  'deep' → depth: 0.7-0.9, 'steep' → steepness: 0.8-1.0\n")
        
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
                logger.debug(f"Missing or invalid count in action, defaulting to 1. Action: {action}")
            else:
                # Ensure count is an integer
                action["count"] = int(action["count"])
                if action["count"] < 1:
                    logger.warning(f"Invalid count {action['count']}, clamping to 1. Action: {action}")
                    action["count"] = 1
            
            if "position" not in action:
                action["position"] = {"region": None, "coords": None}
            if "modifiers" not in action:
                action["modifiers"] = {"taller": False, "deeper": False, "wider": False}
            
            # Handle target_feature_ids (optional field from LLM if it resolved references)
            if "target_feature_ids" in action:
                # Validate target_feature_ids is a list
                if not isinstance(action["target_feature_ids"], list):
                    action["target_feature_ids"] = []
                else:
                    # Ensure all are integers
                    action["target_feature_ids"] = [
                        int(fid) for fid in action["target_feature_ids"] 
                        if isinstance(fid, (int, float))
                    ]
            else:
                # Not provided - will be resolved later by reference resolver
                action["target_feature_ids"] = None
            
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
                logger.debug(f"Extracted count: {action['count']} for type: {action.get('type')}")
        
        return parsed
    
    def _fallback_parse(self, command: str) -> Dict:
        """Fallback to regex-based parsing if LLM fails."""
        # Import the old parser as fallback
        from ..terrain import parse_command
        return parse_command(command)

