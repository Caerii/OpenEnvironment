"""
Full end-to-end test of ReAct agent with quality refinement and logging.
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
from semantic.react_agent_v2 import ReActAgentV2
from semantic.llm.factory import create_llm_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_full_workflow():
    """Test full ReAct workflow with quality refinement."""
    
    # Initialize LLM client
    llm_client = create_llm_client()
    if not llm_client:
        logger.error("Failed to create LLM client - check API keys")
        return None
    
    # Initialize ReAct agent
    agent = ReActAgentV2(
        llm_client=llm_client,
        max_iterations=5,
        prompt_profile="compact"
    )
    
    # Test commands
    test_commands = [
        "create a dramatic mountain landscape with valleys and cliffs",
        "add 5 hills in a circle around the peak",
        "design a serene desert with rolling dunes"
    ]
    
    scene_state = {
        "features": [],
        "semantic_scene": {"entities": []},
        "seed": 42,
        "base_biome_fn": None,
        "action_history": []
    }
    
    all_results = []
    
    for i, command in enumerate(test_commands, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"TEST {i}/{len(test_commands)}: {command}")
        logger.info(f"{'='*80}")
        
        # Run ReAct agent
        result = agent.solve(command, scene_state, temperature=0.3)
        
        # Extract quality info
        quality_info = result.get('quality_info')
        if quality_info:
            initial_score = quality_info.get('initial_score')
            final_score = quality_info.get('final_score')
            refinement_iterations = quality_info.get('refinement_iterations', 0)
            
            logger.info(f"\nQuality: {initial_score:.3f} → {final_score:.3f}")
            logger.info(f"Refinement iterations: {refinement_iterations}")
            logger.info(f"Actions generated: {len(result.get('actions', []))}")
        
        all_results.append({
            "command": command,
            "success": result.get('success'),
            "actions_count": len(result.get('actions', [])),
            "quality_info": quality_info
        })
        
        # Update scene state for next command
        if result.get('success') and result.get('actions'):
            # In a real scenario, we'd apply these actions to update the scene
            # For testing, we'll just continue with empty state
            pass
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("FULL WORKFLOW TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    successful = sum(1 for r in all_results if r['success'])
    logger.info(f"\nSuccessful: {successful}/{len(test_commands)}")
    
    for result in all_results:
        qi = result.get('quality_info')
        if qi:
            logger.info(
                f"\nCommand: {result['command'][:50]}..."
                f"\n  Success: {result['success']}"
                f"\n  Actions: {result['actions_count']}"
                f"\n  Quality: {qi.get('initial_score', 'N/A')} → {qi.get('final_score', 'N/A')}"
                f"\n  Refinements: {qi.get('refinement_iterations', 0)}"
            )
    
    logger.info(f"\n{'='*80}\n")
    
    return all_results


if __name__ == "__main__":
    results = test_full_workflow()
    if results:
        print(f"\n[SUCCESS] Tested {len(results)} commands")
        print("Check logs/quality_history.jsonl for quality progression")

