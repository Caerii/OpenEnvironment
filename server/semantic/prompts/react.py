"""Prompt builders for ReAct agent."""

from __future__ import annotations

from typing import Iterable

from . import load_template


def build_system_prompt(
    scene_summary: str,
    recent_actions: str,
    aesthetic_goals: Iterable[str],
) -> str:
    template = load_template("react_system_prompt")
    goals_text = _format_goals(aesthetic_goals)
    return (
        template
        .replace("{scene_summary}", scene_summary)
        .replace("{recent_actions}", recent_actions)
        .replace("{aesthetic_goals}", goals_text)
    )


def build_user_prompt(
    command: str,
    scene_summary: str,
    recent_actions: str,
    aesthetic_goals: Iterable[str],
    feature_count: int,
    entity_count: int,
    seed: int | None,
) -> str:
    template = load_template("react_user_prompt")
    goals_text = _format_goals(aesthetic_goals)
    result = template
    replacements = {
        "{command}": command,
        "{scene_summary}": scene_summary,
        "{recent_actions}": recent_actions,
        "{aesthetic_goals}": goals_text,
        "{feature_count}": str(feature_count),
        "{entity_count}": str(entity_count),
        "{seed}": str(seed) if seed is not None else "n/a",
    }
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _format_goals(goals: Iterable[str]) -> str:
    goals_list = [goal for goal in goals if goal]
    return ", ".join(goals_list) if goals_list else "balanced"
