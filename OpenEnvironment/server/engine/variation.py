"""Conservative variation engine - Adds subtle, natural variation to features.

Key principles:
- Small variation (±8-12%) to avoid sharp spikes
- Deterministic (seed-based) for reproducibility
- Only applies when no explicit modifiers given
- Preserves smooth Gaussian falloff nature
- Bounded to safe ranges
"""
import numpy as np


class VariationEngine:
    """Engine for adding subtle, natural variation to terrain features."""
    
    @staticmethod
    def apply_variation(base_value: float, variation_percent: float, seed: int,
                       min_value: float = None, max_value: float = None) -> float:
        """
        Apply subtle variation to a float value.
        
        Args:
            base_value: Base value to vary
            variation_percent: Variation percentage (e.g., 0.10 = ±10%)
            seed: Deterministic seed
            min_value: Optional minimum clamp value
            max_value: Optional maximum clamp value
            
        Returns:
            Varied value within bounds
        """
        rng = np.random.RandomState(seed)
        # Generate variation in [-variation_percent, +variation_percent] range
        multiplier = 1.0 + rng.uniform(-variation_percent, variation_percent)
        varied = base_value * multiplier
        
        # Clamp to bounds if provided
        if min_value is not None:
            varied = max(min_value, varied)
        if max_value is not None:
            varied = min(max_value, varied)
        
        return float(varied)
    
    @staticmethod
    def apply_variation_int(base_value: int, variation_percent: float, seed: int,
                           min_value: int = None, max_value: int = None) -> int:
        """
        Apply subtle variation to an integer value.
        
        Args:
            base_value: Base integer value to vary
            variation_percent: Variation percentage (e.g., 0.10 = ±10%)
            seed: Deterministic seed
            min_value: Optional minimum clamp value
            max_value: Optional maximum clamp value
            
        Returns:
            Varied integer value within bounds
        """
        varied_float = VariationEngine.apply_variation(
            float(base_value), variation_percent, seed,
            float(min_value) if min_value is not None else None,
            float(max_value) if max_value is not None else None
        )
        return int(round(varied_float))


# Conservative variation parameters (smaller than recommended to avoid spikes)
VARIATION_CONFIG = {
    "mountain": {
        "height_variation": 0.08,  # ±8% (conservative, avoids spikes)
        "radius_variation": 0.12,  # ±12% (slightly more for size variety)
        "height_min": 0.60,        # Prevent too-small mountains
        "height_max": 1.5,         # Allow dramatic peaks above normalized range
        "radius_min": 40,           # Prevent spike-like tiny mountains
        "radius_max": 80,           # Prevent overwhelming terrain
    },
    "hill": {
        "height_variation": 0.10,  # ±10% (hills can vary more)
        "radius_variation": 0.12,  # ±12%
        "height_min": 0.35,         # Keep hills noticeable
        "height_max": 0.60,          # Keep hills below mountains
        "radius_min": 32,           # Prevent too-small hills
        "radius_max": 65,           # Prevent hills as large as mountains
    },
    "valley": {
        "depth_variation": 0.08,   # ±8% (conservative, maintain depth)
        "radius_variation": 0.12,   # ±12%
        "depth_min": 0.45,          # Keep valleys noticeable
        "depth_max": 1.2,           # Allow dramatic depths (can go negative in terrain)
        "radius_min": 48,           # Prevent tiny valleys
        "radius_max": 90,           # Prevent valleys too large
    },
    "dunes": {
        "amp_variation": 0.10,      # ±10% (dunes can vary more)
        "freq_variation": 0.15,     # ±15% (frequency variation is safe)
        "angle_variation": 0.20,     # ±20% (angle variation is safe)
        "radius_variation": 0.15,   # ±15%
        "radius_min": 72,           # Prevent too-small dune areas
        "radius_max": 120,          # Prevent dunes covering entire terrain
    },
    "mesa": {
        "height_variation": 0.08,   # ±8% (similar to mountains)
        "radius_variation": 0.12,   # ±12%
        "height_min": 0.50,          # Mesas slightly lower than mountains
        "height_max": 1.2,           # Allow dramatic mesa heights
        "radius_min": 40,            # Same as mountains
        "radius_max": 85,            # Can be slightly larger
    },
    "plateau": {
        "height_variation": 0.10,   # ±10%
        "width_variation": 0.15,    # ±15%
        "length_variation": 0.15,   # ±15%
        "height_min": 0.35,          # Plateaus can be moderate elevation
        "height_max": 0.70,          # Not too high
        "width_min": 60,             # Minimum size
        "width_max": 120,            # Maximum size
        "length_min": 80,            # Minimum length
        "length_max": 160,           # Maximum length
    },
    "cliff": {
        "height_variation": 0.10,   # ±10%
        "length_variation": 0.15,   # ±15%
        "height_min": 0.40,          # Cliffs should be noticeable
        "height_max": 1.1,           # Allow dramatic cliff heights
        "length_min": 50,             # Minimum cliff length
        "length_max": 120,           # Maximum cliff length
    },
    "canyon": {
        "depth_variation": 0.08,    # ±8% (conservative)
        "width_variation": 0.15,    # ±15%
        "length_variation": 0.20,    # ±20%
        "depth_min": 0.50,           # Canyons should be deep
        "depth_max": 1.3,            # Allow dramatic canyon depths (can cut deep below terrain)
        "width_min": 8,              # Minimum width
        "width_max": 18,              # Maximum width
        "length_min": 60,             # Minimum length
        "length_max": 150,           # Maximum length
    },
    "slope": {
        "height_variation": 0.10,   # ±10%
        "radius_variation": 0.15,   # ±15%
        "height_min": 0.25,          # Slopes are gentle
        "height_max": 0.50,          # Not too steep
        "radius_min": 40,            # Minimum slope area
        "radius_max": 90,            # Maximum slope area
    }
}

