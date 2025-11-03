"""SemanticEntity - Semantic entity representation.

This module defines semantic entities that track the meaning and context
of terrain features, enabling natural language references like
"the dunes" or "the mountains".
"""

import time
from typing import Dict, List, Optional


class SemanticEntity:
    """
    Semantic entity representing a conceptual grouping of features.
    
    Semantic entities track:
    - What the user called it ("the dunes", "two mountains")
    - Which features belong to it (feature IDs)
    - Keywords for matching ("dunes", "desert", "sandy")
    - Metadata (creation time, user intent, etc.)
    
    Attributes:
        id: Unique entity identifier (e.g., "dunes_1", "mountain_group_1")
        type: Entity type ("scene", "group", "composition", "feature")
        label: User's label ("the dunes", "two mountains")
        keywords: List of keywords for matching
        description: Natural language description
        feature_refs: List of feature IDs belonging to this entity
        metadata: Additional metadata dictionary
        created_at: Timestamp when entity was created
        user_intent: Original user command that created this entity
    """
    
    def __init__(self, entity_id: str, entity_type: str, label: str):
        """
        Initialize a semantic entity.
        
        Args:
            entity_id: Unique identifier (e.g., "dunes_1")
            entity_type: Type of entity ("scene", "group", "composition", "feature")
            label: User's label ("the dunes", "two mountains")
        """
        self.id = entity_id
        self.type = entity_type
        self.label = label
        self.keywords: List[str] = []
        self.description: str = ""
        self.feature_refs: List[int] = []
        self.metadata: Dict = {}
        self.created_at: float = time.time()
        self.user_intent: str = ""
        self.relationship_ids: List[str] = []  # IDs of relationships this entity participates in
    
    def add_keyword(self, keyword: str):
        """
        Add a keyword for matching.
        
        Args:
            keyword: Keyword to add (e.g., "dunes", "desert", "sandy")
        """
        keyword_lower = keyword.lower().strip()
        if keyword_lower and keyword_lower not in self.keywords:
            self.keywords.append(keyword_lower)
    
    def add_keywords(self, keywords: List[str]):
        """
        Add multiple keywords.
        
        Args:
            keywords: List of keywords to add
        """
        for keyword in keywords:
            self.add_keyword(keyword)
    
    def add_feature_ref(self, feature_id: int):
        """
        Add a feature ID reference.
        
        Args:
            feature_id: Feature ID to add
        """
        if feature_id not in self.feature_refs:
            self.feature_refs.append(feature_id)
    
    def add_feature_refs(self, feature_ids: List[int]):
        """
        Add multiple feature ID references.
        
        Args:
            feature_ids: List of feature IDs to add
        """
        for feature_id in feature_ids:
            self.add_feature_ref(feature_id)
    
    def remove_feature_ref(self, feature_id: int) -> bool:
        """
        Remove a feature ID reference.
        
        Args:
            feature_id: Feature ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if feature_id in self.feature_refs:
            self.feature_refs.remove(feature_id)
            return True
        return False
    
    def set_description(self, description: str):
        """
        Set the natural language description.
        
        Args:
            description: Description text
        """
        self.description = description
    
    def set_user_intent(self, intent: str):
        """
        Set the original user command/intent.
        
        Args:
            intent: User command that created this entity
        """
        self.user_intent = intent
    
    def set_metadata(self, key: str, value):
        """
        Set a metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default=None):
        """
        Get a metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def matches_label(self, text: str) -> bool:
        """
        Check if text matches this entity's label.
        
        Args:
            text: Text to check
            
        Returns:
            True if text matches label (case-insensitive)
        """
        text_lower = text.lower().strip()
        label_lower = self.label.lower().strip()
        
        # Exact match
        if text_lower == label_lower:
            return True
        
        # Contains match
        if text_lower in label_lower or label_lower in text_lower:
            return True
        
        return False
    
    def matches_keyword(self, text: str) -> bool:
        """
        Check if text matches any keyword.
        
        Args:
            text: Text to check
            
        Returns:
            True if text matches any keyword
        """
        text_lower = text.lower().strip()
        return any(kw in text_lower or text_lower in kw for kw in self.keywords)
    
    def matches(self, text: str) -> bool:
        """
        Check if text matches this entity (label or keywords).
        
        Args:
            text: Text to check
            
        Returns:
            True if text matches label or any keyword
        """
        return self.matches_label(text) or self.matches_keyword(text)
    
    def add_relationship_id(self, relationship_id: str):
        """Add a relationship ID."""
        if relationship_id not in self.relationship_ids:
            self.relationship_ids.append(relationship_id)
    
    def remove_relationship_id(self, relationship_id: str):
        """Remove a relationship ID."""
        if relationship_id in self.relationship_ids:
            self.relationship_ids.remove(relationship_id)
    
    def to_dict(self) -> Dict:
        """
        Serialize entity to dictionary.
        
        Returns:
            Dictionary representation of entity
        """
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "keywords": self.keywords.copy(),
            "description": self.description,
            "feature_refs": self.feature_refs.copy(),
            "metadata": self.metadata.copy(),
            "created_at": self.created_at,
            "user_intent": self.user_intent,
            "relationship_ids": self.relationship_ids.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SemanticEntity':
        """
        Deserialize entity from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Reconstructed SemanticEntity
        """
        entity = cls(
            entity_id=data["id"],
            entity_type=data["type"],
            label=data["label"]
        )
        entity.keywords = data.get("keywords", []).copy()
        entity.description = data.get("description", "")
        entity.feature_refs = data.get("feature_refs", []).copy()
        entity.metadata = data.get("metadata", {}).copy()
        entity.created_at = data.get("created_at", time.time())
        entity.user_intent = data.get("user_intent", "")
        entity.relationship_ids = data.get("relationship_ids", []).copy()
        
        return entity
    
    def __repr__(self) -> str:
        """String representation of entity."""
        feature_count = len(self.feature_refs)
        keyword_count = len(self.keywords)
        return (
            f"SemanticEntity(id='{self.id}', type='{self.type}', "
            f"label='{self.label}', features={feature_count}, keywords={keyword_count})"
        )

