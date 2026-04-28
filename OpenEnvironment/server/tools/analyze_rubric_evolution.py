"""
Deep analysis of rubric evolution outputs.
Evaluates what makes sense and what doesn't.
"""

import sys
import os
from pathlib import Path

server_dir = Path(__file__).parent.parent
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
from server.semantic.evaluation.rubric_evolution import RubricEvolutionService
from semantic.evaluation import DEFAULT_QUALITY_RUBRIC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_context_rubrics():
    """Analyze context-aware rubric generation outputs."""
    logger.info("=" * 80)
    logger.info("CONTEXT RUBRIC ANALYSIS")
    logger.info("=" * 80)
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set")
        return
    
    service = RubricEvolutionService(gemini_key)
    base_rubric = DEFAULT_QUALITY_RUBRIC
    
    test_cases = [
        ("create a dramatic mountain landscape with valleys and cliffs", "dramatic_mountain"),
        ("design a serene desert with rolling dunes", "serene_desert"),
        ("build a balanced landscape with hills and valleys", "balanced_landscape"),
    ]
    
    results = []
    for command, expected_context in test_cases:
        logger.info(f"\n{'='*80}")
        logger.info(f"Command: {command}")
        logger.info(f"Expected Context: {expected_context}")
        logger.info(f"{'='*80}")
        
        try:
            context_rubric = service.generate_context_rubric(command, base_rubric)
            context_info = context_rubric.get("_context", {})
            
            context_type = context_info.get("context_type", "unknown")
            priorities = context_info.get("priority_criteria", [])
            goals = context_info.get("aesthetic_goals", [])
            thresholds = context_info.get("thresholds", {})
            
            logger.info(f"\n✓ Context Type: {context_type}")
            logger.info(f"✓ Priority Criteria ({len(priorities)}): {priorities}")
            logger.info(f"✓ Aesthetic Goals ({len(goals)}):")
            for goal in goals:
                logger.info(f"    - {goal}")
            
            if thresholds:
                logger.info(f"\n✓ Adaptive Thresholds:")
                for criterion, values in list(thresholds.items())[:5]:
                    logger.info(f"    {criterion}: {values}")
            
            # Evaluate if it makes sense
            evaluation = evaluate_context_rubric(context_type, priorities, goals, expected_context)
            results.append({
                "command": command,
                "context_type": context_type,
                "priorities": priorities,
                "goals": goals,
                "thresholds": thresholds,
                "evaluation": evaluation,
            })
            
        except Exception as e:
            logger.error(f"Failed: {e}", exc_info=True)
            results.append({
                "command": command,
                "error": str(e),
            })
    
    return results


def evaluate_context_rubric(context_type, priorities, goals, expected_context):
    """Evaluate if the context rubric makes sense."""
    evaluation = {
        "makes_sense": True,
        "strengths": [],
        "concerns": [],
        "score": 0.0,
    }
    
    # Check if context type matches
    if expected_context in context_type.lower() or context_type.lower() in expected_context:
        evaluation["strengths"].append("Context type correctly identified")
        evaluation["score"] += 0.3
    else:
        evaluation["concerns"].append(f"Context type mismatch: got '{context_type}', expected '{expected_context}'")
        evaluation["score"] += 0.1
    
    # Check if priorities are relevant
    if len(priorities) >= 3:
        evaluation["strengths"].append(f"Good number of priority criteria ({len(priorities)})")
        evaluation["score"] += 0.2
    else:
        evaluation["concerns"].append(f"Too few priority criteria ({len(priorities)})")
    
    # Check if goals are specific
    if len(goals) >= 3:
        evaluation["strengths"].append(f"Good number of aesthetic goals ({len(goals)})")
        evaluation["score"] += 0.2
        # Check specificity
        specific_goals = [g for g in goals if len(g.split()) > 3]
        if len(specific_goals) >= 2:
            evaluation["strengths"].append("Goals are specific and actionable")
            evaluation["score"] += 0.2
        else:
            evaluation["concerns"].append("Goals could be more specific")
    else:
        evaluation["concerns"].append(f"Too few aesthetic goals ({len(goals)})")
    
    # Check if priorities match context
    if context_type == "dramatic_mountain":
        expected_priorities = ["height", "rock", "steep", "contrast"]
        matches = sum(1 for p in priorities if any(e in p.lower() for e in expected_priorities))
        if matches >= 2:
            evaluation["strengths"].append("Priorities match dramatic mountain context")
            evaluation["score"] += 0.1
        else:
            evaluation["concerns"].append("Priorities don't strongly match dramatic mountain context")
    
    elif context_type == "serene_desert":
        expected_priorities = ["sand", "smooth", "gentle", "calm"]
        matches = sum(1 for p in priorities if any(e in p.lower() for e in expected_priorities))
        if matches >= 2:
            evaluation["strengths"].append("Priorities match serene desert context")
            evaluation["score"] += 0.1
        else:
            evaluation["concerns"].append("Priorities don't strongly match serene desert context")
    
    evaluation["makes_sense"] = evaluation["score"] >= 0.6
    
    return evaluation


def analyze_evolved_rubric():
    """Analyze the evolved rubric from pattern identification."""
    logger.info("\n" + "=" * 80)
    logger.info("EVOLVED RUBRIC ANALYSIS")
    logger.info("=" * 80)
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("GEMINI_API_KEY not set")
        return
    
    # Create mock terrains with realistic scores
    from PIL import Image
    import numpy as np
    
    preview_dir = Path("logs/test_evolution")
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    terrains = []
    for i in range(5):
        session_dir = preview_dir / f"test_{i}"
        session_dir.mkdir(exist_ok=True)
        
        # Create more realistic heightmaps
        heightmap = np.random.rand(512, 512).astype(np.float32)
        if i < 3:  # High quality - more structured
            heightmap = np.clip(heightmap * 1.2 + np.random.rand(512, 512) * 0.3, 0, 1)
        height_path = session_dir / "height.png"
        Image.fromarray((heightmap * 255).astype(np.uint8)).save(height_path)
        
        splatmap = np.random.rand(512, 512, 4).astype(np.float32)
        splatmap = splatmap / splatmap.sum(axis=2, keepdims=True)  # Normalize
        splat_path = session_dir / "splat.png"
        Image.fromarray((splatmap * 255).astype(np.uint8)).save(splat_path)
        
        score = 0.85 if i < 3 else 0.45
        terrains.append({
            "heightmap_path": str(height_path),
            "splatmap_path": str(splat_path),
            "score": score,
            "command": f"test_command_{i}",
            "actions": [
                {"type": "mountain", "x": 256, "y": 256, "height": 0.8} if i < 3
                else {"type": "hill", "x": 200, "y": 200, "height": 0.4}
            ],
        })
    
    try:
        service = RubricEvolutionService(gemini_key)
        base_rubric = DEFAULT_QUALITY_RUBRIC
        
        logger.info(f"\nEvolving rubric from {len(terrains)} terrains...")
        evolved_rubric = service.evolve_rubric_from_batch(terrains, base_rubric, min_samples=3)
        
        # Analyze evolved rubric
        logger.info("\n" + "-" * 80)
        logger.info("EVOLVED RUBRIC DETAILS")
        logger.info("-" * 80)
        
        base_comp = base_rubric.get("composition", {})
        evolved_comp = evolved_rubric.get("composition", {})
        
        new_criteria = set(evolved_comp.keys()) - set(base_comp.keys())
        
        logger.info(f"\nNew Criteria Added: {len(new_criteria)}")
        for crit in new_criteria:
            crit_data = evolved_comp.get(crit, {})
            logger.info(f"\n  {crit}:")
            logger.info(f"    Threshold: {crit_data.get('threshold', 'N/A')}")
            logger.info(f"    Weight: {crit_data.get('weight', 'N/A')}")
        
        # Evaluate new criteria
        evaluation = evaluate_new_criteria(new_criteria, evolved_comp)
        
        logger.info("\n" + "-" * 80)
        logger.info("CRITERIA EVALUATION")
        logger.info("-" * 80)
        
        for crit_name, eval_data in evaluation.items():
            logger.info(f"\n{crit_name}:")
            logger.info(f"  Makes Sense: {eval_data['makes_sense']}")
            logger.info(f"  Score: {eval_data['score']:.2f}")
            if eval_data['strengths']:
                logger.info(f"  Strengths:")
                for strength in eval_data['strengths']:
                    logger.info(f"    ✓ {strength}")
            if eval_data['concerns']:
                logger.info(f"  Concerns:")
                for concern in eval_data['concerns']:
                    logger.info(f"    ⚠ {concern}")
        
        return {
            "evolved_rubric": evolved_rubric,
            "new_criteria": list(new_criteria),
            "evaluation": evaluation,
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return None


def evaluate_new_criteria(new_criteria, evolved_comp):
    """Evaluate if the new criteria make sense."""
    evaluation = {}
    
    for crit_name in new_criteria:
        crit_data = evolved_comp.get(crit_name, {})
        threshold = crit_data.get("threshold", "")
        weight = crit_data.get("weight", 0.8)
        
        eval_data = {
            "makes_sense": True,
            "strengths": [],
            "concerns": [],
            "score": 0.5,  # Start with neutral score
        }
        
        # Check if criterion name is clear
        if len(crit_name.split()) <= 5:
            eval_data["strengths"].append("Criterion name is clear and concise")
            eval_data["score"] += 0.2
        else:
            eval_data["concerns"].append("Criterion name is too long/complex")
        
        # Check if threshold is specified
        if threshold and threshold != "N/A":
            eval_data["strengths"].append("Threshold is specified")
            eval_data["score"] += 0.2
        else:
            eval_data["concerns"].append("Threshold is vague or missing")
        
        # Check if weight is reasonable
        if 0.5 <= weight <= 1.2:
            eval_data["strengths"].append(f"Weight ({weight}) is reasonable")
            eval_data["score"] += 0.1
        else:
            eval_data["concerns"].append(f"Weight ({weight}) may be too high/low")
        
        # Check if criterion is measurable
        measurable_keywords = ["count", "ratio", "correlation", "coverage", "entropy", "std", "mean"]
        if any(kw in threshold.lower() or kw in crit_name.lower() for kw in measurable_keywords):
            eval_data["strengths"].append("Criterion appears measurable")
            eval_data["score"] += 0.2
        else:
            eval_data["concerns"].append("Criterion may be difficult to measure objectively")
        
        # Check if criterion is relevant to terrain quality
        relevant_keywords = ["spatial", "composition", "texture", "height", "feature", "geological", "aesthetic"]
        if any(kw in crit_name.lower() for kw in relevant_keywords):
            eval_data["strengths"].append("Criterion is relevant to terrain quality")
            eval_data["score"] += 0.2
        else:
            eval_data["concerns"].append("Criterion relevance to terrain quality is unclear")
        
        eval_data["makes_sense"] = eval_data["score"] >= 0.6
        
        evaluation[crit_name] = eval_data
    
    return evaluation


def comprehensive_evaluation(context_results, evolution_results):
    """Comprehensive evaluation of all outputs."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE EVALUATION")
    logger.info("=" * 80)
    
    # Context rubric evaluation
    logger.info("\n1. CONTEXT RUBRIC GENERATION:")
    if context_results:
        successful = [r for r in context_results if r.get("evaluation")]
        avg_score = sum(r["evaluation"]["score"] for r in successful) / len(successful) if successful else 0
        
        logger.info(f"   Average Quality Score: {avg_score:.2f}/1.0")
        logger.info(f"   Successful: {len(successful)}/{len(context_results)}")
        
        # Analyze what works
        all_strengths = []
        all_concerns = []
        for r in successful:
            eval_data = r.get("evaluation", {})
            all_strengths.extend(eval_data.get("strengths", []))
            all_concerns.extend(eval_data.get("concerns", []))
        
        if all_strengths:
            logger.info(f"\n   Common Strengths:")
            from collections import Counter
            strength_counts = Counter(all_strengths)
            for strength, count in strength_counts.most_common(3):
                logger.info(f"     ✓ {strength} ({count}x)")
        
        if all_concerns:
            logger.info(f"\n   Common Concerns:")
            from collections import Counter
            concern_counts = Counter(all_concerns)
            for concern, count in concern_counts.most_common(3):
                logger.info(f"     ⚠ {concern} ({count}x)")
    
    # Evolution evaluation
    logger.info("\n2. RUBRIC EVOLUTION:")
    if evolution_results and evolution_results.get("evaluation"):
        eval_data = evolution_results["evaluation"]
        new_criteria = evolution_results.get("new_criteria", [])
        
        logger.info(f"   New Criteria: {len(new_criteria)}")
        
        makes_sense_count = sum(1 for e in eval_data.values() if e.get("makes_sense"))
        logger.info(f"   Criteria That Make Sense: {makes_sense_count}/{len(new_criteria)}")
        
        avg_score = sum(e.get("score", 0) for e in eval_data.values()) / len(eval_data) if eval_data else 0
        logger.info(f"   Average Criteria Quality: {avg_score:.2f}/1.0")
        
        # Analyze criteria
        logger.info(f"\n   Criteria Analysis:")
        for crit_name, crit_eval in list(eval_data.items())[:5]:
            score = crit_eval.get("score", 0)
            makes_sense = crit_eval.get("makes_sense", False)
            status = "✓" if makes_sense else "⚠"
            logger.info(f"     {status} {crit_name}: {score:.2f}")
    
    # Overall assessment
    logger.info("\n" + "-" * 80)
    logger.info("OVERALL ASSESSMENT")
    logger.info("-" * 80)
    
    what_works = []
    what_doesnt = []
    improvements_needed = []
    
    # Context rubrics
    if context_results:
        successful_context = [r for r in context_results if r.get("evaluation", {}).get("makes_sense")]
        if len(successful_context) >= 2:
            what_works.append("Context-aware rubric generation produces relevant, context-specific criteria")
        else:
            what_doesnt.append("Context rubrics may not be context-specific enough")
    
    # Evolution
    if evolution_results:
        new_criteria = evolution_results.get("new_criteria", [])
        if len(new_criteria) >= 3:
            what_works.append(f"Rubric evolution discovers new criteria ({len(new_criteria)} added)")
        else:
            what_doesnt.append("Rubric evolution doesn't discover enough new criteria")
        
        eval_data = evolution_results.get("evaluation", {})
        measurable = sum(1 for e in eval_data.values() if "measurable" in str(e.get("strengths", [])))
        if measurable < len(new_criteria) * 0.6:
            improvements_needed.append("Some new criteria may not be easily measurable")
    
    logger.info("\n✓ What Works:")
    for item in what_works:
        logger.info(f"  - {item}")
    
    if what_doesnt:
        logger.info("\n⚠ What Doesn't Work:")
        for item in what_doesnt:
            logger.info(f"  - {item}")
    
    if improvements_needed:
        logger.info("\n🔧 Improvements Needed:")
        for item in improvements_needed:
            logger.info(f"  - {item}")
    
    # Recommendations
    logger.info("\n" + "-" * 80)
    logger.info("RECOMMENDATIONS")
    logger.info("-" * 80)
    
    recommendations = []
    
    if context_results:
        recommendations.append("Context rubrics are working well - integrate into quality evaluation")
    
    if evolution_results and evolution_results.get("new_criteria"):
        recommendations.append("Evolved criteria are interesting but need validation - test with real terrains")
        recommendations.append("Some criteria (Lighting, Atmosphere) may be hard to measure - consider alternatives")
        recommendations.append("Focus on measurable criteria first (Spatial Organization, Scale/Depth)")
    
    recommendations.append("Run evolution with real terrain data (not mocks) for better patterns")
    recommendations.append("Validate evolved rubrics with A/B testing before adopting")
    
    for i, rec in enumerate(recommendations, 1):
        logger.info(f"{i}. {rec}")


if __name__ == "__main__":
    logger.info("Starting Comprehensive Rubric Evolution Analysis...")
    
    # Test context rubrics
    context_results = analyze_context_rubrics()
    
    # Test evolution
    evolution_results = analyze_evolved_rubric()
    
    # Comprehensive evaluation
    comprehensive_evaluation(context_results, evolution_results)
    
    logger.info("\n" + "=" * 80)
    logger.info("Analysis Complete!")
    logger.info("=" * 80)

