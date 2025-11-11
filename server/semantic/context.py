"""Context helpers for ReAct prompt engineering."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence


def summarize_scene(
    scene_state: Dict[str, Any],
    max_types: int = 4,
    max_chars: int | None = None,
) -> str:
    """Return a concise natural-language summary of the scene."""

    if not scene_state:
        return "Empty terrain. No features yet."

    features: Sequence[Dict[str, Any]] = scene_state.get("features", []) or []
    if not features:
        seed = scene_state.get("seed")
        return f"Empty terrain (seed={seed}) awaiting first features." if seed else "Empty terrain awaiting first features."

    counts = Counter(str(f.get("type", "unknown")) for f in features)
    top_types = ", ".join(
        f"{feature_type} ×{count}"
        for feature_type, count in counts.most_common(max_types)
    )

    seed = scene_state.get("seed")
    extent = _compute_extent(features)
    extent_str = (
        f"span ≈{extent['width']}×{extent['height']}" if extent else "span unknown"
    )

    tail = f" | seed={seed}" if seed is not None else ""
    summary = f"Features: {top_types} | {extent_str}{tail}"
    return _clip_text(summary, max_chars)


def summarize_recent_actions(
    action_history: Iterable[Dict[str, Any]],
    limit: int = 3,
    max_chars: int | None = None,
) -> str:
    """Summarise recent actions for prompt inclusion."""

    history = list(action_history or [])
    if not history:
        return "No prior actions recorded."

    lines: List[str] = []
    for entry in history[-limit:][::-1]:
        command = str(entry.get("command") or "(direct actions)").strip()
        parser = entry.get("parser") or "unknown"
        actions = entry.get("actions") or []
        counts = Counter(action.get("type", "unknown") for action in actions)
        type_summary = ", ".join(
            f"{t}×{c}" for t, c in counts.most_common(3)
        ) or "no actions"
        lines.append(f"• {command} → {type_summary} (via {parser})")

    summary = "\n".join(lines)
    return _clip_text(summary, max_chars)


def infer_active_aesthetic_goals(command: str, scene_state: Dict[str, Any], limit: int = 6) -> List[str]:
    """Infer current aesthetic goals from state metadata and user command."""

    goals: List[str] = []

    meta = scene_state.get("_last_narrative_meta") if scene_state else None
    if isinstance(meta, dict):
        goals.extend(meta.get("aesthetic_goals", []) or [])

    if goals:
        inferred = _unique_preserve_order(goals)[:limit]
        return inferred or ["balanced"]

    command_lower = (command or "").lower()
    keyword_map = {
        "dramatic": "dramatic",
        "beautiful": "beautiful",
        "serene": "serene",
        "rugged": "rugged",
        "majestic": "majestic",
        "vast": "vast",
        "intimate": "intimate",
        "organic": "organic",
        "smooth": "smooth",
        "natural": "organic",
        "ancient": "ancient",
        "mysterious": "mysterious",
    }

    for keyword, goal in keyword_map.items():
        if keyword in command_lower:
            goals.append(goal)

    return _unique_preserve_order(goals)[:limit] or ["balanced"]


def _compute_extent(features: Sequence[Dict[str, Any]]) -> Dict[str, int] | None:
    xs = [feat.get("x") for feat in features if isinstance(feat.get("x"), (int, float))]
    ys = [feat.get("y") for feat in features if isinstance(feat.get("y"), (int, float))]
    if not xs or not ys:
        return None
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    return {"width": int(width), "height": int(height)}


def _unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if not value:
            continue
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _clip_text(text: str, max_chars: int | None) -> str:
    if not text:
        return text
    if max_chars is None or len(text) <= max_chars:
        return text
    clipped = text[: max(0, max_chars - 3)].rstrip()
    return f"{clipped}..."
