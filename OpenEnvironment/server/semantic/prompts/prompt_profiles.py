"""Prompt profile configurations for ReAct agent."""

from __future__ import annotations

PromptProfile = dict[str, object]


PROMPT_PROFILES: dict[str, PromptProfile] = {
    "compact": {
        "max_history": 1,
        "scene_max_chars": 220,
        "actions_max_chars": 220,
        "goal_limit": 4,
        "log_sessions": True,
        "max_completion_tokens": 2000,
        "max_iterations": 3,
    },
    "standard": {
        "max_history": 2,
        "scene_max_chars": 320,
        "actions_max_chars": 320,
        "goal_limit": 6,
        "log_sessions": True,
        "max_completion_tokens": 2500,
        "max_iterations": 4,
    },
    "extended32k": {
        "max_history": 4,
        "scene_max_chars": 520,
        "actions_max_chars": 520,
        "goal_limit": 10,
        "log_sessions": True,
        "max_completion_tokens": 6000,
        "max_iterations": 5,
    },
    "omni": {
        "max_history": 5,
        "scene_max_chars": 720,
        "actions_max_chars": 720,
        "goal_limit": 12,
        "log_sessions": True,
        "max_completion_tokens": 9000,
        "max_iterations": 6,
    },
}
