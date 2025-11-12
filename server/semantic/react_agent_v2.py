"""ReAct Agent V2 - compact prompt orchestration with narrative-first workflow."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .context import (
    summarize_scene,
    summarize_recent_actions,
    infer_active_aesthetic_goals,
)
from .prompt_profiles import PROMPT_PROFILES
from .prompts.react import (
    build_system_prompt as build_react_system_prompt,
    build_user_prompt as build_react_user_prompt,
)
from .llm.clients import LLMClient
from .tools.executor import ToolExecutor
from .tools.schema import get_all_tool_schemas

logger = logging.getLogger(__name__)


class ReActAgentV2:
    """
    ReAct agent using proper function calling.
    
    Key improvements over V1:
    - Works with multiple LLM providers via tool-calling APIs
    - Handles tool_calls in response properly
    - Standardized tool output format
    - Better error handling
    - Conversation history management
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        max_iterations: Optional[int] = None,
        max_tool_calls_per_iteration: int = 3,
        prompt_profile: str = "compact",
    ):
        """
        Initialize ReAct agent.
        
        Args:
            llm_client: Provider-agnostic LLM client
            max_iterations: Maximum reasoning iterations
            max_tool_calls_per_iteration: Max parallel tool calls
            prompt_profile: Prompt budget profile (compact/standard/extended)
        """
        self.llm_client = llm_client
        self.prompt_profile = prompt_profile if prompt_profile in PROMPT_PROFILES else "compact"
        self.prompt_config = PROMPT_PROFILES[self.prompt_profile]
        self.max_iterations = max_iterations or int(self.prompt_config["max_iterations"])
        self.max_tool_calls_per_iteration = max_tool_calls_per_iteration
        self.max_completion_tokens = int(self.prompt_config["max_completion_tokens"])

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

        # STEP 1: Extract narrative EARLY and store constraints
        narrative = self._extract_narrative(user_command, scene_state)
        if narrative:
            scene_state["_narrative"] = self._narrative_to_constraints(narrative)
            scene_state["_narrative_meta"] = {
                "archetype": narrative.archetype.name,
                "story": narrative.story,
                "aesthetic_goals": [g.value for g in narrative.aesthetic_goals],
                "mood": narrative.mood,
                "focal_type": narrative.hero_feature_type,
                "supporting_types": narrative.supporting_feature_types,
                "accent_types": narrative.accent_feature_types,
            }
            logger.info(f"Narrative extracted: archetype={narrative.archetype.name}, goals={[g.value for g in narrative.aesthetic_goals]}")

        cfg = self.prompt_config

        scene_summary = summarize_scene(
            scene_state,
            max_chars=int(cfg["scene_max_chars"]),
        )
        recent_actions_summary = summarize_recent_actions(
            scene_state.get("action_history", []),
            limit=int(cfg["max_history"]),
            max_chars=int(cfg["actions_max_chars"]),
        )
        aesthetic_goals = infer_active_aesthetic_goals(
            user_command,
            scene_state,
            limit=int(cfg["goal_limit"]),
        )

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
            if iteration >= max(2, self.max_iterations - 1):
                remaining = self.max_iterations - iteration + 1
                urgency_msg = (
                    f"Reminder: {remaining} iteration(s) left. Call the narrative tool or return actions now."
                )
                conversation.append({"role": "user", "content": urgency_msg})
                logger.info("Injected compact urgency message")
            
            try:
                # Call LLM with tools
                response = self.llm_client.chat_with_tools(
                    messages=conversation,
                    tools=self.tool_schemas,
                    tool_choice="auto",
                    temperature=temperature,
                    top_p=None,
                    max_completion_tokens=self.max_completion_tokens,
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

                    narrative_actions = self._check_narrative_shortcut(tool_results)
                    if narrative_actions:
                        logger.info(
                            "Narrative tool succeeded during ReAct iteration; evaluating quality..."
                        )
                        
                        # Evaluate and refine quality
                        refined_actions, quality_info = self._evaluate_and_refine(
                            narrative_actions, scene_state, max_refinement_iterations=5
                        )
                        
                        result_payload = {
                            "actions": refined_actions,
                            "iterations": iteration,
                            "total_tool_calls": total_tool_calls,
                            "reasoning_trace": self._build_reasoning_trace(conversation),
                            "quality_info": quality_info,
                            "success": True,
                        }
                        self._log_session(conversation, result_payload, user_command)
                        return result_payload
                    
                    # Continue to next iteration
                    continue
                
                # No tool calls - LLM is done reasoning, extract actions
                logger.info("LLM finished reasoning, extracting actions...")
                
                # Parse final response for actions
                actions = self._extract_actions_from_response(assistant_message.content)
                
                if actions:
                    logger.info(f"ReAct completed in {iteration} iterations with {len(actions)} actions")
                    
                    # Evaluate and refine quality if needed
                    refined_actions, quality_info = self._evaluate_and_refine(
                        actions, scene_state, max_refinement_iterations=5
                    )
                    
                    result_payload = {
                        "actions": refined_actions,
                        "iterations": iteration,
                        "total_tool_calls": total_tool_calls,
                        "reasoning_trace": self._build_reasoning_trace(conversation),
                        "quality_info": quality_info,
                        "success": True,
                    }
                    self._log_session(conversation, result_payload, user_command)
                    return result_payload
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
                result_payload = {
                    "actions": [],
                    "iterations": iteration,
                    "total_tool_calls": total_tool_calls,
                    "error": str(e),
                    "success": False
                }
                self._log_session(conversation, result_payload, user_command)
                return result_payload
        
        # Max iterations reached
        logger.warning(f"ReAct reached max iterations ({self.max_iterations}) without completing")
        
        # Try to extract actions from last message
        last_message = conversation[-1]
        if last_message["role"] == "assistant":
            actions = self._extract_actions_from_response(last_message["content"])
        else:
            actions = []
        
        # Evaluate and refine quality if we have actions
        quality_info = None
        if actions:
            actions, quality_info = self._evaluate_and_refine(
                actions, scene_state, max_refinement_iterations=3
            )
        
        result_payload = {
            "actions": actions,
            "iterations": iteration,
            "total_tool_calls": total_tool_calls,
            "reasoning_trace": self._build_reasoning_trace(conversation),
            "quality_info": quality_info,
            "success": len(actions) > 0
        }
        self._log_session(conversation, result_payload, user_command)
        return result_payload
    
    def _evaluate_and_refine(
        self,
        actions: List[Dict[str, Any]],
        scene_state: Dict[str, Any],
        max_refinement_iterations: int = 5,
        quality_threshold: float = 0.8
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Evaluate terrain quality and refine if below threshold.
        
        Args:
            actions: Initial actions to evaluate
            scene_state: Current scene state
            max_refinement_iterations: Maximum refinement attempts
            quality_threshold: Target quality score (0.0-1.0)
        
        Returns:
            Tuple of (refined_actions, quality_info)
        """
        logger.info(f"Evaluating quality for {len(actions)} actions (threshold={quality_threshold})")
        
        quality_info = {
            "initial_score": None,
            "final_score": None,
            "refinement_iterations": 0,
            "refinements_applied": [],
        }
        
        current_actions = actions
        
        # Evaluate initial quality
        try:
            eval_result = self.executor.execute_tool(
                "evaluate_terrain_quality",
                {"actions": current_actions, "render_preview": True},
                scene_state
            )
            
            if eval_result.get("success"):
                eval_data = eval_result.get("data", {})
                initial_score = eval_data.get("overall_score", 0.0)
                quality_info["initial_score"] = initial_score
                quality_info["warnings"] = eval_data.get("warnings", [])
                quality_info["composition_score"] = eval_data.get("composition_score", 0.0)
                quality_info["texture_score"] = eval_data.get("texture_score", 0.0)
                
                logger.info(f"Initial quality score: {initial_score:.3f}")
                
                # Refine if below threshold
                if initial_score < quality_threshold and max_refinement_iterations > 0:
                    logger.info(f"Quality below threshold ({initial_score:.3f} < {quality_threshold}), refining...")
                    
                    for refine_iter in range(max_refinement_iterations):
                        warnings = eval_data.get("warnings", [])
                        if not warnings:
                            logger.info("No warnings to address, stopping refinement")
                            break
                        
                        # Refine based on warnings
                        refine_result = self.executor.execute_tool(
                            "refine_composition",
                            {
                                "actions": current_actions,
                                "quality_warnings": warnings,
                                "max_refinements": 3
                            },
                            scene_state
                        )
                        
                        if refine_result.get("success"):
                            refine_data = refine_result.get("data", {})
                            current_actions = refine_data.get("refined_actions", current_actions)
                            changes = refine_data.get("changes_made", [])
                            quality_info["refinements_applied"].extend(changes)
                            quality_info["refinement_iterations"] += 1
                            
                            logger.info(f"Refinement {refine_iter + 1}: {len(changes)} changes applied")
                            
                            # Re-evaluate
                            eval_result = self.executor.execute_tool(
                                "evaluate_terrain_quality",
                                {"actions": current_actions, "render_preview": True},
                                scene_state
                            )
                            
                            if eval_result.get("success"):
                                eval_data = eval_result.get("data", {})
                                new_score = eval_data.get("overall_score", 0.0)
                                logger.info(f"Quality after refinement {refine_iter + 1}: {new_score:.3f}")
                                
                                # Stop if we've reached threshold or quality decreased
                                if new_score >= quality_threshold:
                                    logger.info(f"Quality threshold reached: {new_score:.3f} >= {quality_threshold}")
                                    break
                                elif new_score < initial_score * 0.9:  # Quality dropped significantly
                                    logger.warning("Quality decreased after refinement, reverting")
                                    current_actions = actions
                                    break
                        else:
                            logger.warning(f"Refinement failed: {refine_result.get('error')}")
                            break
                    
                    # Final evaluation
                    eval_result = self.executor.execute_tool(
                        "evaluate_terrain_quality",
                        {"actions": current_actions, "render_preview": True},
                        scene_state
                    )
                    
                    if eval_result.get("success"):
                        eval_data = eval_result.get("data", {})
                        quality_info["final_score"] = eval_data.get("overall_score", 0.0)
                        quality_info["final_warnings"] = eval_data.get("warnings", [])
                else:
                    quality_info["final_score"] = initial_score
                    logger.info(f"Quality meets threshold: {initial_score:.3f} >= {quality_threshold}")
            else:
                logger.warning(f"Quality evaluation failed: {eval_result.get('error')}")
        
        except Exception as e:
            logger.error(f"Quality evaluation/refinement error: {e}", exc_info=True)
            # Return original actions if evaluation fails
            current_actions = actions
        
        # Log quality history for tracking improvements over time
        if quality_info and quality_info.get("initial_score") is not None:
            self._log_quality_history(quality_info)
        
        return current_actions, quality_info
    
    def _log_quality_history(self, quality_info: Dict[str, Any]) -> None:
        """Log quality metrics to history file for progress tracking."""
        import os
        from pathlib import Path
        import json
        from datetime import datetime
        
        try:
            history_path = Path(os.environ.get("QUALITY_HISTORY_FILE", "logs/quality_history.jsonl"))
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "initial_score": quality_info.get("initial_score"),
                "final_score": quality_info.get("final_score"),
                "composition_score": quality_info.get("composition_score"),
                "texture_score": quality_info.get("texture_score"),
                "refinement_iterations": quality_info.get("refinement_iterations", 0),
                "refinements_applied": quality_info.get("refinements_applied", []),
                "improvement": (
                    quality_info.get("final_score", 0) - quality_info.get("initial_score", 0)
                    if quality_info.get("initial_score") is not None and quality_info.get("final_score") is not None
                    else None
                ),
                "improvement_pct": (
                    ((quality_info.get("final_score", 0) - quality_info.get("initial_score", 0)) / quality_info.get("initial_score", 1) * 100)
                    if quality_info.get("initial_score") is not None and quality_info.get("initial_score") > 0
                    else None
                ),
            }
            
            with history_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(entry) + "\n")
            
            logger.debug(f"Logged quality history: {entry.get('initial_score')} → {entry.get('final_score')}")
        except Exception as exc:
            logger.warning(f"Failed to log quality history: {exc}")
    
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

    def _log_session(self, conversation: List[Dict[str, Any]], result: Dict[str, Any], command: str) -> None:
        if not self.prompt_config.get("log_sessions", False):
            return

        try:
            log_dir = Path(__file__).resolve().parents[2] / "logs" / "react_sessions"
            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            status = "success" if result.get("success") else "error"
            payload = {
                "timestamp": timestamp,
                "command": command,
                "status": status,
                "result": {
                    k: v for k, v in result.items() if k != "reasoning_trace"
                },
                "reasoning_trace": result.get("reasoning_trace", []),
                "conversation": [self._serialize_message(msg) for msg in conversation],
            }

            log_path = log_dir / f"{timestamp}_{status}.json"
            with log_path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.debug(f"Failed to log ReAct session: {exc}")

    def _serialize_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            k: v for k, v in msg.items() if k not in {"tool_calls"}
        }
        tool_calls = msg.get("tool_calls") or []
        if tool_calls:
            serialized = []
            for tc in tool_calls:
                function = getattr(tc, "function", None)
                serialized.append(
                    {
                        "id": getattr(tc, "id", None),
                        "type": getattr(tc, "type", None),
                        "function": {
                            "name": getattr(function, "name", None),
                            "arguments": getattr(function, "arguments", None),
                        },
                    }
                )
            data["tool_calls"] = serialized
        return data

    def _extract_narrative(self, command: str, scene_state: Dict[str, Any]) -> Optional[Any]:
        """Extract narrative from command early in the solve process."""
        try:
            # Handle both relative and absolute imports
            try:
                from ..narrative.narrative_dev import develop_terrain_narrative
            except ImportError:
                import sys
                from pathlib import Path
                server_dir = Path(__file__).parent.parent.parent
                if str(server_dir) not in sys.path:
                    sys.path.insert(0, str(server_dir))
                from semantic.narrative.narrative_dev import develop_terrain_narrative
            
            narrative = develop_terrain_narrative(command, scene_state)
            return narrative
        except Exception as e:
            logger.warning(f"Failed to extract narrative: {e}", exc_info=True)
            return None
    
    def _narrative_to_constraints(self, narrative: Any) -> Dict[str, Any]:
        """Convert TerrainNarrative to constraint dictionary for tools."""
        archetype = narrative.archetype
        
        constraints = {
            "archetype": archetype.name,
            "aesthetic_goals": [g.value for g in narrative.aesthetic_goals],
            
            # Spatial patterns
            "spatial_patterns": {
                "clustering_tendency": archetype.clustering_tendency,
                "directional_alignment": archetype.directional_alignment,
                "scale_bias": archetype.scale_bias,
                "smoothness_bias": archetype.smoothness_bias,
            },
            
            # Feature preferences
            "feature_preferences": {
                "primary": archetype.primary_features,
                "secondary": archetype.secondary_features,
                "accent": archetype.accent_features,
                "hero_type": narrative.hero_feature_type,
                "supporting_types": narrative.supporting_feature_types,
                "accent_types": narrative.accent_feature_types,
            },
            
            # Texture preferences
            "texture_preferences": archetype.preferred_textures.copy(),
            
            # Composition rules
            "composition_rules": {
                "focal_bias": narrative.focal_point_bias,
                "depth_layers": narrative.depth_layers_needed,
                "negative_space": narrative.negative_space_importance,
            },
            
            # Height/scale constraints
            "height_range": archetype.height_range,
            
            # Environmental
            "wind_direction": narrative.wind_direction,
            "water_flow_direction": narrative.water_flow_direction,
            "climate": narrative.climate,
        }
        
        return constraints

    def _check_narrative_shortcut(self, tool_messages: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        for message in tool_messages:
            if message.get("role") != "tool":
                continue
            if message.get("name") != "generate_narrative_composition":
                continue
            content = message.get("content")
            if not content:
                continue
            try:
                payload = json.loads(content)
                data = payload.get("data", {})
                if payload.get("success") and data.get("actions"):
                    return data["actions"]
            except json.JSONDecodeError:
                continue
        return None

