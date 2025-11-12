"""Walkability constraint system - Encapsulated constraint tracking.

This module provides a constraint system that tracks reserved walkability zones.
It's designed to be used internally by TerrainBuilder, maintaining encapsulation.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from ..engine.config import RES


class WalkabilityZone:
    """Represents a reserved walkability zone (internal to constraint system)."""
    
    def __init__(self, zone_type: str, params: Dict, priority: str = "high"):
        """
        Initialize walkability zone.
        
        Args:
            zone_type: Type of zone ("flat_zone", "path", "clearing")
            params: Zone parameters (position, size, etc.)
            priority: "high", "medium", or "low"
        """
        self.zone_type = zone_type
        self.params = params
        self.priority = priority
    
    def get_priority_weight(self) -> float:
        """Get constraint weight based on priority."""
        weights = {"high": 1.0, "medium": 0.5, "low": 0.2}
        return weights.get(self.priority, 0.5)
    
    def overlaps_with(self, position: Tuple[int, int], radius: int, 
                     threshold: float = 0.3) -> bool:
        """
        Check if a feature at position with radius overlaps with this zone.
        
        Args:
            position: (x, y) feature position
            radius: Feature radius
            threshold: Overlap threshold (0.0-1.0)
            
        Returns:
            True if feature overlaps with zone above threshold
        """
        x, y = position
        
        # Calculate overlap based on zone type
        if self.zone_type == "flat_zone" or self.zone_type == "clearing":
            cx = self.params.get("x", self.params.get("cx", RES // 2))
            cy = self.params.get("y", self.params.get("cy", RES // 2))
            zone_radius = self.params.get("radius", 50)
            
            # Distance between centers
            dx = x - cx
            dy = y - cy
            dist = np.sqrt(dx*dx + dy*dy)
            
            # Overlap if distance < sum of radii
            overlap_dist = radius + zone_radius
            if dist < overlap_dist * (1.0 - threshold):
                return True
                
        elif self.zone_type == "path":
            start = self.params.get("start", (0, 0))
            end = self.params.get("end", (RES, RES))
            width = self.params.get("width", 30)
            
            # Check if feature is near path
            sx, sy = start
            ex, ey = end
            
            # Vector along path
            dx_line = ex - sx
            dy_line = ey - sy
            length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
            
            if length < 1.0:
                return False
            
            # Unit vector along path
            ux = dx_line / length
            uy = dy_line / length
            
            # Perpendicular vector
            px = -uy
            py = ux
            
            # Distance from feature to path
            dx = x - sx
            dy = y - sy
            along = dx * ux + dy * uy
            perp = dx * px + dy * py
            perp_dist = abs(perp)
            
            # Check if feature overlaps path
            if 0 <= along <= length:
                half_width = width / 2.0
                if perp_dist < (half_width + radius) * (1.0 - threshold):
                    return True
        
        return False


class WalkabilityConstraint:
    """
    Encapsulated constraint system for walkability zones.
    
    This class tracks reserved zones and validates placements.
    It's designed to be used internally by TerrainBuilder.
    """
    
    def __init__(self):
        """Initialize constraint system."""
        self._zones: List[WalkabilityZone] = []
    
    def add_zone(self, zone_type: str, params: Dict, priority: str = "high"):
        """
        Add a walkability zone.
        
        Args:
            zone_type: Type of zone ("flat_zone", "path", "clearing")
            params: Zone parameters
            priority: Priority level ("high", "medium", "low")
        """
        zone = WalkabilityZone(zone_type, params, priority)
        self._zones.append(zone)
    
    def can_place_feature(self, feature_type: str, position: Tuple[int, int],
                         radius: int, strict: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Check if a feature can be placed without violating constraints.
        
        Args:
            feature_type: Type of feature (e.g., "mountain", "hill")
            position: (x, y) position
            radius: Feature radius
            strict: If True, high priority zones block all overlaps
                   
        Returns:
            (can_place, reason) tuple
        """
        if not self._zones:
            return True, None
        
        for zone in self._zones:
            if zone.overlaps_with(position, radius, threshold=0.3):
                # High priority zones block all features
                if zone.priority == "high" and strict:
                    return False, f"Overlaps with high-priority {zone.zone_type}"
                
                # Medium priority: block large features
                if zone.priority == "medium":
                    if feature_type in ["mountain", "volcano", "pinnacle"]:
                        return False, f"Large feature overlaps with medium-priority {zone.zone_type}"
                
                # Low priority: block very large features
                if zone.priority == "low":
                    if feature_type in ["mountain", "volcano"]:
                        return False, f"Large feature overlaps with {zone.zone_type}"
        
        return True, None
    
    def find_placement_away_from_zones(self, feature_type: str,
                                      preferred_pos: Tuple[int, int],
                                      radius: int,
                                      search_radius: int = 100,
                                      max_attempts: int = 50) -> Tuple[int, int]:
        """
        Find a valid placement position away from walkability zones.
        
        Args:
            feature_type: Type of feature
            preferred_pos: Preferred (x, y) position
            radius: Feature radius
            search_radius: Maximum distance to search
            max_attempts: Maximum attempts
            
        Returns:
            (x, y) position that doesn't violate constraints
        """
        px, py = preferred_pos
        
        # Try preferred position first
        can_place, _ = self.can_place_feature(feature_type, preferred_pos, radius)
        if can_place:
            return preferred_pos
        
        # Search nearby positions
        rng = np.random.RandomState(hash(f"{px}_{py}_{radius}") % (2**31))
        
        for attempt in range(max_attempts):
            angle = rng.uniform(0, 2 * np.pi)
            dist = rng.uniform(radius + 10, search_radius)
            
            x = int(px + dist * np.cos(angle))
            y = int(py + dist * np.sin(angle))
            
            # Clamp to valid range
            x = max(radius, min(RES - radius, x))
            y = max(radius, min(RES - radius, y))
            
            candidate_pos = (x, y)
            can_place, _ = self.can_place_feature(feature_type, candidate_pos, radius)
            
            if can_place:
                return candidate_pos
        
        # Fallback: return preferred position (should rarely happen)
        return preferred_pos
    
    def get_min_distance_to_zones(self, position: Tuple[int, int]) -> float:
        """
        Get minimum distance from position to any walkability zone.
        
        Args:
            position: (x, y) position
            
        Returns:
            Minimum distance to nearest zone
        """
        if not self._zones:
            return float('inf')
        
        min_dist = float('inf')
        x, y = position
        
        for zone in self._zones:
            if zone.zone_type == "flat_zone" or zone.zone_type == "clearing":
                cx = zone.params.get("x", zone.params.get("cx", RES // 2))
                cy = zone.params.get("y", zone.params.get("cy", RES // 2))
                zone_radius = zone.params.get("radius", 50)
                
                dx = x - cx
                dy = y - cy
                dist = np.sqrt(dx*dx + dy*dy) - zone_radius
                min_dist = min(min_dist, dist)
                
            elif zone.zone_type == "path":
                # Simplified: distance to path center line
                start = zone.params.get("start", (0, 0))
                end = zone.params.get("end", (RES, RES))
                
                sx, sy = start
                ex, ey = end
                dx_line = ex - sx
                dy_line = ey - sy
                length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
                
                if length > 0:
                    ux = dx_line / length
                    uy = dy_line / length
                    px = -uy
                    py = ux
                    
                    dx = x - sx
                    dy = y - sy
                    along = dx * ux + dy * uy
                    perp = dx * px + dy * py
                    
                    if 0 <= along <= length:
                        dist = abs(perp)
                    else:
                        # Distance to nearest endpoint
                        dist_start = np.sqrt((x - sx)**2 + (y - sy)**2)
                        dist_end = np.sqrt((x - ex)**2 + (y - ey)**2)
                        dist = min(dist_start, dist_end)
                    
                    min_dist = min(min_dist, dist)
        
        return min_dist
    
    def has_zones(self) -> bool:
        """Check if any zones are registered."""
        return len(self._zones) > 0
