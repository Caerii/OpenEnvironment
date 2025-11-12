"""
Constants for terrain generation system.

Centralized constants to avoid magic numbers scattered throughout code.
"""

# Terrain dimensions
TERRAIN_RESOLUTION = 512
"""Heightmap resolution (512x512 pixels)"""

TERRAIN_MID_X = 256
"""X coordinate of terrain center"""

TERRAIN_MID_Y = 256
"""Y coordinate of terrain center"""

# Feature limits
MAX_FEATURE_HEIGHT = 1.0
"""Maximum normalized height for features"""

MAX_FEATURE_RADIUS = 128
"""Maximum radius in pixels for point features"""

MAX_FEATURE_DEPTH = 1.0
"""Maximum normalized depth for subtractive features"""

# Spatial query defaults
DEFAULT_PROXIMITY_RADIUS = 150
"""Default radius (pixels) for 'near' spatial queries"""

CONTEXT_WINDOW_CHARS = 50
"""Character window for extracting feature context in regex parser"""

# Cleanup and maintenance
CLEANUP_INTERVAL = 10
"""Run asset cleanup every N terrain generations"""

# Variation multipliers
MODIFIER_MULTIPLIER = 1.3
"""Multiplier for keyword modifiers (taller, wider, deeper)"""

# Seed generation
POSITION_SEED_MULTIPLIER = 31
"""Multiplier for deriving position seed from feature count"""

FEATURE_SEED_MULTIPLIER = 17
"""Multiplier for deriving feature seed from position index"""

# Parsing
NUMBER_WORD_LOOKBACK_CHARS = 30
"""Characters to look back when extracting counts in regex parser"""

# File paths (relative to server/)
DEFAULT_STATE_FILE = "terrain_state.json"
"""Default filename for persisted terrain state"""

