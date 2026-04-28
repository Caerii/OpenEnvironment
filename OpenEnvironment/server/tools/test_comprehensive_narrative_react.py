"""
Comprehensive systematic test suite for Narrative-ReAct integration.
Tests edge cases, long runs, and quality improvements over iterations.
"""

import sys
import os
from pathlib import Path
import time
import json
from typing import Dict, Any, List, Tuple

server_dir = Path(__file__).parent.parent
parent_dir = server_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

# Set Cerebras API key and provider
os.environ["CEREBRAS_API_KEY"] = "csk-w55m3494mx3tr62wnm9fc64e9wp5nfdhm644pxrhpjt5xmhd"
os.environ["LLM_PROVIDER"] = "cerebras"
os.environ["CEREBRAS_MODEL"] = "llama3.1-8b"  # Use available model

# Also load from .env file if it exists (may override above)
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
                    # Always use cerebras for testing, but allow other env vars
                    if key != "LLM_PROVIDER":
                        os.environ[key] = value

# Ensure cerebras is set
os.environ["LLM_PROVIDER"] = "cerebras"

import logging
from semantic.react_agent_v2 import ReActAgentV2
from semantic.llm.factory import create_llm_client
from semantic.narrative.utils import run_narrative_pipeline
from semantic.tools.quality_tools import evaluate_terrain_quality, refine_composition
from semantic.tools.spatial_tools import calculate_position, calculate_region_positions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Comprehensive test commands covering different archetypes and complexities
TEST_COMMANDS = {
    "simple": [
        "create a mountain",
        "add dunes",
        "make a valley",
    ],
    "moderate": [
        "create dramatic mountains with valleys",
        "design a serene desert with rolling dunes",
        "build a balanced landscape with hills and valleys",
        "make a rugged canyon with cliffs",
    ],
    "complex": [
        "create a dramatic mountain range with deep valleys, towering cliffs, and rolling plateaus",
        "design a serene desert landscape with vast dunes, scattered mesas, and occasional oases",
        "build a balanced terrain with hills, valleys, canyons, and plateaus in harmonious composition",
        "make a rugged alpine landscape with sharp peaks, deep valleys, and snow-capped ridges",
    ],
    "edge_cases": [
        "create something beautiful",  # Very vague
        "add everything",  # Ambiguous
        "make it dramatic and serene",  # Conflicting goals
        "create mountains mountains mountains",  # Repetitive
        "",  # Empty command
    ],
}

# Different archetypes to test
ARCHETYPES_TO_TEST = [
    "Ancient Uplift",
    "Wind Architect",
    "Water's Legacy",
    "Volcanic",
    "Glacial",
]

# Edge case clustering values
CLUSTERING_EDGE_CASES = [0.0, 0.1, 0.5, 0.9, 1.0]

# Edge case alignment values
ALIGNMENT_EDGE_CASES = [None, 0.0, 45.0, 90.0, 180.0, 270.0, 360.0]


def test_narrative_extraction_edge_cases():
    """Test narrative extraction with edge cases."""
    logger.info("=" * 80)
    logger.info("TEST SUITE 1: NARRATIVE EXTRACTION EDGE CASES")
    logger.info("=" * 80)
    
    from semantic.narrative.narrative_dev import develop_terrain_narrative
    
    results = []
    
    for category, commands in TEST_COMMANDS.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"Category: {category.upper()}")
        logger.info(f"{'='*80}")
        
        for command in commands:
            logger.info(f"\nTesting: '{command}'")
            
            scene_state = {
                "features": [],
                "semantic_scene": {"entities": []},
                "seed": 42,
                "base_biome_fn": None,
                "action_history": []
            }
            
            try:
                narrative = develop_terrain_narrative(command, scene_state)
                
                if narrative:
                    logger.info(f"  ✓ Extracted: {narrative.archetype.name}")
                    logger.info(f"    Goals: {[g.value for g in narrative.aesthetic_goals]}")
                    logger.info(f"    Clustering: {narrative.archetype.clustering_tendency}")
                    logger.info(f"    Alignment: {narrative.archetype.directional_alignment}")
                    
                    results.append({
                        "command": command,
                        "category": category,
                        "success": True,
                        "archetype": narrative.archetype.name,
                        "aesthetic_goals": [g.value for g in narrative.aesthetic_goals],
                        "clustering": narrative.archetype.clustering_tendency,
                        "alignment": narrative.archetype.directional_alignment,
                    })
                else:
                    logger.warning(f"  ✗ Failed: No narrative returned")
                    results.append({
                        "command": command,
                        "category": category,
                        "success": False,
                        "error": "No narrative returned",
                    })
            except Exception as e:
                logger.error(f"  ✗ Error: {e}", exc_info=True)
                results.append({
                    "command": command,
                    "category": category,
                    "success": False,
                    "error": str(e),
                })
    
    success_rate = sum(1 for r in results if r.get("success")) / len(results) * 100
    logger.info(f"\n{'='*80}")
    logger.info(f"Success Rate: {success_rate:.1f}% ({sum(1 for r in results if r.get('success'))}/{len(results)})")
    logger.info(f"{'='*80}")
    
    return results


def test_spatial_constraints_edge_cases():
    """Test spatial tools with edge case constraint values."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE 2: SPATIAL CONSTRAINTS EDGE CASES")
    logger.info("=" * 80)
    
    results = []
    
    # Test different clustering values
    logger.info("\nTesting Clustering Edge Cases:")
    for clustering in CLUSTERING_EDGE_CASES:
        logger.info(f"\n  Clustering: {clustering}")
        
        scene_state = {
            "features": [{"id": 1, "type": "mountain", "x": 256, "y": 256}],
            "semantic_scene": {"entities": []},
            "_narrative": {
                "spatial_patterns": {
                    "clustering_tendency": clustering,
                    "directional_alignment": None,
                },
            },
        }
        
        pos = calculate_position(
            scene_state,
            reference_ids=[1],
            relationship="near",
            offset_distance=80
        )
        
        import math
        ref_pos = (256, 256)
        calc_pos = pos.get("position", [256, 256])
        distance = math.sqrt((calc_pos[0] - ref_pos[0])**2 + (calc_pos[1] - ref_pos[1])**2)
        
        logger.info(f"    Position: {calc_pos}, Distance: {distance:.1f}")
        
        results.append({
            "clustering": clustering,
            "alignment": None,
            "position": calc_pos,
            "distance": distance,
        })
    
    # Test different alignment values
    logger.info("\nTesting Alignment Edge Cases:")
    for alignment in ALIGNMENT_EDGE_CASES:
        logger.info(f"\n  Alignment: {alignment}")
        
        scene_state = {
            "features": [{"id": 1, "type": "mountain", "x": 256, "y": 256}],
            "semantic_scene": {"entities": []},
            "_narrative": {
                "spatial_patterns": {
                    "clustering_tendency": 0.7,
                    "directional_alignment": alignment,
                },
            },
        }
        
        pos = calculate_position(
            scene_state,
            reference_ids=[1],
            relationship="near",
            offset_distance=80
        )
        
        import math
        ref_pos = (256, 256)
        calc_pos = pos.get("position", [256, 256])
        distance = math.sqrt((calc_pos[0] - ref_pos[0])**2 + (calc_pos[1] - ref_pos[1])**2)
        
        logger.info(f"    Position: {calc_pos}, Distance: {distance:.1f}")
        
        results.append({
            "clustering": 0.7,
            "alignment": alignment,
            "position": calc_pos,
            "distance": distance,
        })
    
    return results


def test_quality_iterative_refinement(max_iterations=10, skip_refinement=False):
    """Test quality improvement over multiple refinement iterations."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST SUITE 3: ITERATIVE QUALITY REFINEMENT ({max_iterations} iterations)")
    logger.info("=" * 80)
    
    if skip_refinement:
        logger.info("Skipping refinement (LLM not available) - testing evaluation only")
    
    test_command = "create dramatic mountains with valleys and cliffs"
    
    logger.info(f"\nCommand: {test_command}")
    logger.info(f"Max Iterations: {max_iterations}")
    
    scene_state = {
        "features": [],
        "semantic_scene": {"entities": []},
        "seed": 42,
        "base_biome_fn": None,
        "action_history": []
    }
    
    # Generate initial actions
    actions, metadata = run_narrative_pipeline(test_command, scene_state)
    
    if not actions:
        logger.error("Failed to generate initial actions")
        return []
    
    logger.info(f"\nInitial Actions: {len(actions)}")
    
    # Store narrative metadata
    scene_state["_narrative_meta"] = {
        "archetype": metadata.get("archetype", ""),
        "aesthetic_goals": metadata.get("aesthetic_goals", []),
    }
    
    iteration_results = []
    current_actions = actions.copy()
    
    for iteration in range(max_iterations):
        logger.info(f"\n{'='*60}")
        logger.info(f"Iteration {iteration + 1}/{max_iterations}")
        logger.info(f"{'='*60}")
        
        # Evaluate quality
        eval_result = evaluate_terrain_quality(
            scene_state=scene_state,
            actions=current_actions,
            render_preview=True,
            command=test_command
        )
        
        if not eval_result.get("success"):
            logger.warning(f"Quality evaluation failed at iteration {iteration + 1}")
            break
        
        eval_data = eval_result.get("data", {})
        overall_score = eval_data.get("overall_score", 0.0)
        warnings = eval_data.get("warnings", [])
        
        logger.info(f"  Overall Score: {overall_score:.3f}")
        logger.info(f"  Composition: {eval_data.get('composition_score', 0):.3f}")
        logger.info(f"  Texture: {eval_data.get('texture_score', 0):.3f}")
        logger.info(f"  Warnings: {len(warnings)}")
        
        iteration_results.append({
            "iteration": iteration + 1,
            "overall_score": overall_score,
            "composition_score": eval_data.get("composition_score", 0),
            "texture_score": eval_data.get("texture_score", 0),
            "warnings_count": len(warnings),
            "actions_count": len(current_actions),
        })
        
        # Stop if we've reached high quality
        if overall_score >= 0.8:
            logger.info(f"\n✓ Reached target quality (0.8) at iteration {iteration + 1}")
            break
        
        # Refine if quality is low
        if not skip_refinement and overall_score < 0.8 and warnings:
            logger.info(f"  Refining based on {len(warnings)} warnings...")
            
            refine_result = refine_composition(
                scene_state=scene_state,
                actions=current_actions,
                quality_warnings=warnings[:5],  # Top 5 warnings
                max_refinements=3
            )
            
            if refine_result.get("success"):
                refined_data = refine_result.get("data", {})
                refined_actions = refined_data.get("refined_actions", current_actions)
                changes = refined_data.get("changes_made", [])
                
                logger.info(f"  Changes: {len(changes)}")
                for change in changes:
                    logger.info(f"    - {change}")
                
                current_actions = refined_actions
            else:
                logger.warning(f"  Refinement failed: {refine_result.get('error')}")
                # Don't break - continue evaluating to see quality progression
        else:
            if skip_refinement:
                logger.info("  Skipping refinement (LLM not available) - continuing evaluation")
            else:
                logger.info("  Quality acceptable or no warnings - stopping refinement")
            # Continue for a few more iterations even if quality is good, to show stability
            if overall_score >= 0.8 and iteration >= 3:
                break
    
    # Final evaluation
    logger.info(f"\n{'='*60}")
    logger.info("FINAL EVALUATION")
    logger.info(f"{'='*60}")
    
    final_eval = evaluate_terrain_quality(
        scene_state=scene_state,
        actions=current_actions,
        render_preview=True,
        command=test_command
    )
    
    if final_eval.get("success"):
        final_data = final_eval.get("data", {})
        logger.info(f"Final Score: {final_data.get('overall_score', 0):.3f}")
        logger.info(f"Improvement: {final_data.get('overall_score', 0) - iteration_results[0]['overall_score']:+.3f}")
    
    return iteration_results


def test_long_run_quality_progression(commands: List[str], iterations_per_command=5):
    """Test quality progression over long runs with multiple commands."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST SUITE 4: LONG RUN QUALITY PROGRESSION")
    logger.info(f"Commands: {len(commands)}, Iterations per command: {iterations_per_command}")
    logger.info("=" * 80)
    
    # Ensure Cerebras provider is set (should already be set at module level)
    os.environ["LLM_PROVIDER"] = "cerebras"
    os.environ["CEREBRAS_MODEL"] = "llama3.1-8b"
    
    llm_client = create_llm_client()
    if not llm_client:
        logger.warning("LLM client not available - skipping long run test")
        return []
    
    agent = ReActAgentV2(llm_client, prompt_profile="compact", max_iterations=5)
    
    all_results = []
    
    for cmd_idx, command in enumerate(commands, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Command {cmd_idx}/{len(commands)}: {command}")
        logger.info(f"{'='*80}")
        
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42 + cmd_idx,
            "base_biome_fn": None,
            "action_history": []
        }
        
        command_results = []
        
        for iteration in range(iterations_per_command):
            logger.info(f"\n  Iteration {iteration + 1}/{iterations_per_command}")
            
            start_time = time.time()
            
            # Run ReAct agent
            result = agent.solve(command, scene_state, temperature=0.3)
            
            elapsed = time.time() - start_time
            
            if result.get("success"):
                actions = result.get("actions", [])
                tool_calls = result.get("total_tool_calls", 0)
                react_iterations = result.get("iterations", 0)
                
                # Evaluate quality
                eval_result = evaluate_terrain_quality(
                    scene_state=scene_state,
                    actions=actions,
                    render_preview=True,
                    command=command
                )
                
                if eval_result.get("success"):
                    eval_data = eval_result.get("data", {})
                    overall_score = eval_data.get("overall_score", 0.0)
                    
                    logger.info(f"    Score: {overall_score:.3f}, Actions: {len(actions)}, "
                              f"Tool Calls: {tool_calls}, Time: {elapsed:.1f}s")
                    
                    command_results.append({
                        "iteration": iteration + 1,
                        "overall_score": overall_score,
                        "composition_score": eval_data.get("composition_score", 0),
                        "texture_score": eval_data.get("texture_score", 0),
                        "actions_count": len(actions),
                        "tool_calls": tool_calls,
                        "react_iterations": react_iterations,
                        "elapsed_time": elapsed,
                        "narrative_extracted": bool(scene_state.get("_narrative_meta")),
                    })
                else:
                    logger.warning(f"    Quality evaluation failed")
            else:
                logger.warning(f"    ReAct failed: {result.get('error')}")
        
        if command_results:
            avg_score = sum(r["overall_score"] for r in command_results) / len(command_results)
            best_score = max(r["overall_score"] for r in command_results)
            logger.info(f"\n  Average Score: {avg_score:.3f}")
            logger.info(f"  Best Score: {best_score:.3f}")
        
        all_results.append({
            "command": command,
            "results": command_results,
        })
    
    return all_results


def test_archetype_coverage():
    """Test that all archetypes are properly handled."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE 5: ARCHETYPE COVERAGE")
    logger.info("=" * 80)
    
    from semantic.narrative.narrative_dev import develop_terrain_narrative
    from semantic.narrative.archetypes import TERRAIN_ARCHETYPES
    
    results = []
    
    # Test commands that should trigger each archetype
    archetype_commands = {
        "Ancient Uplift": "create dramatic mountains with peaks",
        "Wind Architect": "design a desert with dunes",
        "Water's Legacy": "make a valley with rivers",
        "Volcanic Birth": "create volcanic terrain",
        "Glacial Legacy": "make glacial landscape",
        "Depositional Plains": "create gentle plains",
    }
    
    for archetype_key, archetype_obj in TERRAIN_ARCHETYPES.items():
        archetype_name = archetype_obj.name
        logger.info(f"\nTesting Archetype: {archetype_name}")
        
        command = archetype_commands.get(archetype_name, f"create {archetype_name.lower()} terrain")
        
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42,
            "base_biome_fn": None,
            "action_history": []
        }
        
        try:
            narrative = develop_terrain_narrative(command, scene_state)
            
            if narrative:
                matched_archetype = narrative.archetype.name
                is_match = matched_archetype == archetype_name
                
                logger.info(f"  Command: '{command}'")
                logger.info(f"  Matched: {matched_archetype} {'✓' if is_match else '✗'}")
                
                results.append({
                    "archetype": archetype_name,
                    "command": command,
                    "matched": matched_archetype,
                    "is_match": is_match,
                    "clustering": narrative.archetype.clustering_tendency,
                    "alignment": narrative.archetype.directional_alignment,
                })
        except Exception as e:
            logger.error(f"  Error: {e}", exc_info=True)
            results.append({
                "archetype": archetype_name,
                "command": command,
                "error": str(e),
            })
    
    match_rate = sum(1 for r in results if r.get("is_match")) / len(results) * 100
    logger.info(f"\n{'='*80}")
    logger.info(f"Match Rate: {match_rate:.1f}%")
    logger.info(f"{'='*80}")
    
    return results


def comprehensive_test_suite():
    """Run all test suites and generate comprehensive report."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE NARRATIVE-REACT TEST SUITE")
    logger.info("=" * 80)
    
    all_results = {}
    
    # Test 1: Narrative extraction edge cases
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: NARRATIVE EXTRACTION EDGE CASES")
    logger.info("=" * 80)
    all_results["narrative_edge_cases"] = test_narrative_extraction_edge_cases()
    
    # Test 2: Spatial constraints edge cases
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: SPATIAL CONSTRAINTS EDGE CASES")
    logger.info("=" * 80)
    all_results["spatial_edge_cases"] = test_spatial_constraints_edge_cases()
    
    # Test 3: Iterative quality refinement
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: ITERATIVE QUALITY REFINEMENT")
    logger.info("=" * 80)
    # Check if LLM is available (refinement uses LLM)
    llm_available = create_llm_client() is not None
    if not llm_available:
        logger.warning("LLM client not available - will skip refinement steps")
    all_results["iterative_refinement"] = test_quality_iterative_refinement(
        max_iterations=10,
        skip_refinement=not llm_available
    )
    
    # Test 4: Long run quality progression
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 4: LONG RUN QUALITY PROGRESSION")
    logger.info("=" * 80)
    # Only run if LLM is available (ReAct requires LLM)
    if llm_available:
        long_run_commands = TEST_COMMANDS["moderate"] + TEST_COMMANDS["complex"][:2]
        all_results["long_run"] = test_long_run_quality_progression(
            commands=long_run_commands,
            iterations_per_command=5
        )
    else:
        logger.warning("Skipping long run test - LLM not available")
        all_results["long_run"] = []
    
    # Test 5: Archetype coverage
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 5: ARCHETYPE COVERAGE")
    logger.info("=" * 80)
    all_results["archetype_coverage"] = test_archetype_coverage()
    
    # Generate summary report
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info("=" * 80)
    
    # Narrative extraction summary
    narrative_results = all_results["narrative_edge_cases"]
    narrative_success = sum(1 for r in narrative_results if r.get("success"))
    logger.info(f"\n1. NARRATIVE EXTRACTION:")
    logger.info(f"   Success Rate: {narrative_success}/{len(narrative_results)} ({narrative_success/len(narrative_results)*100:.1f}%)")
    
    # Iterative refinement summary
    refinement_results = all_results["iterative_refinement"]
    if refinement_results:
        initial_score = refinement_results[0]["overall_score"]
        final_score = refinement_results[-1]["overall_score"]
        improvement = final_score - initial_score
        logger.info(f"\n2. ITERATIVE REFINEMENT:")
        logger.info(f"   Initial Score: {initial_score:.3f}")
        logger.info(f"   Final Score: {final_score:.3f}")
        logger.info(f"   Improvement: {improvement:+.3f}")
        logger.info(f"   Iterations: {len(refinement_results)}")
    
    # Long run summary
    long_run_results = all_results["long_run"]
    if long_run_results:
        logger.info(f"\n3. LONG RUN QUALITY PROGRESSION:")
        for cmd_result in long_run_results:
            cmd = cmd_result["command"]
            results = cmd_result["results"]
            if results:
                avg_score = sum(r["overall_score"] for r in results) / len(results)
                best_score = max(r["overall_score"] for r in results)
                logger.info(f"   '{cmd[:50]}...': avg={avg_score:.3f}, best={best_score:.3f}")
    
    # Archetype coverage summary
    archetype_results = all_results["archetype_coverage"]
    archetype_matches = sum(1 for r in archetype_results if r.get("is_match"))
    logger.info(f"\n4. ARCHETYPE COVERAGE:")
    logger.info(f"   Match Rate: {archetype_matches}/{len(archetype_results)} ({archetype_matches/len(archetype_results)*100:.1f}%)")
    
    # Save detailed results
    output_file = Path("logs/comprehensive_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"\n✓ Detailed results saved to: {output_file}")
    logger.info("\n" + "=" * 80)
    logger.info("Comprehensive Tests Complete!")
    logger.info("=" * 80)
    
    return all_results


if __name__ == "__main__":
    results = comprehensive_test_suite()

