"""Configuration system - Centralized terrain generation parameters."""
from dataclasses import dataclass
from typing import Dict, Any

RES = 512  # Resolution constant


@dataclass
class MountainConfig:
    """Configuration for mountain features."""
    default_height: float = 0.75
    default_radius: int = 56
    height_variation: float = 0.15  # ±15% variation
    radius_variation: float = 0.20  # ±20% variation
    max_height: float = 1.0
    max_radius: int = 128


@dataclass
class HillConfig:
    """Configuration for hill features."""
    default_height: float = 0.45
    default_radius: int = 42
    height_variation: float = 0.15
    radius_variation: float = 0.20
    max_height: float = 1.0
    max_radius: int = 128


@dataclass
class ValleyConfig:
    """Configuration for valley features."""
    default_depth: float = 0.55
    default_radius: int = 64
    depth_variation: float = 0.15
    radius_variation: float = 0.20
    max_depth: float = 1.0
    max_radius: int = 128


@dataclass
class DuneConfig:
    """Configuration for dune features."""
    default_amp: float = 0.08
    default_freq: float = 18.0
    default_angle: float = 20.0
    default_radius: int = 96


@dataclass
class TerrainConfig:
    """Main terrain configuration."""
    resolution: int = RES
    smoothing_sigma: float = 0.8
    mountains: MountainConfig = None
    hills: HillConfig = None
    valleys: ValleyConfig = None
    dunes: DuneConfig = None
    
    def __post_init__(self):
        if self.mountains is None:
            self.mountains = MountainConfig()
        if self.hills is None:
            self.hills = HillConfig()
        if self.valleys is None:
            self.valleys = ValleyConfig()
        if self.dunes is None:
            self.dunes = DuneConfig()


# Global config instance (can be overridden for testing)
_config: TerrainConfig = None


def get_config() -> TerrainConfig:
    """Get the global terrain configuration."""
    global _config
    if _config is None:
        _config = TerrainConfig()
    return _config


def set_config(config: TerrainConfig):
    """Set the global terrain configuration."""
    global _config
    _config = config


def reset_config():
    """Reset to default configuration."""
    global _config
    _config = TerrainConfig()

