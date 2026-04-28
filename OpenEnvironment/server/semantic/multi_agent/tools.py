"""Tool functions exposed to AG2 agents."""

import json
import logging
import copy
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import numpy as np
from PIL import Image

from ..narrative.utils import run_narrative_pipeline
from ..evaluation import (
    compute_feature_metrics,
    compute_texture_metrics,
    evaluate_aesthetic_quality,
    evaluate_quality_rubric,
    summarize_quality_rubric,
)
from ...terrain import apply_actions

try:
    from google import genai  # type: ignore
    from google.genai import types as genai_types  # type: ignore
except ImportError:  # pragma: no cover
    genai = None
    genai_types = None

logger = logging.getLogger(__name__)


def generate_scene_plan(
    command: Annotated[str, "User intent for the terrain scene"],
    critique: Annotated[Optional[str], "Optional critique to address" ] = None,
    scene_state: Annotated[Optional[Dict[str, Any]], "Current terrain state"] = None,
) -> Dict[str, Any]:
    """Run the narrative pipeline and return actions/metadata."""

    state_copy = copy.deepcopy(scene_state) if scene_state is not None else {}
    augmented_command = command.strip()
    if critique:
        augmented_command = f"{augmented_command}\n\nPlease address the following critiques: {critique.strip()}"

    actions, metadata = run_narrative_pipeline(augmented_command, state_copy)
    return {"actions": actions, "metadata": metadata}


def evaluate_scene_actions(
    actions: Annotated[List[Dict[str, Any]], "Actions proposed by the artist"],
) -> Dict[str, Any]:
    """Compute heuristic quality metrics for a proposed action list."""

    features_as_dicts = []
    for action in actions or []:
        feature_type = action.get("type")
        position = action.get("position", {})
        modifiers = action.get("modifiers", {})
        entry = {"type": feature_type, **position, **modifiers}
        features_as_dicts.append(entry)

    metrics = compute_feature_metrics(features_as_dicts)
    quality = evaluate_aesthetic_quality(metrics)
    return {"metrics": metrics, "quality": quality}


def score_scene_plan_visual(
    actions: Annotated[List[Dict[str, Any]], "Actions to render and evaluate"],
    scene_state: Annotated[Optional[Dict[str, Any]], "Current terrain state" ] = None,
    command: Annotated[str, "Original user command" ] = "",
) -> Dict[str, Any]:
    """Render the scene, evaluate heuristics, and optionally call Gemini for feedback."""

    preview = render_scene_preview(
        actions=actions,
        scene_state=scene_state,
        command=command,
        include_arrays=True,
    )
    heuristics = evaluate_scene_actions(actions)
    heightmap_array = preview.pop("heightmap_array", None)
    splatmap_array = preview.pop("splatmap_array", None)
    texture_metrics = compute_texture_metrics(heightmap_array, splatmap_array)
    quality_rubric = evaluate_quality_rubric(
        heuristics["metrics"], texture_metrics
    )
    quality_summary = summarize_quality_rubric(quality_rubric)

    gemini_feedback = None
    if os.environ.get("GEMINI_API_KEY") and genai is not None:
        try:
            gemini_feedback = _call_gemini_judge(
                preview["preview_images"],
                heuristics,
                texture_metrics,
                quality_summary,
            )
        except Exception as exc:  # pragma: no cover - best effort only
            logger.warning("Gemini feedback failed: %s", exc)
            gemini_feedback = {"error": str(exc)}

    return {
        "heuristics": heuristics,
        "texture_metrics": texture_metrics,
        "quality_rubric": quality_rubric,
        "quality_summary": quality_summary,
        "preview": preview,
        "gemini_feedback": gemini_feedback,
    }


def render_scene_preview(
    actions: Annotated[List[Dict[str, Any]], "Actions to render"],
    scene_state: Annotated[Optional[Dict[str, Any]], "Current terrain state" ] = None,
    command: Annotated[str, "Original command for logging" ] = "",
    include_arrays: bool = False,
) -> Dict[str, Any]:
    """Apply the actions to generate height/splat previews saved to disk."""

    base_state = _prepare_state(scene_state)
    base_dir = Path(os.environ.get("TERRAIN_PREVIEW_DIR", "logs/terrain_previews"))
    temp_dir = base_dir / datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    temp_dir.mkdir(parents=True, exist_ok=True)

    heightmap, new_state, splatmap = apply_actions(
        command or "",
        base_state,
        direct_actions=actions,
    )

    height_path = temp_dir / "height.png"
    splat_path = temp_dir / "splat.png"

    _save_heightmap(heightmap, height_path)
    _save_splatmap(splatmap, splat_path)

    preview = {
        "preview_dir": str(temp_dir),
        "preview_images": [str(height_path), str(splat_path)],
        "state": new_state,
        "command": command,
    }

    if include_arrays:
        preview["heightmap_array"] = heightmap
        preview["splatmap_array"] = splatmap

    return preview


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _prepare_state(scene_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if scene_state:
        return copy.deepcopy(scene_state)

    return {
        "features": [],
        "seed": 42,
        "semantic_scene": {},
        "next_id": 1,
    }


def _save_heightmap(heightmap: np.ndarray, path: Path) -> None:
    arr_clipped = np.clip(heightmap, 0.0, 1.0)
    arr16 = (arr_clipped * 65535).astype(np.uint16)
    Image.fromarray(arr16).save(path)


def _save_splatmap(splatmap: np.ndarray, path: Path) -> None:
    arr = np.clip(splatmap, 0.0, 1.0)
    arr8 = (arr * 255).astype(np.uint8)
    if arr8.shape[-1] == 4:
        mode = "RGBA"
    elif arr8.shape[-1] == 3:
        mode = "RGB"
    else:
        mode = "L"
        arr8 = arr8[..., 0]
    Image.fromarray(arr8, mode=mode).save(path)


def _call_gemini_judge(
    image_paths: List[str],
    heuristics: Dict[str, Any],
    texture_metrics: Dict[str, Any],
    quality_summary: str,
) -> Dict[str, Any]:
    if genai is None or genai_types is None:
        raise RuntimeError("google-genai package not available")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    # Use gemini-2.5-flash-image for visual critique (supports images + text, image generation)
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-image")

    parts = []
    parts.append(
        genai_types.Part.from_text(
            "You are an art director evaluating terrain renders. Provide actionable critique grounded in geology and texture placement."
        )
    )
    heuristic_summary = json.dumps(heuristics, indent=2)
    parts.append(genai_types.Part.from_text(
        f"Heuristic metrics:```json\n{heuristic_summary}\n```"
    ))
    texture_summary = json.dumps(texture_metrics, indent=2)
    parts.append(
        genai_types.Part.from_text(
            f"Texture metrics:```json\n{texture_summary}\n```"
        )
    )
    parts.append(
        genai_types.Part.from_text(
            f"Quality rubric summary:\n{quality_summary}"
        )
    )

    for image_path in image_paths:
        with open(image_path, "rb") as fp:
            data = fp.read()
        parts.append(genai_types.Part.from_bytes(data=data, mime_type="image/png"))

    prompt = genai_types.Content(role="user", parts=parts)

    response = client.responses.generate(
        model=model,
        input=[prompt],
        config=genai_types.GenerationConfig(
            temperature=0.3,
            top_p=0.9,
            max_output_tokens=1024,
        ),
    )

    text = getattr(response, "output_text", None)
    text = text or ""
    return {
        "verdict": text,
    }
