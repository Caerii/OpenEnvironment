"""
Geometric primitives for terrain generation.

These are immutable, validated value objects that represent positions and
regions on the 512x512 terrain grid.
"""

import math
from dataclasses import dataclass
from typing import Tuple


# Terrain dimensions (global constant)
TERRAIN_SIZE = 512


@dataclass(frozen=True)
class Position:
    """
    2D position on terrain grid.
    
    Immutable value object representing a point on the 512x512 terrain.
    Coordinates are validated on construction.
    
    Examples:
        >>> pos = Position(100, 200)
        >>> pos.x
        100
        >>> pos.distance_to(Position(150, 250))
        70.71...
    """
    x: int
    y: int
    
    def __post_init__(self):
        """Validate coordinates are within terrain bounds."""
        if not (0 <= self.x <= TERRAIN_SIZE):
            raise ValueError(f"x coordinate out of bounds: {self.x} (must be 0-{TERRAIN_SIZE})")
        if not (0 <= self.y <= TERRAIN_SIZE):
            raise ValueError(f"y coordinate out of bounds: {self.y} (must be 0-{TERRAIN_SIZE})")
    
    def distance_to(self, other: 'Position') -> float:
        """
        Calculate Euclidean distance to another position.
        
        Args:
            other: Target position
            
        Returns:
            Distance in terrain units
            
        Examples:
            >>> Position(0, 0).distance_to(Position(3, 4))
            5.0
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def offset(self, dx: int, dy: int) -> 'Position':
        """
        Create new position offset by given deltas.
        
        Args:
            dx: X offset
            dy: Y offset
            
        Returns:
            New Position (validated)
            
        Raises:
            ValueError: If resulting position is out of bounds
            
        Examples:
            >>> Position(100, 200).offset(50, 30)
            Position(x=150, y=230)
        """
        return Position(self.x + dx, self.y + dy)
    
    def midpoint_to(self, other: 'Position') -> 'Position':
        """
        Calculate midpoint between this and another position.
        
        Args:
            other: Target position
            
        Returns:
            Midpoint position
            
        Examples:
            >>> Position(0, 0).midpoint_to(Position(100, 200))
            Position(x=50, y=100)
        """
        return Position(
            (self.x + other.x) // 2,
            (self.y + other.y) // 2
        )
    
    def to_tuple(self) -> Tuple[int, int]:
        """Convert to tuple (for compatibility with numpy indexing)."""
        return (self.x, self.y)


@dataclass(frozen=True)
class Region:
    """
    Rectangular region on terrain.
    
    Immutable value object representing an axis-aligned bounding box.
    Coordinates are validated to ensure x_min < x_max and y_min < y_max.
    
    Examples:
        >>> region = Region(100, 200, 150, 250)
        >>> region.area()
        10000
        >>> region.contains(Position(150, 200))
        True
    """
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    
    def __post_init__(self):
        """Validate region bounds."""
        if self.x_min >= self.x_max:
            raise ValueError(f"x_min ({self.x_min}) must be less than x_max ({self.x_max})")
        if self.y_min >= self.y_max:
            raise ValueError(f"y_min ({self.y_min}) must be less than y_max ({self.y_max})")
        
        # Validate bounds are within terrain
        if not (0 <= self.x_min <= TERRAIN_SIZE):
            raise ValueError(f"x_min out of bounds: {self.x_min}")
        if not (0 <= self.x_max <= TERRAIN_SIZE):
            raise ValueError(f"x_max out of bounds: {self.x_max}")
        if not (0 <= self.y_min <= TERRAIN_SIZE):
            raise ValueError(f"y_min out of bounds: {self.y_min}")
        if not (0 <= self.y_max <= TERRAIN_SIZE):
            raise ValueError(f"y_max out of bounds: {self.y_max}")
    
    def contains(self, pos: Position) -> bool:
        """
        Check if position is within this region (inclusive).
        
        Args:
            pos: Position to check
            
        Returns:
            True if position is inside region
            
        Examples:
            >>> region = Region(0, 100, 0, 100)
            >>> region.contains(Position(50, 50))
            True
            >>> region.contains(Position(150, 50))
            False
        """
        return (self.x_min <= pos.x <= self.x_max and
                self.y_min <= pos.y <= self.y_max)
    
    def overlaps_with(self, other: 'Region') -> bool:
        """
        Check if this region overlaps with another.
        
        Regions must have actual area overlap (not just touching edges).
        
        Args:
            other: Region to check
            
        Returns:
            True if regions overlap (share interior area)
            
        Examples:
            >>> r1 = Region(0, 100, 0, 100)
            >>> r2 = Region(50, 150, 50, 150)
            >>> r1.overlaps_with(r2)
            True
        """
        return not (self.x_max <= other.x_min or
                    other.x_max <= self.x_min or
                    self.y_max <= other.y_min or
                    other.y_max <= self.y_min)
    
    def area(self) -> int:
        """
        Calculate area of region.
        
        Returns:
            Area in square terrain units
            
        Examples:
            >>> Region(0, 100, 0, 50).area()
            5000
        """
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    def center(self) -> Position:
        """
        Calculate center point of region.
        
        Returns:
            Center position
            
        Examples:
            >>> Region(0, 100, 0, 200).center()
            Position(x=50, y=100)
        """
        return Position(
            (self.x_min + self.x_max) // 2,
            (self.y_min + self.y_max) // 2
        )
    
    def width(self) -> int:
        """Get region width."""
        return self.x_max - self.x_min
    
    def height(self) -> int:
        """Get region height."""
        return self.y_max - self.y_min
    
    def expand(self, margin: int) -> 'Region':
        """
        Expand region by margin on all sides.
        
        Args:
            margin: Amount to expand (can be negative to shrink)
            
        Returns:
            Expanded region (validated)
            
        Examples:
            >>> Region(100, 200, 100, 200).expand(10)
            Region(x_min=90, x_max=210, y_min=90, y_max=210)
        """
        return Region(
            max(0, self.x_min - margin),
            min(TERRAIN_SIZE, self.x_max + margin),
            max(0, self.y_min - margin),
            min(TERRAIN_SIZE, self.y_max + margin)
        )


@dataclass(frozen=True)
class Circle:
    """
    Circular region on terrain.
    
    Immutable value object representing a circle defined by center and radius.
    Used for feature bounds and spatial queries.
    
    Examples:
        >>> circle = Circle(Position(256, 256), 50)
        >>> circle.contains(Position(256, 300))
        True
        >>> circle.area()
        7853.98...
    """
    center: Position
    radius: int
    
    def __post_init__(self):
        """Validate radius is positive."""
        if self.radius <= 0:
            raise ValueError(f"radius must be positive: {self.radius}")
    
    def contains(self, pos: Position) -> bool:
        """
        Check if position is within this circle.
        
        Args:
            pos: Position to check
            
        Returns:
            True if position is inside circle
            
        Examples:
            >>> circle = Circle(Position(0, 0), 10)
            >>> circle.contains(Position(5, 5))
            True
            >>> circle.contains(Position(20, 0))
            False
        """
        return self.center.distance_to(pos) <= self.radius
    
    def overlaps_with(self, other: 'Circle') -> bool:
        """
        Check if this circle overlaps with another.
        
        Args:
            other: Circle to check
            
        Returns:
            True if circles overlap
            
        Examples:
            >>> c1 = Circle(Position(0, 0), 10)
            >>> c2 = Circle(Position(15, 0), 10)
            >>> c1.overlaps_with(c2)
            True
        """
        distance = self.center.distance_to(other.center)
        return distance <= (self.radius + other.radius)
    
    def area(self) -> float:
        """
        Calculate area of circle.
        
        Returns:
            Area in square terrain units
            
        Examples:
            >>> Circle(Position(0, 0), 10).area()
            314.159...
        """
        return math.pi * self.radius ** 2
    
    def bounding_box(self) -> Region:
        """
        Get axis-aligned bounding box for this circle.
        
        Returns:
            Smallest Region containing the entire circle
            
        Examples:
            >>> Circle(Position(100, 100), 50).bounding_box()
            Region(x_min=50, x_max=150, y_min=50, y_max=150)
        """
        return Region(
            max(0, self.center.x - self.radius),
            min(TERRAIN_SIZE, self.center.x + self.radius),
            max(0, self.center.y - self.radius),
            min(TERRAIN_SIZE, self.center.y + self.radius)
        )

