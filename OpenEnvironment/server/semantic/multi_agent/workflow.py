"""Multi-agent terrain design workflow orchestrated with AG2."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Mapping

# Apply Together.AI patch BEFORE importing autogen
from .together_patch import patch_together_client
_patch_applied = patch_together_client()

try:  # pragma: no cover - optional dependency for testing environments
    from autogen import ConversableAgent, UserProxyAgent, register_function
    from autogen.agentchat import run_group_chat
    from autogen.agentchat.group.patterns import AutoPattern
except ImportError:  # pragma: no cover
    ConversableAgent = None  # type: ignore
    UserProxyAgent = None  # type: ignore
    register_function = None  # type: ignore
    run_group_chat = None  # type: ignore
    AutoPattern = None  # type: ignore

from .config import build_llm_config
from .tools import (
    generate_scene_plan,
    evaluate_scene_actions,
    score_scene_plan_visual,
)

logger = logging.getLogger(__name__)

if _patch_applied:
    logger.debug("Applied Together.AI role alternation patch")
else:
    logger.debug("Together.AI patch not available (may not be using Together provider)")

ARTIST_PROMPT = (
    "You are a master terrain artist specialising in geological storytelling.\n"
    "Workflow for every round:\n"
    "1. Reflect on the user brief and latest critique; extract 2-3 geological goals.\n"
    "2. Outline a concise rationale (<=3 bullet points) connecting the brief to terrain choices.\n"
    "3. CALL `generate_scene_plan` exactly once. Provide arguments as JSON with keys "
    "`command`, `critique`, and `scene_state` (use null when absent).\n"
    "4. After the tool response, summarise how the actions realise the goals.\n"
    "Use vivid but precise language; never fabricate action JSON yourself."
)

CRITIC_RESPONSE_SCHEMA = (
    "{\n"
    '  "strengths": ["Highlight what works and why"],\n'
    '  "issues": ["Specific problems with impact assessment"],\n'
    '  "priority_recommendations": ["Ordered list of revisions to attempt next"],\n'
    '  "blocking": true | false,\n'
    '  "required_focus": ["Key aesthetic or traversal objectives to emphasise next round"]\n'
    "}"
)

CRITIC_PROMPT = (
    "You are a meticulous art director and terrain traversal expert.\n"
    "Analyse the latest proposal using the provided actions, heuristics, texture_metrics, and quality_rubric summary.\n"
    "Reference concrete geological and aesthetic principles.\n"
    "Respond STRICTLY as minified JSON matching:\n"
    f"{CRITIC_RESPONSE_SCHEMA}\n"
    "Use rubric warnings to justify recommendations. Set `blocking` true only when the plan fundamentally fails the brief."
)

INTEGRATOR_FINAL_SCHEMA = (
    "{\n"
    '  "actions": [...],\n'
    '  "notes": "Concise explanation of final design",\n'
    '  "assets": {\n'
    '    "heightmap": "path/to/height.png",\n'
    '    "splatmap": "path/to/splat.png"\n'
    "  },\n"
    '  "quality": {\n'
    '    "heuristics": {...},\n'
    '    "texture_metrics": {...},\n'
    '    "quality_rubric": {...},\n'
    '    "quality_summary": "...",\n'
    '    "gemini_feedback": {...}\n'
    "  }\n"
    "}"
)

INTEGRATOR_PROMPT = (
    "You merge critiques into a refined plan. Follow this loop each round:\n"
    "1. Summarise critic feedback and previous scores.\n"
    "2. CALL `generate_scene_plan` with critique summary to draft revisions.\n"
    "3. CALL `evaluate_scene_actions` to compute heuristics.\n"
    "4. CALL `score_scene_plan_visual` to render previews and obtain heuristics, texture metrics, quality_rubric, and optional Gemini feedback. Use these signals to guide revisions.\n"
    "5. Decide whether another revision is needed; if so, reply with a short action plan.\n"
    "6. When the scene is production-ready, respond with JSON EXACTLY matching:\n"
    f"{INTEGRATOR_FINAL_SCHEMA}\n"
    "Append the token FINAL_APPROVAL anywhere in your message when returning the final JSON.\n"
    "Do not invent action JSON: rely on tool outputs."
)

JUDGE_PROMPT = (
    "You are the final judge. Review the integrator's latest response including heuristics "
    "and visual feedback. Return STRICT JSON:\n"
    "{\n"
    '  "score": 0-10,\n'
    '  "summary": "Two-sentence verdict on aesthetics and functionality",\n'
    '  "next_steps": "Optional guidance for future iterations"\n'
    "}"
)


def run_multi_agent_terrain_design(
    command: str,
    scene_state: Optional[Dict[str, Any]] = None,
    profile: Optional[str] = None,
    max_rounds: int = 6,
) -> Dict[str, Any]:
    """Run the artist/critic/integrator loop and return actions + transcripts."""

    llm_config = build_llm_config(profile)

    if ConversableAgent is None or AutoPattern is None or run_group_chat is None:
        raise RuntimeError(
            "autogen (AG2) is not installed. Install 'autogen-agentchat' to use the multi-agent workflow."
        )

    artist = ConversableAgent(
        name="terrain_artist",
        system_message=ARTIST_PROMPT,
        description="Creates first-pass terrain plans using provided tools.",
        human_input_mode="NEVER",
        llm_config=llm_config,
    )

    critic = ConversableAgent(
        name="terrain_critic",
        system_message=CRITIC_PROMPT,
        description="Evaluates terrain plans, calling tools if needed.",
        human_input_mode="NEVER",
        llm_config=llm_config,
    )

    integrator = ConversableAgent(
        name="terrain_integrator",
        system_message=INTEGRATOR_PROMPT,
        description="Incorporates critique and produces the final plan.",
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: "FINAL_APPROVAL" in (msg.get("content", "") or "").upper(),
        llm_config=llm_config,
    )

    judge = ConversableAgent(
        name="terrain_judge",
        system_message=JUDGE_PROMPT,
        description="LLM-as-a-judge providing overall score and guidance.",
        human_input_mode="NEVER",
        llm_config=llm_config,
    )

    # Optional human oversight placeholder (disabled by default but available if needed).
    observer = UserProxyAgent(
        name="human_observer",
        system_message="Human reviewer. Respond with instructions or 'OK' to continue.",
        description="Can step in to steer the agents if required.",
        human_input_mode="NEVER",
    )

    # Tool executor runs python functions on behalf of agents.
    tool_executor = ConversableAgent(
        name="tool_executor",
        system_message="You execute registered python functions without modification.",
        human_input_mode="NEVER",
        llm_config=llm_config,
    )

    # Register tool functions for artist and integrator.
    register_function(
        generate_scene_plan,
        caller=artist,
        executor=tool_executor,
        description="Generate terrain actions and metadata from a command and optional critique.",
    )
    register_function(
        generate_scene_plan,
        caller=integrator,
        executor=tool_executor,
        description="Generate updated terrain actions when incorporating critique.",
    )
    register_function(
        evaluate_scene_actions,
        caller=integrator,
        executor=tool_executor,
        description="Evaluate action lists for diversity and quality heuristics.",
    )
    register_function(
        score_scene_plan_visual,
        caller=integrator,
        executor=tool_executor,
        description="Render terrain previews and gather heuristic + Gemini feedback.",
    )

    pattern = AutoPattern(
        agents=[artist, critic, integrator, judge],
        initial_agent=artist,
        user_agent=observer,
        group_manager_args={"name": "terrain_group_manager", "llm_config": llm_config},
    )

    conversation = run_group_chat(
        pattern=pattern,
        messages=command,
        max_rounds=max_rounds,
    )

    conversation.process()

    payload = _extract_payload(conversation.summary)
    final_actions = []
    if isinstance(payload, dict):
        final_actions = payload.get("actions", []) or []
    if not final_actions:
        final_actions = _extract_actions(conversation.summary)

    # Extract transcript from conversation object
    transcript = []
    try:
        # Try different ways to access chat history
        if hasattr(conversation, "chat_history"):
            transcript = conversation.chat_history
        elif hasattr(conversation, "messages"):
            transcript = conversation.messages
        elif hasattr(pattern, "group_manager") and hasattr(pattern.group_manager, "chat_messages"):
            # Extract from group manager's chat messages
            chat_msgs = pattern.group_manager.chat_messages
            transcript = [msg for msgs in chat_msgs.values() for msg in msgs]
    except Exception as exc:
        logger.warning("Failed to extract transcript: %s", exc)
        transcript = []

    _log_conversation(command, conversation.summary, transcript, payload)

    result: Dict[str, Any] = {
        "summary": conversation.summary,
        "actions": final_actions,
        "transcript": transcript,
    }
    if payload:
        result["result"] = payload

    return result


def _extract_payload(summary: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse the final JSON payload from the integrator summary."""

    if not summary:
        return None

    try:
        # Look for JSON code blocks first.
        if "```" in summary:
            blocks = summary.split("```")
            for block in blocks:
                block_trimmed = block.strip()
                if block_trimmed.lower().startswith("json"):
                    block_trimmed = block_trimmed[4:].strip()
                try:
                    payload = json.loads(block_trimmed)
                    if isinstance(payload, dict):
                        return payload
                except json.JSONDecodeError:
                    continue

        payload = json.loads(summary)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        logger.debug("Failed to parse final payload from summary: %s", summary)

    return None


def _extract_actions(summary: str) -> List[Dict[str, Any]]:
    """Extract actions list from integrator summary."""

    payload = _extract_payload(summary)
    if isinstance(payload, dict):
        actions = payload.get("actions")
        if isinstance(actions, list):
            return actions

    return []


def _log_conversation(
    command: str,
    summary: str,
    transcript: List[Dict[str, Any]],
    payload: Optional[Dict[str, Any]],
) -> None:
    """Persist conversation summary and transcript for offline analysis."""

    base_dir = Path(os.environ.get("MULTI_AGENT_LOG_DIR", "logs/multi_agent_sessions"))
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    session_dir = base_dir / timestamp

    try:
        session_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # pragma: no cover - best effort logging
        logger.warning("Failed to create multi-agent log dir %s: %s", session_dir, exc)
        return

    metadata = {
        "command": command,
        "summary": summary,
    }

    try:
        with (session_dir / "summary.json").open("w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2)

        serialised_history = []
        for message in transcript or []:
            if isinstance(message, dict):
                serialised_history.append(message)
            else:
                try:
                    serialised_history.append(json.loads(json.dumps(message, default=str)))
                except Exception:
                    serialised_history.append({"repr": repr(message)})

        with (session_dir / "transcript.json").open("w", encoding="utf-8") as fp:
            json.dump(serialised_history, fp, indent=2)
        if payload:
            with (session_dir / "result.json").open("w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2)
            _log_quality_history(command, timestamp, payload)
    except Exception as exc:  # pragma: no cover - logging should not break workflow
        logger.warning("Failed to persist multi-agent transcript: %s", exc)


def _log_quality_history(command: str, timestamp: str, payload: Mapping[str, Any]) -> None:
    """Append quality metrics to global history log for progress tracking."""

    raw_quality = payload.get("quality")
    quality: Optional[Mapping[str, Any]] = raw_quality if isinstance(raw_quality, Mapping) else None
    if quality is None:
        rubric = payload.get("quality_rubric")
        if isinstance(rubric, Mapping):
            quality = {"overall_score": rubric.get("overall_score"), "categories": rubric.get("categories")}
        else:
            return

    categories = quality.get("categories", {}) if isinstance(quality, Mapping) else {}
    entry: Dict[str, Any] = {
        "timestamp": timestamp,
        "command": command,
        "overall_score": quality.get("overall_score"),
        "composition_score": (categories.get("composition") or {}).get("score"),
        "textures_score": (categories.get("textures") or {}).get("score"),
        "quality_summary": payload.get("quality_summary"),
    }

    texture_metrics = payload.get("texture_metrics")
    if not isinstance(texture_metrics, Mapping) and isinstance(raw_quality, Mapping):
        candidate = raw_quality.get("texture_metrics")
        if isinstance(candidate, Mapping):
            texture_metrics = candidate
    if isinstance(texture_metrics, Mapping):
        entry["texture_metrics"] = texture_metrics

    history_path = Path(os.environ.get("QUALITY_HISTORY_FILE", "logs/quality_history.jsonl"))
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to append quality history: %s", exc)
