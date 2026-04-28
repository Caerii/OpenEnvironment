from fastapi.testclient import TestClient

from server.main import app, terrain_controller


client = TestClient(app)


def test_multi_agent_endpoint(monkeypatch):
    def fake_run_design(command_text: str, profile=None, max_rounds=6):
        assert command_text == "design a serene valley"
        assert max_rounds == 4
        return {
            "workflow": {"summary": "ok", "actions": [{"type": "valley"}]},
            "heightmap": None,
            "splatmap": None,
            "state": {"features": []},
            "actions": [{"type": "valley"}],
        }

    monkeypatch.setattr(terrain_controller.multi_agent_service, "run_design", fake_run_design)

    response = client.post(
        "/api/design/multi-agent",
        json={"text": "design a serene valley", "max_rounds": 4},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["workflow"]["summary"] == "ok"
    assert payload["actions"] == [{"type": "valley"}]


