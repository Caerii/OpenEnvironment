"""
Tests for narrative composition tool integration.

Verifies that the narrative tool works correctly when called directly via
the ToolExecutor. These tests exercise the pure narrative pipeline (no LLM).
"""

import sys
from pathlib import Path
from typing import Dict

import pytest

# Ensure project root is importable regardless of pytest cwd
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.semantic.tools.executor import ToolExecutor
from server.semantic.tools.schema import get_all_tool_schemas


def _make_scene(seed: int = 42) -> Dict:
    """Minimal scene state expected by narrative pipeline."""
    return {
        "features": [],
        "seed": seed,
        "semantic_scene": {
            "version": 1,
            "root": {
                "path": "/World",
                "name": "World",
                "data": {},
                "feature_ids": [],
                "children": {}
            },
            "entities": [],
            "relationships": {"relationships": [], "next_id": 1}
        }
    }


class TestNarrativeTool:
    """Test narrative composition tool."""

    def test_tool_is_registered(self):
        executor = ToolExecutor()
        assert "generate_narrative_composition" in executor.tools
        # Tool count is deterministic for regression protection
        assert len(executor.tools) == 14

    def test_narrative_tool_execution(self):
        executor = ToolExecutor()
        scene_state = _make_scene()

        result = executor.execute_tool(
            tool_name="generate_narrative_composition",
            arguments={"command": "create dramatic mountains"},
            scene_state=scene_state
        )

        assert result["success"] is True
        data = result["data"]
        actions = data["actions"]

        assert len(actions) >= 2  # focal + at least one supporting/accent
        types = {action["type"] for action in actions}
        assert types.issubset({"mountain", "valley", "dunes", "cliff", "plateau", "canyon"})

        # Narrative metadata should be populated
        assert data["archetype"]
        assert data["focal_type"]
        assert data["feature_count"] == len(actions)
        assert "quality" in data and "score" in data["quality"]
        assert "metrics" in data and data["metrics"]["feature_count"] == len(actions)

    def test_narrative_tool_with_different_commands(self):
        executor = ToolExecutor()
        commands = [
            "create dramatic mountains",
            "design serene valley",
            "build rugged cliffs",
            "generate beautiful dunes"
        ]

        for idx, command in enumerate(commands):
            scene_state = _make_scene(seed=100 + idx)
            result = executor.execute_tool(
                tool_name="generate_narrative_composition",
                arguments={"command": command},
                scene_state=scene_state
            )

            assert result["success"] is True, f"Failed for command: {command}"
            actions = result["data"]["actions"]
            assert len(actions) >= 2
            assert result["data"]["quality"]["score"] >= 0.0

    def test_narrative_tool_returns_valid_actions(self):
        executor = ToolExecutor()
        scene_state = _make_scene()

        result = executor.execute_tool(
            tool_name="generate_narrative_composition",
            arguments={"command": "create dramatic landscape"},
            scene_state=scene_state
        )

        assert result["success"] is True
        actions = result["data"]["actions"]

        for action in actions:
            assert action["kind"] == "add"
            assert action["type"] in {"mountain", "valley", "dunes", "cliff", "plateau", "canyon"}
            assert "position" in action
            assert "modifiers" in action

    def test_narrative_tool_schema_generation(self):
        executor = ToolExecutor()
        schemas = get_all_tool_schemas(executor.tools)

        narrative_schema = next(
            (schema for schema in schemas if schema["function"]["name"] == "generate_narrative_composition"),
            None
        )

        assert narrative_schema is not None
        func = narrative_schema["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        assert "properties" in func["parameters"]

        props = func["parameters"]["properties"]
        assert "command" in props

