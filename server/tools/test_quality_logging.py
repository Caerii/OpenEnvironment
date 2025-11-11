"""
Test script to generate quality logs and demonstrate improvements over time.
"""

import sys
import os
from pathlib import Path

# Add server to path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

# Load environment variables
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
from datetime import datetime
from semantic.tools.quality_tools import evaluate_terrain_quality, refine_composition

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def generate_quality_logs(num_iterations=5):
    """Generate multiple quality evaluations to show improvement over time."""
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    quality_history_file = Path(os.environ.get("QUALITY_HISTORY_FILE", "logs/quality_history.jsonl"))
    quality_history_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info(f"Generating {num_iterations} quality evaluations")
    logger.info(f"Quality history will be logged to: {quality_history_file}")
    logger.info("=" * 80)
    
    scene_state = {
        "features": [],
        "semantic_scene": {"entities": []},
        "seed": 42,
        "base_biome_fn": None,
        "action_history": []
    }
    
    # Start with low-quality actions (2 features, same type)
    current_actions = [
        {
            "kind": "add",
            "type": "mountain",
            "x": 256,
            "y": 256,
            "modifiers": {
                "height": 0.7,
                "radius": 60
            }
        },
        {
            "kind": "add",
            "type": "mountain",
            "x": 300,
            "y": 300,
            "modifiers": {
                "height": 0.65,
                "radius": 55
            }
        }
    ]
    
    results = []
    
    for iteration in range(num_iterations):
        logger.info(f"\n{'='*80}")
        logger.info(f"ITERATION {iteration + 1}/{num_iterations}")
        logger.info(f"{'='*80}")
        
        # Evaluate quality
        logger.info(f"\nEvaluating quality for {len(current_actions)} actions...")
        eval_result = evaluate_terrain_quality(scene_state, current_actions, render_preview=True)
        
        if not eval_result.get("success"):
            logger.error(f"Quality evaluation failed: {eval_result.get('error')}")
            break
        
        eval_data = eval_result.get("data", {})
        score = eval_data.get("overall_score", 0.0)
        composition_score = eval_data.get("composition_score", 0.0)
        texture_score = eval_data.get("texture_score", 0.0)
        warnings = eval_data.get("warnings", [])
        
        logger.info(f"\nQuality Score: {score:.3f}")
        logger.info(f"  Composition: {composition_score:.3f}")
        logger.info(f"  Texture: {texture_score:.3f}")
        logger.info(f"  Warnings: {len(warnings)}")
        
        # Log to quality history
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "iteration": iteration + 1,
            "initial_score": score if iteration == 0 else results[0]["score"],
            "final_score": score,
            "composition_score": composition_score,
            "texture_score": texture_score,
            "refinement_iterations": 0,
            "refinements_applied": [],
            "action_count": len(current_actions),
            "warnings_count": len(warnings),
            "improvement": score - (results[0]["score"] if results else score),
            "improvement_pct": ((score - (results[0]["score"] if results else score)) / (results[0]["score"] if results else 0.01) * 100) if results else 0.0,
        }
        
        # Append to quality history file
        try:
            with quality_history_file.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(entry) + "\n")
            logger.info(f"✓ Logged to {quality_history_file}")
        except Exception as e:
            logger.warning(f"Failed to log quality history: {e}")
        
        results.append({
            "iteration": iteration + 1,
            "score": score,
            "composition_score": composition_score,
            "texture_score": texture_score,
            "action_count": len(current_actions),
            "warnings": warnings[:3]  # First 3 warnings
        })
        
        # Refine if score < 0.8 and we have warnings
        if score < 0.8 and warnings and iteration < num_iterations - 1:
            logger.info(f"\nRefining (score {score:.3f} < 0.8)...")
            refine_result = refine_composition(
                scene_state,
                current_actions,
                warnings[:5],  # Top 5 warnings
                max_refinements=3
            )
            
            if refine_result.get("success"):
                refine_data = refine_result.get("data", {})
                current_actions = refine_data.get("refined_actions", current_actions)
                changes = refine_data.get("changes_made", [])
                logger.info(f"  Applied {len(changes)} refinements:")
                for change in changes:
                    logger.info(f"    - {change}")
            else:
                logger.warning(f"Refinement failed: {refine_result.get('error')}")
                break
        else:
            logger.info(f"\nQuality threshold reached ({score:.3f} >= 0.8) or no more iterations")
            break
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("QUALITY PROGRESSION SUMMARY")
    logger.info(f"{'='*80}")
    
    if results:
        initial_score = results[0]["score"]
        final_score = results[-1]["score"]
        improvement = final_score - initial_score
        improvement_pct = (improvement / initial_score * 100) if initial_score > 0 else 0
        
        logger.info(f"\nInitial Score:  {initial_score:.3f}")
        logger.info(f"Final Score:    {final_score:.3f}")
        logger.info(f"Improvement:    +{improvement:.3f} ({improvement_pct:+.1f}%)")
        logger.info(f"\nIterations:     {len(results)}")
        logger.info(f"Final Actions:  {results[-1]['action_count']}")
        
        logger.info(f"\n{'='*80}")
        logger.info("ITERATION BREAKDOWN")
        logger.info(f"{'='*80}")
        for result in results:
            logger.info(
                f"Iteration {result['iteration']}: "
                f"Score={result['score']:.3f} "
                f"(comp={result['composition_score']:.3f}, "
                f"tex={result['texture_score']:.3f}) "
                f"Actions={result['action_count']}"
            )
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Quality history logged to: {quality_history_file}")
    logger.info(f"Total entries: {len(results)}")
    logger.info(f"{'='*80}\n")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate quality logs")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations")
    args = parser.parse_args()
    
    results = generate_quality_logs(num_iterations=args.iterations)
    
    if results:
        print(f"\n[SUCCESS] Generated {len(results)} quality log entries")
        print(f"Check logs/quality_history.jsonl to see the progression")

