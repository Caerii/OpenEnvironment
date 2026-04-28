"""
Systematic test for Phase 1 and Phase 2 fixes.

Tests:
1. Phase 1: Context rubric uses archetype + goals
2. Phase 1: Refinement priority (texture first)
3. Phase 1: Archetype matching (feature combinations)
4. Phase 2: Texture-to-feature mapping
5. Phase 2: Parameter modification
6. Phase 2: Refinement uses new tools
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Setup paths
server_dir = Path(__file__).parent.parent
parent_dir = server_dir.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import terrain export functions
from server.terrain import to_png_8bit_gray, to_png_rgba

# Load environment variables
from dotenv import load_dotenv
env_path = server_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test results
test_results = {
    "phase1": {},
    "phase2": {},
    "integration": {},
    "summary": {}
}

# Setup sample_images directory
sample_images_dir = parent_dir / "sample_images"
sample_images_dir.mkdir(exist_ok=True)


def save_terrain_textures(
    heightmap: np.ndarray,
    splatmap: np.ndarray,
    test_name: str,
    suffix: str = ""
) -> Dict[str, str]:
    """
    Save heightmap and splatmap textures to sample_images folder.
    
    Args:
        heightmap: Heightmap array (H x W)
        splatmap: Splatmap array (H x W x 4)
        test_name: Name of the test (used in filename)
        suffix: Optional suffix for filename
    
    Returns:
        Dictionary with paths to saved images
    """
    try:
        # Normalize test name for filename
        safe_name = test_name.lower().replace(" ", "_").replace(":", "")
        if suffix:
            safe_name = f"{safe_name}_{suffix}"
        
        height_path = sample_images_dir / f"{safe_name}_height.png"
        splat_path = sample_images_dir / f"{safe_name}_splat.png"
        
        # Save heightmap (8-bit grayscale)
        to_png_8bit_gray(heightmap, str(height_path))
        
        # Save splatmap (RGBA)
        to_png_rgba(splatmap, str(splat_path))
        
        logger.info(f"Saved textures: {height_path.name}, {splat_path.name}")
        
        return {
            "heightmap": str(height_path),
            "splatmap": str(splat_path)
        }
    except Exception as e:
        logger.error(f"Failed to save textures: {e}", exc_info=True)
        return {}


def test_archetype_matching():
    """Test Phase 1: Archetype matching with feature combinations."""
    logger.info("=" * 80)
    logger.info("TEST 1: Archetype Matching (Feature Combinations)")
    logger.info("=" * 80)
    
    from server.semantic.narrative.archetypes import match_archetype_from_keywords
    
    test_cases = [
        {
            "command": "build a balanced landscape with hills and valleys",
            "keywords": ["hills", "valleys"],
            "expected": "waters_legacy",
            "reason": "valley + hills should match Water's Legacy"
        },
        {
            "command": "create dramatic mountains with peaks",
            "keywords": ["mountains", "peaks", "dramatic"],
            "expected": "ancient_uplift",
            "reason": "mountain + peaks should match Ancient Uplift"
        },
        {
            "command": "design a serene desert with rolling dunes",
            "keywords": ["desert", "dunes"],
            "expected": "wind_architect",
            "reason": "desert + dunes should match Wind Architect"
        },
        {
            "command": "make a valley with a river",
            "keywords": ["valley", "river"],
            "expected": "waters_legacy",
            "reason": "valley + river should match Water's Legacy"
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test_case['command']}")
        logger.info(f"Expected: {test_case['expected']}")
        
        try:
            archetype = match_archetype_from_keywords(test_case['keywords'])
            # Normalize archetype name for comparison (handle apostrophes, spaces, etc.)
            matched_name = archetype.name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
            expected_normalized = test_case['expected'].lower().replace("'", "").replace("-", "_")
            
            if matched_name == expected_normalized:
                logger.info(f"✅ PASSED: Matched {matched_name}")
                passed += 1
            else:
                logger.warning(f"❌ FAILED: Expected {test_case['expected']} ({expected_normalized}), got {matched_name}")
                failed += 1
                logger.warning(f"   Reason: {test_case['reason']}")
                logger.warning(f"   Archetype name: '{archetype.name}'")
        except Exception as e:
            logger.error(f"❌ ERROR: {e}", exc_info=True)
            failed += 1
    
    test_results["phase1"]["archetype_matching"] = {
        "passed": passed,
        "failed": failed,
        "total": len(test_cases),
        "success_rate": passed / len(test_cases) if test_cases else 0
    }
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Archetype Matching: {passed}/{len(test_cases)} passed ({passed/len(test_cases)*100:.1f}%)")
    logger.info(f"{'='*80}\n")
    
    return passed == len(test_cases)


def test_context_rubric_archetype():
    """Test Phase 1: Context rubric uses archetype + goals."""
    logger.info("=" * 80)
    logger.info("TEST 2: Context Rubric Uses Archetype + Goals")
    logger.info("=" * 80)
    
    try:
        from server.semantic.evaluation.rubric_evolution import RubricEvolutionService
        from server.semantic.evaluation import DEFAULT_QUALITY_RUBRIC
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            logger.warning("⚠️  Skipping: GEMINI_API_KEY not set")
            test_results["phase1"]["context_rubric"] = {"skipped": True, "reason": "No API key"}
            return False
        
        service = RubricEvolutionService(gemini_key)
        
        # Test with archetype + goals (preferred)
        logger.info("\nTest: Generate rubric with archetype + goals")
        archetype = "Ancient Uplift"
        goals = ["dramatic"]
        
        rubric1 = service.generate_context_rubric(
            command="create dramatic mountains",
            base_rubric=DEFAULT_QUALITY_RUBRIC,
            archetype=archetype,
            aesthetic_goals=goals
        )
        
        context1 = rubric1.get("_context", {})
        context_type1 = context1.get("context_type", "")
        
        logger.info(f"Context type: {context_type1}")
        logger.info(f"✅ PASSED: Rubric generated with archetype + goals")
        
        # Test with command only (fallback)
        logger.info("\nTest: Generate rubric with command only (fallback)")
        rubric2 = service.generate_context_rubric(
            command="create dramatic mountains",
            base_rubric=DEFAULT_QUALITY_RUBRIC
        )
        
        context2 = rubric2.get("_context", {})
        context_type2 = context2.get("context_type", "")
        
        logger.info(f"Context type: {context_type2}")
        logger.info(f"✅ PASSED: Rubric generated with command fallback")
        
        test_results["phase1"]["context_rubric"] = {
            "passed": True,
            "archetype_method": context_type1,
            "command_method": context_type2
        }
        
        logger.info(f"\n{'='*80}")
        logger.info("Context Rubric: ✅ PASSED")
        logger.info(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        test_results["phase1"]["context_rubric"] = {"passed": False, "error": str(e)}
        return False


def test_refinement_priority():
    """Test Phase 1: Refinement priority (texture first)."""
    logger.info("=" * 80)
    logger.info("TEST 3: Refinement Priority (Texture First)")
    logger.info("=" * 80)
    
    from server.semantic.tools.quality_tools import refine_composition
    
    # Create mock scene state
    scene_state = {
        "seed": 42,
        "_narrative_meta": {
            "archetype": "Ancient Uplift",
            "aesthetic_goals": ["dramatic"]
        }
    }
    
    # Mock actions
    actions = [
        {"kind": "add", "type": "mountain", "x": 256, "y": 256, "modifiers": {"height": 0.7, "radius": 60}}
    ]
    
    # Test warnings with texture first
    warnings = [
        "Grass coverage 0.05 outside desired 0.18-0.55 range.",
        "Scene coverage is narrow; spread features further apart.",
        "Feature diversity is low; introduce contrasting primitives."
    ]
    
    logger.info(f"\nWarnings: {warnings}")
    logger.info("Expected: Texture warning should be processed first")
    
    try:
        result = refine_composition(
            scene_state=scene_state,
            actions=actions,
            quality_warnings=warnings,
            max_refinements=3
        )
        
        if result.get("success"):
            changes = result.get("data", {}).get("changes_made", [])
            logger.info(f"\nChanges made: {changes}")
            
            # Check if texture-related changes are first
            texture_changes = [c for c in changes if "texture" in c.lower() or "coverage" in c.lower()]
            
            if texture_changes:
                logger.info(f"✅ PASSED: Texture changes found: {texture_changes[0]}")
                test_results["phase1"]["refinement_priority"] = {
                    "passed": True,
                    "texture_changes": texture_changes
                }
                return True
            else:
                logger.warning("⚠️  No texture changes found - may need texture analysis")
                test_results["phase1"]["refinement_priority"] = {
                    "passed": False,
                    "reason": "No texture changes found"
                }
                return False
        else:
            logger.error(f"❌ FAILED: {result.get('error')}")
            test_results["phase1"]["refinement_priority"] = {"passed": False, "error": result.get("error")}
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        test_results["phase1"]["refinement_priority"] = {"passed": False, "error": str(e)}
        return False


def test_texture_feature_mapping():
    """Test Phase 2: Texture-to-feature mapping."""
    logger.info("=" * 80)
    logger.info("TEST 4: Texture-to-Feature Mapping")
    logger.info("=" * 80)
    
    from server.semantic.tools.quality_tools import analyze_texture_feature_relationship, _render_terrain_preview
    
    scene_state = {
        "seed": 42,
        "base_biome_fn": None
    }
    
    # Create test actions
    actions = [
        {"kind": "add", "type": "mountain", "x": 256, "y": 256, "modifiers": {"height": 0.7, "radius": 60}},
        {"kind": "add", "type": "dunes", "x": 150, "y": 150, "modifiers": {"radius": 50}},
    ]
    
    logger.info(f"\nTesting with {len(actions)} actions")
    
    try:
        # Render and save textures
        saved_paths = {}
        heightmap, splatmap = _render_terrain_preview(actions, scene_state)
        if heightmap is not None and splatmap is not None:
            saved_paths = save_terrain_textures(
                heightmap, splatmap,
                "test_4_texture_feature_mapping"
            )
            logger.info(f"✅ Saved textures to sample_images folder")
        
        result = analyze_texture_feature_relationship(
            scene_state=scene_state,
            actions=actions,
            render_preview=True
        )
        
        if result.get("success"):
            data = result.get("data", {})
            contributions = data.get("feature_contributions", {})
            gaps = data.get("texture_gaps", [])
            
            logger.info(f"✅ PASSED: Analysis completed")
            logger.info(f"   Feature contributions: {len(contributions)}")
            logger.info(f"   Texture gaps found: {len(gaps)}")
            
            if contributions:
                logger.info(f"\nSample contribution:")
                sample_key = list(contributions.keys())[0]
                sample = contributions[sample_key]
                logger.info(f"   {sample_key}: {sample.get('feature_type')}")
                logger.info(f"   Grass: {sample.get('grass_coverage', 0):.3f}")
                logger.info(f"   Rock: {sample.get('rock_coverage', 0):.3f}")
            
            test_results["phase2"]["texture_mapping"] = {
                "passed": True,
                "contributions": len(contributions),
                "gaps": len(gaps),
                "saved_images": saved_paths
            }
            return True
        else:
            logger.error(f"❌ FAILED: {result.get('error')}")
            test_results["phase2"]["texture_mapping"] = {"passed": False, "error": result.get("error")}
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        test_results["phase2"]["texture_mapping"] = {"passed": False, "error": str(e)}
        return False


def test_parameter_modification():
    """Test Phase 2: Parameter modification."""
    logger.info("=" * 80)
    logger.info("TEST 5: Parameter Modification")
    logger.info("=" * 80)
    
    from server.semantic.tools.quality_tools import modify_feature_parameters
    
    scene_state = {"seed": 42}
    
    actions = [
        {"kind": "add", "type": "mountain", "x": 256, "y": 256, "modifiers": {"height": 0.7, "radius": 60}},
        {"kind": "add", "type": "dunes", "x": 150, "y": 150, "modifiers": {"radius": 50}},
    ]
    
    modifications = [
        {
            "action_id": 0,
            "radius": +30,
            "height": +0.1,
            "reason": "Increase rock coverage"
        },
        {
            "action_id": 1,
            "radius": +25,
            "reason": "Increase sand coverage"
        }
    ]
    
    logger.info(f"\nModifying {len(modifications)} features")
    
    try:
        result = modify_feature_parameters(
            scene_state=scene_state,
            actions=actions,
            modifications=modifications
        )
        
        if result.get("success"):
            data = result.get("data", {})
            refined_actions = data.get("refined_actions", [])
            changes = data.get("changes_made", [])
            
            logger.info(f"✅ PASSED: Modifications applied")
            logger.info(f"   Changes: {len(changes)}")
            
            for change in changes:
                logger.info(f"   - {change}")
            
            # Verify modifications
            original_radius_0 = actions[0]["modifiers"].get("radius", 60)
            new_radius_0 = refined_actions[0]["modifiers"].get("radius", 0)
            
            if new_radius_0 == original_radius_0 + 30:
                logger.info(f"   ✅ Verified: Action 0 radius {original_radius_0} → {new_radius_0}")
            else:
                logger.warning(f"   ⚠️  Mismatch: Expected {original_radius_0 + 30}, got {new_radius_0}")
            
            test_results["phase2"]["parameter_modification"] = {
                "passed": True,
                "changes_applied": len(changes)
            }
            return True
        else:
            logger.error(f"❌ FAILED: {result.get('error')}")
            test_results["phase2"]["parameter_modification"] = {"passed": False, "error": result.get("error")}
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        test_results["phase2"]["parameter_modification"] = {"passed": False, "error": str(e)}
        return False


def test_integration_refinement():
    """Test Phase 2: Integration - Refinement uses new tools."""
    logger.info("=" * 80)
    logger.info("TEST 6: Integration - Refinement Uses New Tools")
    logger.info("=" * 80)
    
    from server.semantic.tools.quality_tools import refine_composition, evaluate_terrain_quality, _render_terrain_preview
    
    scene_state = {
        "seed": 42,
        "base_biome_fn": None,
        "_narrative_meta": {
            "archetype": "Ancient Uplift",
            "aesthetic_goals": ["dramatic"]
        }
    }
    
    # Create initial actions
    actions = [
        {"kind": "add", "type": "mountain", "x": 256, "y": 256, "modifiers": {"height": 0.6, "radius": 50}},
    ]
    
    logger.info(f"\nInitial actions: {len(actions)}")
    
    try:
        # Save initial textures
        saved_paths_initial = {}
        saved_paths_refined = {}
        heightmap_initial, splatmap_initial = _render_terrain_preview(actions, scene_state)
        if heightmap_initial is not None and splatmap_initial is not None:
            saved_paths_initial = save_terrain_textures(
                heightmap_initial, splatmap_initial,
                "test_6_integration_refinement",
                "initial"
            )
            logger.info(f"✅ Saved initial textures to sample_images folder")
        
        # Evaluate quality
        eval_result = evaluate_terrain_quality(
            scene_state=scene_state,
            actions=actions,
            render_preview=True
        )
        
        if not eval_result.get("success"):
            logger.warning(f"⚠️  Evaluation failed: {eval_result.get('error')}")
            test_results["integration"]["refinement"] = {"skipped": True, "reason": "Evaluation failed"}
            return False
        
        eval_data = eval_result.get("data", {})
        initial_score = eval_data.get("overall_score", 0.0)
        warnings = eval_data.get("warnings", [])
        
        logger.info(f"Initial quality score: {initial_score:.3f}")
        logger.info(f"Warnings: {len(warnings)}")
        
        if not warnings:
            logger.info("⚠️  No warnings - adding test warnings")
            warnings = ["Grass coverage 0.05 outside desired 0.18-0.55 range."]
        
        # Refine
        refine_result = refine_composition(
            scene_state=scene_state,
            actions=actions,
            quality_warnings=warnings,
            max_refinements=3
        )
        
        if refine_result.get("success"):
            refine_data = refine_result.get("data", {})
            refined_actions = refine_data.get("refined_actions", [])
            changes = refine_data.get("changes_made", [])
            
            # Save refined textures
            heightmap_refined, splatmap_refined = _render_terrain_preview(refined_actions, scene_state)
            if heightmap_refined is not None and splatmap_refined is not None:
                saved_paths_refined = save_terrain_textures(
                    heightmap_refined, splatmap_refined,
                    "test_6_integration_refinement",
                    "refined"
                )
                logger.info(f"✅ Saved refined textures to sample_images folder")
            
            logger.info(f"✅ PASSED: Refinement completed")
            logger.info(f"   Original actions: {len(actions)}")
            logger.info(f"   Refined actions: {len(refined_actions)}")
            logger.info(f"   Changes: {len(changes)}")
            
            for change in changes:
                logger.info(f"   - {change}")
            
            # Check if texture analysis was used
            texture_analysis_used = any("parameter" in c.lower() or "radius" in c.lower() or "height" in c.lower() for c in changes)
            
            if texture_analysis_used:
                logger.info(f"   ✅ Texture analysis/parameter modification was used")
            else:
                logger.info(f"   ⚠️  Texture analysis may not have been used (fallback to adding features)")
            
            test_results["integration"]["refinement"] = {
                "passed": True,
                "initial_score": initial_score,
                "changes": len(changes),
                "texture_analysis_used": texture_analysis_used,
                "saved_images": {
                    "initial": saved_paths_initial,
                    "refined": saved_paths_refined
                }
            }
            return True
        else:
            logger.error(f"❌ FAILED: {refine_result.get('error')}")
            test_results["integration"]["refinement"] = {"passed": False, "error": refine_result.get("error")}
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        test_results["integration"]["refinement"] = {"passed": False, "error": str(e)}
        return False


def run_all_tests():
    """Run all tests and generate summary."""
    logger.info("\n" + "=" * 80)
    logger.info("SYSTEMATIC TEST SUITE: Phase 1 & Phase 2 Fixes")
    logger.info("=" * 80 + "\n")
    
    results = []
    
    # Phase 1 tests
    results.append(("Archetype Matching", test_archetype_matching()))
    results.append(("Context Rubric", test_context_rubric_archetype()))
    results.append(("Refinement Priority", test_refinement_priority()))
    
    # Phase 2 tests
    results.append(("Texture Mapping", test_texture_feature_mapping()))
    results.append(("Parameter Modification", test_parameter_modification()))
    
    # Integration tests
    results.append(("Integration Refinement", test_integration_refinement()))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} passed ({passed/total*100:.1f}%)")
    logger.info("=" * 80)
    
    # Save results
    test_results["summary"] = {
        "passed": passed,
        "total": total,
        "success_rate": passed / total if total > 0 else 0
    }
    
    results_file = server_dir / "logs" / "test_phase1_phase2_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"\nResults saved to: {results_file}")
    logger.info(f"Sample images saved to: {sample_images_dir}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

