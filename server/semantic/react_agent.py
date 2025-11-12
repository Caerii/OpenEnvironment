"""
ReAct (Reasoning + Acting) Agent for Multi-Turn Terrain Generation.

This module implements a ReAct-style agent that can reason through complex
terrain generation tasks by calling tools, gathering information, and
iteratively refining its understanding before generating final actions.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from cerebras.cloud.sdk import Cerebras

from .tools import (
    query_entities, get_feature_details, get_spatial_relationships, query_scene_summary,
    calculate_position, calculate_region_positions, get_region_bounds,
    resolve_reference, resolve_temporal_reference, resolve_attribute_filter,
    infer_feature_parameters, suggest_modification, validate_action
)

logger = logging.getLogger(__name__)


# Tool registry for the agent
AVAILABLE_TOOLS = {
    # Query tools
    "query_entities": {
        "function": query_entities,
        "description": "Search for entities by label, keyword, or type",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "label": "Filter by label (e.g., 'the mountains')",
            "keyword": "Filter by keyword (e.g., 'tall', 'steep')",
            "entity_type": "Filter by type ('feature' or 'group')",
            "limit": "Max results (default: 10)"
        }
    },
    "get_feature_details": {
        "function": get_feature_details,
        "description": "Get detailed attributes of specific features",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "feature_ids": "List of feature IDs to query"
        }
    },
    "get_spatial_relationships": {
        "function": get_spatial_relationships,
        "description": "Calculate spatial relationships (centroid, bounding_box, between, nearby, etc.)",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "reference_ids": "Feature IDs to use as reference",
            "relationship_type": "Type: centroid, between_position, north_of, south_of, nearby_positions, etc."
        }
    },
    "query_scene_summary": {
        "function": query_scene_summary,
        "description": "Get overall scene statistics and composition",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)"
        }
    },
    
    # Spatial calculation tools
    "calculate_position": {
        "function": calculate_position,
        "description": "Calculate position for spatial relationships",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "reference_ids": "Feature IDs for reference (optional)",
            "relationship": "Spatial relationship: near, between, north_of, south_of, etc.",
            "region": "Explicit region: left, center, right, top, bottom, etc.",
            "offset_distance": "Distance for directional offsets (default: 80)"
        }
    },
    "calculate_region_positions": {
        "function": calculate_region_positions,
        "description": "Generate multiple positions in a pattern",
        "parameters": {
            "count": "Number of positions",
            "scene_state": "Current scene state (provided automatically)",
            "reference_ids": "Feature IDs for reference point",
            "pattern": "Pattern: scattered, circular, line, grid",
            "radius": "Radius for pattern (default: 100)",
            "region": "Region for scattered pattern"
        }
    },
    "get_region_bounds": {
        "function": get_region_bounds,
        "description": "Get coordinate bounds for a region name",
        "parameters": {
            "region": "Region name (left, center, top-right, etc.)"
        }
    },
    
    # Reference resolution
    "resolve_reference": {
        "function": resolve_reference,
        "description": "Resolve natural language reference to feature IDs",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "reference": "Natural language reference (e.g., 'the mountains')"
        }
    },
    "resolve_temporal_reference": {
        "function": resolve_temporal_reference,
        "description": "Resolve time-based references (recent, last, etc.)",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "temporal_phrase": "Temporal phrase (e.g., 'recent', 'just added')"
        }
    },
    "resolve_attribute_filter": {
        "function": resolve_attribute_filter,
        "description": "Find entities matching attribute keywords",
        "parameters": {
            "scene_state": "Current scene state (provided automatically)",
            "keyword": "Attribute keyword (e.g., 'tall', 'steep')"
        }
    },
    
    # Inference tools
    "infer_feature_parameters": {
        "function": infer_feature_parameters,
        "description": "Suggest parameters based on user modifiers",
        "parameters": {
            "feature_type": "Type of feature",
            "user_modifiers": "List of modifiers (e.g., ['tall', 'steep'])",
            "position": "Position [x, y]"
        }
    },
    "suggest_modification": {
        "function": suggest_modification,
        "description": "Suggest how to modify features",
        "parameters": {
            "feature_ids": "Features to modify",
            "modification_type": "Type: taller, wider, deeper, etc.",
            "intensity": "Intensity: slightly, moderate, much"
        }
    },
    "validate_action": {
        "function": validate_action,
        "description": "Validate if proposed action is valid",
        "parameters": {
            "action": "Action dictionary to validate"
        }
    }
}


class ReActAgent:
    """
    ReAct Agent for multi-turn reasoning about terrain generation.
    
    The agent follows a Thought -> Action -> Observation loop:
    1. **Thought**: Reason about what information is needed
    2. **Action**: Call a tool to gather information
    3. **Observation**: Process tool result and update understanding
    4. Repeat until ready to generate final actions
    """
    
    def __init__(self, client: Cerebras, model: str):
        self.client = client
        self.model = model
        self.max_iterations = 5  # Prevent infinite loops
        
    def solve(self, command: str, scene_state: Dict) -> Dict:
        """
        Solve a terrain generation command using ReAct reasoning.
        
        Args:
            command: Natural language command
            scene_state: Current terrain state
            
        Returns:
            {
                "actions": List[Dict],  # Final actions to execute
                "reasoning_trace": List[Dict],  # Thought/Action/Observation history
                "iterations": int
            }
        """
        conversation_history = []
        reasoning_trace = []
        
        # Initial system prompt with tool descriptions
        system_prompt = self._build_system_prompt()
        
        # Initial user message
        user_message = f"""Task: Parse this terrain generation command and generate appropriate actions.

Command: "{command}"

You have access to tools to query the scene, calculate positions, and gather information.
Use the ReAct pattern: Thought -> Action -> Observation -> repeat until ready to generate final actions.

Format your response as JSON:
{{
  "thought": "Your reasoning about what to do next",
  "action": {{
    "tool": "tool_name",
    "parameters": {{...}}
  }},
  "ready": false
}}

When you have all the information needed, set "ready": true and include "final_actions": [...]
"""
        
        conversation_history.append({"role": "system", "content": system_prompt})
        conversation_history.append({"role": "user", "content": user_message})
        
        # ReAct loop
        for iteration in range(self.max_iterations):
            try:
                # Get LLM response
                response = self.client.chat.completions.create(
                    messages=conversation_history,
                    model=self.model,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                parsed = json.loads(content)
                
                thought = parsed.get("thought", "")
                action = parsed.get("action")
                ready = parsed.get("ready", False)
                
                logger.info(f"ReAct iteration {iteration + 1}: {thought[:100]}...")
                
                reasoning_trace.append({
                    "iteration": iteration + 1,
                    "thought": thought,
                    "action": action,
                    "ready": ready
                })
                
                # Check if ready to generate final actions
                if ready:
                    final_actions = parsed.get("final_actions", parsed.get("actions", []))
                    return {
                        "actions": final_actions,
                        "reasoning_trace": reasoning_trace,
                        "iterations": iteration + 1
                    }
                
                # Execute tool action
                if action and "tool" in action:
                    tool_name = action["tool"]
                    tool_params = action.get("parameters", {})
                    
                    observation = self._execute_tool(
                        tool_name,
                        tool_params,
                        scene_state
                    )
                    
                    reasoning_trace[-1]["observation"] = observation
                    
                    # Add observation to conversation
                    observation_message = f"""Observation from {tool_name}:
{json.dumps(observation, indent=2)}

Continue reasoning or set "ready": true if you have enough information."""
                    
                    conversation_history.append({"role": "assistant", "content": content})
                    conversation_history.append({"role": "user", "content": observation_message})
                else:
                    # No action specified, prompt for next step
                    conversation_history.append({"role": "assistant", "content": content})
                    conversation_history.append({"role": "user", "content": "Please specify a tool action or set ready=true."})
                    
            except Exception as e:
                logger.error(f"ReAct iteration {iteration + 1} failed: {e}", exc_info=True)
                # Fallback: try to generate actions anyway
                break
        
        # Max iterations reached or error - try to extract any actions from last response
        logger.warning(f"ReAct max iterations reached ({self.max_iterations})")
        return {
            "actions": [],
            "reasoning_trace": reasoning_trace,
            "iterations": self.max_iterations,
            "error": "Max iterations reached"
        }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with tool descriptions."""
        prompt_parts = [
            "You are an intelligent terrain generation agent with ReAct reasoning capabilities.",
            "",
            "You have access to the following tools:",
            ""
        ]
        
        for tool_name, tool_info in AVAILABLE_TOOLS.items():
            prompt_parts.append(f"## {tool_name}")
            prompt_parts.append(f"Description: {tool_info['description']}")
            prompt_parts.append("Parameters:")
            for param, desc in tool_info['parameters'].items():
                prompt_parts.append(f"  - {param}: {desc}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Use the ReAct pattern:",
            "1. Think about what information you need",
            "2. Call a tool to get that information",
            "3. Observe the result",
            "4. Repeat until you have enough information",
            "5. Generate final actions",
            "",
            "Output format:",
            '{',
            '  "thought": "Reasoning about next step",',
            '  "action": {"tool": "tool_name", "parameters": {...}},',
            '  "ready": false',
            '}',
            "",
            "When ready to generate actions:",
            '{',
            '  "thought": "I have all the information I need",',
            '  "ready": true,',
            '  "final_actions": [{"kind": "add", "type": "mountain", ...}]',
            '}'
        ])
        
        return "\n".join(prompt_parts)
    
    def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict,
        scene_state: Dict
    ) -> Dict:
        """Execute a tool and return its result."""
        try:
            if tool_name not in AVAILABLE_TOOLS:
                return {"error": f"Unknown tool: {tool_name}"}
            
            tool_func = AVAILABLE_TOOLS[tool_name]["function"]
            
            # Inject scene_state for tools that need it
            if "scene_state" in AVAILABLE_TOOLS[tool_name]["parameters"]:
                parameters["scene_state"] = scene_state
            
            result = tool_func(**parameters)
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}", exc_info=True)
            return {"error": str(e)}

