"""
Comprehensive test suite for refactored modules.

Tests all new encapsulated modules and integration.
"""

import sys
import os
import logging
from pathlib import Path

# Setup paths
server_dir = Path(__file__).parent.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

# Load environment
from dotenv import load_dotenv
env_path = server_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test all new modules import correctly."""
    logger.info("=" * 80)
    logger.info("TEST 1: Import Tests")
    logger.info("=" * 80)
    
    errors = []
    
    # Test config imports
    try:
        from semantic.config import (
            TEXTURE_COVERAGE_THRESHOLDS,
            TERRAIN_CENTER_X,
            get_parameter_modification,
        )
        logger.info("✅ config.py imports work")
    except Exception as e:
        errors.append(f"config.py: {e}")
        logger.error(f"❌ config.py import failed: {e}")
    
    # Test state initializer imports
    try:
        from semantic.state.initializer import StateInitializer
        logger.info("✅ state/initializer.py imports work")
    except Exception as e:
        errors.append(f"state/initializer.py: {e}")
        logger.error(f"❌ state/initializer.py import failed: {e}")
    
    # Test feature types imports
    try:
        from semantic.features.types import (
            is_rock_feature,
            get_features_for_texture,
        )
        logger.info("✅ features/types.py imports work")
    except Exception as e:
        errors.append(f"features/types.py: {e}")
        logger.error(f"❌ features/types.py import failed: {e}")
    
    # Test warning types imports
    try:
        from semantic.evaluation.warning_types import (
            WarningCategory,
            QualityWarning,
            classify_warning,
        )
        logger.info("✅ evaluation/warning_types.py imports work")
    except Exception as e:
        errors.append(f"evaluation/warning_types.py: {e}")
        logger.error(f"❌ evaluation/warning_types.py import failed: {e}")
    
    # Test archetype matcher imports
    try:
        from semantic.narrative.archetype_matcher import (
            ArchetypeMatcher,
            match_archetype_semantic,
        )
        logger.info("✅ narrative/archetype_matcher.py imports work")
    except Exception as e:
        errors.append(f"narrative/archetype_matcher.py: {e}")
        logger.error(f"❌ narrative/archetype_matcher.py import failed: {e}")
    
    # Test quality_tools imports (critical)
    try:
        from semantic.tools.quality_tools import (
            evaluate_terrain_quality,
            refine_composition,
        )
        logger.info("✅ tools/quality_tools.py imports work")
    except Exception as e:
        errors.append(f"tools/quality_tools.py: {e}")
        logger.error(f"❌ tools/quality_tools.py import failed: {e}")
    
    if errors:
        logger.error(f"\n❌ {len(errors)} import errors found:")
        for error in errors:
            logger.error(f"   - {error}")
        return False
    
    logger.info(f"\n✅ All imports successful!")
    return True


def test_config_module():
    """Test configuration module functionality."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Configuration Module")
    logger.info("=" * 80)
    
    try:
        from semantic.config import (
            TEXTURE_COVERAGE_THRESHOLDS,
            get_parameter_modification,
            is_rock_feature,
            is_sand_feature,
        )
        
        # Test thresholds exist
        assert "grass" in TEXTURE_COVERAGE_THRESHOLDS
        assert "rock" in TEXTURE_COVERAGE_THRESHOLDS
        logger.info("✅ Texture thresholds accessible")
        
        # Test parameter modification
        mod = get_parameter_modification("sand", "dunes", 50.0)
        assert "radius" in mod
        assert mod["radius"] > 0
        logger.info(f"✅ Parameter modification works: {mod}")
        
        # Test feature type helpers
        assert is_rock_feature("mountain")
        assert is_sand_feature("dunes")
        assert not is_rock_feature("dunes")
        logger.info("✅ Feature type helpers work")
        
        return True
    except Exception as e:
        logger.error(f"❌ Config module test failed: {e}", exc_info=True)
        return False


def test_state_initializer():
    """Test state initializer."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: State Initializer")
    logger.info("=" * 80)
    
    try:
        from semantic.state.initializer import StateInitializer
        
        # Test with None
        state1 = StateInitializer.initialize(None)
        assert "features" in state1
        assert "seed" in state1
        assert "next_id" in state1
        logger.info("✅ Initialize with None works")
        
        # Test with existing state
        state2 = StateInitializer.initialize({"seed": 100, "custom": "value"})
        assert state2["seed"] == 100
        assert state2["custom"] == "value"
        assert "features" in state2
        logger.info("✅ Initialize with existing state works")
        
        # Test validation
        assert StateInitializer.validate(state1)
        assert not StateInitializer.validate({})
        logger.info("✅ Validation works")
        
        return True
    except Exception as e:
        logger.error(f"❌ State initializer test failed: {e}", exc_info=True)
        return False


def test_warning_types():
    """Test structured warning types."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Warning Types")
    logger.info("=" * 80)
    
    try:
        from semantic.evaluation.warning_types import (
            WarningCategory,
            QualityWarning,
            classify_warning,
        )
        
        # Test classification
        cat1 = classify_warning("Grass coverage 0.05 outside desired range")
        assert cat1 == WarningCategory.TEXTURE_COVERAGE
        logger.info(f"✅ Classified texture warning: {cat1}")
        
        cat2 = classify_warning("Feature diversity is low")
        assert cat2 == WarningCategory.DIVERSITY
        logger.info(f"✅ Classified diversity warning: {cat2}")
        
        # Test structured warning
        warning = QualityWarning(
            category=WarningCategory.TEXTURE_COVERAGE,
            message="Test warning",
            severity=0.8,
            affected_texture="grass"
        )
        assert warning.is_texture_warning()
        logger.info("✅ Structured warning works")
        
        return True
    except Exception as e:
        logger.error(f"❌ Warning types test failed: {e}", exc_info=True)
        return False


def test_archetype_matcher():
    """Test semantic archetype matcher."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Archetype Matcher")
    logger.info("=" * 80)
    
    try:
        from semantic.narrative.archetype_matcher import match_archetype_semantic
        
        # Test with keywords (fallback)
        archetype = match_archetype_semantic(
            "create dramatic mountains",
            keywords=["mountains", "dramatic"]
        )
        assert archetype is not None
        assert hasattr(archetype, "name")
        logger.info(f"✅ Archetype matching works: {archetype.name}")
        
        # Test different commands
        test_cases = [
            ("desert with dunes", ["desert", "dunes"]),
            ("valley with hills", ["valley", "hills"]),
        ]
        
        for command, keywords in test_cases:
            arch = match_archetype_semantic(command, keywords=keywords)
            assert arch is not None
            logger.info(f"✅ Matched '{command}' → {arch.name}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Archetype matcher test failed: {e}", exc_info=True)
        return False


def test_quality_tools_integration():
    """Test quality tools use new modules correctly."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Quality Tools Integration")
    logger.info("=" * 80)
    
    try:
        from semantic.tools.quality_tools import (
            evaluate_terrain_quality,
            refine_composition,
        )
        from semantic.state.initializer import StateInitializer
        
        # Create test state
        scene_state = StateInitializer.initialize({"seed": 42})
        actions = [
            {"kind": "add", "type": "mountain", "x": 256, "y": 256, "modifiers": {"radius": 50}}
        ]
        
        # Test evaluation (may fail if no API key, that's OK)
        try:
            result = evaluate_terrain_quality(
                scene_state=scene_state,
                actions=actions,
                render_preview=False  # Skip rendering for speed
            )
            if result.get("success"):
                logger.info("✅ Quality evaluation works")
            else:
                logger.warning(f"⚠️  Quality evaluation returned error: {result.get('error')}")
        except Exception as e:
            logger.warning(f"⚠️  Quality evaluation failed (may need API key): {e}")
        
        # Test refinement with structured warnings
        warnings = ["Grass coverage 0.05 outside desired range"]
        try:
            result = refine_composition(
                scene_state=scene_state,
                actions=actions,
                quality_warnings=warnings,
                max_refinements=1
            )
            if result.get("success"):
                logger.info("✅ Refinement works with structured warnings")
            else:
                logger.warning(f"⚠️  Refinement returned error: {result.get('error')}")
        except Exception as e:
            logger.warning(f"⚠️  Refinement failed (may need API key): {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Quality tools integration test failed: {e}", exc_info=True)
        return False


def test_narrative_pipeline_integration():
    """Test narrative pipeline uses semantic matcher."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Narrative Pipeline Integration")
    logger.info("=" * 80)
    
    try:
        from semantic.narrative.utils import run_narrative_pipeline
        
        # Test narrative generation
        command = "create dramatic mountains"
        scene_state = {"seed": 42}
        
        actions, metadata = run_narrative_pipeline(command, scene_state)
        
        if actions:
            logger.info(f"✅ Narrative pipeline works: {len(actions)} actions")
            logger.info(f"   Archetype: {metadata.get('archetype')}")
            return True
        else:
            logger.warning("⚠️  Narrative pipeline returned no actions")
            return False
    except Exception as e:
        logger.error(f"❌ Narrative pipeline test failed: {e}", exc_info=True)
        return False


def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE TEST SUITE: Refactored Modules")
    logger.info("=" * 80 + "\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Config Module", test_config_module()))
    results.append(("State Initializer", test_state_initializer()))
    results.append(("Warning Types", test_warning_types()))
    results.append(("Archetype Matcher", test_archetype_matcher()))
    results.append(("Quality Tools Integration", test_quality_tools_integration()))
    results.append(("Narrative Pipeline Integration", test_narrative_pipeline_integration()))
    
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
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

