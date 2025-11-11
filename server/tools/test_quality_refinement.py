"""
Test script to demonstrate quality evaluation and refinement improvements.
"""

import sys
import os
from pathlib import Path

# Add server to path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

# Load environment variables from .env file
env_file = server_dir / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.split("#")[0].strip()  # Remove comments
                if key and value:
                    os.environ[key] = value

import json
import logging
from semantic.react_agent_v2 import ReActAgentV2
from semantic.llm.factory import create_llm_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_quality_refinement():
    """Test quality evaluation and refinement with a real command."""
    
    # Initialize LLM client
    llm_client = create_llm_client()
    if not llm_client:
        logger.error("Failed to create LLM client - check API keys")
        return
    
    # Initialize ReAct agent
    agent = ReActAgentV2(
        llm_client=llm_client,
        max_iterations=5,
        prompt_profile="compact"
    )
    
    # Test command
    command = "create a dramatic mountain landscape with valleys and cliffs"
    
    # Initial scene state
    scene_state = {
        "features": [],
        "semantic_scene": {"entities": []},
        "seed": 42,
        "base_biome_fn": None,
        "action_history": []
    }
    
    logger.info("=" * 80)
    logger.info(f"Testing quality refinement with command: '{command}'")
    logger.info("=" * 80)
    
    # Run ReAct agent
    result = agent.solve(command, scene_state, temperature=0.3)
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    
    logger.info(f"\nSuccess: {result.get('success')}")
    logger.info(f"Iterations: {result.get('iterations')}")
    logger.info(f"Total tool calls: {result.get('total_tool_calls')}")
    logger.info(f"Actions generated: {len(result.get('actions', []))}")
    
    # Quality info
    quality_info = result.get('quality_info')
    if quality_info:
        logger.info("\n" + "-" * 80)
        logger.info("QUALITY METRICS")
        logger.info("-" * 80)
        
        initial_score = quality_info.get('initial_score')
        final_score = quality_info.get('final_score')
        composition_score = quality_info.get('composition_score')
        texture_score = quality_info.get('texture_score')
        refinement_iterations = quality_info.get('refinement_iterations', 0)
        refinements_applied = quality_info.get('refinements_applied', [])
        warnings = quality_info.get('warnings', [])
        
        logger.info(f"\nInitial Quality Score: {initial_score:.3f}")
        logger.info(f"Final Quality Score: {final_score:.3f}")
        
        if initial_score and final_score:
            improvement = final_score - initial_score
            improvement_pct = (improvement / initial_score * 100) if initial_score > 0 else 0
            logger.info(f"Improvement: +{improvement:.3f} ({improvement_pct:+.1f}%)")
        
        logger.info(f"\nComposition Score: {composition_score:.3f}")
        logger.info(f"Texture Score: {texture_score:.3f}")
        
        logger.info(f"\nRefinement Iterations: {refinement_iterations}")
        if refinements_applied:
            logger.info("\nRefinements Applied:")
            for i, refinement in enumerate(refinements_applied, 1):
                logger.info(f"  {i}. {refinement}")
        
        if warnings:
            logger.info("\nQuality Warnings:")
            for i, warning in enumerate(warnings[:5], 1):
                logger.info(f"  {i}. {warning}")
    
    # Actions summary
    actions = result.get('actions', [])
    if actions:
        logger.info("\n" + "-" * 80)
        logger.info("GENERATED ACTIONS")
        logger.info("-" * 80)
        
        type_counts = {}
        for action in actions:
            action_type = action.get('type', 'unknown')
            type_counts[action_type] = type_counts.get(action_type, 0) + 1
        
        logger.info(f"\nTotal actions: {len(actions)}")
        logger.info("\nFeature types:")
        for feat_type, count in sorted(type_counts.items()):
            logger.info(f"  - {feat_type}: {count}")
        
        # Show first few actions
        logger.info("\nFirst 3 actions:")
        for i, action in enumerate(actions[:3], 1):
            logger.info(f"\n  {i}. {action.get('kind')} {action.get('type')}")
            logger.info(f"     Position: ({action.get('x', '?')}, {action.get('y', '?')})")
            modifiers = action.get('modifiers', {})
            if modifiers:
                logger.info(f"     Modifiers: {list(modifiers.keys())}")
    
    # Save results
    output_file = Path("logs") / "quality_test_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    logger.info(f"\n\nResults saved to: {output_file}")
    logger.info("\n" + "=" * 80)
    
    return result


if __name__ == "__main__":
    test_quality_refinement()

