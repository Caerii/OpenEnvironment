import numpy as np
import pytest

from server.semantic.evaluation import (
    compute_feature_metrics,
    compute_texture_metrics,
    evaluate_aesthetic_quality,
    evaluate_quality_rubric,
)


def test_compute_feature_metrics_basic():
    features = [
        {"type": "mountain", "x": 100, "y": 200, "height": 0.8, "radius": 60},
        {"type": "plateau", "x": 260, "y": 240, "height": 0.45, "width": 90},
    ]
    metrics = compute_feature_metrics(features)
    assert metrics["feature_count"] == 2
    assert metrics["type_diversity"] == 2
    assert metrics["extent"] == {"width": 160, "height": 40}


def test_evaluate_aesthetic_quality_scoring():
    metrics = {
        "feature_count": 4,
        "type_diversity": 3,
        "extent": {"width": 120, "height": 140},
        "height_stats": {"std": 0.08},
    }
    result = evaluate_aesthetic_quality(metrics)
    assert result["score"] > 0.5
    assert isinstance(result["warnings"], list)


def test_texture_metrics_and_rubric():
    heightmap = np.linspace(0.0, 1.0, 16, dtype=np.float32).reshape(4, 4)
    splatmap = np.zeros((4, 4, 4), dtype=np.float32)
    splatmap[..., 0] = 0.4  # grass
    splatmap[..., 1] = 0.3  # rock
    splatmap[..., 2] = 0.2  # sand
    splatmap[..., 3] = 0.1  # snow

    texture_metrics = compute_texture_metrics(heightmap, splatmap)
    assert texture_metrics["channel_coverage"]["grass"] == pytest.approx(0.4, rel=1e-3)
    assert "rock_slope_corr" in texture_metrics

    feature_metrics = compute_feature_metrics(
        [{"type": "mountain", "x": 100, "y": 120, "height": 0.6, "radius": 50},
         {"type": "valley", "x": 220, "y": 260, "depth": 0.4, "radius": 70},
         {"type": "cliff", "x": 280, "y": 160, "height": 0.5, "length": 90}]
    )

    rubric = evaluate_quality_rubric(feature_metrics, texture_metrics)
    assert 0.0 <= rubric["overall_score"] <= 1.0
    assert "composition" in rubric["categories"]
    assert "textures" in rubric["categories"]
