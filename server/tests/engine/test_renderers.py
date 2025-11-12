"""
Tests for feature renderers.

Validates:
- Renderer registration
- Stamp generation for each feature type
- BlendingMode correctness
- Parameter handling
"""

import pytest
import numpy as np

from server.engine.renderers import (
    RendererRegistry,
    MountainRenderer,
    ValleyRenderer,
    DunesRenderer,
    CliffRenderer,
    PlateauRenderer,
    CanyonRenderer,
)
from server.domain.models import Feature, Position, FeatureParameters
from server.engine.stamping import BlendingMode


class TestRendererRegistry:
    """Tests for RendererRegistry."""
    
    def test_core_renderers_registered(self):
        """All 6 core renderers should be auto-registered."""
        supported = RendererRegistry.get_supported_types()
        
        assert "mountain" in supported
        assert "valley" in supported
        assert "dunes" in supported
        assert "cliff" in supported
        assert "plateau" in supported
        assert "canyon" in supported
        assert len(supported) == 6
    
    def test_has_renderer(self):
        """has_renderer should correctly identify supported types."""
        assert RendererRegistry.has_renderer("mountain") is True
        assert RendererRegistry.has_renderer("valley") is True
        assert RendererRegistry.has_renderer("unknown") is False
    
    def test_render_unsupported_type(self):
        """Rendering unsupported type should raise ValueError."""
        feature = Feature(
            id=1,
            type="unsupported",
            position=Position(x=256, y=256),
            parameters=FeatureParameters()
        )
        
        with pytest.raises(ValueError, match="No renderer registered"):
            RendererRegistry.render(feature, seed=42)


class TestMountainRenderer:
    """Tests for MountainRenderer."""
    
    def test_mountain_render_returns_stamp_and_mode(self):
        """Rendering should return stamp + BlendingMode."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56)
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.MAX
    
    def test_mountain_stamp_has_elevation(self):
        """Mountain stamp should have non-zero elevation at center."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56)
        )
        
        stamp, _ = RendererRegistry.render(feature, seed=42)
        
        # Check center has elevation
        center_value = stamp[256, 256]
        assert center_value > 0.1
    
    def test_mountain_with_custom_params(self):
        """Mountain should use custom steepness parameter."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=200, y=300),
            parameters=FeatureParameters(
                height=0.8,
                radius=70,
                params={"steepness": 1.5, "use_noise": False}
            )
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.MAX


class TestValleyRenderer:
    """Tests for ValleyRenderer."""
    
    def test_valley_render_returns_stamp_and_mode(self):
        """Valley rendering should return stamp + SUBTRACT mode."""
        feature = Feature(
            id=2,
            type="valley",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(depth=0.5, radius=80)
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.SUBTRACT
    
    def test_valley_stamp_has_depression(self):
        """Valley stamp should have depression at center."""
        feature = Feature(
            id=2,
            type="valley",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(depth=0.6, radius=80)
        )
        
        stamp, _ = RendererRegistry.render(feature, seed=42)
        
        # Valley should have depression (check for negative values or reduced elevation)
        center_value = stamp[256, 256]
        # Valley generates negative stamps for subtraction, so check it's below baseline
        assert center_value < 1.0  # Should be depressed relative to flat terrain


class TestDunesRenderer:
    """Tests for DunesRenderer."""
    
    def test_dunes_render_returns_stamp_and_mode(self):
        """Dunes rendering should return stamp + MAX mode."""
        feature = Feature(
            id=3,
            type="dunes",
            position=Position(x=256, y=256),  # Not used for dunes (uses box)
            parameters=FeatureParameters(
                params={
                    "x0": 50,
                    "y0": 50,
                    "x1": 450,
                    "y1": 450,
                    "count": 5,
                    "spacing": 40
                }
            )
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.MAX


class TestCliffRenderer:
    """Tests for CliffRenderer."""
    
    def test_cliff_render_returns_stamp_and_mode(self):
        """Cliff rendering should return stamp + MAX mode."""
        feature = Feature(
            id=4,
            type="cliff",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(
                height=0.7,
                params={"length": 150, "width": 20, "angle": 45.0}
            )
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.MAX


class TestPlateauRenderer:
    """Tests for PlateauRenderer."""
    
    def test_plateau_render_returns_stamp_and_mode(self):
        """Plateau rendering should return stamp + MAX mode."""
        feature = Feature(
            id=5,
            type="plateau",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(
                height=0.6,
                width=80,
                params={"length": 80}
            )
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.MAX


class TestCanyonRenderer:
    """Tests for CanyonRenderer."""
    
    def test_canyon_render_returns_stamp_and_mode(self):
        """Canyon rendering should return stamp + SUBTRACT mode."""
        feature = Feature(
            id=6,
            type="canyon",
            position=Position(x=100, y=100),
            parameters=FeatureParameters(
                depth=0.6,
                width=40,
                params={"end_x": 400, "end_y": 400}
            )
        )
        
        stamp, mode = RendererRegistry.render(feature, seed=42)
        
        assert isinstance(stamp, np.ndarray)
        assert stamp.shape == (512, 512)
        assert mode == BlendingMode.SUBTRACT


class TestRendererIntegration:
    """Integration tests for renderers."""
    
    def test_render_all_core_types(self):
        """Render all 6 core feature types successfully."""
        features = [
            Feature(1, "mountain", Position(x=256, y=256), FeatureParameters(height=0.75, radius=56)),
            Feature(2, "valley", Position(x=150, y=150), FeatureParameters(depth=0.5, radius=80)),
            Feature(3, "dunes", Position(x=0, y=0), FeatureParameters(params={"x0": 50, "y0": 50, "x1": 450, "y1": 450})),
            Feature(4, "cliff", Position(x=300, y=300), FeatureParameters(height=0.7, params={"length": 150})),
            Feature(5, "plateau", Position(x=400, y=400), FeatureParameters(height=0.6, width=80)),
            Feature(6, "canyon", Position(x=100, y=100), FeatureParameters(depth=0.6, width=40, params={"end_x": 400, "end_y": 400})),
        ]
        
        for feature in features:
            stamp, mode = RendererRegistry.render(feature, seed=42)
            
            assert stamp.shape == (512, 512)
            # Mode should be a string constant from BlendingMode
            assert isinstance(mode, str), f"Expected string mode, got {type(mode)} = {mode}"
            assert mode in ["max", "min", "add", "subtract", "weighted", "replace"]
    
    def test_deterministic_rendering(self):
        """Same seed should produce same stamp."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(height=0.75, radius=56)
        )
        
        stamp1, _ = RendererRegistry.render(feature, seed=42)
        stamp2, _ = RendererRegistry.render(feature, seed=42)
        
        np.testing.assert_array_equal(stamp1, stamp2)
    
    def test_different_seeds_produce_different_stamps(self):
        """Different seeds should produce different stamps (with noise)."""
        feature = Feature(
            id=1,
            type="mountain",
            position=Position(x=256, y=256),
            parameters=FeatureParameters(
                height=0.75,
                radius=56,
                params={"use_noise": True}
            )
        )
        
        stamp1, _ = RendererRegistry.render(feature, seed=42)
        stamp2, _ = RendererRegistry.render(feature, seed=99)
        
        # Should be different (if noise is enabled)
        assert not np.array_equal(stamp1, stamp2)

