import pytest

pytest.importorskip("numpy")
pytest.importorskip("dotenv")

from server.bootstrap import ensure_bootstrapped

ensure_bootstrapped()

from server.orchestration import parse_command_to_actions


def _empty_scene(seed: int = 42) -> dict:
    return {
        "features": [],
        "seed": seed,
        "semantic_scene": {},
    }


@pytest.mark.parametrize(
    "command",
    [
        "create dramatic mountains",
        "design serene valley",
    ],
)
def test_narrative_pipeline_is_default_for_aesthetic_commands(command: str):
    state = _empty_scene()

    actions = parse_command_to_actions(command, state)

    assert actions, "Narrative pipeline should generate actions"
    assert state.get("_debug_last_parser") == "narrative"
    meta = state.get("_last_narrative_meta")
    assert meta and meta.get("archetype"), "Narrative metadata should be captured"
    assert "metrics" in meta and meta["metrics"]["feature_count"] == len(actions)
    assert "quality" in meta and "score" in meta["quality"]

    labels = {action.get("label", "") for action in actions}
    assert any(label.startswith("supporting") for label in labels)
    assert any(label.startswith("accent") for label in labels)

    types = {action["type"] for action in actions}
    assert "mountain" in types, "Focal mountain expected by archetype heuristics"
    assert len(types) >= 2, "Expect at least one supporting feature type"
