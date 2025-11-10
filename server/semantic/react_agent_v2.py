"""
ReAct Agent V2 - Using Proper Cerebras Tool Calling.

This version uses Cerebras SDK's native tool calling support instead of JSON parsing.
Much more reliable and efficient!
"""

import json
import logging
from typing import Dict, List, Optional, Any
from cerebras.cloud.sdk import Cerebras

from .context import (
    summarize_scene,
    summarize_recent_actions,
    infer_active_aesthetic_goals,
)
from .prompts.react import (
    build_system_prompt as build_react_system_prompt,
    build_user_prompt as build_react_user_prompt,
)
from .tools.executor import ToolExecutor
from .tools.schema import get_all_tool_schemas

logger = logging.getLogger(__name__)


class ReActAgentV2:
    """
    ReAct agent using proper function calling.
    
    Key improvements over V1:
    - Uses Cerebras SDK's native `tools` parameter
    - Handles tool_calls in response properly
    - Standardized tool output format
    - Better error handling
    - Conversation history management
    """
    
    def __init__(
        self,
        client: Cerebras,
        model: str = "llama3.1-8b",
        max_iterations: int = 5,
        max_tool_calls_per_iteration: int = 3
    ):
        """
        Initialize ReAct agent.
        
        Args:
            client: Cerebras client
            model: Model name
            max_iterations: Maximum reasoning iterations
            max_tool_calls_per_iteration: Max parallel tool calls
        """
        self.client = client
        self.model = model
        self.max_iterations = max_iterations
        self.max_tool_calls_per_iteration = max_tool_calls_per_iteration
        
        # Initialize tool executor
        self.executor = ToolExecutor()
        
        # Get tool schemas for LLM
        self.tool_schemas = get_all_tool_schemas(self.executor.get_tool_functions())
        
        logger.info(f"ReActAgentV2 initialized with {len(self.tool_schemas)} tools")
    
    def solve(
        self,
        user_command: str,
        scene_state: Dict[str, Any],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Solve a terrain generation task using ReAct reasoning.
        
        Args:
            user_command: Natural language command
            scene_state: Current scene state
            temperature: LLM temperature
            
        Returns:
            Dict with actions, reasoning trace, and metadata
        """
        logger.info(f"ReAct solving: {user_command[:100]}...")
        
        scene_state = scene_state or {}

        scene_summary = summarize_scene(scene_state)
        recent_actions_summary = summarize_recent_actions(scene_state.get("action_history", []))
        aesthetic_goals = infer_active_aesthetic_goals(user_command, scene_state)

        system_prompt = self._build_system_prompt(scene_summary, recent_actions_summary, aesthetic_goals)
        user_prompt = self._build_user_prompt(
            user_command,
            scene_state,
            scene_summary,
            recent_actions_summary,
            aesthetic_goals,
        )

        conversation = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]
        
        # Track iterations
        iteration = 0
        total_tool_calls = 0
        
        # ReAct loop
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"ReAct iteration {iteration}/{self.max_iterations}")
            
            # Inject iteration urgency after iteration 3
            if iteration >= 3:
                urgency_msg = f"""⚠️ ITERATION {iteration}/{self.max_iterations}

You are running low on iterations! Status:
- Tools called so far: {total_tool_calls}
- Iterations remaining: {self.max_iterations - iteration + 1}

If you have coordinates (x, y), generate actions NOW.
If you need ONE more critical piece of information, use ONE tool, then generate.
Do NOT keep exploring - it's time to commit to a solution."""
                
                conversation.append({"role": "user", "content": urgency_msg})
                logger.info(f"Injected urgency message at iteration {iteration}")
            
            try:
                # Call LLM with tools
                response = self.client.chat.completions.create(
                    messages=conversation,
                    model=self.model,
                    tools=self.tool_schemas,  # ✅ Use proper tool calling!
                    tool_choice="auto",  # Let LLM decide
                    parallel_tool_calls=True,  # Enable parallel execution
                    temperature=temperature,
                    max_completion_tokens=4000
                )
                
                # Get assistant message
                assistant_message = response.choices[0].message
                
                # Add to conversation
                conversation.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": assistant_message.tool_calls if assistant_message.tool_calls else None
                })
                
                # Check if LLM wants to call tools
                if assistant_message.tool_calls:
                    logger.info(f"LLM requested {len(assistant_message.tool_calls)} tool calls")
                    
                    # Limit tool calls
                    tool_calls = assistant_message.tool_calls[:self.max_tool_calls_per_iteration]
                    total_tool_calls += len(tool_calls)
                    
                    # Execute tools and add results to conversation
                    tool_results = self.executor.execute_tool_calls(tool_calls, scene_state)
                    conversation.extend(tool_results)
                    
                    # Continue to next iteration
                    continue
                
                # No tool calls - LLM is done reasoning, extract actions
                logger.info("LLM finished reasoning, extracting actions...")
                
                # Parse final response for actions
                actions = self._extract_actions_from_response(assistant_message.content)
                
                if actions:
                    logger.info(f"ReAct completed in {iteration} iterations with {len(actions)} actions")
                    return {
                        "actions": actions,
                        "iterations": iteration,
                        "total_tool_calls": total_tool_calls,
                        "reasoning_trace": self._build_reasoning_trace(conversation),
                        "success": True
                    }
                else:
                    logger.warning("LLM finished but no actions generated")
                    # Try one more iteration with explicit prompt
                    conversation.append({
                        "role": "user",
                        "content": "Please provide the final terrain actions in JSON format."
                    })
                    continue
                    
            except Exception as e:
                logger.error(f"ReAct iteration {iteration} failed: {e}", exc_info=True)
                return {
                    "actions": [],
                    "iterations": iteration,
                    "total_tool_calls": total_tool_calls,
                    "error": str(e),
                    "success": False
                }
        
        # Max iterations reached
        logger.warning(f"ReAct reached max iterations ({self.max_iterations}) without completing")
        
        # Try to extract actions from last message
        last_message = conversation[-1]
        if last_message["role"] == "assistant":
            actions = self._extract_actions_from_response(last_message["content"])
        else:
            actions = []
        
        return {
            "actions": actions,
            "iterations": iteration,
            "total_tool_calls": total_tool_calls,
            "reasoning_trace": self._build_reasoning_trace(conversation),
            "success": len(actions) > 0
        }
    
    def _build_system_prompt(
        self,
        scene_summary: str,
        recent_actions: str,
        aesthetic_goals: List[str],
    ) -> str:
        """Build system prompt for ReAct agent."""
        return build_react_system_prompt(scene_summary, recent_actions, aesthetic_goals)
    
    def _build_user_prompt(
        self,
        command: str,
        scene_state: Dict[str, Any],
        scene_summary: str,
        recent_actions: str,
        aesthetic_goals: List[str],
    ) -> str:
        feature_count = len(scene_state.get("features", []))
        entity_count = len(scene_state.get("semantic_scene", {}).get("entities", []))
        seed = scene_state.get("seed")
        return build_react_user_prompt(
            command,
            scene_summary,
            recent_actions,
            aesthetic_goals,
            feature_count,
            entity_count,
            seed,
        )
    
    def _extract_actions_from_response(self, content: Optional[str]) -> List[Dict]:
        """
        Extract actions from LLM response (robust multi-strategy).
        
        Handles:
        - JSON in ```json blocks
        - Multiple JSON objects (picks the one with "actions")
        - Raw JSON without code blocks
        - Text before/after JSON
        """
        if not content:
            return []
        
        import re
        
        try:
            # Strategy 1: Find ```json blocks with regex
            json_blocks = re.findall(r'```json\s*\n?(.*?)\n?```', content, re.DOTALL)
            
            for block in json_blocks:
                # Block might contain multiple JSON objects - try each line
                lines = block.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('//') or line.startswith('#'):
                        continue
                    
                    try:
                        parsed = json.loads(line)
                        if "actions" in parsed:
                            logger.debug(f"Found actions in JSON block line")
                            return parsed["actions"]
                    except json.JSONDecodeError:
                        continue  # Try next line
                
                # If no line worked, try the whole block
                try:
                    parsed = json.loads(block.strip())
                    if "actions" in parsed:
                        logger.debug(f"Found actions in full JSON block")
                        return parsed["actions"]
                    elif isinstance(parsed, list):
                        logger.debug(f"Found action list directly")
                        return parsed
                except json.JSONDecodeError:
                    continue  # Try next block
            
            # Strategy 2: Find generic ``` blocks
            if not json_blocks:
                code_blocks = re.findall(r'```\s*\n?(.*?)\n?```', content, re.DOTALL)
                for block in code_blocks:
                    try:
                        parsed = json.loads(block.strip())
                        if "actions" in parsed:
                            logger.debug(f"Found actions in code block")
                            return parsed["actions"]
                    except json.JSONDecodeError:
                        continue
            
            # Strategy 3: Find raw JSON with "actions" key using regex
            json_match = re.search(r'\{[^{}]*"actions"[^{}]*\[[^\]]*\][^{}]*\}', content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    parsed = json.loads(json_str)
                    if "actions" in parsed:
                        logger.debug(f"Found actions in raw JSON")
                        return parsed["actions"]
                except json.JSONDecodeError:
                    pass
            
            # Strategy 4: Find ANY JSON object and check for actions
            json_objects = re.findall(r'\{[^{}]+\}', content)
            for obj_str in json_objects:
                try:
                    parsed = json.loads(obj_str)
                    if "actions" in parsed:
                        logger.debug(f"Found actions in extracted JSON object")
                        return parsed["actions"]
                except json.JSONDecodeError:
                    continue
            
            # No actions found
            logger.warning(f"No actions found in response (tried 4 strategies)")
            logger.debug(f"Response content: {content[:300]}...")
            return []
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
            logger.debug(f"Content was: {content[:200]}...")
            return []
        except Exception as e:
            logger.error(f"Error extracting actions: {e}", exc_info=True)
            return []
    
    def _build_reasoning_trace(self, conversation: List[Dict]) -> List[str]:
        """Build human-readable reasoning trace from conversation."""
        trace = []
        
        for msg in conversation:
            role = msg["role"]
            
            if role == "system":
                continue
            elif role == "user":
                trace.append(f"USER: {msg['content'][:100]}...")
            elif role == "assistant":
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls")
                
                if tool_calls:
                    tool_names = [tc.function.name for tc in tool_calls]
                    trace.append(f"ASSISTANT: Calling tools: {', '.join(tool_names)}")
                elif content:
                    trace.append(f"ASSISTANT: {content[:150]}...")
            elif role == "tool":
                tool_name = msg.get("name", "unknown")
                result = json.loads(msg["content"])
                success = result.get("success", False)
                trace.append(f"TOOL [{tool_name}]: {'✓' if success else '✗'}")
        
        return trace

