"""Action domain models for terrain operations.

Actions represent user intents (add, remove, modify features) with proper typing.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

from .models import Position, Modifier


class ActionKind(Enum):
    """Type of terrain action."""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


@dataclass
class Action(ABC):
    """
    Base class for terrain actions.
    
    Actions represent user intents that will be executed against the terrain.
    They are the structured output of parsing and the input to execution.
    """
    kind: ActionKind
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for serialization."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        """Create Action from dictionary representation."""
        pass


@dataclass
class AddAction(Action):
    """
    Action to add new features to the terrain.
    
    Attributes:
        kind: Always ActionKind.ADD
        feature_type: Type of feature to add (e.g., "mountain", "valley")
        count: Number of features to add (default: 1)
        position: Where to place the feature(s)
        modifiers: Optional modifiers to adjust feature parameters
        metadata: Additional metadata (user intent, etc.)
    """
    feature_type: str
    count: int = 1
    position: Position = field(default_factory=lambda: Position(region="random"))
    modifiers: Modifier = field(default_factory=Modifier)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure kind is set correctly."""
        self.kind = ActionKind.ADD
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "kind": self.kind.value,
            "type": self.feature_type,
            "count": self.count,
        }
        
        # Add position
        position_dict = self.position.to_dict()
        if position_dict:
            result["position"] = position_dict
        
        # Add modifiers
        modifiers_dict = self.modifiers.to_dict()
        if modifiers_dict:
            result["modifiers"] = modifiers_dict
        
        # Add metadata
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AddAction":
        """Create AddAction from dictionary."""
        feature_type = data["type"]
        count = data.get("count", 1)
        
        # Parse position
        position_data = data.get("position", {})
        position = Position.from_dict(position_data) if position_data else Position(region="random")
        
        # Parse modifiers
        modifiers_data = data.get("modifiers", {})
        modifiers = Modifier.from_dict(modifiers_data) if modifiers_data else Modifier()
        
        # Extract metadata
        metadata = data.get("metadata", {})
        
        return cls(
            kind=ActionKind.ADD,
            feature_type=feature_type,
            count=count,
            position=position,
            modifiers=modifiers,
            metadata=metadata
        )


@dataclass
class RemoveAction(Action):
    """
    Action to remove features from the terrain.
    
    Supports multiple removal strategies:
    - By feature ID: target_feature_ids
    - By type: feature_type (removes most recent of that type)
    - By ordinal: feature_type + ordinal (e.g., "first mountain")
    
    Attributes:
        kind: Always ActionKind.REMOVE
        feature_type: Optional type filter
        ordinal: Optional ordinal position (1-based: 1 = first, 2 = second)
        target_feature_ids: Optional explicit list of feature IDs to remove
        metadata: Additional metadata
    """
    feature_type: Optional[str] = None
    ordinal: Optional[int] = None
    target_feature_ids: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure kind is set correctly and validate."""
        self.kind = ActionKind.REMOVE
        
        # Validate that at least one targeting method is specified
        if not any([self.feature_type, self.target_feature_ids]):
            raise ValueError("RemoveAction requires either feature_type or target_feature_ids")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "kind": self.kind.value,
        }
        
        if self.feature_type is not None:
            result["type"] = self.feature_type
        if self.ordinal is not None:
            result["ordinal"] = self.ordinal
        if self.target_feature_ids is not None:
            result["target_feature_ids"] = self.target_feature_ids
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoveAction":
        """Create RemoveAction from dictionary."""
        feature_type = data.get("type")
        ordinal = data.get("ordinal")
        target_feature_ids = data.get("target_feature_ids")
        metadata = data.get("metadata", {})
        
        return cls(
            kind=ActionKind.REMOVE,
            feature_type=feature_type,
            ordinal=ordinal,
            target_feature_ids=target_feature_ids,
            metadata=metadata
        )


@dataclass
class ModifyAction(Action):
    """
    Action to modify existing features.
    
    Similar to RemoveAction, supports multiple targeting strategies.
    Modifiers are applied to the targeted features.
    
    Attributes:
        kind: Always ActionKind.MODIFY
        feature_type: Optional type filter
        ordinal: Optional ordinal position
        target_feature_ids: Optional explicit list of feature IDs to modify
        modifiers: Modifiers to apply
        metadata: Additional metadata
    """
    modifiers: Modifier
    feature_type: Optional[str] = None
    ordinal: Optional[int] = None
    target_feature_ids: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure kind is set correctly and validate."""
        self.kind = ActionKind.MODIFY
        
        # Validate that at least one targeting method is specified
        if not any([self.feature_type, self.target_feature_ids]):
            raise ValueError("ModifyAction requires either feature_type or target_feature_ids")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "kind": self.kind.value,
            "modifiers": self.modifiers.to_dict(),
        }
        
        if self.feature_type is not None:
            result["type"] = self.feature_type
        if self.ordinal is not None:
            result["ordinal"] = self.ordinal
        if self.target_feature_ids is not None:
            result["target_feature_ids"] = self.target_feature_ids
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModifyAction":
        """Create ModifyAction from dictionary."""
        modifiers_data = data.get("modifiers", {})
        modifiers = Modifier.from_dict(modifiers_data)
        
        feature_type = data.get("type")
        ordinal = data.get("ordinal")
        target_feature_ids = data.get("target_feature_ids")
        metadata = data.get("metadata", {})
        
        return cls(
            kind=ActionKind.MODIFY,
            modifiers=modifiers,
            feature_type=feature_type,
            ordinal=ordinal,
            target_feature_ids=target_feature_ids,
            metadata=metadata
        )


def action_from_dict(data: Dict[str, Any]) -> Action:
    """
    Factory function to create appropriate Action subclass from dictionary.
    
    Args:
        data: Dictionary representation of an action
        
    Returns:
        Appropriate Action subclass instance
        
    Raises:
        ValueError: If action kind is unknown
    """
    kind_str = data.get("kind", "add")
    
    if kind_str == "add":
        return AddAction.from_dict(data)
    elif kind_str == "remove":
        return RemoveAction.from_dict(data)
    elif kind_str == "modify":
        return ModifyAction.from_dict(data)
    else:
        raise ValueError(f"Unknown action kind: {kind_str}")

