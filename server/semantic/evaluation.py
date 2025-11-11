"""Evaluation helpers for terrain outputs."""

from __future__ import annotations

from collections import Counter
from math import sqrt
from statistics import pstdev
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Optional

import numpy as np


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


DEFAULT_QUALITY_RUBRIC: Dict[str, Any] = {
    "composition": {
        "min_feature_count": 4,
        "min_type_diversity": 3,
        "min_extent_diagonal": 110.0,
        "min_height_std": 0.06,
    },
    "textures": {
        "coverage_targets": {
            "grass": (0.18, 0.55),
            "rock": (0.10, 0.45),
            "sand": (0.05, 0.35),
            "snow": (0.00, 0.25),
        },
        "min_entropy": 1.2,
        "min_rock_slope_corr": 0.35,
        "min_snow_height_corr": 0.45,
        "min_sand_low_corr": 0.30,
    },
}


def compute_texture_metrics(
    heightmap: np.ndarray | None,
    splatmap: np.ndarray | None,
) -> Dict[str, Any]:
    """Compute texture coverage and alignment metrics from rendered outputs."""

    if heightmap is None or splatmap is None:
        return {
            "channel_coverage": {},
            "coverage_entropy": 0.0,
            "rock_slope_corr": 0.0,
            "snow_height_corr": 0.0,
            "sand_height_corr": 0.0,
            "sand_low_corr": 0.0,
            "roughness_mean": 0.0,
            "roughness_std": 0.0,
        }

    height = np.asarray(heightmap, dtype=np.float32)
    splat = np.asarray(splatmap, dtype=np.float32)

    if splat.ndim != 3 or splat.shape[-1] < 4:
        raise ValueError("Splatmap must be HxWx4 array")

    # Normalise height to [0, 1]
    h_min = float(height.min())
    h_ptp = float(height.max() - h_min)
    height_norm = (height - h_min) / (h_ptp + 1e-6)

    # Compute slope magnitude
    gy, gx = np.gradient(height_norm)
    slope = np.sqrt(gx * gx + gy * gy)
    slope_norm = slope / (slope.max() + 1e-6)

    # Channel coverage statistics
    channel_means = splat.mean(axis=(0, 1))
    channel_names = ("grass", "rock", "sand", "snow")
    coverage_map = {
        name: float(channel_means[idx]) for idx, name in enumerate(channel_names)
    }

    coverage_entropy = 0.0
    positive_means = [val for val in channel_means if val > 1e-6]
    if positive_means:
        coverage_entropy = float(
            -sum(val * np.log(val) for val in positive_means)
        )

    rock_corr = _safe_corr(slope_norm, splat[..., 1])
    snow_corr = _safe_corr(height_norm, splat[..., 3])
    sand_height_corr = _safe_corr(height_norm, splat[..., 2])
    sand_low_corr = _safe_corr(1.0 - height_norm, splat[..., 2])

    return {
        "channel_coverage": coverage_map,
        "coverage_entropy": coverage_entropy,
        "rock_slope_corr": rock_corr,
        "snow_height_corr": snow_corr,
        "sand_height_corr": sand_height_corr,
        "sand_low_corr": sand_low_corr,
        "roughness_mean": float(slope_norm.mean()),
        "roughness_std": float(slope_norm.std()),
    }


def evaluate_quality_rubric(
    feature_metrics: Mapping[str, Any],
    texture_metrics: Mapping[str, Any],
    rubric: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Evaluate scene quality against a composite rubric."""

    rubric = rubric or DEFAULT_QUALITY_RUBRIC

    warnings: List[str] = []
    categories: Dict[str, Any] = {}
    scores: List[float] = []

    composition_rules = rubric.get("composition", {})
    extent = feature_metrics.get("extent") or {"width": 0.0, "height": 0.0}
    diag = sqrt(
        float(extent.get("width", 0.0)) ** 2 + float(extent.get("height", 0.0)) ** 2
    )
    height_std = (feature_metrics.get("height_stats") or {}).get("std", 0.0) or 0.0

    composition_checks = [
        {
            "name": "feature_count",
            "value": feature_metrics.get("feature_count", 0),
            "target": f">= {composition_rules.get('min_feature_count', 0)}",
            "passed": feature_metrics.get("feature_count", 0)
            >= composition_rules.get("min_feature_count", 0),
            "weight": 1.0,
            "warning": "Add more focal/supporting features to reach the desired density.",
        },
        {
            "name": "type_diversity",
            "value": feature_metrics.get("type_diversity", 0),
            "target": f">= {composition_rules.get('min_type_diversity', 0)}",
            "passed": feature_metrics.get("type_diversity", 0)
            >= composition_rules.get("min_type_diversity", 0),
            "weight": 1.0,
            "warning": "Feature diversity is low; introduce contrasting primitives.",
        },
        {
            "name": "extent_diagonal",
            "value": round(diag, 2),
            "target": f">= {composition_rules.get('min_extent_diagonal', 0)}",
            "passed": diag >= composition_rules.get("min_extent_diagonal", 0.0),
            "weight": 1.0,
            "warning": "Scene coverage is narrow; spread features further apart.",
        },
        {
            "name": "height_std",
            "value": round(height_std, 3),
            "target": f">= {composition_rules.get('min_height_std', 0.0)}",
            "passed": height_std >= composition_rules.get("min_height_std", 0.0),
            "weight": 1.0,
            "warning": "Elevation variance is low; vary heights/depths for richer silhouettes.",
        },
    ]

    composition_score, composition_details = _evaluate_checks(
        composition_checks, warnings
    )
    categories["composition"] = {
        "score": composition_score,
        "checks": composition_details,
    }
    scores.append(composition_score)

    texture_rules = rubric.get("textures", {})
    coverage = texture_metrics.get("channel_coverage", {})

    coverage_checks: List[Dict[str, Any]] = []
    for channel, bounds in texture_rules.get("coverage_targets", {}).items():
        value = float(coverage.get(channel, 0.0))
        low, high = bounds
        passed = low <= value <= high
        coverage_checks.append(
            {
                "name": f"{channel}_coverage",
                "value": round(value, 3),
                "target": f"{low:.2f}–{high:.2f}",
                "passed": passed,
                "weight": 1.0,
                "warning": f"{channel.title()} coverage {value:.2f} outside desired {low:.2f}-{high:.2f} range.",
            }
        )

    entropy_value = float(texture_metrics.get("coverage_entropy", 0.0))
    coverage_checks.append(
        {
            "name": "coverage_entropy",
            "value": round(entropy_value, 3),
            "target": f">= {texture_rules.get('min_entropy', 0.0)}",
            "passed": entropy_value >= texture_rules.get("min_entropy", 0.0),
            "weight": 1.0,
            "warning": "Texture allocation is overly concentrated; increase distribution variety.",
        }
    )

    alignment_checks = [
        {
            "name": "rock_slope_corr",
            "value": round(float(texture_metrics.get("rock_slope_corr", 0.0)), 3),
            "target": f">= {texture_rules.get('min_rock_slope_corr', 0.0)}",
            "passed": float(texture_metrics.get("rock_slope_corr", 0.0))
            >= texture_rules.get("min_rock_slope_corr", 0.0),
            "weight": 1.0,
            "warning": "Rock texture placement does not align with steep slopes; tighten cliff masks.",
        },
        {
            "name": "snow_height_corr",
            "value": round(float(texture_metrics.get("snow_height_corr", 0.0)), 3),
            "target": f">= {texture_rules.get('min_snow_height_corr', 0.0)}",
            "passed": float(texture_metrics.get("snow_height_corr", 0.0))
            >= texture_rules.get("min_snow_height_corr", 0.0),
            "weight": 1.0,
            "warning": "Snow coverage is not focusing on high elevations; adjust snowline thresholds.",
        },
        {
            "name": "sand_low_corr",
            "value": round(float(texture_metrics.get("sand_low_corr", 0.0)), 3),
            "target": f">= {texture_rules.get('min_sand_low_corr', 0.0)}",
            "passed": float(texture_metrics.get("sand_low_corr", 0.0))
            >= texture_rules.get("min_sand_low_corr", 0.0),
            "weight": 1.0,
            "warning": "Sand coverage isn't grounded in low/flat regions; revisit dune placement.",
        },
    ]

    texture_checks = coverage_checks + alignment_checks
    texture_score, texture_details = _evaluate_checks(texture_checks, warnings)
    categories["textures"] = {
        "score": texture_score,
        "checks": texture_details,
    }
    scores.append(texture_score)

    overall = round(sum(scores) / len(scores), 2) if scores else 0.0

    return {
        "overall_score": overall,
        "categories": categories,
        "warnings": warnings,
    }


def summarize_quality_rubric(
    rubric_result: Mapping[str, Any],
    max_warnings: int = 4,
) -> str:
    """Generate a concise textual summary of rubric results."""

    if not rubric_result:
        return "No rubric evaluation available."

    overall = rubric_result.get("overall_score")
    warnings = rubric_result.get("warnings", [])
    categories = rubric_result.get("categories", {})

    lines = [f"Overall quality score: {overall:.2f}" if isinstance(overall, (int, float)) else "Overall quality score unavailable."]

    for name, data in categories.items():
        score = data.get("score")
        if isinstance(score, (int, float)):
            lines.append(f"- {name.title()} score: {score:.2f}")

        checks = data.get("checks") or []
        failed = [c for c in checks if not c.get("passed")]
        if failed:
            sample = failed[:max_warnings]
            for check in sample:
                lines.append(
                    f"  • {check.get('name')}: observed {check.get('value')} vs target {check.get('target')}"
                )

    if warnings:
        for warning in warnings[:max_warnings]:
            lines.append(f"Warning: {warning}")

    return "\n".join(lines)


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


def _evaluate_checks(
    checks: Sequence[Dict[str, Any]], warnings: List[str]
) -> Tuple[float, List[Dict[str, Any]]]:
    if not checks:
        return 1.0, []

    total_weight = sum(check.get("weight", 1.0) for check in checks)
    if total_weight <= 0:
        total_weight = 1.0

    score = 0.0
    details: List[Dict[str, Any]] = []

    for check in checks:
        weight = check.get("weight", 1.0)
        passed = bool(check.get("passed"))
        detail = {
            "name": check.get("name"),
            "value": check.get("value"),
            "target": check.get("target"),
            "passed": passed,
            "weight": weight,
        }
        details.append(detail)

        if passed:
            score += weight
        else:
            warning = check.get("warning")
            if warning:
                warnings.append(warning)

    normalized = score / total_weight if total_weight else 0.0
    return round(min(normalized, 1.0), 2), details


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)
    a_std = float(a.std())
    b_std = float(b.std())
    if a_std < 1e-6 or b_std < 1e-6:
        return 0.0
    corr = np.corrcoef(a, b)[0, 1]
    if np.isnan(corr):
        return 0.0
    return float(corr)
