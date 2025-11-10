"""Diagnostic script to evaluate narrative-driven generation end-to-end."""

import json
import time
import urllib.request
from typing import List, Dict, Any

from server.semantic.evaluation import compute_feature_metrics, evaluate_aesthetic_quality, features_to_dicts

API_URL = "http://localhost:8001/api/generate"

TEST_COMMANDS: List[str] = [
    "create dramatic mountains",
    "design serene valley",
    "build rugged cliffs",
    "generate beautiful dunes",
    "craft a majestic canyon scene"
]


def reset_state() -> None:
    data = json.dumps({"text": ""}).encode("utf-8")
    req = urllib.request.Request(
        API_URL.replace("/api/generate", "/api/reset"),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req):
        pass


def call_generate(command: str) -> Dict[str, Any]:
    data = json.dumps({"text": command}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload)


def analyze_features(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    metrics["count"] = len(features)

    type_counts: Dict[str, int] = {}
    xs: List[float] = []
    ys: List[float] = []

    for feat in features:
        ftype = feat.get("type", "unknown")
        type_counts[ftype] = type_counts.get(ftype, 0) + 1

        x = feat.get("x")
        y = feat.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            xs.append(float(x))
            ys.append(float(y))

    metrics["types"] = type_counts

    if xs and ys:
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        metrics["spatial_width"] = max_x - min_x
        metrics["spatial_height"] = max_y - min_y
        metrics["centroid"] = {
            "x": sum(xs) / len(xs),
            "y": sum(ys) / len(ys)
        }
    else:
        metrics["spatial_width"] = None
        metrics["spatial_height"] = None
        metrics["centroid"] = None

    return metrics


def main() -> None:
    print("Narrative Tool End-to-End Analysis")
    print("API:", API_URL)
    print("Commands:")
    for cmd in TEST_COMMANDS:
        print("  -", cmd)

    results: List[Dict[str, Any]] = []

    for cmd in TEST_COMMANDS:
        reset_state()
        print("\n=== Command:", cmd)
        payload = call_generate(cmd)
        state = payload.get("state", {})
        features = state.get("features", [])
        metrics = compute_feature_metrics(features)
        quality = evaluate_aesthetic_quality(metrics)

        print(f"  ok: {payload.get('ok')}")
        print(f"  feature_count: {metrics['feature_count']}")
        print(f"  parser: {state.get('_debug_last_parser')}\n  type_distribution: {metrics['type_counts']}")
        extent = metrics.get("extent") or {}
        print(f"  spatial_width: {extent.get('width')}\n  spatial_height: {extent.get('height')}")
        print(f"  centroid: {metrics.get('centroid')}")
        print(f"  height_stats: {metrics.get('height_stats')}\n  quality_score: {quality['score']}")
        if quality["warnings"]:
            print("  warnings:")
            for warning in quality["warnings"]:
                print(f"    - {warning}")

        if features:
            sample = features[0]
            print("  sample_feature:", json.dumps(sample, indent=2))

        results.append({
            "command": cmd,
            "ok": payload.get("ok"),
            "metrics": metrics,
            "feature_count": metrics["feature_count"]
        })

        # Rate limit requests slightly
        time.sleep(0.5)

    # Summary report
    print("\n=== Summary ===")
    for result in results:
        cmd = result["command"]
        fc = result["feature_count"]
        type_counts = result["metrics"].get("type_counts", {})
        print(f"{cmd!r}: features={fc}, types={type_counts}")


if __name__ == "__main__":
    main()
