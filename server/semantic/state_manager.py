"""State management - Feature tracking and terrain state."""
from typing import Dict, List, Optional
import json

class FeatureState:
    """Manages terrain feature state with IDs and tracking."""
    
    def __init__(self, state: Optional[Dict] = None):
        if state is None:
            state = {"features": [], "seed": 0, "next_id": 1}
        self.state = state
        self._ensure_next_id()
    
    def _ensure_next_id(self):
        """Ensure next_id exists in state."""
        if "next_id" not in self.state:
            # Find max existing ID
            max_id = 0
            for feat in self.state.get("features", []):
                if "id" in feat:
                    max_id = max(max_id, feat["id"])
            self.state["next_id"] = max_id + 1
    
    def add_feature(self, feature: Dict) -> int:
        """
        Add a feature with auto-assigned ID.
        
        Args:
            feature: Feature dictionary (type, position, params, etc.)
            
        Returns:
            Assigned feature ID
        """
        feature_id = self.state["next_id"]
        feature["id"] = feature_id
        self.state["features"].append(feature)
        self.state["next_id"] += 1
        return feature_id
    
    def remove_feature(self, feature_id: Optional[int] = None, 
                      feature_type: Optional[str] = None,
                      ordinal: Optional[int] = None) -> bool:
        """
        Remove a feature by ID, type, or ordinal position.
        
        Args:
            feature_id: Remove by specific ID
            feature_type: Remove by type (removes most recent of that type)
            ordinal: Remove by ordinal (1 = first, 2 = second, etc.)
            
        Returns:
            True if feature was removed, False otherwise
        """
        features = self.state["features"]
        
        if feature_id:
            # Remove by ID
            for i, feat in enumerate(features):
                if feat.get("id") == feature_id:
                    del features[i]
                    return True
        
        elif ordinal and feature_type:
            # Remove Nth feature of type
            matching = [f for f in features if f.get("type") == feature_type]
            if len(matching) >= ordinal:
                target = matching[ordinal - 1]
                target_id = target.get("id")
                features[:] = [f for f in features if f.get("id") != target_id]
                return True
        
        elif feature_type:
            # Remove most recent of type
            for i in range(len(features) - 1, -1, -1):
                if features[i].get("type") == feature_type:
                    del features[i]
                    return True
        
        return False
    
    def find_feature(self, feature_id: Optional[int] = None,
                    feature_type: Optional[str] = None,
                    ordinal: Optional[int] = None) -> Optional[Dict]:
        """
        Find a feature by ID, type, or ordinal.
        
        Returns:
            Feature dictionary or None
        """
        features = self.state["features"]
        
        if feature_id:
            for feat in features:
                if feat.get("id") == feature_id:
                    return feat
        
        elif ordinal and feature_type:
            matching = [f for f in features if f.get("type") == feature_type]
            if len(matching) >= ordinal:
                return matching[ordinal - 1]
        
        elif feature_type:
            # Find most recent of type
            for i in range(len(features) - 1, -1, -1):
                if features[i].get("type") == feature_type:
                    return features[i]
        
        return None
    
    def list_features(self, feature_type: Optional[str] = None) -> List[Dict]:
        """
        List all features, optionally filtered by type.
        
        Args:
            feature_type: Optional type filter
            
        Returns:
            List of feature dictionaries
        """
        features = self.state["features"]
        if feature_type:
            return [f for f in features if f.get("type") == feature_type]
        return features.copy()
    
    def to_dict(self) -> Dict:
        """Export state as dictionary."""
        return self.state.copy()
    
    def from_dict(self, state: Dict):
        """Import state from dictionary."""
        self.state = state
        self._ensure_next_id()

