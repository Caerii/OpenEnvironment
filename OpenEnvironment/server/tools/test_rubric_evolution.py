"""
Test script for rubric evolution system.
Tests the LLM-as-a-Judge rubric evolution with real terrain data.
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
from server.semantic.evaluation.rubric_evolution import RubricEvolutionService
from semantic.evaluation import DEFAULT_QUALITY_RUBRIC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def find_terrain_previews():
    """Find available terrain preview images."""
    preview_dir = Path("logs/terrain_previews")
    if not preview_dir.exists():
        logger.warning(f"Preview directory not found: {preview_dir}")
        return []
    
    terrains = []
    for session_dir in preview_dir.iterdir():
        if session_dir.is_dir():
            height_path = session_dir / "height.png"
            splat_path = session_dir / "splat.png"
            
            if height_path.exists() and splat_path.exists():
                # Try to find associated quality score
                score = 0.5  # Default
                command = "unknown"
                
                # Look for metadata
                metadata_path = session_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path) as f:
                            metadata = json.load(f)
                            score = metadata.get("score", 0.5)
                            command = metadata.get("command", "unknown")
                    except:
                        pass
                
                terrains.append({
                    "heightmap_path": str(height_path),
                    "splatmap_path": str(splat_path),
                    "score": score,
                    "command": command,
                    "actions": [],  # Would need to load from metadata
                })
    
    return terrains


def test_context_rubric_generation():
    """Test context-aware rubric generation."""
    logger.info("=" * 80)
    logger.info("TEST 1: Context-Aware Rubric Generation")
    logger.info("=" * 80)
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set, skipping test")
        return None
    
    try:
        service = RubricEvolutionService(gemini_key)
        
        test_commands = [
            "create a dramatic mountain landscape with valleys and cliffs",
            "design a serene desert with rolling dunes",
            "build a balanced landscape with hills and valleys",
        ]
        
        base_rubric = DEFAULT_QUALITY_RUBRIC
        
        results = []
        for command in test_commands:
            logger.info(f"\nTesting command: {command}")
            try:
                context_rubric = service.generate_context_rubric(command, base_rubric)
                
                context_info = context_rubric.get("_context", {})
                logger.info(f"Context type: {context_info.get('context_type', 'unknown')}")
                logger.info(f"Priority criteria: {context_info.get('priority_criteria', [])}")
                logger.info(f"Aesthetic goals: {context_info.get('aesthetic_goals', [])}")
                
                results.append({
                    "command": command,
                    "context_rubric": context_rubric,
                    "success": True,
                })
            except Exception as e:
                logger.error(f"Failed for command '{command}': {e}", exc_info=True)
                results.append({
                    "command": command,
                    "error": str(e),
                    "success": False,
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Context rubric generation test failed: {e}", exc_info=True)
        return None


def test_rubric_evolution():
    """Test rubric evolution from terrain batch."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Rubric Evolution from Terrain Batch")
    logger.info("=" * 80)
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set, skipping test")
        return None
    
    # Find available terrains
    terrains = find_terrain_previews()
    logger.info(f"Found {len(terrains)} terrain previews")
    
    if len(terrains) < 3:
        logger.warning("Need at least 3 terrains for evolution test")
        # Create mock terrains for testing
        logger.info("Creating mock terrain data for testing...")
        terrains = create_mock_terrain_batch()
    
    # Simulate scores (high and low quality)
    for i, terrain in enumerate(terrains):
        if terrain["score"] == 0.5:  # Default score
            # Simulate: first half high quality, second half low quality
            terrain["score"] = 0.85 if i < len(terrains) / 2 else 0.45
            terrain["command"] = f"test_command_{i}"
    
    logger.info(f"Terrain batch: {len(terrains)} terrains")
    logger.info(f"High quality (0.8+): {sum(1 for t in terrains if t['score'] >= 0.8)}")
    logger.info(f"Low quality (<0.6): {sum(1 for t in terrains if t['score'] < 0.6)}")
    
    try:
        service = RubricEvolutionService(gemini_key)
        base_rubric = DEFAULT_QUALITY_RUBRIC
        
        logger.info("\nEvolving rubric...")
        evolved_rubric = service.evolve_rubric_from_batch(
            terrains,
            base_rubric,
            min_samples=3
        )
        
        # Compare rubrics
        logger.info("\n" + "-" * 80)
        logger.info("RUBRIC COMPARISON")
        logger.info("-" * 80)
        
        logger.info("\nBase Rubric Composition Criteria:")
        base_comp = base_rubric.get("composition", {})
        for key, value in base_comp.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("\nEvolved Rubric Composition Criteria:")
        evolved_comp = evolved_rubric.get("composition", {})
        for key, value in evolved_comp.items():
            logger.info(f"  {key}: {value}")
        
        # Check for new criteria
        new_criteria = set(evolved_comp.keys()) - set(base_comp.keys())
        if new_criteria:
            logger.info(f"\n✓ New criteria added: {new_criteria}")
        else:
            logger.info("\n⚠ No new criteria added")
        
        # Check metadata
        metadata = evolved_rubric.get("_metadata", {})
        if metadata:
            logger.info(f"\nRubric Metadata:")
            logger.info(f"  Version: {metadata.get('version', 'N/A')}")
            logger.info(f"  Evolved at: {metadata.get('evolved_at', 'N/A')}")
            logger.info(f"  Improvements applied: {metadata.get('improvements_applied', 0)}")
        
        return {
            "base_rubric": base_rubric,
            "evolved_rubric": evolved_rubric,
            "new_criteria": list(new_criteria),
            "success": True,
        }
        
    except Exception as e:
        logger.error(f"Rubric evolution test failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "success": False,
        }


def create_mock_terrain_batch():
    """Create mock terrain data for testing when real data isn't available."""
    # Create dummy image files for testing
    from PIL import Image
    import numpy as np
    
    preview_dir = Path("logs/test_terrains")
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    terrains = []
    for i in range(5):
        session_dir = preview_dir / f"test_{i}"
        session_dir.mkdir(exist_ok=True)
        
        # Create dummy heightmap
        heightmap = np.random.rand(512, 512).astype(np.float32)
        height_path = session_dir / "height.png"
        Image.fromarray((heightmap * 255).astype(np.uint8)).save(height_path)
        
        # Create dummy splatmap
        splatmap = np.random.rand(512, 512, 4).astype(np.float32)
        splat_path = session_dir / "splat.png"
        Image.fromarray((splatmap * 255).astype(np.uint8)).save(splat_path)
        
        # Simulate scores
        score = 0.85 if i < 3 else 0.45  # First 3 high quality, last 2 low
        
        terrains.append({
            "heightmap_path": str(height_path),
            "splatmap_path": str(splat_path),
            "score": score,
            "command": f"test_command_{i}",
            "actions": [
                {"type": "mountain", "x": 256, "y": 256} if i < 3 else {"type": "hill", "x": 200, "y": 200}
            ],
        })
    
    return terrains


def evaluate_outputs(context_results, evolution_results):
    """Evaluate the outputs and report what works and what doesn't."""
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 80)
    
    # Evaluate context rubric generation
    if context_results:
        logger.info("\n1. CONTEXT RUBRIC GENERATION:")
        successful = sum(1 for r in context_results if r.get("success"))
        logger.info(f"   Success rate: {successful}/{len(context_results)}")
        
        for result in context_results:
            if result.get("success"):
                context_info = result.get("context_rubric", {}).get("_context", {})
                logger.info(f"   ✓ '{result['command'][:50]}...'")
                logger.info(f"     Context: {context_info.get('context_type', 'N/A')}")
                logger.info(f"     Priorities: {context_info.get('priority_criteria', [])}")
            else:
                logger.info(f"   ✗ '{result['command'][:50]}...' - {result.get('error', 'Unknown error')}")
    
    # Evaluate rubric evolution
    if evolution_results:
        logger.info("\n2. RUBRIC EVOLUTION:")
        if evolution_results.get("success"):
            logger.info("   ✓ Rubric evolution completed")
            
            new_criteria = evolution_results.get("new_criteria", [])
            if new_criteria:
                logger.info(f"   ✓ Added {len(new_criteria)} new criteria: {new_criteria}")
            else:
                logger.info("   ⚠ No new criteria added (may need more/better samples)")
            
            metadata = evolution_results.get("evolved_rubric", {}).get("_metadata", {})
            improvements = metadata.get("improvements_applied", 0)
            if improvements > 0:
                logger.info(f"   ✓ Applied {improvements} improvements")
            else:
                logger.info("   ⚠ No improvements applied")
        else:
            logger.info(f"   ✗ Evolution failed: {evolution_results.get('error', 'Unknown error')}")
    
    # Overall assessment
    logger.info("\n" + "-" * 80)
    logger.info("OVERALL ASSESSMENT")
    logger.info("-" * 80)
    
    issues = []
    successes = []
    
    if context_results:
        success_rate = sum(1 for r in context_results if r.get("success")) / len(context_results)
        if success_rate >= 0.8:
            successes.append("Context rubric generation works well")
        else:
            issues.append(f"Context rubric generation unreliable ({success_rate:.0%} success)")
    
    if evolution_results and evolution_results.get("success"):
        if evolution_results.get("new_criteria"):
            successes.append("Rubric evolution discovers new criteria")
        else:
            issues.append("Rubric evolution not discovering new criteria (may need better samples)")
    elif evolution_results:
        issues.append(f"Rubric evolution failed: {evolution_results.get('error', 'Unknown')}")
    
    if successes:
        logger.info("\n✓ What Works:")
        for success in successes:
            logger.info(f"  - {success}")
    
    if issues:
        logger.info("\n⚠ Issues Found:")
        for issue in issues:
            logger.info(f"  - {issue}")
    
    if not issues and successes:
        logger.info("\n✓ All tests passed! System is working well.")
    elif not successes:
        logger.info("\n✗ System needs improvement - no successful tests.")


if __name__ == "__main__":
    logger.info("Starting Rubric Evolution Tests...")
    
    # Test 1: Context-aware rubric generation
    context_results = test_context_rubric_generation()
    
    # Test 2: Rubric evolution
    evolution_results = test_rubric_evolution()
    
    # Evaluate outputs
    evaluate_outputs(context_results, evolution_results)
    
    logger.info("\n" + "=" * 80)
    logger.info("Tests Complete!")
    logger.info("=" * 80)

