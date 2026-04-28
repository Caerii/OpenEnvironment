import numpy as np
import pytest

from server.services.multi_agent_service import MultiAgentService


class DummyTerrainService:
    def __init__(self):
        self.called = False

    def generate_terrain(self, command_text="", actions=None, **kwargs):
        self.called = True
        height = np.zeros((4, 4), dtype=np.float32)
        splat = np.zeros((4, 4, 4), dtype=np.float32)
        state = {"features": actions or []}
        return height, state, splat


class DummyStateService:
    def __init__(self, state=None):
        self._state = state or {"features": []}

    def get_state(self):
        return self._state


def test_run_design_applies_actions(monkeypatch):
    terrain = DummyTerrainService()
    state = DummyStateService()
    service = MultiAgentService(terrain, state)

    def fake_run_multi_agent_terrain_design(command, scene_state, profile=None, max_rounds=6):
        assert command == "make an epic canyon"
        assert scene_state == state.get_state()
        return {
            "summary": "Integration agent response",
            "actions": [{"type": "canyon", "kind": "add"}],
            "transcript": [],
        }

    monkeypatch.setattr(
        "server.services.multi_agent_service.run_multi_agent_terrain_design",
        fake_run_multi_agent_terrain_design,
    )

    result = service.run_design("make an epic canyon", profile="standard", max_rounds=5)

    assert terrain.called is True
    assert result["actions"] == [{"type": "canyon", "kind": "add"}]
    assert isinstance(result["heightmap"], np.ndarray)
    assert isinstance(result["splatmap"], np.ndarray)
    assert result["state"]["features"] == [{"type": "canyon", "kind": "add"}]


def test_run_design_handles_generate_failure(monkeypatch):
    class FailingTerrain(DummyTerrainService):
        def generate_terrain(self, *args, **kwargs):
            self.called = True
            raise RuntimeError("boom")

    terrain = FailingTerrain()
    state = DummyStateService()
    service = MultiAgentService(terrain, state)

    monkeypatch.setattr(
        "server.services.multi_agent_service.run_multi_agent_terrain_design",
        lambda **_: {"summary": "ok", "actions": [{"type": "mountain"}]},
    )

    result = service.run_design("make a mountain vista")

    assert terrain.called is True
    assert result["heightmap"] is None
    assert result["splatmap"] is None
    assert result["state"] is None
    assert result["actions"] == [{"type": "mountain"}]

