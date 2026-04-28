"""Reference resolution tools - see query_tools.py for implementation."""

from typing import Dict, List, Any

def resolve_reference(scene_state: Dict, reference: str) -> Dict[str, Any]:
    """Resolve natural language reference to feature IDs."""
    from .query_tools import query_entities
    return query_entities(scene_state, label=reference)

def resolve_temporal_reference(scene_state: Dict, temporal_phrase: str) -> Dict[str, Any]:
    """Resolve time-based references like 'recent', 'last'."""
    from .query_tools import query_entities
    import time
    
    if "recent" in temporal_phrase or "just" in temporal_phrase:
        threshold = time.time() - 60  # Last minute
        return query_entities(scene_state, created_after=threshold)
    return {"entities": []}

def resolve_attribute_filter(scene_state: Dict, keyword: str) -> Dict[str, Any]:
    """Resolve attribute-based filters like 'tall', 'steep'."""
    from .query_tools import query_entities
    return query_entities(scene_state, keyword=keyword)

