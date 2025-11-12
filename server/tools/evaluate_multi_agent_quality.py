"""Batch runner to evaluate multi-agent terrain quality scores."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

# Ensure repository root is on sys.path for absolute imports when executed as a script
import sys

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv()

from server.semantic.multi_agent.workflow import run_multi_agent_terrain_design
from server.semantic.evaluation import (
    compute_feature_metrics,
    evaluate_quality_rubric,
)


DEFAULT_COMMANDS = [
    "craft a dramatic alpine valley with jagged cliffs and icy accents",
    "create a sweeping dune sea with wind-carved ridges and a rocky oasis",
    "design a lush plateau surrounded by canyons and layered terraces",
]


@dataclass
class RunResult:
    command: str
    rounds: int
    iteration: int
    duration: float
    actions: int
    overall_score: float
    composition_score: float
    textures_score: float
    summary: str


def _extract_quality(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract or compute quality rubric from payload."""

    quality_block = payload.get("quality")
    if isinstance(quality_block, Mapping):
        rubric = quality_block.get("quality_rubric")
        if isinstance(rubric, Mapping):
            return rubric

    rubric = payload.get("quality_rubric")
    if isinstance(rubric, Mapping):
        return rubric

    # Fallback: build heuristic-based rubric if not supplied
    actions = payload.get("actions") if isinstance(payload.get("actions"), Sequence) else []
    metrics = compute_feature_metrics(actions)
    return evaluate_quality_rubric(metrics, {}, {})


def _extract_summary(payload: Mapping[str, Any]) -> str:
    quality = payload.get("quality")
    if isinstance(quality, Mapping):
        summary = quality.get("quality_summary")
        if isinstance(summary, str):
            return summary
    summary = payload.get("quality_summary")
    if isinstance(summary, str):
        return summary
    return ""


def _summarize_rubric(rubric: Mapping[str, Any]) -> Dict[str, float]:
    overall = float(rubric.get("overall_score", 0.0) or 0.0)
    categories = rubric.get("categories", {})
    composition = 0.0
    textures = 0.0
    if isinstance(categories, Mapping):
        comp = categories.get("composition")
        tex = categories.get("textures")
        if isinstance(comp, Mapping):
            composition = float(comp.get("score", 0.0) or 0.0)
        if isinstance(tex, Mapping):
            textures = float(tex.get("score", 0.0) or 0.0)
    return {
        "overall": overall,
        "composition": composition,
        "textures": textures,
    }


def run_experiments(
    commands: Sequence[str],
    rounds: Sequence[int],
    iterations: int,
    profile: Optional[str],
) -> List[RunResult]:
    results: List[RunResult] = []

    for max_rounds in rounds:
        for command in commands:
            for iteration in range(1, iterations + 1):
                start = time.perf_counter()
                output = run_multi_agent_terrain_design(
                    command=command,
                    scene_state=None,
                    profile=profile,
                    max_rounds=max_rounds,
                )
                elapsed = time.perf_counter() - start

                payload = output.get("result")
                if not isinstance(payload, Mapping):
                    payload = {}

                rubric = _extract_quality(payload)
                scores = _summarize_rubric(rubric)
                summary = _extract_summary(payload)
                actions = payload.get("actions")
                action_count = len(actions) if isinstance(actions, Sequence) else len(output.get("actions") or [])

                result = RunResult(
                    command=command,
                    rounds=max_rounds,
                    iteration=iteration,
                    duration=elapsed,
                    actions=action_count,
                    overall_score=scores["overall"],
                    composition_score=scores["composition"],
                    textures_score=scores["textures"],
                    summary=summary,
                )
                results.append(result)

                print(
                    f"[rounds={max_rounds} iter={iteration}] "
                    f"score={result.overall_score:.2f} "
                    f"(comp={result.composition_score:.2f}, tex={result.textures_score:.2f}) "
                    f"actions={action_count} time={elapsed:.1f}s"
                )
                if summary:
                    print(f"  summary: {summary.splitlines()[0]}")

    return results


def analyse_history(since_token: str, history_path: Path) -> List[Dict[str, Any]]:
    if not history_path.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with history_path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = record.get("timestamp")
            if not isinstance(timestamp, str):
                continue
            if timestamp >= since_token:
                entries.append(record)
    return entries


def summarise_results(results: Iterable[RunResult]) -> None:
    records = list(results)
    if not records:
        print("No runs executed.")
        return

    by_rounds: Dict[int, List[RunResult]] = {}
    for record in records:
        by_rounds.setdefault(record.rounds, []).append(record)

    print("\n=== Summary by max_rounds ===")
    for rounds, items in sorted(by_rounds.items()):
        overalls = [r.overall_score for r in items]
        avg = mean(overalls)
        best = max(overalls)
        worst = min(overalls)
        avg_time = mean(r.duration for r in items)
        print(
            f"rounds={rounds}: avg_score={avg:.2f}, best={best:.2f}, worst={worst:.2f}, avg_time={avg_time:.1f}s"
        )

    overall_scores = [r.overall_score for r in records]
    print(
        f"\nGlobal: avg={mean(overall_scores):.2f}, best={max(overall_scores):.2f}, "
        f"worst={min(overall_scores):.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate multi-agent terrain quality across multiple runs.")
    parser.add_argument("--commands", nargs="*", default=None, help="Commands to execute (defaults to curated list)")
    parser.add_argument("--rounds", nargs="*", type=int, default=[3, 5], help="max_rounds values to evaluate")
    parser.add_argument("--iterations", type=int, default=2, help="Runs per command per rounds setting")
    parser.add_argument("--profile", type=str, default=None, help="Prompt profile to use")
    parser.add_argument("--history", type=str, default=None, help="Override path to quality history JSONL file")
    args = parser.parse_args()

    commands = args.commands or DEFAULT_COMMANDS
    rounds = args.rounds
    iterations = max(1, args.iterations)

    start_token = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    history_path = Path(args.history or os.environ.get("QUALITY_HISTORY_FILE", "logs/quality_history.jsonl"))

    print(f"Running {len(commands) * len(rounds) * iterations} experiments...")
    results = run_experiments(commands, rounds, iterations, args.profile)
    summarise_results(results)

    history_entries = analyse_history(start_token, history_path)
    if history_entries:
        print("\n=== Quality history appended entries ===")
        for entry in history_entries[-10:]:
            overall = entry.get("overall_score")
            comp = entry.get("composition_score")
            tex = entry.get("textures_score")
            timestamp = entry.get("timestamp")
            print(
                f"{timestamp}: overall={overall:.2f} comp={comp:.2f} tex={tex:.2f} command={entry.get('command')!r}"
            )


if __name__ == "__main__":
    main()

