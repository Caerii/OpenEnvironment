"""
Test rubric evolution with REAL terrain data.
Generates actual terrains, evaluates them, and evolves rubrics.
"""

import sys
import os
from pathlib import Path

# Add both server directory and parent directory to path
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
# Import with proper path handling
try:
    from semantic.rubric_evolution import RubricEvolutionService
    from semantic.evaluation import DEFAULT_QUALITY_RUBRIC
    from semantic.tools.quality_tools import evaluate_terrain_quality
    from semantic.narrative.utils import run_narrative_pipeline
except ImportError:
    # Fallback: try absolute imports
    from server.semantic.rubric_evolution import RubricEvolutionService
    from server.semantic.evaluation import DEFAULT_QUALITY_RUBRIC
    from server.semantic.tools.quality_tools import evaluate_terrain_quality
    from server.semantic.narrative.utils import run_narrative_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def generate_real_terrains(commands: list[str], num_per_command: int = 2):
    """Generate real terrains using the narrative pipeline."""
    logger.info("=" * 80)
    logger.info("GENERATING REAL TERRAIN DATA")
    logger.info("=" * 80)
    
    terrains = []
    
    for command in commands:
        logger.info(f"\nGenerating {num_per_command} terrains for: {command}")
        
        for i in range(num_per_command):
            try:
                # Generate terrain using narrative pipeline
                scene_state = {
                    "features": [],
                    "semantic_scene": {"entities": []},
                    "seed": 42 + i,
                    "base_biome_fn": None,
                    "action_history": []
                }
                
                actions, metadata = run_narrative_pipeline(command, scene_state)
                
                if not actions:
                    logger.warning(f"  Failed to generate actions for iteration {i+1}")
                    continue
                
                # Evaluate quality
                eval_result = evaluate_terrain_quality(
                    scene_state=scene_state,
                    actions=actions,
                    render_preview=True,
                    command=command
                )
                
                if not eval_result.get("success"):
                    logger.warning(f"  Failed to evaluate quality for iteration {i+1}")
                    continue
                
                eval_data = eval_result.get("data", {})
                score = eval_data.get("overall_score", 0.0)
                
                # Get preview paths from evaluation (already rendered)
                # The preview was rendered during evaluate_terrain_quality
                # We'll use the preview directory from the most recent render
                from pathlib import Path
                import glob
                
                # Find most recent preview directory
                preview_base = Path("logs/terrain_previews")
                preview_dirs = sorted(preview_base.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True) if preview_base.exists() else []
                
                heightmap_path = None
                splatmap_path = None
                if preview_dirs:
                    latest_dir = preview_dirs[0]
                    height_path = latest_dir / "height.png"
                    splat_path = latest_dir / "splat.png"
                    if height_path.exists():
                        heightmap_path = str(height_path)
                    if splat_path.exists():
                        splatmap_path = str(splat_path)
                
                terrain_data = {
                    "command": command,
                    "actions": actions,
                    "score": score,
                    "composition_score": eval_data.get("composition_score", 0.0),
                    "texture_score": eval_data.get("texture_score", 0.0),
                    "heightmap_path": heightmap_path,
                    "splatmap_path": splatmap_path,
                    "metadata": metadata,
                }
                
                terrains.append(terrain_data)
                logger.info(f"  ✓ Generated terrain {i+1}: score={score:.3f}")
                
            except Exception as e:
                logger.error(f"  ✗ Failed to generate terrain {i+1}: {e}", exc_info=True)
    
    logger.info(f"\n✓ Generated {len(terrains)} real terrains")
    return terrains


def test_context_rubrics_integration(terrains):
    """Test that context rubrics are being used in evaluation."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING CONTEXT RUBRIC INTEGRATION")
    logger.info("=" * 80)
    
    # Test with different commands
    test_commands = [
        "create a dramatic mountain landscape with valleys and cliffs",
        "design a serene desert with rolling dunes",
    ]
    
    for command in test_commands:
        logger.info(f"\nTesting command: {command}")
        
        # Generate actions
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42,
            "base_biome_fn": None,
            "action_history": []
        }
        
        actions, _ = run_narrative_pipeline(command, scene_state)
        if not actions:
            logger.warning("  Failed to generate actions")
            continue
        
        # Evaluate WITH context rubric
        result_with_context = evaluate_terrain_quality(
            scene_state=scene_state,
            actions=actions,
            render_preview=True,
            command=command
        )
        
        # Evaluate WITHOUT context rubric (default)
        result_without_context = evaluate_terrain_quality(
            scene_state=scene_state,
            actions=actions,
            render_preview=True,
            command=None  # No command = no context rubric
        )
        
        if result_with_context.get("success") and result_without_context.get("success"):
            with_data = result_with_context.get("data", {})
            without_data = result_without_context.get("data", {})
            
            logger.info(f"  With context:    score={with_data.get('overall_score', 0):.3f}")
            logger.info(f"  Without context: score={without_data.get('overall_score', 0):.3f}")
            logger.info(f"  Difference:     {with_data.get('overall_score', 0) - without_data.get('overall_score', 0):.3f}")


def test_rubric_evolution_real_data(terrains):
    """Test rubric evolution with real terrain data."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING RUBRIC EVOLUTION WITH REAL DATA")
    logger.info("=" * 80)
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set, skipping evolution test")
        return None
    
    if len(terrains) < 5:
        logger.warning(f"Need at least 5 terrains, got {len(terrains)}")
        return None
    
    # Separate by quality
    high_quality = [t for t in terrains if t.get("score", 0) >= 0.7]
    low_quality = [t for t in terrains if t.get("score", 0) < 0.5]
    
    logger.info(f"High quality (>=0.7): {len(high_quality)}")
    logger.info(f"Low quality (<0.5): {len(low_quality)}")
    
    if len(high_quality) < 2:
        logger.warning("Not enough high-quality terrains for evolution")
        return None
    
    try:
        service = RubricEvolutionService(gemini_key)
        base_rubric = DEFAULT_QUALITY_RUBRIC
        
        logger.info("\nEvolving rubric from real terrain data...")
        evolved_rubric = service.evolve_rubric_from_batch(
            terrains,
            base_rubric,
            min_samples=3
        )
        
        # Compare rubrics
        logger.info("\n" + "-" * 80)
        logger.info("RUBRIC COMPARISON")
        logger.info("-" * 80)
        
        base_comp = base_rubric.get("composition", {})
        evolved_comp = evolved_rubric.get("composition", {})
        
        new_criteria = set(evolved_comp.keys()) - set(base_comp.keys())
        
        logger.info(f"\nBase Rubric Criteria: {len(base_comp)}")
        for key in base_comp.keys():
            logger.info(f"  - {key}")
        
        logger.info(f"\nEvolved Rubric Criteria: {len(evolved_comp)}")
        for key in evolved_comp.keys():
            marker = "  [NEW]" if key in new_criteria else "  "
            logger.info(f"{marker} {key}")
        
        if new_criteria:
            logger.info(f"\n✓ Added {len(new_criteria)} new criteria:")
            for crit in new_criteria:
                crit_data = evolved_comp.get(crit, {})
                logger.info(f"  - {crit}: {crit_data.get('threshold', 'N/A')}")
        
        # Filter criteria (remove unmeasurable ones)
        filtered_criteria = filter_evolved_criteria(new_criteria, evolved_comp)
        
        logger.info(f"\n✓ Filtered Criteria (measurable): {len(filtered_criteria)}")
        for crit in filtered_criteria:
            logger.info(f"  - {crit}")
        
        removed = new_criteria - filtered_criteria
        if removed:
            logger.info(f"\n⚠ Removed Criteria (unmeasurable): {len(removed)}")
            for crit in removed:
                logger.info(f"  - {crit}")
        
        return {
            "base_rubric": base_rubric,
            "evolved_rubric": evolved_rubric,
            "new_criteria": list(new_criteria),
            "filtered_criteria": list(filtered_criteria),
            "removed_criteria": list(removed),
        }
        
    except Exception as e:
        logger.error(f"Evolution failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return None


def filter_evolved_criteria(new_criteria, evolved_comp):
    """Filter criteria to keep only measurable ones."""
    measurable_keywords = [
        "spatial", "composition", "organization", "scale", "depth",
        "geological", "feature", "count", "diversity", "extent",
        "height", "texture", "coverage", "correlation", "entropy"
    ]
    
    unmeasurable_keywords = [
        "lighting", "atmosphere", "color", "palette", "harmony",
        "mood", "feeling", "emotion"
    ]
    
    filtered = set()
    
    for crit in new_criteria:
        crit_lower = crit.lower()
        
        # Check if it's measurable
        is_measurable = any(kw in crit_lower for kw in measurable_keywords)
        is_unmeasurable = any(kw in crit_lower for kw in unmeasurable_keywords)
        
        # Keep if measurable and not explicitly unmeasurable
        if is_measurable and not is_unmeasurable:
            filtered.add(crit)
        elif not is_unmeasurable:
            # If it doesn't match either, check the threshold description
            crit_data = evolved_comp.get(crit, {})
            threshold = str(crit_data.get("threshold", "")).lower()
            if any(kw in threshold for kw in measurable_keywords):
                filtered.add(crit)
    
    return filtered


def comprehensive_test():
    """Run comprehensive tests with real data."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE RUBRIC EVOLUTION TEST WITH REAL DATA")
    logger.info("=" * 80)
    
    # Test commands covering different contexts
    test_commands = [
        "create a dramatic mountain landscape with valleys and cliffs",
        "design a serene desert with rolling dunes",
        "build a balanced landscape with hills and valleys",
        "create an epic mountain range with multiple peaks",
        "design a peaceful valley with a river",
    ]
    
    # Generate real terrains
    terrains = generate_real_terrains(test_commands, num_per_command=2)
    
    if not terrains:
        logger.error("Failed to generate any terrains")
        return
    
    # Test context rubric integration
    test_context_rubrics_integration(terrains)
    
    # Test rubric evolution
    evolution_results = test_rubric_evolution_real_data(terrains)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    logger.info(f"\n✓ Generated {len(terrains)} real terrains")
    logger.info(f"  Score range: {min(t.get('score', 0) for t in terrains):.3f} - {max(t.get('score', 0) for t in terrains):.3f}")
    logger.info(f"  Average score: {sum(t.get('score', 0) for t in terrains) / len(terrains):.3f}")
    
    if evolution_results:
        logger.info(f"\n✓ Rubric evolution completed")
        logger.info(f"  New criteria: {len(evolution_results.get('new_criteria', []))}")
        logger.info(f"  Filtered (measurable): {len(evolution_results.get('filtered_criteria', []))}")
        logger.info(f"  Removed (unmeasurable): {len(evolution_results.get('removed_criteria', []))}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Tests Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    comprehensive_test()

