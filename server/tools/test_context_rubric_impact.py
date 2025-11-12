"""
Test to show actual impact of context-aware rubrics.
Compares scores with and without context rubrics to demonstrate improvements.
"""

import sys
import os
from pathlib import Path

server_dir = Path(__file__).parent.parent
parent_dir = server_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

env_file = server_dir / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.split("#")[0].strip()
                if key and value:
                    os.environ[key] = value

import json
import logging
from semantic.tools.quality_tools import evaluate_terrain_quality
from semantic.narrative.utils import run_narrative_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_context_rubric_impact():
    """Test actual impact of context rubrics on quality scores."""
    logger.info("=" * 80)
    logger.info("TESTING CONTEXT RUBRIC IMPACT")
    logger.info("=" * 80)
    
    test_commands = [
        ("create a dramatic mountain landscape with valleys and cliffs", "dramatic_mountain"),
        ("design a serene desert with rolling dunes", "serene_desert"),
        ("build a balanced landscape with hills and valleys", "balanced_landscape"),
    ]
    
    results = []
    
    for command, expected_context in test_commands:
        logger.info(f"\n{'='*80}")
        logger.info(f"Command: {command}")
        logger.info(f"Expected Context: {expected_context}")
        logger.info(f"{'='*80}")
        
        # Generate terrain
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42,
            "base_biome_fn": None,
            "action_history": []
        }
        
        actions, metadata = run_narrative_pipeline(command, scene_state)
        if not actions:
            logger.error("Failed to generate actions")
            continue
        
        logger.info(f"Generated {len(actions)} actions")
        
        # Test WITHOUT context rubric
        result_no_context = evaluate_terrain_quality(
            scene_state=scene_state,
            actions=actions,
            render_preview=True,
            command=None  # No command = no context rubric
        )
        
        # Test WITH context rubric
        result_with_context = evaluate_terrain_quality(
            scene_state=scene_state,
            actions=actions,
            render_preview=True,
            command=command  # With command = context rubric
        )
        
        if result_no_context.get("success") and result_with_context.get("success"):
            no_ctx_data = result_no_context.get("data", {})
            with_ctx_data = result_with_context.get("data", {})
            
            no_ctx_score = no_ctx_data.get("overall_score", 0.0)
            with_ctx_score = with_ctx_data.get("overall_score", 0.0)
            difference = with_ctx_score - no_ctx_score
            
            no_ctx_comp = no_ctx_data.get("composition_score", 0.0)
            with_ctx_comp = with_ctx_data.get("composition_score", 0.0)
            comp_diff = with_ctx_comp - no_ctx_comp
            
            no_ctx_tex = no_ctx_data.get("texture_score", 0.0)
            with_ctx_tex = with_ctx_data.get("texture_score", 0.0)
            tex_diff = with_ctx_tex - no_ctx_tex
            
            logger.info(f"\nResults:")
            logger.info(f"  Without context rubric:")
            logger.info(f"    Overall: {no_ctx_score:.3f}")
            logger.info(f"    Composition: {no_ctx_comp:.3f}")
            logger.info(f"    Texture: {no_ctx_tex:.3f}")
            logger.info(f"    Warnings: {len(no_ctx_data.get('warnings', []))}")
            
            logger.info(f"\n  With context rubric:")
            logger.info(f"    Overall: {with_ctx_score:.3f}")
            logger.info(f"    Composition: {with_ctx_comp:.3f}")
            logger.info(f"    Texture: {with_ctx_tex:.3f}")
            logger.info(f"    Warnings: {len(with_ctx_data.get('warnings', []))}")
            
            logger.info(f"\n  Difference:")
            logger.info(f"    Overall: {difference:+.3f} ({difference*100:+.1f}%)")
            logger.info(f"    Composition: {comp_diff:+.3f}")
            logger.info(f"    Texture: {tex_diff:+.3f}")
            logger.info(f"    Warnings: {len(with_ctx_data.get('warnings', [])) - len(no_ctx_data.get('warnings', [])):+d}")
            
            # Analyze what changed
            no_ctx_warnings = set(no_ctx_data.get("warnings", []))
            with_ctx_warnings = set(with_ctx_data.get("warnings", []))
            
            if no_ctx_warnings != with_ctx_warnings:
                logger.info(f"\n  Warning Changes:")
                removed = no_ctx_warnings - with_ctx_warnings
                added = with_ctx_warnings - no_ctx_warnings
                if removed:
                    logger.info(f"    Removed: {list(removed)}")
                if added:
                    logger.info(f"    Added: {list(added)}")
            
            results.append({
                "command": command,
                "expected_context": expected_context,
                "no_context": {
                    "overall": no_ctx_score,
                    "composition": no_ctx_comp,
                    "texture": no_ctx_tex,
                    "warnings": no_ctx_data.get("warnings", []),
                },
                "with_context": {
                    "overall": with_ctx_score,
                    "composition": with_ctx_comp,
                    "texture": with_ctx_tex,
                    "warnings": with_ctx_data.get("warnings", []),
                },
                "difference": {
                    "overall": difference,
                    "composition": comp_diff,
                    "texture": tex_diff,
                },
            })
        else:
            logger.error("Failed to evaluate quality")
            if not result_no_context.get("success"):
                logger.error(f"  No context error: {result_no_context.get('error')}")
            if not result_with_context.get("success"):
                logger.error(f"  With context error: {result_with_context.get('error')}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    
    if results:
        avg_diff = sum(r["difference"]["overall"] for r in results) / len(results)
        logger.info(f"\nAverage Overall Score Difference: {avg_diff:+.3f}")
        
        logger.info(f"\nDetailed Results:")
        for r in results:
            diff = r["difference"]["overall"]
            status = "✓ IMPROVED" if diff > 0.05 else "⚠ SAME" if abs(diff) < 0.05 else "✗ WORSE"
            logger.info(f"\n  {r['command'][:50]}...")
            logger.info(f"    {status}: {r['no_context']['overall']:.3f} → {r['with_context']['overall']:.3f} ({diff:+.3f})")
            logger.info(f"    Context: {r['expected_context']}")
            logger.info(f"    Warnings: {len(r['no_context']['warnings'])} → {len(r['with_context']['warnings'])}")
    
    return results


if __name__ == "__main__":
    results = test_context_rubric_impact()
    logger.info("\n" + "=" * 80)
    logger.info("Test Complete!")
    logger.info("=" * 80)

