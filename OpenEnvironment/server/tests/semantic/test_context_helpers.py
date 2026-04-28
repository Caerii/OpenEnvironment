import pytest

from server.semantic.prompts.context import (
    summarize_scene,
    summarize_recent_actions,
    infer_active_aesthetic_goals,
)


def test_summarize_scene_empty():
    assert "Empty" in summarize_scene({})


def test_summarize_scene_with_features():
    scene = {
        "seed": 42,
        "features": [
            {"type": "mountain", "x": 100, "y": 200},
            {"type": "mountain", "x": 200, "y": 300},
            {"type": "dunes", "x": 150, "y": 250},
        ],
    }
    summary = summarize_scene(scene)
    assert "mountain" in summary
    assert "span" in summary


def test_summarize_recent_actions():
    history = [
        {
            "command": "create dramatic mountains",
            "parser": "narrative",
            "actions": [
                {"kind": "add", "type": "mountain"},
                {"kind": "add", "type": "cliff"},
            ],
        },
    ]
    summary = summarize_recent_actions(history)
    assert "mountain" in summary
    assert "cliff" in summary


@pytest.mark.parametrize(
    "command,expected",
    [
        ("create dramatic mountains", "dramatic"),
        ("design a serene valley", "serene"),
    ],
)
def test_infer_aesthetic_goals_from_command(command, expected):
    goals = infer_active_aesthetic_goals(command, {})
    assert expected in goals


def test_infer_aesthetic_goals_from_meta():
    scene_state = {
        "_last_narrative_meta": {
            "aesthetic_goals": ["dramatic", "rugged"],
        }
    }
    goals = infer_active_aesthetic_goals("", scene_state)
    assert goals == ["dramatic", "rugged"]
