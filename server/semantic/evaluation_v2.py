"""
Enhanced evaluation system with progressive scoring and granular rubrics.
"""

from __future__ import annotations

from collections import Counter
from math import sqrt
from statistics import pstdev
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Optional

import numpy as np

# Import from evaluation.py module (not package)
import importlib.util
import sys
from pathlib import Path
evaluation_module_path = Path(__file__).parent / "evaluation.py"
spec = importlib.util.spec_from_file_location("semantic.evaluation_module", evaluation_module_path)
evaluation_module = importlib.util.module_from_spec(spec)
sys.modules["semantic.evaluation_module"] = evaluation_module
spec.loader.exec_module(evaluation_module)

# Use functions from evaluation_module
compute_feature_metrics = evaluation_module.compute_feature_metrics
compute_texture_metrics = evaluation_module.compute_texture_metrics
features_to_dicts = evaluation_module.features_to_dicts


def progressive_score(value: float, thresholds: Dict[str, float]) -> float:
    """
    Calculate progressive score based on tiered thresholds.
    
    Args:
        value: The value to score
        thresholds: Dict with keys: "excellent", "good", "minimum", "poor"
    
    Returns:
        Score between 0.0 and 1.0
    """
    excellent = thresholds.get("excellent", thresholds.get("good", 0))
    good = thresholds.get("good", thresholds.get("minimum", 0))
    minimum = thresholds.get("minimum", 0)
    poor = thresholds.get("poor", minimum * 0.5)
    
    if value >= excellent:
        return 1.0
    elif value >= good:
        # Linear interpolation between good and excellent
        ratio = (value - good) / (excellent - good) if excellent > good else 1.0
        return 0.8 + (0.2 * ratio)
    elif value >= minimum:
        # Linear interpolation between minimum and good
        ratio = (value - minimum) / (good - minimum) if good > minimum else 1.0
        return 0.6 + (0.2 * ratio)
    elif value >= poor:
        # Linear interpolation between poor and minimum
        ratio = (value - poor) / (minimum - poor) if minimum > poor else 1.0
        return 0.3 + (0.3 * ratio)
    else:
        # Below poor threshold
        ratio = min(value / poor, 1.0) if poor > 0 else 0.0
        return 0.3 * ratio


def progressive_range_score(value: float, target_range: Tuple[float, float], ideal_range: Optional[Tuple[float, float]] = None) -> float:
    """
    Score a value within a target range, with optional ideal range for bonus.
    
    Args:
        value: The value to score
        target_range: (min, max) acceptable range
        ideal_range: Optional (min, max) ideal range for bonus points
    
    Returns:
        Score between 0.0 and 1.0
    """
    low, high = target_range
    
    if ideal_range:
        ideal_low, ideal_high = ideal_range
        if ideal_low <= value <= ideal_high:
            return 1.0  # Perfect
    
    if low <= value <= high:
        # Within target range
        if ideal_range:
            ideal_low, ideal_high = ideal_range
            # Check how close to ideal
            if value < ideal_low:
                ratio = (value - low) / (ideal_low - low) if ideal_low > low else 1.0
                return 0.8 + (0.2 * ratio)
            elif value > ideal_high:
                ratio = (high - value) / (high - ideal_high) if high > ideal_high else 1.0
                return 0.8 + (0.2 * ratio)
            else:
                return 1.0
        return 0.8
    elif value < low:
        # Below target
        ratio = max(0.0, value / low) if low > 0 else 0.0
        return 0.8 * ratio
    else:
        # Above target
        excess = value - high
        # Penalize excess more harshly
        return max(0.0, 0.8 - (excess / high * 0.5))


# Enhanced rubric with progressive thresholds
ENHANCED_QUALITY_RUBRIC: Dict[str, Any] = {
    "composition": {
        "feature_count": {
            "poor": 1,
            "minimum": 4,
            "good": 6,
            "excellent": 8,
            "weight": 1.2,  # Higher weight for feature count
        },
        "type_diversity": {
            "poor": 1,
            "minimum": 3,
            "good": 4,
            "excellent": 5,
            "weight": 1.0,
        },
        "extent_diagonal": {
            "poor": 50.0,
            "minimum": 110.0,
            "good": 150.0,
            "excellent": 200.0,
            "weight": 0.8,
        },
        "height_std": {
            "poor": 0.02,
            "minimum": 0.06,
            "good": 0.10,
            "excellent": 0.15,
            "weight": 0.8,
        },
        # New: Spatial balance
        "spatial_balance": {
            "golden_ratio_score": 0.6,  # How close to golden ratio spacing
            "weight": 0.6,
        },
        # New: Feature relationships
        "feature_clustering": {
            "optimal_cluster_score": 0.7,  # Balance between clustered and scattered
            "weight": 0.5,
        },
        # New: Visual hierarchy
        "height_hierarchy": {
            "focal_point_height_ratio": 1.3,  # Focal should be 30% taller than average
            "weight": 0.6,
        },
    },
    "textures": {
        "coverage_targets": {
            "grass": {"target": (0.18, 0.55), "ideal": (0.25, 0.45), "weight": 1.0},
            "rock": {"target": (0.10, 0.45), "ideal": (0.15, 0.35), "weight": 1.0},
            "sand": {"target": (0.05, 0.35), "ideal": (0.10, 0.25), "weight": 0.8},
            "snow": {"target": (0.00, 0.25), "ideal": (0.05, 0.15), "weight": 0.8},
        },
        "min_entropy": {
            "poor": 0.8,
            "minimum": 1.2,
            "good": 1.5,
            "excellent": 2.0,
            "weight": 0.8,
        },
        "alignment": {
            "rock_slope_corr": {
                "poor": 0.15,
                "minimum": 0.35,
                "good": 0.50,
                "excellent": 0.70,
                "weight": 1.0,
            },
            "snow_height_corr": {
                "poor": 0.20,
                "minimum": 0.45,
                "good": 0.60,
                "excellent": 0.80,
                "weight": 1.0,
            },
            "sand_low_corr": {
                "poor": 0.15,
                "minimum": 0.30,
                "good": 0.45,
                "excellent": 0.65,
                "weight": 0.8,
            },
        },
    },
    "weights": {
        "composition": 0.65,  # 65% weight on composition
        "textures": 0.35,      # 35% weight on textures
    },
}


def compute_spatial_balance_score(features: Sequence[Mapping[str, Any]]) -> float:
    """Calculate spatial balance score based on golden ratio and distribution."""
    if len(features) < 2:
        return 0.5  # Neutral score
    
    xs = [float(f.get("x", 0)) for f in features]
    ys = [float(f.get("y", 0)) for f in features]
    
    if not xs or not ys:
        return 0.5
    
    # Calculate centroid
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    
    # Calculate distances from centroid
    distances = [sqrt((x - cx)**2 + (y - cy)**2) for x, y in zip(xs, ys)]
    
    if not distances:
        return 0.5
    
    # Check if distribution is balanced (not all clustered, not all scattered)
    mean_dist = sum(distances) / len(distances)
    std_dist = pstdev(distances) if len(distances) > 1 else 0.0
    
    # Optimal balance: moderate spread with some variation
    if mean_dist > 50 and std_dist > 20:
        return 1.0
    elif mean_dist > 30 and std_dist > 10:
        return 0.8
    elif mean_dist > 20:
        return 0.6
    else:
        return 0.4


def compute_feature_clustering_score(features: Sequence[Mapping[str, Any]]) -> float:
    """Calculate clustering score - balance between clustered and scattered."""
    if len(features) < 3:
        return 0.5
    
    xs = [float(f.get("x", 0)) for f in features]
    ys = [float(f.get("y", 0)) for f in features]
    
    # Calculate average distance between features
    distances = []
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            dist = sqrt((xs[i] - xs[j])**2 + (ys[i] - ys[j])**2)
            distances.append(dist)
    
    if not distances:
        return 0.5
    
    mean_dist = sum(distances) / len(distances)
    
    # Optimal: moderate clustering (not too tight, not too spread)
    if 40 <= mean_dist <= 80:
        return 1.0
    elif 30 <= mean_dist <= 100:
        return 0.8
    elif 20 <= mean_dist <= 120:
        return 0.6
    else:
        return 0.4


def compute_height_hierarchy_score(features: Sequence[Mapping[str, Any]]) -> float:
    """Calculate visual hierarchy score based on height variation."""
    if len(features) < 2:
        return 0.5
    
    heights = []
    for feat in features:
        h = feat.get("height") or feat.get("depth") or feat.get("amp")
        if h is not None:
            heights.append(float(h))
    
    if len(heights) < 2:
        return 0.5
    
    # Find focal point (highest feature)
    max_height = max(heights)
    mean_height = sum(heights) / len(heights)
    
    # Focal should be significantly taller
    if mean_height > 0:
        ratio = max_height / mean_height
        if ratio >= 1.5:
            return 1.0
        elif ratio >= 1.3:
            return 0.8
        elif ratio >= 1.2:
            return 0.6
        else:
            return 0.4
    return 0.5


def evaluate_enhanced_quality_rubric(
    feature_metrics: Mapping[str, Any],
    texture_metrics: Mapping[str, Any],
    rubric: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Evaluate scene quality using enhanced progressive rubric.
    
    Returns:
        Dict with overall_score, categories, warnings, and detailed breakdown
    """
    rubric = rubric or ENHANCED_QUALITY_RUBRIC
    
    warnings: List[str] = []
    categories: Dict[str, Any] = {}
    
    # === COMPOSITION SCORING ===
    composition_rules = rubric.get("composition", {})
    composition_checks: List[Dict[str, Any]] = []
    
    # Feature count (progressive)
    feature_count = feature_metrics.get("feature_count", 0)
    count_thresholds = composition_rules.get("feature_count", {})
    count_score = progressive_score(feature_count, count_thresholds)
    composition_checks.append({
        "name": "feature_count",
        "value": feature_count,
        "score": count_score,
        "weight": count_thresholds.get("weight", 1.0),
        "target": f"{count_thresholds.get('minimum', 4)}+ (excellent: {count_thresholds.get('excellent', 8)}+)",
    })
    if count_score < 0.6:
        warnings.append(f"Feature count ({feature_count}) is below minimum threshold")
    
    # Type diversity (progressive)
    type_diversity = feature_metrics.get("type_diversity", 0)
    diversity_thresholds = composition_rules.get("type_diversity", {})
    diversity_score = progressive_score(type_diversity, diversity_thresholds)
    composition_checks.append({
        "name": "type_diversity",
        "value": type_diversity,
        "score": diversity_score,
        "weight": diversity_thresholds.get("weight", 1.0),
        "target": f"{diversity_thresholds.get('minimum', 3)}+ types",
    })
    if diversity_score < 0.6:
        warnings.append(f"Type diversity ({type_diversity}) is low")
    
    # Extent diagonal (progressive)
    extent = feature_metrics.get("extent") or {"width": 0.0, "height": 0.0}
    diag = sqrt(float(extent.get("width", 0.0))**2 + float(extent.get("height", 0.0))**2)
    extent_thresholds = composition_rules.get("extent_diagonal", {})
    extent_score = progressive_score(diag, extent_thresholds)
    composition_checks.append({
        "name": "extent_diagonal",
        "value": round(diag, 2),
        "score": extent_score,
        "weight": extent_thresholds.get("weight", 1.0),
        "target": f">= {extent_thresholds.get('minimum', 110.0)}",
    })
    if extent_score < 0.6:
        warnings.append(f"Spatial extent ({diag:.1f}) is narrow")
    
    # Height std (progressive)
    height_std = (feature_metrics.get("height_stats") or {}).get("std", 0.0) or 0.0
    height_thresholds = composition_rules.get("height_std", {})
    height_score = progressive_score(height_std, height_thresholds)
    composition_checks.append({
        "name": "height_std",
        "value": round(height_std, 3),
        "score": height_score,
        "weight": height_thresholds.get("weight", 1.0),
        "target": f">= {height_thresholds.get('minimum', 0.06)}",
    })
    if height_score < 0.6:
        warnings.append(f"Height variation ({height_std:.3f}) is low")
    
    # Spatial balance (new)
    features_list = feature_metrics.get("_features", [])
    if not features_list:
        # Try to reconstruct from metrics
        features_list = []
    balance_score = compute_spatial_balance_score(features_list)
    balance_thresholds = composition_rules.get("spatial_balance", {})
    composition_checks.append({
        "name": "spatial_balance",
        "value": round(balance_score, 2),
        "score": balance_score,
        "weight": balance_thresholds.get("weight", 0.6),
        "target": "Balanced distribution",
    })
    
    # Feature clustering (new)
    clustering_score = compute_feature_clustering_score(features_list)
    clustering_thresholds = composition_rules.get("feature_clustering", {})
    composition_checks.append({
        "name": "feature_clustering",
        "value": round(clustering_score, 2),
        "score": clustering_score,
        "weight": clustering_thresholds.get("weight", 0.5),
        "target": "Optimal clustering",
    })
    
    # Height hierarchy (new)
    hierarchy_score = compute_height_hierarchy_score(features_list)
    hierarchy_thresholds = composition_rules.get("height_hierarchy", {})
    composition_checks.append({
        "name": "height_hierarchy",
        "value": round(hierarchy_score, 2),
        "score": hierarchy_score,
        "weight": hierarchy_thresholds.get("weight", 0.6),
        "target": "Clear visual hierarchy",
    })
    
    # Calculate weighted composition score
    total_weight = sum(c.get("weight", 1.0) for c in composition_checks)
    composition_score = sum(c.get("score", 0.0) * c.get("weight", 1.0) for c in composition_checks)
    composition_score = composition_score / total_weight if total_weight > 0 else 0.0
    
    categories["composition"] = {
        "score": round(composition_score, 3),
        "checks": composition_checks,
    }
    
    # === TEXTURE SCORING ===
    texture_rules = rubric.get("textures", {})
    texture_checks: List[Dict[str, Any]] = []
    
    coverage = texture_metrics.get("channel_coverage", {})
    coverage_targets = texture_rules.get("coverage_targets", {})
    
    for channel, config in coverage_targets.items():
        value = float(coverage.get(channel, 0.0))
        target_range = config.get("target", (0.0, 1.0))
        ideal_range = config.get("ideal")
        weight = config.get("weight", 1.0)
        
        coverage_score = progressive_range_score(value, target_range, ideal_range)
        texture_checks.append({
            "name": f"{channel}_coverage",
            "value": round(value, 3),
            "score": coverage_score,
            "weight": weight,
            "target": f"{target_range[0]:.2f}-{target_range[1]:.2f}",
        })
        if coverage_score < 0.6:
            warnings.append(f"{channel.title()} coverage ({value:.2f}) outside target range")
    
    # Entropy (progressive)
    entropy_value = float(texture_metrics.get("coverage_entropy", 0.0))
    entropy_thresholds = texture_rules.get("min_entropy", {})
    entropy_score = progressive_score(entropy_value, entropy_thresholds)
    texture_checks.append({
        "name": "coverage_entropy",
        "value": round(entropy_value, 3),
        "score": entropy_score,
        "weight": entropy_thresholds.get("weight", 0.8),
        "target": f">= {entropy_thresholds.get('minimum', 1.2)}",
    })
    
    # Alignment checks (progressive)
    alignment_rules = texture_rules.get("alignment", {})
    for name, thresholds in alignment_rules.items():
        value = float(texture_metrics.get(name, 0.0))
        score = progressive_score(value, thresholds)
        texture_checks.append({
            "name": name,
            "value": round(value, 3),
            "score": score,
            "weight": thresholds.get("weight", 1.0),
            "target": f">= {thresholds.get('minimum', 0.3)}",
        })
        if score < 0.6:
            warnings.append(f"{name} ({value:.3f}) below threshold")
    
    # Calculate weighted texture score
    total_weight = sum(c.get("weight", 1.0) for c in texture_checks)
    texture_score = sum(c.get("score", 0.0) * c.get("weight", 1.0) for c in texture_checks)
    texture_score = texture_score / total_weight if total_weight > 0 else 0.0
    
    categories["textures"] = {
        "score": round(texture_score, 3),
        "checks": texture_checks,
    }
    
    # === OVERALL SCORE (WEIGHTED) ===
    weights = rubric.get("weights", {"composition": 0.65, "textures": 0.35})
    comp_weight = weights.get("composition", 0.65)
    tex_weight = weights.get("textures", 0.35)
    
    overall_score = (composition_score * comp_weight) + (texture_score * tex_weight)
    
    return {
        "overall_score": round(overall_score, 3),
        "categories": categories,
        "warnings": warnings,
        "detailed_breakdown": {
            "composition_weight": comp_weight,
            "texture_weight": tex_weight,
        },
    }

