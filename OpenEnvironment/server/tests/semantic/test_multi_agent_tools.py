import os
import shutil
from pathlib import Path

import numpy as np

from server.semantic.multi_agent.tools import (
    render_scene_preview,
    evaluate_scene_actions,
    score_scene_plan_visual,
)


def _sample_actions():
    return [
        {
            "kind": "add",
            "type": "mountain",
            "position": {"x": 205, "y": 136},
            "modifiers": {"height": 0.9, "radius": 60, "use_noise": True},
            "count": 1,
            "label": "focal",
        },
        {
            "kind": "add",
            "type": "plateau",
            "position": {"x": 300, "y": 180},
            "modifiers": {"height": 0.45, "width": 90, "length": 120, "orientation": 0.0},
            "count": 1,
            "label": "supporting",
        },
    ]


def test_render_scene_preview_creates_files(tmp_path):
    preview_dir = tmp_path / "previews"
    os.environ["TERRAIN_PREVIEW_DIR"] = str(preview_dir)

    result = render_scene_preview(actions=_sample_actions(), command="test scene")

    try:
        assert Path(result["preview_dir"]).exists()
        for image_path in result["preview_images"]:
            path = Path(image_path)
            assert path.exists() and path.stat().st_size > 0
        assert "heightmap_array" not in result
        assert "splatmap_array" not in result
    finally:
        del os.environ["TERRAIN_PREVIEW_DIR"]
        shutil.rmtree(preview_dir, ignore_errors=True)


def test_evaluate_scene_actions_counts_types():
    metrics = evaluate_scene_actions(_sample_actions())
    counts = metrics["metrics"]["type_counts"]
    assert counts.get("mountain") == 1
    assert counts.get("plateau") == 1


def test_score_scene_plan_visual_without_gemini(tmp_path, monkeypatch):
    preview_dir = tmp_path / "previews"
    os.environ["TERRAIN_PREVIEW_DIR"] = str(preview_dir)

    # Ensure Gemini is treated as unavailable
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = score_scene_plan_visual(_sample_actions(), command="test scene")

    try:
        assert "heuristics" in result
        assert "texture_metrics" in result
        assert "quality_rubric" in result
        assert "quality_summary" in result
        assert isinstance(result["quality_summary"], str)
        assert result["gemini_feedback"] is None
        assert Path(result["preview"]["preview_dir"]).exists()

        texture_metrics = result["texture_metrics"]
        assert "channel_coverage" in texture_metrics
        coverage = texture_metrics["channel_coverage"]
        assert set(coverage.keys()) == {"grass", "rock", "sand", "snow"}

        quality = result["quality_rubric"]
        assert 0.0 <= quality["overall_score"] <= 1.0
        assert "composition" in quality["categories"]
        assert "textures" in quality["categories"]
        assert isinstance(quality["warnings"], list)
    finally:
        del os.environ["TERRAIN_PREVIEW_DIR"]
        shutil.rmtree(preview_dir, ignore_errors=True)
