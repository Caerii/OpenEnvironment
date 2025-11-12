"""
Direct test of quality evaluation and refinement without narrative tool.
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
from semantic.tools.quality_tools import evaluate_terrain_quality, refine_composition

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_quality_evaluation():
    """Test quality evaluation with sample actions."""
    
    # Sample actions (low quality - only 2 features, same type)
    initial_actions = [
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
    
    scene_state = {
        "features": [],
        "semantic_scene": {"entities": []},
        "seed": 42,
        "base_biome_fn": None,
        "action_history": []
    }
    
    logger.info("=" * 80)
    logger.info("TESTING QUALITY EVALUATION AND REFINEMENT")
    logger.info("=" * 80)
    
    logger.info(f"\nInitial actions: {len(initial_actions)} features")
    for i, action in enumerate(initial_actions, 1):
        logger.info(f"  {i}. {action['type']} at ({action['x']}, {action['y']})")
    
    # Step 1: Evaluate initial quality
    logger.info("\n" + "-" * 80)
    logger.info("STEP 1: Evaluating Initial Quality")
    logger.info("-" * 80)
    
    eval_result = evaluate_terrain_quality(scene_state, initial_actions, render_preview=True)
    
    if not eval_result.get("success"):
        logger.error(f"Quality evaluation failed: {eval_result.get('error')}")
        return
    
    eval_data = eval_result.get("data", {})
    initial_score = eval_data.get("overall_score", 0.0)
    composition_score = eval_data.get("composition_score", 0.0)
    texture_score = eval_data.get("texture_score", 0.0)
    warnings = eval_data.get("warnings", [])
    
    logger.info(f"\nInitial Quality Score: {initial_score:.3f}")
    logger.info(f"  Composition: {composition_score:.3f}")
    logger.info(f"  Texture: {texture_score:.3f}")
    logger.info(f"\nWarnings ({len(warnings)}):")
    for i, warning in enumerate(warnings[:5], 1):
        logger.info(f"  {i}. {warning}")
    
    # Step 2: Refine if needed
    if initial_score < 0.8 and warnings:
        logger.info("\n" + "-" * 80)
        logger.info("STEP 2: Refining Composition")
        logger.info("-" * 80)
        
        refine_result = refine_composition(
            scene_state,
            initial_actions,
            warnings,
            max_refinements=5
        )
        
        if refine_result.get("success"):
            refine_data = refine_result.get("data", {})
            refined_actions = refine_data.get("refined_actions", initial_actions)
            changes_made = refine_data.get("changes_made", [])
            
            logger.info(f"\nRefined actions: {len(refined_actions)} features")
            logger.info(f"\nChanges made ({len(changes_made)}):")
            for i, change in enumerate(changes_made, 1):
                logger.info(f"  {i}. {change}")
            
            # Step 3: Re-evaluate
            logger.info("\n" + "-" * 80)
            logger.info("STEP 3: Evaluating Refined Quality")
            logger.info("-" * 80)
            
            final_eval_result = evaluate_terrain_quality(
                scene_state,
                refined_actions,
                render_preview=True
            )
            
            if final_eval_result.get("success"):
                final_eval_data = final_eval_result.get("data", {})
                final_score = final_eval_data.get("overall_score", 0.0)
                final_composition = final_eval_data.get("composition_score", 0.0)
                final_texture = final_eval_data.get("texture_score", 0.0)
                final_warnings = final_eval_data.get("warnings", [])
                
                logger.info(f"\nFinal Quality Score: {final_score:.3f}")
                logger.info(f"  Composition: {final_composition:.3f}")
                logger.info(f"  Texture: {final_texture:.3f}")
                
                improvement = final_score - initial_score
                improvement_pct = (improvement / initial_score * 100) if initial_score > 0 else 0
                
                logger.info("\n" + "=" * 80)
                logger.info("IMPROVEMENT SUMMARY")
                logger.info("=" * 80)
                logger.info(f"\nInitial Score:  {initial_score:.3f}")
                logger.info(f"Final Score:    {final_score:.3f}")
                logger.info(f"Improvement:    +{improvement:.3f} ({improvement_pct:+.1f}%)")
                logger.info(f"\nComposition: {composition_score:.3f} → {final_composition:.3f}")
                logger.info(f"Texture:     {texture_score:.3f} → {final_texture:.3f}")
                
                if final_warnings:
                    logger.info(f"\nRemaining warnings ({len(final_warnings)}):")
                    for i, warning in enumerate(final_warnings[:3], 1):
                        logger.info(f"  {i}. {warning}")
                
                # Show refined actions
                logger.info("\n" + "-" * 80)
                logger.info("REFINED ACTIONS")
                logger.info("-" * 80)
                type_counts = {}
                for action in refined_actions:
                    action_type = action.get('type', 'unknown')
                    type_counts[action_type] = type_counts.get(action_type, 0) + 1
                
                logger.info(f"\nTotal: {len(refined_actions)} features")
                for feat_type, count in sorted(type_counts.items()):
                    logger.info(f"  - {feat_type}: {count}")
                
                logger.info("\n" + "=" * 80)
                
                return {
                    "initial_score": initial_score,
                    "final_score": final_score,
                    "improvement": improvement,
                    "initial_actions": len(initial_actions),
                    "refined_actions": len(refined_actions),
                    "changes": changes_made
                }
    
    logger.info("\n" + "=" * 80)
    return None


if __name__ == "__main__":
    result = test_quality_evaluation()
    if result:
        print(f"\n[SUCCESS] Test completed successfully!")
        print(f"   Quality improved from {result['initial_score']:.3f} to {result['final_score']:.3f}")
        print(f"   Improvement: +{result['improvement']:.3f} ({result['improvement']/result['initial_score']*100:.1f}%)")
    else:
        print("\n[INFO] Test completed but no refinement was applied")

