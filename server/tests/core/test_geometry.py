"""
Tests for geometric primitives (Position, Region, Circle).

Validates:
- Bounds checking
- Immutability
- Distance calculations
- Overlap detection
- Area calculations
"""

import pytest
import math
from server.core.geometry import Position, Region, Circle, TERRAIN_SIZE


class TestPosition:
    """Tests for Position value object."""
    
    def test_valid_position(self):
        """Valid positions should be created successfully."""
        pos = Position(100, 200)
        assert pos.x == 100
        assert pos.y == 200
    
    def test_position_at_origin(self):
        """Position at origin (0,0) should be valid."""
        pos = Position(0, 0)
        assert pos.x == 0
        assert pos.y == 0
    
    def test_position_at_max_bounds(self):
        """Position at maximum bounds should be valid."""
        pos = Position(TERRAIN_SIZE, TERRAIN_SIZE)
        assert pos.x == TERRAIN_SIZE
        assert pos.y == TERRAIN_SIZE
    
    def test_position_x_out_of_bounds_negative(self):
        """Negative x coordinate should raise ValueError."""
        with pytest.raises(ValueError, match="x coordinate out of bounds"):
            Position(-1, 100)
    
    def test_position_x_out_of_bounds_positive(self):
        """X coordinate exceeding TERRAIN_SIZE should raise ValueError."""
        with pytest.raises(ValueError, match="x coordinate out of bounds"):
            Position(TERRAIN_SIZE + 1, 100)
    
    def test_position_y_out_of_bounds_negative(self):
        """Negative y coordinate should raise ValueError."""
        with pytest.raises(ValueError, match="y coordinate out of bounds"):
            Position(100, -1)
    
    def test_position_y_out_of_bounds_positive(self):
        """Y coordinate exceeding TERRAIN_SIZE should raise ValueError."""
        with pytest.raises(ValueError, match="y coordinate out of bounds"):
            Position(100, TERRAIN_SIZE + 1)
    
    def test_position_immutability(self):
        """Positions should be immutable (frozen dataclass)."""
        pos = Position(100, 200)
        with pytest.raises(Exception):  # FrozenInstanceError
            pos.x = 150
    
    def test_distance_to_same_position(self):
        """Distance from position to itself should be 0."""
        pos = Position(100, 100)
        assert pos.distance_to(pos) == 0.0
    
    def test_distance_to_pythagorean_triple(self):
        """Distance calculation should follow Pythagorean theorem."""
        pos1 = Position(0, 0)
        pos2 = Position(3, 4)
        assert pos1.distance_to(pos2) == 5.0
    
    def test_distance_to_symmetric(self):
        """Distance should be symmetric (A→B = B→A)."""
        pos1 = Position(100, 100)
        pos2 = Position(200, 150)
        assert pos1.distance_to(pos2) == pos2.distance_to(pos1)
    
    def test_offset_positive(self):
        """Offset with positive deltas should work."""
        pos = Position(100, 200)
        new_pos = pos.offset(50, 30)
        assert new_pos.x == 150
        assert new_pos.y == 230
    
    def test_offset_negative(self):
        """Offset with negative deltas should work."""
        pos = Position(100, 200)
        new_pos = pos.offset(-50, -30)
        assert new_pos.x == 50
        assert new_pos.y == 170
    
    def test_offset_out_of_bounds(self):
        """Offset resulting in out-of-bounds position should raise ValueError."""
        pos = Position(10, 10)
        with pytest.raises(ValueError):
            pos.offset(-20, 0)
    
    def test_offset_immutability(self):
        """Offset should return new position, not modify original."""
        pos = Position(100, 100)
        new_pos = pos.offset(50, 50)
        assert pos.x == 100  # Original unchanged
        assert new_pos.x == 150
    
    def test_midpoint_to_center(self):
        """Midpoint calculation should be accurate."""
        pos1 = Position(0, 0)
        pos2 = Position(100, 200)
        mid = pos1.midpoint_to(pos2)
        assert mid.x == 50
        assert mid.y == 100
    
    def test_midpoint_to_symmetric(self):
        """Midpoint should be symmetric (A→B = B→A)."""
        pos1 = Position(100, 100)
        pos2 = Position(200, 300)
        assert pos1.midpoint_to(pos2) == pos2.midpoint_to(pos1)
    
    def test_to_tuple(self):
        """to_tuple() should return (x, y)."""
        pos = Position(123, 456)
        assert pos.to_tuple() == (123, 456)
    
    def test_equality(self):
        """Positions with same coordinates should be equal."""
        pos1 = Position(100, 200)
        pos2 = Position(100, 200)
        assert pos1 == pos2
    
    def test_inequality(self):
        """Positions with different coordinates should not be equal."""
        pos1 = Position(100, 200)
        pos2 = Position(100, 201)
        assert pos1 != pos2


class TestRegion:
    """Tests for Region value object."""
    
    def test_valid_region(self):
        """Valid region should be created successfully."""
        region = Region(100, 200, 150, 250)
        assert region.x_min == 100
        assert region.x_max == 200
        assert region.y_min == 150
        assert region.y_max == 250
    
    def test_region_full_terrain(self):
        """Region covering entire terrain should be valid."""
        region = Region(0, TERRAIN_SIZE, 0, TERRAIN_SIZE)
        assert region.area() == TERRAIN_SIZE * TERRAIN_SIZE
    
    def test_region_x_min_equals_x_max(self):
        """Region with x_min == x_max should be invalid."""
        with pytest.raises(ValueError, match="x_min.*must be less than.*x_max"):
            Region(100, 100, 0, 100)
    
    def test_region_x_min_greater_than_x_max(self):
        """Region with x_min > x_max should be invalid."""
        with pytest.raises(ValueError, match="x_min.*must be less than.*x_max"):
            Region(200, 100, 0, 100)
    
    def test_region_y_min_equals_y_max(self):
        """Region with y_min == y_max should be invalid."""
        with pytest.raises(ValueError, match="y_min.*must be less than.*y_max"):
            Region(0, 100, 100, 100)
    
    def test_region_out_of_bounds(self):
        """Region with coordinates outside terrain should be invalid."""
        with pytest.raises(ValueError, match="out of bounds"):
            Region(0, TERRAIN_SIZE + 100, 0, 100)
    
    def test_region_immutability(self):
        """Regions should be immutable."""
        region = Region(0, 100, 0, 100)
        with pytest.raises(Exception):  # FrozenInstanceError
            region.x_min = 50
    
    def test_contains_inside(self):
        """Position inside region should return True."""
        region = Region(0, 100, 0, 100)
        assert region.contains(Position(50, 50))
    
    def test_contains_on_boundary(self):
        """Position on region boundary should return True (inclusive)."""
        region = Region(0, 100, 0, 100)
        assert region.contains(Position(0, 0))
        assert region.contains(Position(100, 100))
    
    def test_contains_outside(self):
        """Position outside region should return False."""
        region = Region(0, 100, 0, 100)
        assert not region.contains(Position(150, 50))
    
    def test_overlaps_with_fully_overlapping(self):
        """Fully overlapping regions should return True."""
        r1 = Region(0, 100, 0, 100)
        r2 = Region(50, 150, 50, 150)
        assert r1.overlaps_with(r2)
        assert r2.overlaps_with(r1)  # Symmetric
    
    def test_overlaps_with_edge_touching(self):
        """Regions touching at edge should not overlap."""
        r1 = Region(0, 100, 0, 100)
        r2 = Region(100, 200, 0, 100)
        assert not r1.overlaps_with(r2)
    
    def test_overlaps_with_separate(self):
        """Separate regions should not overlap."""
        r1 = Region(0, 100, 0, 100)
        r2 = Region(200, 300, 200, 300)
        assert not r1.overlaps_with(r2)
    
    def test_area_square(self):
        """Area calculation for square region."""
        region = Region(0, 100, 0, 100)
        assert region.area() == 10000
    
    def test_area_rectangle(self):
        """Area calculation for rectangular region."""
        region = Region(0, 50, 0, 100)
        assert region.area() == 5000
    
    def test_center_calculation(self):
        """Center should be midpoint of region."""
        region = Region(0, 100, 0, 200)
        center = region.center()
        assert center.x == 50
        assert center.y == 100
    
    def test_width(self):
        """Width calculation."""
        region = Region(50, 150, 0, 100)
        assert region.width() == 100
    
    def test_height(self):
        """Height calculation."""
        region = Region(0, 100, 50, 250)
        assert region.height() == 200
    
    def test_expand_positive(self):
        """Expand region by positive margin."""
        region = Region(100, 200, 100, 200)
        expanded = region.expand(10)
        assert expanded.x_min == 90
        assert expanded.x_max == 210
        assert expanded.y_min == 90
        assert expanded.y_max == 210
    
    def test_expand_negative_shrink(self):
        """Expand with negative margin should shrink region."""
        region = Region(100, 200, 100, 200)
        shrunk = region.expand(-10)
        assert shrunk.x_min == 110
        assert shrunk.x_max == 190
    
    def test_expand_clamped_to_bounds(self):
        """Expand should clamp to terrain bounds."""
        region = Region(0, 100, 0, 100)
        expanded = region.expand(1000)
        assert expanded.x_min == 0
        assert expanded.x_max == TERRAIN_SIZE
        assert expanded.y_min == 0
        assert expanded.y_max == TERRAIN_SIZE


class TestCircle:
    """Tests for Circle value object."""
    
    def test_valid_circle(self):
        """Valid circle should be created successfully."""
        circle = Circle(Position(256, 256), 50)
        assert circle.center == Position(256, 256)
        assert circle.radius == 50
    
    def test_circle_zero_radius(self):
        """Circle with radius 0 should be invalid."""
        with pytest.raises(ValueError, match="radius must be positive"):
            Circle(Position(100, 100), 0)
    
    def test_circle_negative_radius(self):
        """Circle with negative radius should be invalid."""
        with pytest.raises(ValueError, match="radius must be positive"):
            Circle(Position(100, 100), -10)
    
    def test_circle_immutability(self):
        """Circles should be immutable."""
        circle = Circle(Position(100, 100), 50)
        with pytest.raises(Exception):  # FrozenInstanceError
            circle.radius = 100
    
    def test_contains_at_center(self):
        """Position at center should be inside circle."""
        circle = Circle(Position(100, 100), 50)
        assert circle.contains(Position(100, 100))
    
    def test_contains_inside(self):
        """Position inside circle should return True."""
        circle = Circle(Position(100, 100), 50)
        assert circle.contains(Position(120, 120))
    
    def test_contains_on_boundary(self):
        """Position on circle boundary should return True."""
        circle = Circle(Position(100, 100), 50)
        assert circle.contains(Position(150, 100))  # Distance = 50
    
    def test_contains_outside(self):
        """Position outside circle should return False."""
        circle = Circle(Position(100, 100), 50)
        assert not circle.contains(Position(200, 200))
    
    def test_overlaps_with_fully_overlapping(self):
        """Overlapping circles should return True."""
        c1 = Circle(Position(100, 100), 50)
        c2 = Circle(Position(120, 100), 50)
        assert c1.overlaps_with(c2)
        assert c2.overlaps_with(c1)  # Symmetric
    
    def test_overlaps_with_touching(self):
        """Circles touching at exactly one point should overlap."""
        c1 = Circle(Position(100, 100), 50)
        c2 = Circle(Position(200, 100), 50)  # Distance = 100 = r1 + r2
        assert c1.overlaps_with(c2)
    
    def test_overlaps_with_separate(self):
        """Separate circles should not overlap."""
        c1 = Circle(Position(100, 100), 50)
        c2 = Circle(Position(300, 300), 50)
        assert not c1.overlaps_with(c2)
    
    def test_area_calculation(self):
        """Area should be π * r²."""
        circle = Circle(Position(100, 100), 10)
        expected_area = math.pi * 100
        assert abs(circle.area() - expected_area) < 0.01
    
    def test_bounding_box_centered(self):
        """Bounding box should be correct for centered circle."""
        circle = Circle(Position(100, 100), 50)
        bbox = circle.bounding_box()
        assert bbox.x_min == 50
        assert bbox.x_max == 150
        assert bbox.y_min == 50
        assert bbox.y_max == 150
    
    def test_bounding_box_clamped_to_terrain(self):
        """Bounding box should be clamped to terrain bounds."""
        circle = Circle(Position(10, 10), 50)
        bbox = circle.bounding_box()
        assert bbox.x_min == 0  # Clamped from -40
        assert bbox.y_min == 0  # Clamped from -40
    
    def test_bounding_box_area_exceeds_circle_area(self):
        """Bounding box area should always be >= circle area."""
        circle = Circle(Position(256, 256), 50)
        bbox = circle.bounding_box()
        assert bbox.area() >= circle.area()


class TestGeometryIntegration:
    """Integration tests for geometric primitives working together."""
    
    def test_region_contains_circle_center(self):
        """Region should contain circle's center."""
        region = Region(0, 200, 0, 200)
        circle = Circle(Position(100, 100), 30)
        assert region.contains(circle.center)
    
    def test_circle_bounding_box_is_region(self):
        """Circle's bounding box should be a valid Region."""
        circle = Circle(Position(256, 256), 100)
        bbox = circle.bounding_box()
        assert isinstance(bbox, Region)
        assert bbox.contains(circle.center)
    
    def test_position_offset_chain(self):
        """Multiple offsets should be composable."""
        pos = Position(100, 100)
        pos2 = pos.offset(50, 50)
        pos3 = pos2.offset(50, 50)
        assert pos3 == Position(200, 200)
    
    def test_region_center_is_position(self):
        """Region center should return valid Position."""
        region = Region(0, 100, 0, 200)
        center = region.center()
        assert isinstance(center, Position)
        assert region.contains(center)

