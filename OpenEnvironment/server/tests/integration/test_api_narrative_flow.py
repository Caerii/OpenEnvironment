import pytest

pytest.importorskip("numpy")
pytest.importorskip("dotenv")

from fastapi.testclient import TestClient

from server.bootstrap import ensure_bootstrapped

ensure_bootstrapped()

from server.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_generate_endpoint_uses_narrative_pipeline(client: TestClient):
    reset_resp = client.post("/api/reset", json={"text": ""})
    assert reset_resp.status_code == 200

    resp = client.post("/api/generate", json={"text": "create dramatic mountains"})
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get("ok") is True

    state = payload.get("state", {})
    features = state.get("features", [])
    assert len(features) >= 3, "Narrative pipeline should produce supporting/accent features"

    types = {feat["type"] for feat in features}
    assert "mountain" in types
    assert len(types) >= 2

    assert state.get("_debug_last_parser") == "narrative"
    history = state.get("action_history", [])
    assert history, "Action history should capture executed commands"
    assert history[-1].get("parser") == "narrative"

    meta = state.get("_last_narrative_meta")
    assert meta and meta.get("archetype")
    assert "quality" in meta and "score" in meta["quality"]
    assert "metrics" in meta and meta["metrics"]["feature_count"] >= 1
