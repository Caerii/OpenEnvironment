"""
Command parsing for terrain generation.

This module provides a single CommandParser class that handles:
1. LLM-based parsing (Cerebras API) for complex commands
2. Regex-based parsing as reliable fallback
3. Graceful degradation when LLM is unavailable

Design: Keep it simple - one class, clear flow, obvious behavior.
"""
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LLMParseError(Exception):
    """Raised when LLM parsing fails."""
    pass


class CommandParser:
    """
    Parse natural language commands into structured terrain actions.
    
    Strategy:
        1. Try LLM first (if available) - handles complex/ambiguous commands
        2. Fall back to regex - always works, handles simple patterns
    
    Returns: Dict with structure:
        {
            "actions": [
                {
                    "kind": "add" | "remove" | "modify",
                    "type": "mountain" | "valley" | ...,
                    "count": int,
                    "position": {"region": str, "coords": [x, y]},
                    "modifiers": {"taller": bool, "height_percent": float, ...}
                },
                ...
            ]
        }
    
    Example:
        parser = CommandParser()
        result = parser.parse("add three mountains in the center", context=state)
        actions = result["actions"]
    """
    
    def __init__(self):
        """Initialize parser. LLM is optional (gracefully disabled if no API key)."""
        self._llm_available = self._init_llm()
    
    def _init_llm(self) -> bool:
        """
        Try to initialize LLM client.
        
        Returns:
            True if LLM is available, False otherwise
        """
        try:
            api_key = os.getenv("CEREBRAS_API_KEY")
            if not api_key:
                logger.info("CEREBRAS_API_KEY not found - LLM parsing disabled, using regex only")
                return False
            
            from cerebras.cloud.sdk import Cerebras
            self._llm_client = Cerebras(api_key=api_key)
            self._llm_model = "llama3.1-8b"
            
            # Load tool registry for context-aware prompts
            try:
                from .semantic.tool_registry import get_tool_registry
                self._tool_registry = get_tool_registry()
            except ImportError:
                self._tool_registry = None
            
            logger.info("LLM parser initialized successfully")
            return True
            
        except ImportError as e:
            logger.info(f"Cerebras SDK not available: {e} - using regex parser only")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize LLM parser: {e} - using regex parser only")
            return False
    
    def parse(self, command: str, context: Optional[Dict] = None) -> Dict:
        """
        Parse a natural language command into structured actions.
        
        Args:
            command: Natural language command (e.g., "add three mountains")
            context: Optional terrain state for context-aware parsing
        
        Returns:
            Dictionary with "actions" key containing list of action dicts
        
        Examples:
            >>> parser.parse("add a mountain in the center")
            {"actions": [{"kind": "add", "type": "mountain", "count": 1, ...}]}
            
            >>> parser.parse("remove the valley")
            {"actions": [{"kind": "remove", "type": "valley", ...}]}
        """
        # Try LLM first if available
        if self._llm_available:
            try:
                return self._parse_with_llm(command, context)
            except LLMParseError as e:
                logger.warning(f"LLM parsing failed: {e}, falling back to regex parser")
                # Fall through to regex
        
        # Regex fallback (always works)
        return self._parse_with_regex(command)
    
    def _parse_with_llm(self, command: str, context: Optional[Dict]) -> Dict:
        """
        Parse using LLM (Cerebras API).
        
        Raises:
            LLMParseError: If LLM call fails or returns invalid response
        """
        try:
            # Check for spatial queries first
            from .core.spatial_queries import handle_spatial_query
            query_result = handle_spatial_query(command, context)
            if query_result:
                return query_result
            
            # Build context-aware system prompt
            system_prompt = self._build_llm_prompt(context)
            
            user_message = f"""Parse this terrain generation command:

"{command}"

Output only valid JSON, no additional text."""
            
            # Call LLM
            response = self._llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model=self._llm_model,
                stream=False,
                max_completion_tokens=4000,
                temperature=0.3,
                top_p=0.8,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            import json
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Normalize and validate
            return self._normalize_llm_response(parsed)
            
        except json.JSONDecodeError as e:
            raise LLMParseError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise LLMParseError(f"LLM call failed: {e}")
    
    def _handle_spatial_query_DEPRECATED(self, command: str, context: Optional[Dict]) -> Optional[Dict]:
        """
        Check if command is a spatial query (e.g., "find features near the dunes").
        
        Returns query result dict or None if not a query.
        """
        if not context or "semantic_scene" not in context:
            return None
        
        command_lower = command.lower()
        
        # Check for query keywords
        query_keywords = ["find", "show", "locate", "where", "what", "list"]
        if not any(keyword in command_lower for keyword in query_keywords):
            return None
        
        try:
            from .semantic.scene import SceneGraphSerializer, QueryEngine, ReferenceResolver
            
            # Load scene graph
            scene_graph = SceneGraphSerializer.from_dict(context["semantic_scene"])
            query_engine = QueryEngine(scene_graph)
            resolver = ReferenceResolver(scene_graph)
            
            result = {"queries": []}
            
            # Handle "near X" queries
            if "near" in command_lower:
                # Extract reference entity
                ref_match = re.search(r"near\s+(?:the\s+)?(\w+)", command_lower)
                if ref_match:
                    ref_text = ref_match.group(1)
                    ref_ids = resolver.resolve(ref_text)
                    if ref_ids:
                        nearby = query_engine.find_near_feature(ref_ids[0], radius=150)
                        feature_ids = query_engine.get_feature_ids(nearby)
                        result["queries"].append({
                            "type": "near",
                            "reference": ref_text,
                            "reference_feature_ids": [ref_ids[0]],
                            "results": feature_ids,
                            "count": len(feature_ids)
                        })
            
            # Handle "in region" queries
            elif any(word in command_lower for word in ["left", "right", "center"]):
                if "left" in command_lower:
                    region_features = query_engine.find_within_region((0, 0, 256, 512))
                    region_name = "left"
                elif "right" in command_lower:
                    region_features = query_engine.find_within_region((256, 0, 512, 512))
                    region_name = "right"
                else:
                    region_features = query_engine.find_within_region((0, 0, 512, 512))
                    region_name = "all"
                
                feature_ids = query_engine.get_feature_ids(region_features)
                result["queries"].append({
                    "type": "region",
                    "region": region_name,
                    "results": feature_ids,
                    "count": len(feature_ids)
                })
            
            if result["queries"]:
                return result
                
        except (ImportError, AttributeError, KeyError) as e:
            logger.debug(f"Spatial query handling failed: {e}")
        
        return None
    
    def _build_llm_prompt(self, context: Optional[Dict]) -> str:
        """Build context-aware system prompt for LLM."""
        prompt_parts = [
            "You are a terrain generation command parser.",
            "Parse natural language commands into structured JSON actions.",
            "",
            "Output format:",
            '{',
            '  "actions": [',
            '    {',
            '      "kind": "add" | "remove" | "modify",',
            '      "type": "mountain" | "hill" | "valley" | "dunes" | "canyon" | ...,',
            '      "count": 1,',
            '      "position": {"region": "center"},',
            '      "modifiers": {"taller": true}',
            '    }',
            '  ]',
            '}',
            "",
            "Available feature types:",
        ]
        
        # Add feature types from registry
        try:
            from .engine.feature_registry import FeatureRegistry
            feature_types = FeatureRegistry.get_registered_types()
            prompt_parts.append(", ".join(feature_types))
        except ImportError:
            prompt_parts.append("mountain, hill, valley, canyon, ridge, dunes, etc.")
        
        # Add tool registry context if available
        if self._tool_registry and context:
            try:
                tools_context = self._tool_registry.get_context_for_llm(context)
                if tools_context:
                    prompt_parts.extend(["", "Current scene context:", tools_context])
            except Exception:
                pass
        
        return "\n".join(prompt_parts)
    
    def _normalize_llm_response(self, parsed: Dict) -> Dict:
        """Normalize LLM response to ensure consistent structure."""
        if "actions" not in parsed:
            parsed["actions"] = []
        
        # Validate and normalize each action
        for action in parsed["actions"]:
            # Ensure required fields
            if "kind" not in action:
                action["kind"] = "add"
            if "type" not in action:
                logger.warning(f"Action missing type: {action}")
                action["type"] = None
            if "count" not in action or not isinstance(action["count"], (int, float)):
                action["count"] = 1
            if "position" not in action:
                action["position"] = {"region": "random"}
            if "modifiers" not in action:
                action["modifiers"] = {}
        
        return parsed
    
    def _parse_with_regex(self, command: str) -> Dict:
        """
        Parse using regex patterns (reliable fallback).
        
        This always succeeds - returns empty actions if nothing matches.
        """
        from .terrain import parse_command
        return parse_command(command)


# Convenience function for backward compatibility
def parse_terrain_command(command: str, context: Optional[Dict] = None) -> Dict:
    """
    Parse a terrain generation command.
    
    Convenience function that creates parser instance and calls parse().
    For repeated parsing, create a CommandParser instance directly.
    
    Args:
        command: Natural language command
        context: Optional terrain state for context
    
    Returns:
        Dict with "actions" list
    """
    parser = CommandParser()
    return parser.parse(command, context)

