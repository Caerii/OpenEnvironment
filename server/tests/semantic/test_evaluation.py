from server.semantic.evaluation import compute_feature_metrics, evaluate_aesthetic_quality


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
