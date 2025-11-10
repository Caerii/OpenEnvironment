"""
Narrative development tool - extract geological stories from user commands.

This module analyzes user intent and creates a TerrainNarrative that guides
aesthetically pleasing and geologically plausible terrain generation.
"""

import re
import logging
from typing import List, Optional, Dict, Any

from .types import (
    TerrainNarrative,
    AestheticGoal,
    GeologicalProcess
)
from .archetypes import match_archetype_from_keywords, TERRAIN_ARCHETYPES


logger = logging.getLogger(__name__)


# Aesthetic keyword mapping
AESTHETIC_KEYWORDS = {
    # Scale & Drama
    "dramatic": AestheticGoal.DRAMATIC,
    "vast": AestheticGoal.VAST,
    "expansive": AestheticGoal.VAST,
    "intimate": AestheticGoal.INTIMATE,
    "cozy": AestheticGoal.INTIMATE,
    "monumental": AestheticGoal.MONUMENTAL,
    "massive": AestheticGoal.MONUMENTAL,
    "epic": AestheticGoal.MONUMENTAL,
    
    # Mood & Atmosphere
    "serene": AestheticGoal.SERENE,
    "peaceful": AestheticGoal.SERENE,
    "calm": AestheticGoal.SERENE,
    "mysterious": AestheticGoal.MYSTERIOUS,
    "enigmatic": AestheticGoal.MYSTERIOUS,
    "harsh": AestheticGoal.HARSH,
    "brutal": AestheticGoal.HARSH,
    "inviting": AestheticGoal.INVITING,
    "welcoming": AestheticGoal.INVITING,
    "desolate": AestheticGoal.DESOLATE,
    "barren": AestheticGoal.DESOLATE,
    "lonely": AestheticGoal.DESOLATE,
    
    # Visual Qualities
    "rugged": AestheticGoal.RUGGED,
    "rough": AestheticGoal.RUGGED,
    "jagged": AestheticGoal.RUGGED,
    "smooth": AestheticGoal.SMOOTH,
    "gentle": AestheticGoal.SMOOTH,
    "soft": AestheticGoal.SMOOTH,
    "organic": AestheticGoal.ORGANIC,
    "natural": AestheticGoal.ORGANIC,
    "geometric": AestheticGoal.GEOMETRIC,
    "angular": AestheticGoal.GEOMETRIC,
    "layered": AestheticGoal.LAYERED,
    "stratified": AestheticGoal.LAYERED,
    
    # Color & Texture
    "warm": AestheticGoal.WARM,
    "golden": AestheticGoal.WARM,
    "cool": AestheticGoal.COOL,
    "icy": AestheticGoal.COOL,
    "varied": AestheticGoal.VARIED,
    "diverse": AestheticGoal.VARIED,
    "uniform": AestheticGoal.UNIFORM,
    "consistent": AestheticGoal.UNIFORM,
    
    # Quality modifiers
    "beautiful": AestheticGoal.VARIED,  # Beauty through variety
    "stunning": AestheticGoal.DRAMATIC,  # Stunning = dramatic
    "majestic": AestheticGoal.MONUMENTAL  # Majestic = monumental
}


def extract_aesthetic_goals(command: str) -> List[AestheticGoal]:
    """
    Extract aesthetic goals from user command.
    
    Args:
        command: Natural language command
        
    Returns:
        List of AestheticGoal enums
    """
    goals = []
    command_lower = command.lower()
    
    for keyword, goal in AESTHETIC_KEYWORDS.items():
        if keyword in command_lower:
            if goal not in goals:
                goals.append(goal)
    
    # If no aesthetic keywords, infer from archetype keywords
    if not goals:
        if any(word in command_lower for word in ["desert", "dune", "sand"]):
            goals = [AestheticGoal.VAST, AestheticGoal.WARM, AestheticGoal.SMOOTH]
        elif any(word in command_lower for word in ["mountain", "peak", "alpine"]):
            goals = [AestheticGoal.DRAMATIC, AestheticGoal.RUGGED, AestheticGoal.MONUMENTAL]
        elif any(word in command_lower for word in ["valley", "river", "water"]):
            goals = [AestheticGoal.INVITING, AestheticGoal.LAYERED, AestheticGoal.ORGANIC]
        else:
            # Default: varied and natural
            goals = [AestheticGoal.VARIED, AestheticGoal.ORGANIC]
    
    return goals


def extract_mood_keywords(command: str) -> List[str]:
    """
    Extract free-form mood descriptors from command.
    
    Args:
        command: Natural language command
        
    Returns:
        List of mood keywords
    """
    mood_keywords = []
    
    # Common mood descriptors
    mood_patterns = [
        r'\b(beautiful|stunning|amazing|gorgeous|lovely)\b',
        r'\b(dark|light|bright|dim|shadowy)\b',
        r'\b(ancient|old|new|young|weathered)\b',
        r'\b(wild|tame|civilized|pristine|untouched)\b',
        r'\b(alien|familiar|strange|exotic|foreign)\b'
    ]
    
    for pattern in mood_patterns:
        matches = re.findall(pattern, command, re.IGNORECASE)
        mood_keywords.extend([m.lower() for m in matches])
    
    return list(set(mood_keywords))  # Remove duplicates


def infer_time_scale(command: str, archetype_name: str) -> str:
    """
    Infer geological time scale from command and archetype.
    
    Args:
        command: Natural language command
        archetype_name: Selected archetype name
        
    Returns:
        "young", "mature", or "ancient"
    """
    command_lower = command.lower()
    
    # Explicit keywords
    if any(word in command_lower for word in ["new", "young", "fresh", "recent"]):
        return "young"
    elif any(word in command_lower for word in ["ancient", "old", "weathered", "eroded"]):
        return "ancient"
    
    # Infer from archetype
    if "volcanic" in archetype_name.lower():
        return "young"  # Volcanic landscapes are typically young
    elif "glacial" in archetype_name.lower():
        return "mature"  # Glacial features are mature
    elif "depositional" in archetype_name.lower():
        return "ancient"  # Plains take long time
    else:
        return "mature"  # Default


def infer_weathering_level(time_scale: str, aesthetic_goals: List[AestheticGoal]) -> float:
    """
    Infer weathering level from time scale and aesthetics.
    
    Args:
        time_scale: "young", "mature", or "ancient"
        aesthetic_goals: List of aesthetic goals
        
    Returns:
        0.0-1.0 (fresh → heavily weathered)
    """
    # Base from time scale
    base_weathering = {
        "young": 0.2,
        "mature": 0.5,
        "ancient": 0.8
    }[time_scale]
    
    # Adjust for aesthetics
    if AestheticGoal.RUGGED in aesthetic_goals:
        base_weathering *= 0.8  # Less weathered = more rugged
    elif AestheticGoal.SMOOTH in aesthetic_goals:
        base_weathering *= 1.2  # More weathered = smoother
    
    return min(1.0, max(0.0, base_weathering))


def infer_wind_direction(archetype_name: str) -> Optional[float]:
    """
    Infer wind direction from archetype.
    
    Args:
        archetype_name: Selected archetype name
        
    Returns:
        0-360 degrees, or None if not wind-relevant
    """
    if "wind" in archetype_name.lower() or "aeolian" in archetype_name.lower():
        return 45.0  # Default: NE winds (common prevailing wind)
    return None


def infer_climate(archetype_name: str, aesthetic_goals: List[AestheticGoal]) -> str:
    """
    Infer climate from archetype and aesthetics.
    
    Args:
        archetype_name: Selected archetype name
        aesthetic_goals: List of aesthetic goals
        
    Returns:
        "arid", "temperate", "alpine", "tropical"
    """
    archetype_lower = archetype_name.lower()
    
    if "wind" in archetype_lower or "volcanic" in archetype_lower:
        return "arid"
    elif "glacial" in archetype_lower or "alpine" in str(aesthetic_goals):
        return "alpine"
    elif "water" in archetype_lower:
        return "temperate"
    else:
        return "temperate"  # Default


def calculate_focal_point_bias(aesthetic_goals: List[AestheticGoal]) -> tuple[float, float]:
    """
    Calculate focal point position bias using golden ratio or rule of thirds.
    
    Args:
        aesthetic_goals: List of aesthetic goals
        
    Returns:
        (x, y) normalized 0-1, golden ratio position
    """
    # Golden ratio: ~0.618
    golden_ratio = 0.618
    
    # Use golden ratio for dramatic/monumental
    if AestheticGoal.DRAMATIC in aesthetic_goals or AestheticGoal.MONUMENTAL in aesthetic_goals:
        return (golden_ratio, 1.0 - golden_ratio)  # Upper-right golden position
    
    # Rule of thirds: 0.333 or 0.667
    if AestheticGoal.ORGANIC in aesthetic_goals:
        return (0.4, 0.35)  # Slightly off-center for natural feel
    
    # Center for serene/uniform
    if AestheticGoal.SERENE in aesthetic_goals or AestheticGoal.UNIFORM in aesthetic_goals:
        return (0.5, 0.5)
    
    # Default: golden ratio
    return (golden_ratio, 1.0 - golden_ratio)


def develop_terrain_narrative(
    user_command: str,
    scene_state: Optional[Dict[str, Any]] = None
) -> Optional[TerrainNarrative]:
    """
    Develop terrain narrative from user command.
    
    This function analyzes the user's natural language command and creates a
    comprehensive TerrainNarrative that guides all subsequent generation steps.
    
    Args:
        user_command: Natural language terrain command
        scene_state: Current scene state (optional, for context)
        
    Returns:
        TerrainNarrative object or None if development fails
    """
    try:
        logger.info(f"Developing narrative for: {user_command[:100]}...")
        
        # Step 1: Extract keywords
        words = re.findall(r'\b\w+\b', user_command.lower())
        
        # Step 2: Match archetype
        archetype = match_archetype_from_keywords(words)
        logger.info(f"Selected archetype: {archetype.name}")
        
        # Step 3: Extract aesthetic goals
        aesthetic_goals = extract_aesthetic_goals(user_command)
        if not aesthetic_goals:
            aesthetic_goals = archetype.typical_aesthetics
        logger.info(f"Aesthetic goals: {[g.value for g in aesthetic_goals]}")
        
        # Step 4: Extract mood
        mood = extract_mood_keywords(user_command)
        
        # Step 5: Infer parameters
        time_scale = infer_time_scale(user_command, archetype.name)
        weathering = infer_weathering_level(time_scale, aesthetic_goals)
        wind_dir = infer_wind_direction(archetype.name)
        climate = infer_climate(archetype.name, aesthetic_goals)
        
        # Step 6: Determine feature guidance
        hero_type = archetype.primary_features[0] if archetype.primary_features else None
        supporting_types = archetype.secondary_features
        accent_types = archetype.accent_features
        
        # Step 7: Calculate composition parameters
        focal_bias = calculate_focal_point_bias(aesthetic_goals)
        depth_layers = 3 if AestheticGoal.LAYERED in aesthetic_goals else 2
        negative_space = 0.7 if AestheticGoal.VAST in aesthetic_goals else 0.3
        
        # Step 8: Generate story
        story = generate_geological_story(
            archetype,
            aesthetic_goals,
            time_scale,
            weathering
        )
        
        # Step 9: Create narrative
        narrative = TerrainNarrative(
            archetype=archetype,
            story=story,
            aesthetic_goals=aesthetic_goals,
            mood=mood,
            primary_process=archetype.primary_process,
            time_scale=time_scale,
            weathering_level=weathering,
            wind_direction=wind_dir,
            water_flow_direction=None,  # TODO: Infer from topography
            climate=climate,
            hero_feature_type=hero_type,
            supporting_feature_types=supporting_types,
            accent_feature_types=accent_types,
            focal_point_bias=focal_bias,
            depth_layers_needed=depth_layers,
            negative_space_importance=negative_space,
            target_coherence=0.8,  # Aim for high quality
            max_refinement_iterations=5
        )
        
        logger.info(f"Narrative developed successfully")
        logger.info(f"Story: {story[:150]}...")
        
        return narrative
        
    except Exception as e:
        logger.error(f"Failed to develop narrative: {e}", exc_info=True)
        return None


def generate_geological_story(
    archetype,
    aesthetic_goals: List[AestheticGoal],
    time_scale: str,
    weathering: float
) -> str:
    """
    Generate human-readable geological story.
    
    Args:
        archetype: TerrainArchetype
        aesthetic_goals: List of aesthetic goals
        time_scale: "young", "mature", or "ancient"
        weathering: 0.0-1.0 weathering level
        
    Returns:
        Story string
    """
    # Build story components
    time_desc = {
        "young": "recently",
        "mature": "over millennia",
        "ancient": "over eons"
    }[time_scale]
    
    weathering_desc = "heavily weathered" if weathering > 0.7 else \
                      "moderately weathered" if weathering > 0.4 else \
                      "fresh and sharp"
    
    aesthetic_desc = " and ".join([g.value for g in aesthetic_goals[:2]])
    
    # Process-specific story templates
    process_stories = {
        GeologicalProcess.AEOLIAN_DEPOSITION: f"Prevailing winds have {time_desc} sculpted golden sand into {aesthetic_desc} dunes across this {weathering_desc} basin.",
        GeologicalProcess.FLUVIAL_EROSION: f"Ancient waters have {time_desc} carved {aesthetic_desc} valleys through layers of {weathering_desc} rock.",
        GeologicalProcess.TECTONIC_UPLIFT: f"Tectonic forces have {time_desc} thrust {aesthetic_desc} peaks skyward, their {weathering_desc} faces telling stories of upheaval.",
        GeologicalProcess.VOLCANIC_FORMATION: f"Volcanic activity has {time_desc} built {aesthetic_desc} cones and flows of {weathering_desc} lava.",
        GeologicalProcess.ALLUVIAL_DEPOSITION: f"Rivers have {time_desc} deposited sediments, creating {aesthetic_desc} plains of {weathering_desc} alluvium.",
        GeologicalProcess.GLACIAL_CARVING: f"Glaciers have {time_desc} carved {aesthetic_desc} valleys with U-shaped profiles through {weathering_desc} bedrock."
    }
    
    base_story = process_stories.get(
        archetype.primary_process,
        f"{archetype.description} shaped {time_desc}."
    )
    
    return base_story

