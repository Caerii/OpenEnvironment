"""
Analyze what context rubrics are actually doing - show the threshold changes.
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
                    os.environ[key] = value

import json
import logging
from semantic.rubric_evolution import RubricEvolutionService
from semantic.evaluation import DEFAULT_QUALITY_RUBRIC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def analyze_context_rubrics():
    """Show what context rubrics actually change."""
    logger.info("=" * 80)
    logger.info("ANALYZING CONTEXT RUBRIC THRESHOLDS")
    logger.info("=" * 80)
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set")
        return
    
    service = RubricEvolutionService(gemini_key)
    
    test_commands = [
        ("create a dramatic mountain landscape with valleys and cliffs", "dramatic_mountain"),
        ("design a serene desert with rolling dunes", "serene_desert"),
        ("build a balanced landscape with hills and valleys", "balanced_landscape"),
    ]
    
    base_rubric = DEFAULT_QUALITY_RUBRIC
    base_comp = base_rubric.get("composition", {})
    base_tex = base_rubric.get("textures", {})
    
    logger.info("\nBASE RUBRIC THRESHOLDS:")
    logger.info(f"  Composition:")
    logger.info(f"    min_feature_count: {base_comp.get('min_feature_count', 'N/A')}")
    logger.info(f"    min_type_diversity: {base_comp.get('min_type_diversity', 'N/A')}")
    logger.info(f"    min_extent_diagonal: {base_comp.get('min_extent_diagonal', 'N/A')}")
    logger.info(f"    min_height_std: {base_comp.get('min_height_std', 'N/A')}")
    logger.info(f"  Textures:")
    logger.info(f"    coverage_targets: {base_tex.get('coverage_targets', 'N/A')}")
    
    for command, expected_context in test_commands:
        logger.info(f"\n{'='*80}")
        logger.info(f"Command: {command}")
        logger.info(f"Expected Context: {expected_context}")
        logger.info(f"{'='*80}")
        
        try:
            context_rubric = service.generate_context_rubric(command, base_rubric)
            context_info = context_rubric.get("_context", {})
            
            if not context_info:
                logger.warning("No context info returned")
                continue
            
            logger.info(f"\nContext Type: {context_info.get('context_type', 'unknown')}")
            logger.info(f"Priority Criteria: {context_info.get('priority_criteria', [])}")
            logger.info(f"Aesthetic Goals: {context_info.get('aesthetic_goals', [])}")
            
            thresholds = context_info.get("thresholds", {})
            if thresholds:
                logger.info(f"\nADAPTED THRESHOLDS:")
                
                # Composition thresholds
                if "feature_count" in thresholds:
                    fc = thresholds["feature_count"]
                    if isinstance(fc, dict):
                        logger.info(f"  feature_count: {fc.get('minimum', 'N/A')} - {fc.get('maximum', 'N/A')} (base: {base_comp.get('min_feature_count', 'N/A')})")
                    else:
                        logger.info(f"  feature_count: {fc} (base: {base_comp.get('min_feature_count', 'N/A')})")
                
                if "type_diversity" in thresholds:
                    td = thresholds["type_diversity"]
                    if isinstance(td, dict):
                        logger.info(f"  type_diversity: {td.get('minimum', 'N/A')} - {td.get('maximum', 'N/A')} (base: {base_comp.get('min_type_diversity', 'N/A')})")
                    else:
                        logger.info(f"  type_diversity: {td} (base: {base_comp.get('min_type_diversity', 'N/A')})")
                
                if "height_std" in thresholds:
                    hs = thresholds["height_std"]
                    if isinstance(hs, dict):
                        logger.info(f"  height_std: {hs.get('minimum', 'N/A')} - {hs.get('maximum', 'N/A')} (base: {base_comp.get('min_height_std', 'N/A')})")
                    else:
                        logger.info(f"  height_std: {hs} (base: {base_comp.get('min_height_std', 'N/A')})")
                
                # Texture coverage targets
                if "coverage_targets" in thresholds:
                    ct = thresholds["coverage_targets"]
                    logger.info(f"\n  Texture Coverage Targets:")
                    base_ct = base_tex.get("coverage_targets", {})
                    for texture, target in ct.items():
                        base_target = base_ct.get(texture, "N/A")
                        if isinstance(target, dict):
                            logger.info(f"    {texture}: {target.get('minimum', 'N/A')} - {target.get('maximum', 'N/A')} (base: {base_target})")
                        else:
                            logger.info(f"    {texture}: {target} (base: {base_target})")
            
            # Show the full context info
            logger.info(f"\nFull Context Info:")
            logger.info(json.dumps(context_info, indent=2))
            
        except Exception as e:
            logger.error(f"Failed to generate context rubric: {e}", exc_info=True)


if __name__ == "__main__":
    analyze_context_rubrics()

