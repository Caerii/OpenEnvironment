"""
Systematic test of Narrative-ReAct deep integration.
Tests various commands, verifies constraints are used, and analyzes outputs.
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
                    # Override LLM_PROVIDER to use Cerebras for testing
                    if key == "LLM_PROVIDER":
                        os.environ[key] = "cerebras"
                    else:
                        os.environ[key] = value

# Use Cerebras by default for testing
if "LLM_PROVIDER" not in os.environ:
    os.environ["LLM_PROVIDER"] = "cerebras"

import json
import logging
from typing import Dict, Any, List
from semantic.react_agent_v2 import ReActAgentV2
from semantic.llm.factory import create_llm_client
from semantic.tools.spatial_tools import calculate_position
from semantic.tools.quality_tools import evaluate_terrain_quality

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_narrative_extraction():
    """Test that narrative is extracted and constraints are stored."""
    logger.info("=" * 80)
    logger.info("TEST 1: NARRATIVE EXTRACTION")
    logger.info("=" * 80)
    
    test_commands = [
        "create dramatic mountains with valleys",
        "design a serene desert with rolling dunes",
        "build a balanced landscape with hills and valleys",
    ]
    
    results = []
    
    for command in test_commands:
        logger.info(f"\n{'='*80}")
        logger.info(f"Command: {command}")
        logger.info(f"{'='*80}")
        
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42,
            "base_biome_fn": None,
            "action_history": []
        }
        
        # Extract narrative directly (bypassing ReAct agent import issues)
        try:
            from semantic.narrative.narrative_dev import develop_terrain_narrative
            narrative = develop_terrain_narrative(command, scene_state)
            
            if narrative:
                # Extract constraints manually (same logic as agent)
                archetype = narrative.archetype
                constraints = {
                    "archetype": archetype.name,
                    "aesthetic_goals": [g.value for g in narrative.aesthetic_goals],
                    "spatial_patterns": {
                        "clustering_tendency": archetype.clustering_tendency,
                        "directional_alignment": archetype.directional_alignment,
                        "scale_bias": archetype.scale_bias,
                        "smoothness_bias": archetype.smoothness_bias,
                    },
                    "feature_preferences": {
                        "primary": archetype.primary_features,
                        "secondary": archetype.secondary_features,
                        "accent": archetype.accent_features,
                        "hero_type": narrative.hero_feature_type,
                        "supporting_types": narrative.supporting_feature_types,
                        "accent_types": narrative.accent_feature_types,
                    },
                    "texture_preferences": archetype.preferred_textures.copy(),
                }
                
                scene_state["_narrative"] = constraints
                scene_state["_narrative_meta"] = {
                    "archetype": narrative.archetype.name,
                    "story": narrative.story,
                    "aesthetic_goals": [g.value for g in narrative.aesthetic_goals],
                }
                
                logger.info(f"\n✓ Narrative extracted:")
                logger.info(f"  Archetype: {narrative.archetype.name}")
                logger.info(f"  Aesthetic Goals: {[g.value for g in narrative.aesthetic_goals]}")
                logger.info(f"  Hero Type: {narrative.hero_feature_type}")
                logger.info(f"  Supporting Types: {narrative.supporting_feature_types}")
                
                logger.info(f"\n✓ Constraints extracted:")
                logger.info(f"  Clustering Tendency: {constraints['spatial_patterns']['clustering_tendency']}")
                logger.info(f"  Directional Alignment: {constraints['spatial_patterns']['directional_alignment']}")
                logger.info(f"  Primary Features: {constraints['feature_preferences']['primary']}")
                logger.info(f"  Texture Preferences: {constraints['texture_preferences']}")
                
                results.append({
                    "command": command,
                    "narrative_extracted": True,
                    "archetype": narrative.archetype.name,
                    "constraints": constraints,
                })
            else:
                logger.warning("✗ Failed to extract narrative (returned None)")
                results.append({
                    "command": command,
                    "narrative_extracted": False,
                })
        except Exception as e:
            logger.error(f"✗ Failed to extract narrative: {e}", exc_info=True)
            results.append({
                "command": command,
                "narrative_extracted": False,
                "error": str(e),
            })
    
    return results


def test_spatial_tool_constraints():
    """Test that spatial tools use narrative constraints."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: SPATIAL TOOL CONSTRAINT USAGE")
    logger.info("=" * 80)
    
    # Create scene with narrative constraints
    scene_state = {
        "features": [
            {"id": 1, "type": "mountain", "x": 256, "y": 256},
        ],
        "semantic_scene": {"entities": []},
        "seed": 42,
        "base_biome_fn": None,
        "action_history": [],
        "_narrative": {
            "archetype": "Ancient Uplift",
            "spatial_patterns": {
                "clustering_tendency": 0.7,  # High clustering
                "directional_alignment": 45.0,  # 45-degree alignment
            },
        },
    }
    
    logger.info("\nTesting calculate_position with narrative constraints...")
    
    # Test 1: Without narrative (should use defaults)
    scene_no_narrative = {
        "features": scene_state["features"],
        "semantic_scene": {"entities": []},
    }
    pos_no_narrative = calculate_position(
        scene_no_narrative,
        reference_ids=[1],
        relationship="near",
        offset_distance=80
    )
    
    # Test 2: With narrative (should use constraints)
    pos_with_narrative = calculate_position(
        scene_state,
        reference_ids=[1],
        relationship="near",
        offset_distance=80
    )
    
    logger.info(f"\nWithout narrative constraints:")
    logger.info(f"  Position: {pos_no_narrative.get('position')}")
    logger.info(f"  Method: {pos_no_narrative.get('calculation_method')}")
    
    logger.info(f"\nWith narrative constraints (clustering=0.7, alignment=45°):")
    logger.info(f"  Position: {pos_with_narrative.get('position')}")
    logger.info(f"  Method: {pos_with_narrative.get('calculation_method')}")
    
    # Calculate distance from reference
    ref_pos = (256, 256)
    pos_no = pos_no_narrative.get("position", [256, 256])
    pos_with = pos_with_narrative.get("position", [256, 256])
    
    import math
    dist_no = math.sqrt((pos_no[0] - ref_pos[0])**2 + (pos_no[1] - ref_pos[1])**2)
    dist_with = math.sqrt((pos_with[0] - ref_pos[0])**2 + (pos_with[1] - ref_pos[1])**2)
    
    logger.info(f"\nDistance from reference:")
    logger.info(f"  Without narrative: {dist_no:.1f}")
    logger.info(f"  With narrative: {dist_with:.1f}")
    logger.info(f"  Difference: {abs(dist_no - dist_with):.1f}")
    
    if dist_with < dist_no:
        logger.info("  ✓ Constraint applied: Higher clustering = smaller offset")
    else:
        logger.warning("  ⚠ Constraint may not be applied correctly")
    
    return {
        "without_narrative": pos_no_narrative,
        "with_narrative": pos_with_narrative,
        "distance_diff": abs(dist_no - dist_with),
    }


def test_quality_evaluation_narrative():
    """Test that quality evaluation uses narrative context."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: QUALITY EVALUATION WITH NARRATIVE")
    logger.info("=" * 80)
    
    # Generate actions using narrative pipeline
    from semantic.narrative.utils import run_narrative_pipeline
    
    test_commands = [
        "create dramatic mountains with valleys",
        "design a serene desert with rolling dunes",
    ]
    
    results = []
    
    for command in test_commands:
        logger.info(f"\n{'='*80}")
        logger.info(f"Command: {command}")
        logger.info(f"{'='*80}")
        
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42,
            "base_biome_fn": None,
            "action_history": []
        }
        
        # Generate actions
        actions, metadata = run_narrative_pipeline(command, scene_state)
        
        if not actions:
            logger.warning("Failed to generate actions")
            continue
        
        logger.info(f"Generated {len(actions)} actions")
        logger.info(f"Archetype: {metadata.get('archetype')}")
        logger.info(f"Aesthetic Goals: {metadata.get('aesthetic_goals')}")
        
        # Test WITHOUT narrative context
        result_no_narrative = evaluate_terrain_quality(
            scene_state=scene_state.copy(),
            actions=actions,
            render_preview=True,
            command=None  # No command = no narrative context
        )
        
        # Test WITH narrative context (from metadata)
        scene_with_narrative = scene_state.copy()
        scene_with_narrative["_narrative_meta"] = {
            "archetype": metadata.get("archetype", ""),
            "aesthetic_goals": metadata.get("aesthetic_goals", []),
        }
        
        result_with_narrative = evaluate_terrain_quality(
            scene_state=scene_with_narrative,
            actions=actions,
            render_preview=True,
            command=None  # Will use narrative_meta to build command
        )
        
        if result_no_narrative.get("success") and result_with_narrative.get("success"):
            no_data = result_no_narrative.get("data", {})
            with_data = result_with_narrative.get("data", {})
            
            logger.info(f"\nQuality Scores:")
            logger.info(f"  Without narrative context:")
            logger.info(f"    Overall: {no_data.get('overall_score', 0):.3f}")
            logger.info(f"    Composition: {no_data.get('composition_score', 0):.3f}")
            logger.info(f"    Texture: {no_data.get('texture_score', 0):.3f}")
            logger.info(f"    Warnings: {len(no_data.get('warnings', []))}")
            
            logger.info(f"  With narrative context:")
            logger.info(f"    Overall: {with_data.get('overall_score', 0):.3f}")
            logger.info(f"    Composition: {with_data.get('composition_score', 0):.3f}")
            logger.info(f"    Texture: {with_data.get('texture_score', 0):.3f}")
            logger.info(f"    Warnings: {len(with_data.get('warnings', []))}")
            
            diff = with_data.get('overall_score', 0) - no_data.get('overall_score', 0)
            logger.info(f"\n  Difference: {diff:+.3f}")
            
            results.append({
                "command": command,
                "archetype": metadata.get("archetype"),
                "without_narrative": {
                    "overall": no_data.get('overall_score', 0),
                    "composition": no_data.get('composition_score', 0),
                    "texture": no_data.get('texture_score', 0),
                    "warnings": len(no_data.get('warnings', [])),
                },
                "with_narrative": {
                    "overall": with_data.get('overall_score', 0),
                    "composition": with_data.get('composition_score', 0),
                    "texture": with_data.get('texture_score', 0),
                    "warnings": len(with_data.get('warnings', [])),
                },
                "difference": diff,
            })
    
    return results


def test_full_react_flow():
    """Test full ReAct flow with narrative integration."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: FULL REACT FLOW WITH NARRATIVE")
    logger.info("=" * 80)
    
    test_commands = [
        "create dramatic mountains with valleys and cliffs",
        "design a serene desert with rolling dunes",
    ]
    
    llm_client = create_llm_client()
    if not llm_client:
        logger.warning("LLM client not available - skipping full ReAct flow test")
        return [{"command": cmd, "success": False, "error": "LLM client not available"} for cmd in test_commands]
    
    agent = ReActAgentV2(llm_client, prompt_profile="compact", max_iterations=3)
    
    results = []
    
    for command in test_commands:
        logger.info(f"\n{'='*80}")
        logger.info(f"Command: {command}")
        logger.info(f"{'='*80}")
        
        scene_state = {
            "features": [],
            "semantic_scene": {"entities": []},
            "seed": 42,
            "base_biome_fn": None,
            "action_history": []
        }
        
        # Run ReAct agent
        result = agent.solve(command, scene_state, temperature=0.3)
        
        if result.get("success"):
            actions = result.get("actions", [])
            iterations = result.get("iterations", 0)
            tool_calls = result.get("total_tool_calls", 0)
            
            logger.info(f"\n✓ ReAct completed:")
            logger.info(f"  Iterations: {iterations}")
            logger.info(f"  Tool Calls: {tool_calls}")
            logger.info(f"  Actions Generated: {len(actions)}")
            
            # Check if narrative was extracted
            narrative_meta = scene_state.get("_narrative_meta", {})
            narrative_constraints = scene_state.get("_narrative", {})
            
            if narrative_meta:
                logger.info(f"\n✓ Narrative extracted:")
                logger.info(f"  Archetype: {narrative_meta.get('archetype')}")
                logger.info(f"  Aesthetic Goals: {narrative_meta.get('aesthetic_goals')}")
                
                if narrative_constraints:
                    logger.info(f"\n✓ Constraints stored:")
                    logger.info(f"  Clustering: {narrative_constraints.get('spatial_patterns', {}).get('clustering_tendency')}")
                    logger.info(f"  Primary Features: {narrative_constraints.get('feature_preferences', {}).get('primary', [])}")
            else:
                logger.warning("✗ Narrative not extracted")
            
            # Analyze actions
            if actions:
                logger.info(f"\n✓ Actions Analysis:")
                action_types = {}
                for action in actions:
                    action_type = action.get("type", "unknown")
                    action_types[action_type] = action_types.get(action_type, 0) + 1
                
                for action_type, count in action_types.items():
                    logger.info(f"  {action_type}: {count}")
                
                # Check if actions match narrative preferences
                if narrative_constraints:
                    feature_prefs = narrative_constraints.get("feature_preferences", {})
                    primary = feature_prefs.get("primary", [])
                    
                    matching = sum(1 for a in actions if a.get("type") in primary)
                    logger.info(f"\n  Actions matching primary features: {matching}/{len(actions)}")
            
            results.append({
                "command": command,
                "success": True,
                "iterations": iterations,
                "tool_calls": tool_calls,
                "actions_count": len(actions),
                "narrative_extracted": bool(narrative_meta),
                "constraints_stored": bool(narrative_constraints),
                "actions": actions[:5],  # First 5 for analysis
            })
        else:
            logger.error(f"✗ ReAct failed: {result.get('error')}")
            results.append({
                "command": command,
                "success": False,
                "error": result.get("error"),
            })
    
    return results


def comprehensive_test():
    """Run all tests and generate comprehensive report."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE NARRATIVE-REACT INTEGRATION TEST")
    logger.info("=" * 80)
    
    all_results = {}
    
    # Test 1: Narrative Extraction
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: Testing Narrative Extraction")
    logger.info("=" * 80)
    all_results["narrative_extraction"] = test_narrative_extraction()
    
    # Test 2: Spatial Tool Constraints
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: Testing Spatial Tool Constraint Usage")
    logger.info("=" * 80)
    all_results["spatial_constraints"] = test_spatial_tool_constraints()
    
    # Test 3: Quality Evaluation
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: Testing Quality Evaluation with Narrative")
    logger.info("=" * 80)
    all_results["quality_evaluation"] = test_quality_evaluation_narrative()
    
    # Test 4: Full ReAct Flow
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 4: Testing Full ReAct Flow")
    logger.info("=" * 80)
    all_results["full_flow"] = test_full_react_flow()
    
    # Summary Report
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info("=" * 80)
    
    # Narrative Extraction Summary
    logger.info("\n1. NARRATIVE EXTRACTION:")
    extraction_results = all_results["narrative_extraction"]
    successful = sum(1 for r in extraction_results if r.get("narrative_extracted"))
    logger.info(f"   Success Rate: {successful}/{len(extraction_results)}")
    for r in extraction_results:
        if r.get("narrative_extracted"):
            logger.info(f"   ✓ {r['command'][:50]}... → {r.get('archetype')}")
    
    # Spatial Constraints Summary
    logger.info("\n2. SPATIAL CONSTRAINT USAGE:")
    spatial_results = all_results["spatial_constraints"]
    logger.info(f"   Distance Difference: {spatial_results.get('distance_diff', 0):.1f}")
    if spatial_results.get('distance_diff', 0) > 0:
        logger.info("   ✓ Constraints are affecting spatial calculations")
    else:
        logger.warning("   ⚠ Constraints may not be affecting calculations")
    
    # Quality Evaluation Summary
    logger.info("\n3. QUALITY EVALUATION:")
    quality_results = all_results["quality_evaluation"]
    for r in quality_results:
        diff = r.get("difference", 0)
        status = "✓ DIFFERENT" if abs(diff) > 0.01 else "⚠ SAME"
        logger.info(f"   {status}: {r['command'][:40]}... → {diff:+.3f}")
    
    # Full Flow Summary
    logger.info("\n4. FULL REACT FLOW:")
    flow_results = all_results["full_flow"]
    successful_flows = sum(1 for r in flow_results if r.get("success"))
    logger.info(f"   Success Rate: {successful_flows}/{len(flow_results)}")
    for r in flow_results:
        if r.get("success"):
            narrative_ok = "✓" if r.get("narrative_extracted") else "✗"
            constraints_ok = "✓" if r.get("constraints_stored") else "✗"
            logger.info(f"   {narrative_ok} Narrative | {constraints_ok} Constraints | "
                       f"{r.get('actions_count', 0)} actions | {r.get('iterations', 0)} iterations")
    
    # Save detailed results
    output_file = Path("logs/narrative_react_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"\n✓ Detailed results saved to: {output_file}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Tests Complete!")
    logger.info("=" * 80)
    
    return all_results


if __name__ == "__main__":
    results = comprehensive_test()

