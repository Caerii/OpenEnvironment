"""Evaluation helpers for terrain outputs."""

from __future__ import annotations

from collections import Counter
from math import sqrt
from statistics import pstdev
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


def compute_feature_metrics(features: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Compute descriptive metrics for generated features."""

    features = [ _to_mapping(feat) for feat in (features or []) ]
    if not features:
        return {
            "feature_count": 0,
            "type_counts": {},
            "type_diversity": 0,
            "extent": None,
            "centroid": None,
            "height_stats": None,
            "radius_stats": None,
        }

    type_counts = Counter(str(feat.get("type", "unknown")) for feat in features)
    xs = [ _as_number(feat.get("x")) for feat in features if _as_number(feat.get("x")) is not None ]
    ys = [ _as_number(feat.get("y")) for feat in features if _as_number(feat.get("y")) is not None ]

    extent = None
    centroid = None
    if xs and ys:
        extent = {
            "width": int(max(xs) - min(xs)),
            "height": int(max(ys) - min(ys)),
        }
        centroid = {
            "x": float(sum(xs) / len(xs)),
            "y": float(sum(ys) / len(ys)),
        }

    height_values = list(_collect_numeric(features, ("height", "depth", "amp")))
    height_stats = _build_stats(height_values)

    radius_values = list(_collect_numeric(features, ("radius", "width", "length")))
    radius_stats = _build_stats(radius_values)

    return {
        "feature_count": len(features),
        "type_counts": dict(type_counts),
        "type_diversity": len(type_counts),
        "extent": extent,
        "centroid": centroid,
        "height_stats": height_stats,
        "radius_stats": radius_stats,
    }


def evaluate_aesthetic_quality(metrics: Mapping[str, Any]) -> Dict[str, Any]:
    """Produce a coarse quality score based on feature metrics."""

    score = 0.0
    warnings: List[str] = []

    feature_count = metrics.get("feature_count", 0)
    type_diversity = metrics.get("type_diversity", 0)
    extent = metrics.get("extent") or {"width": 0, "height": 0}
    height_stats = metrics.get("height_stats") or {"std": 0.0}

    if feature_count >= 3:
        score += 0.25
    else:
        warnings.append("Low feature count; scene may feel sparse")

    if type_diversity >= 2:
        score += 0.25
    else:
        warnings.append("Feature diversity low; consider adding supporting contrasts")

    if extent["width"] >= 40 and extent["height"] >= 40:
        score += 0.2
    else:
        warnings.append("Spatial spread is limited; scene might feel cramped")

    if height_stats["std"] >= 0.05:
        score += 0.15
    else:
        warnings.append("Height variation is minimal; increase contrast for drama")

    # Encourage some asymmetry / spread
    diagonal = sqrt(extent["width"]**2 + extent["height"]**2)
    if diagonal >= 80:
        score += 0.15
    else:
        warnings.append("Composition diagonal short; consider wider placement")

    score = min(score, 1.0)

    return {
        "score": round(score, 2),
        "warnings": warnings,
    }


def features_to_dicts(features: Iterable[Any]) -> List[Mapping[str, Any]]:
    return [_to_mapping(feat) for feat in (features or [])]


def _collect_numeric(features: Iterable[Mapping[str, Any]], keys: Tuple[str, ...]) -> Iterable[float]:
    for feat in features:
        for key in keys:
            value = feat.get(key)
            number = _as_number(value)
            if number is not None:
                yield float(number)


def _build_stats(values: List[float]) -> Dict[str, float] | None:
    if not values:
        return None
    if len(values) == 1:
        std = 0.0
    else:
        std = pstdev(values)
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "std": std,
    }


def _to_mapping(feature: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(feature, dict):
        return feature
    if hasattr(feature, "to_dict") and callable(feature.to_dict):
        return feature.to_dict()
    return {k: getattr(feature, k) for k in dir(feature) if not k.startswith("_")}


def _as_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None
