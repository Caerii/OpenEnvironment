"""
Rubric Evolution System - LLM-as-a-Judge Meta-Learning

Uses Gemini to analyze terrains and evolve quality rubrics over time.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

logger = logging.getLogger(__name__)


class RubricEvolutionService:
    """
    Evolves quality rubrics using LLM-as-a-Judge visual analysis.
    
    The judge analyzes terrains and proposes rubric improvements based on
    what actually makes terrain aesthetically pleasing, rather than static thresholds.
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        if genai is None:
            raise RuntimeError("google-genai package required for rubric evolution")
        self.client = genai.Client(api_key=gemini_api_key or "")
        self.model = "gemini-2.5-flash-image"  # Visual analysis model
    
    def evolve_rubric_from_batch(
        self,
        terrain_batch: List[Dict[str, Any]],
        current_rubric: Dict[str, Any],
        min_samples: int = 5,
    ) -> Dict[str, Any]:
        """
        Analyze a batch of terrains and evolve the rubric.
        
        Args:
            terrain_batch: List of dicts with:
                - "actions": terrain actions
                - "score": quality score
                - "heightmap_path": path to heightmap image
                - "splatmap_path": path to splatmap image
                - "command": original command
            current_rubric: Current rubric to evolve
            min_samples: Minimum samples needed for evolution
        
        Returns:
            Evolved rubric with improvements
        """
        if len(terrain_batch) < min_samples:
            logger.warning(f"Need at least {min_samples} samples, got {len(terrain_batch)}")
            return current_rubric
        
        # Separate high and low quality terrains
        high_quality = [t for t in terrain_batch if t.get("score", 0) >= 0.8]
        low_quality = [t for t in terrain_batch if t.get("score", 0) < 0.6]
        
        if not high_quality:
            logger.warning("No high-quality terrains to learn from")
            return current_rubric
        
        # Analyze patterns
        patterns = self._identify_aesthetic_patterns(high_quality, low_quality)
        
        # Propose improvements
        improvements = self._propose_rubric_improvements(
            patterns, current_rubric, terrain_batch
        )
        
        # Integrate improvements
        evolved_rubric = self._integrate_improvements(current_rubric, improvements)
        
        return evolved_rubric
    
    def _identify_aesthetic_patterns(
        self,
        high_quality: List[Dict[str, Any]],
        low_quality: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Use Gemini to identify aesthetic patterns in high vs low quality terrains."""
        
        parts = []
        
        # System prompt
        parts.append(genai_types.Part(
            text="""You are an expert art director and terrain aesthetics specialist.
Your task is to analyze terrain renders and identify what makes them aesthetically pleasing.

Analyze the following terrains and identify:
1. Common patterns in high-quality terrains (score 0.8+)
2. What distinguishes them from low-quality terrains
3. Aesthetic principles they follow (spatial balance, visual hierarchy, texture coherence, etc.)
4. Missing or inadequate rubric criteria

Focus on:
- Spatial relationships and composition
- Visual hierarchy and focal points
- Texture placement and coherence
- Geological plausibility
- Aesthetic principles (contrast, rhythm, unity, balance)

Return structured JSON with your analysis."""
        ))
        
        # High quality examples
        parts.append(genai_types.Part(
            text=f"\n=== HIGH QUALITY TERRAINS (Score 0.8+) ===\n"
            f"Analyzing {len(high_quality)} high-quality examples:\n"
        ))
        
        for i, terrain in enumerate(high_quality[:5], 1):  # Limit to 5 for token efficiency
            parts.append(genai_types.Part(
                text=f"\n--- High Quality Example {i} ---\n"
                f"Score: {terrain.get('score', 0):.3f}\n"
                f"Command: {terrain.get('command', 'N/A')}\n"
                f"Actions: {len(terrain.get('actions', []))} features\n"
            ))
            
            # Add images
            if terrain.get("heightmap_path"):
                try:
                    with open(terrain["heightmap_path"], "rb") as f:
                        parts.append(genai_types.Part(
                            inline_data=genai_types.Blob(
                                data=f.read(),
                                mime_type="image/png"
                            )
                        ))
                except Exception as e:
                    logger.warning(f"Failed to load heightmap: {e}")
            
            if terrain.get("splatmap_path"):
                try:
                    with open(terrain["splatmap_path"], "rb") as f:
                        parts.append(genai_types.Part(
                            inline_data=genai_types.Blob(
                                data=f.read(),
                                mime_type="image/png"
                            )
                        ))
                except Exception as e:
                    logger.warning(f"Failed to load splatmap: {e}")
        
        # Low quality examples (for contrast)
        if low_quality:
            parts.append(genai_types.Part(
                text=f"\n=== LOW QUALITY TERRAINS (Score < 0.6) ===\n"
                f"Analyzing {len(low_quality[:3])} low-quality examples for contrast:\n"
            ))
            
            for i, terrain in enumerate(low_quality[:3], 1):
                parts.append(genai_types.Part(
                    text=f"\n--- Low Quality Example {i} ---\n"
                    f"Score: {terrain.get('score', 0):.3f}\n"
                    f"Command: {terrain.get('command', 'N/A')}\n"
                ))
                
                if terrain.get("heightmap_path"):
                    try:
                        with open(terrain["heightmap_path"], "rb") as f:
                            parts.append(genai_types.Part(
                                inline_data=genai_types.Blob(
                                    data=f.read(),
                                    mime_type="image/png"
                                )
                            ))
                    except Exception as e:
                        logger.warning(f"Failed to load heightmap: {e}")
        
        # Analysis request
        parts.append(genai_types.Part(
            text="""
Based on your analysis, return JSON with:
{
  "observed_patterns": [
    {
      "pattern": "Description of pattern",
      "frequency": "How often it appears in high-quality terrains",
      "aesthetic_principle": "What principle it follows",
      "importance": "high/medium/low"
    }
  ],
  "distinguishing_factors": [
    "What makes high-quality terrains different from low-quality ones"
  ],
  "missing_criteria": [
    {
      "criterion": "Name of missing criterion",
      "description": "What it measures",
      "suggested_threshold": "Suggested threshold or range",
      "rationale": "Why this matters"
    }
  ],
  "threshold_adjustments": {
    "criterion_name": {
      "current": "Current threshold",
      "suggested": "Suggested threshold",
      "rationale": "Why adjust"
    }
  },
  "aesthetic_principles": [
    "Key aesthetic principles observed in high-quality terrains"
  ]
}
"""
        ))
        
        # Build content from parts
        content = genai_types.Content(role="user", parts=parts)
        
        try:
            # Use models.generate_content (newer API)
            # Pass config as dict to avoid Pydantic validation issues
            response = self.client.models.generate_content(
                model=self.model,
                contents=[content],
                config={
                    "temperature": 0.4,  # Slightly higher for creative analysis
                    "top_p": 0.9,
                    "max_output_tokens": 2048,
                },
            )
            
            # Extract text from response
            text = ""
            if hasattr(response, "text"):
                text = response.text
            elif hasattr(response, "candidates") and response.candidates:
                text = response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else ""
            elif hasattr(response, "output_text"):
                text = response.output_text
            
            # Extract JSON from response
            json_text = self._extract_json(text)
            if json_text:
                return json.loads(json_text)
            else:
                logger.warning("Failed to extract JSON from judge response")
                logger.debug(f"Response text: {text[:500]}")
                return {}
                
        except Exception as e:
            logger.error(f"Pattern identification failed: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return {}
    
    def _propose_rubric_improvements(
        self,
        patterns: Dict[str, Any],
        current_rubric: Dict[str, Any],
        terrain_batch: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Propose specific rubric improvements based on patterns."""
        
        improvements = {
            "new_criteria": [],
            "threshold_adjustments": {},
            "weight_adjustments": {},
            "context_adaptations": {},
        }
        
        # Extract missing criteria
        missing = patterns.get("missing_criteria", [])
        for criterion in missing:
            improvements["new_criteria"].append({
                "name": criterion.get("criterion"),
                "description": criterion.get("description"),
                "threshold": criterion.get("suggested_threshold"),
                "weight": 0.8,  # Default weight
                "category": self._categorize_criterion(criterion.get("criterion", "")),
            })
        
        # Extract threshold adjustments
        adjustments = patterns.get("threshold_adjustments", {})
        for criterion, adjustment in adjustments.items():
            improvements["threshold_adjustments"][criterion] = {
                "current": adjustment.get("current"),
                "suggested": adjustment.get("suggested"),
                "rationale": adjustment.get("rationale"),
            }
        
        # Analyze context-specific needs
        context_patterns = self._analyze_context_patterns(terrain_batch)
        if context_patterns:
            improvements["context_adaptations"] = context_patterns
        
        return improvements
    
    def _integrate_improvements(
        self,
        current_rubric: Dict[str, Any],
        improvements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Integrate improvements into rubric, creating evolved version."""
        
        evolved = json.loads(json.dumps(current_rubric))  # Deep copy
        
        # Filter criteria to keep only measurable ones
        measurable_keywords = [
            "spatial", "composition", "organization", "scale", "depth",
            "geological", "feature", "count", "diversity", "extent",
            "height", "texture", "coverage", "correlation", "entropy"
        ]
        
        unmeasurable_keywords = [
            "lighting", "atmosphere", "color", "palette", "harmony",
            "mood", "feeling", "emotion"
        ]
        
        # Add new criteria (filtered)
        for new_crit in improvements.get("new_criteria", []):
            crit_name = new_crit.get("name", "")
            crit_lower = crit_name.lower()
            
            # Skip unmeasurable criteria
            if any(kw in crit_lower for kw in unmeasurable_keywords):
                logger.info(f"Skipping unmeasurable criterion: {crit_name}")
                continue
            
            # Keep measurable criteria
            if any(kw in crit_lower for kw in measurable_keywords):
                category = new_crit.get("category", "composition")
                if category not in evolved:
                    evolved[category] = {}
                
                evolved[category][crit_name] = {
                    "threshold": new_crit.get("threshold"),
                    "weight": new_crit.get("weight", 0.8),
                }
                logger.info(f"Added measurable criterion: {crit_name}")
        
        # Adjust thresholds
        for criterion, adjustment in improvements.get("threshold_adjustments", {}).items():
            # Find criterion in rubric and update
            for category in evolved.values():
                if isinstance(category, dict) and criterion in category:
                    if isinstance(category[criterion], dict):
                        category[criterion]["threshold"] = adjustment.get("suggested")
                    else:
                        # Convert to dict format
                        category[criterion] = {
                            "threshold": adjustment.get("suggested"),
                            "weight": 1.0,
                        }
        
        # Add context adaptations
        if improvements.get("context_adaptations"):
            evolved["context_adaptations"] = improvements["context_adaptations"]
        
        # Add metadata
        evolved["_metadata"] = {
            "evolved_at": datetime.now().isoformat(),
            "improvements_applied": len(improvements.get("new_criteria", [])) + len(improvements.get("threshold_adjustments", {})),
            "version": evolved.get("_metadata", {}).get("version", 0) + 1,
        }
        
        return evolved
    
    def generate_context_rubric(
        self,
        command: str,
        base_rubric: Dict[str, Any],
        archetype: Optional[str] = None,
        aesthetic_goals: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate context-specific rubric based on command intent.
        
        Uses LLM to understand command context and adapt thresholds accordingly.
        
        Args:
            command: User command (for fallback)
            base_rubric: Base quality rubric
            archetype: Terrain archetype name (preferred over command analysis)
            aesthetic_goals: List of aesthetic goals (preferred over command analysis)
        """
        
        parts = []
        
        # Build context description - prefer structured data over command string
        if archetype and aesthetic_goals:
            context_desc = f"""Terrain Archetype: {archetype}
Aesthetic Goals: {', '.join(aesthetic_goals)}
Original Command: "{command}" (for reference)"""
        else:
            context_desc = f'Command: "{command}"'
        
        parts.append(genai_types.Part(
            text=f"""You are a terrain design specialist. Analyze this terrain context and suggest appropriate quality thresholds.

{context_desc}

Base Rubric:
{json.dumps(base_rubric, indent=2)}

Based on the archetype and aesthetic goals, suggest:
1. Appropriate thresholds for this context (dramatic vs serene, sparse vs dense, etc.)
2. Priority criteria (what matters most for this scene type)
3. Texture coverage targets (what textures should dominate for this archetype)

Return JSON:
{{
  "context_type": "dramatic_mountain|serene_desert|balanced_landscape|wind_sculpted|water_carved|etc",
  "thresholds": {{
    "feature_count": {{"minimum": 4, "good": 6, "excellent": 8}},
    "type_diversity": {{"minimum": 3, "good": 4, "excellent": 5}},
    "grass_coverage": {{"minimum": [0.1, 0.3], "good": [0.2, 0.4], "excellent": [0.25, 0.5]}},
    "rock_coverage": {{"minimum": [0.05, 0.25], "good": [0.1, 0.3], "excellent": [0.15, 0.35]}},
    "sand_coverage": {{"minimum": [0.0, 0.2], "good": [0.05, 0.25], "excellent": [0.1, 0.3]}},
    "snow_coverage": {{"minimum": [0.0, 0.15], "good": [0.05, 0.2], "excellent": [0.1, 0.25]}},
    ...
  }},
  "priority_criteria": ["criterion1", "criterion2", ...],
  "aesthetic_goals": ["goal1", "goal2", ...]
}}"""
        ))
        
        # Build content from parts
        content = genai_types.Content(role="user", parts=parts)
        
        try:
            # Use models.generate_content (newer API)
            # Pass config as dict to avoid Pydantic validation issues
            response = self.client.models.generate_content(
                model=self.model,
                contents=[content],
                config={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_output_tokens": 1024,
                },
            )
            
            # Extract text from response
            text = ""
            if hasattr(response, "text"):
                text = response.text
            elif hasattr(response, "candidates") and response.candidates:
                text = response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else ""
            elif hasattr(response, "output_text"):
                text = response.output_text
            
            json_text = self._extract_json(text)
            
            if json_text:
                context_rubric = json.loads(json_text)
                # Merge with base rubric
                adapted = json.loads(json.dumps(base_rubric))
                adapted["_context"] = context_rubric
                return adapted
            else:
                logger.warning("Failed to extract context rubric JSON")
                return base_rubric
                
        except Exception as e:
            logger.error(f"Context rubric generation failed: {e}", exc_info=True)
            return base_rubric
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from LLM response."""
        # Try to find JSON block
        import re
        
        # Look for JSON code block
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Look for JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return None
    
    def _categorize_criterion(self, name: str) -> str:
        """Categorize a criterion as composition or textures."""
        name_lower = name.lower()
        if any(term in name_lower for term in ["texture", "coverage", "alignment", "splat"]):
            return "textures"
        return "composition"
    
    def _analyze_context_patterns(
        self,
        terrain_batch: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze patterns by command context."""
        # Group by command type
        contexts = {}
        for terrain in terrain_batch:
            command = terrain.get("command", "").lower()
            context_type = self._classify_context(command)
            if context_type not in contexts:
                contexts[context_type] = []
            contexts[context_type].append(terrain)
        
        # Analyze each context
        adaptations = {}
        for context_type, terrains in contexts.items():
            if len(terrains) >= 3:  # Need minimum samples
                avg_score = sum(t.get("score", 0) for t in terrains) / len(terrains)
                if avg_score > 0.7:  # Good quality for this context
                    adaptations[context_type] = {
                        "avg_score": avg_score,
                        "sample_count": len(terrains),
                        "suggested_thresholds": self._infer_thresholds(terrains),
                    }
        
        return adaptations
    
    def _classify_context(self, command: str) -> str:
        """Classify command into context type."""
        command_lower = command.lower()
        
        if any(term in command_lower for term in ["dramatic", "epic", "grand", "majestic"]):
            return "dramatic"
        elif any(term in command_lower for term in ["serene", "peaceful", "calm", "tranquil"]):
            return "serene"
        elif any(term in command_lower for term in ["desert", "dunes", "sand"]):
            return "desert"
        elif any(term in command_lower for term in ["mountain", "peak", "summit"]):
            return "mountain"
        else:
            return "balanced"
    
    def _infer_thresholds(self, terrains: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer thresholds from high-quality terrains in this context."""
        # Simple heuristic: use median values from high-quality terrains
        # In practice, this would be more sophisticated
        return {
            "feature_count": {"minimum": 4, "good": 6, "excellent": 8},
            "type_diversity": {"minimum": 3, "good": 4, "excellent": 5},
        }


def evolve_rubric_from_history(
    history_file: Path,
    current_rubric: Dict[str, Any],
    gemini_api_key: Optional[str] = None,
    min_samples: int = 10,
) -> Dict[str, Any]:
    """
    Evolve rubric from quality history.
    
    Args:
        history_file: Path to quality_history.jsonl
        current_rubric: Current rubric to evolve
        gemini_api_key: Gemini API key
        min_samples: Minimum samples needed
    
    Returns:
        Evolved rubric
    """
    if not history_file.exists():
        logger.warning(f"History file not found: {history_file}")
        return current_rubric
    
    # Load history
    terrains = []
    with open(history_file) as f:
        for line in f:
            entry = json.loads(line)
            # Would need to load associated terrain images
            terrains.append({
                "score": entry.get("final_score", 0),
                "command": entry.get("command", ""),
                # Would need to store image paths in history
            })
    
    if len(terrains) < min_samples:
        logger.warning(f"Need at least {min_samples} samples, got {len(terrains)}")
        return current_rubric
    
    # Evolve rubric
    service = RubricEvolutionService(gemini_api_key)
    evolved = service.evolve_rubric_from_batch(terrains, current_rubric, min_samples)
    
    return evolved

