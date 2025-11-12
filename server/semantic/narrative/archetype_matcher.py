"""
Semantic archetype matching using LLM with keyword fallback.

Leverages existing narrative pipeline infrastructure for robust matching.
"""

import logging
from typing import List, Optional, Dict, Any

from .archetypes import match_archetype_from_keywords, TERRAIN_ARCHETYPES, TerrainArchetype
from ..llm.factory import create_llm_client
from ..llm.clients import LLMClient

logger = logging.getLogger(__name__)


class ArchetypeMatcher:
    """
    Semantic archetype matching using LLM (preferred) or keywords (fallback).
    
    Leverages existing narrative pipeline infrastructure for robust matching.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize archetype matcher.
        
        Args:
            llm_client: Optional LLM client (if None, will try to create one)
        """
        self.llm_client = llm_client
        if self.llm_client is None:
            self.llm_client = create_llm_client()
    
    def match(
        self,
        command: str,
        keywords: Optional[List[str]] = None
    ) -> TerrainArchetype:
        """
        Match archetype using LLM (preferred) or keywords (fallback).
        
        Args:
            command: User command
            keywords: Optional extracted keywords (for fallback)
        
        Returns:
            Best matching TerrainArchetype
        """
        # Try LLM-based semantic matching first
        if self.llm_client:
            try:
                archetype = self._match_with_llm(command)
                if archetype:
                    logger.info(f"LLM matched archetype: {archetype.name}")
                    return archetype
            except Exception as e:
                logger.warning(f"LLM matching failed: {e}, using keyword fallback")
        
        # Fallback to keyword matching
        if keywords is None:
            import re
            keywords = re.findall(r'\b\w+\b', command.lower())
        
        archetype = match_archetype_from_keywords(keywords)
        logger.info(f"Keyword fallback matched archetype: {archetype.name}")
        return archetype
    
    def _match_with_llm(self, command: str) -> Optional[TerrainArchetype]:
        """
        Use LLM to semantically match archetype.
        
        Leverages the same semantic understanding used by narrative pipeline.
        """
        # Get archetype names and descriptions
        archetype_descriptions = {
            name: f"{arch.name}: {arch.description}"
            for name, arch in TERRAIN_ARCHETYPES.items()
        }
        
        archetype_list = "\n".join([
            f"- {name}: {desc}"
            for name, desc in archetype_descriptions.items()
        ])
        
        prompt = f"""Analyze this terrain generation command and select the most appropriate geological archetype.

Command: "{command}"

Available archetypes:
{archetype_list}

Consider:
- The primary geological processes described
- The dominant feature types mentioned
- The overall landscape character
- The aesthetic intent

Respond with ONLY the archetype key name (e.g., "ancient_uplift", "wind_architect", "waters_legacy").
Do not include any explanation or additional text."""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_completion_tokens=50
            )
            
            # Extract content from response (handles different client formats)
            content = None
            if hasattr(response, "choices") and len(response.choices) > 0:
                # Cerebras/Together format
                content = getattr(response.choices[0].message, "content", None)
            elif hasattr(response, "content"):
                # Direct content attribute
                content = response.content
            elif isinstance(response, dict):
                # Dictionary format
                content = response.get("content")
            
            if not content:
                return None
            
            archetype_key = str(content).strip().lower()
            
            # Clean up response (remove quotes, extra text)
            archetype_key = archetype_key.replace('"', '').replace("'", "")
            archetype_key = archetype_key.split()[0] if archetype_key.split() else ""
            
            # Validate archetype key
            if archetype_key in TERRAIN_ARCHETYPES:
                return TERRAIN_ARCHETYPES[archetype_key]
            else:
                logger.warning(f"LLM returned invalid archetype key: {archetype_key}")
                return None
                
        except Exception as e:
            logger.error(f"LLM archetype matching error: {e}", exc_info=True)
            return None


# Global instance (lazy initialization)
_matcher_instance: Optional[ArchetypeMatcher] = None


def get_archetype_matcher() -> ArchetypeMatcher:
    """Get global archetype matcher instance."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = ArchetypeMatcher()
    return _matcher_instance


def match_archetype_semantic(
    command: str,
    keywords: Optional[List[str]] = None
) -> TerrainArchetype:
    """
    Convenience function for semantic archetype matching.
    
    Uses LLM if available, falls back to keywords.
    """
    matcher = get_archetype_matcher()
    return matcher.match(command, keywords)

