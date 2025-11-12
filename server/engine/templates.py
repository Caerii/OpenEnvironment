"""Terrain Templates - Curated environments showcasing system capabilities.

Templates are predefined terrain configurations that demonstrate:
- Different feature combinations
- Walkability zones and constraints
- Semantic relationships
- Visual variety
- System capabilities
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TerrainTemplate:
    """A terrain template definition."""
    id: str
    name: str
    description: str
    category: str  # "mountain", "desert", "valley", "volcanic", "mixed", "walkability"
    commands: Optional[List[str]] = None  # Natural language commands (alternative to actions)
    actions: Optional[List[Dict]] = None  # Pre-composed JSON actions (alternative to commands)
    tags: List[str] = None  # Searchable tags
    thumbnail_hint: str = ""  # Description for thumbnail generation
    
    def __post_init__(self):
        """Validate that either commands or actions is provided."""
        if self.commands is None and self.actions is None:
            raise ValueError(f"Template {self.id} must have either 'commands' or 'actions'")
        if self.commands is not None and self.actions is not None:
            raise ValueError(f"Template {self.id} cannot have both 'commands' and 'actions'")
        if self.tags is None:
            self.tags = []


# Template Definitions
TEMPLATES: List[TerrainTemplate] = [
    # ========================================================================
    # Mountain Landscapes
    # ========================================================================
    
    TerrainTemplate(
        id="mountain_range",
        name="Mountain Range",
        description="A dramatic mountain range with peaks, valleys, and a mountain pass",
        category="mountain",
        commands=[
            "create a desert biome",
            "add a large mountain in the top-left",
            "add a large mountain in the top-right",
            "add a mountain pass between the two mountains",
            "add a deep valley in the center",
            "add three hills scattered in the bottom half"
        ],
        tags=["mountains", "valleys", "passes", "dramatic", "elevation"],
        thumbnail_hint="Mountain range with peaks and valleys"
    ),
    
    TerrainTemplate(
        id="mountain_range_precise",
        name="Mountain Range (Precise)",
        description="Same as Mountain Range but with pre-composed JSON actions for deterministic generation",
        category="mountain",
        actions=[
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "top-left"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "top-right"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "pass",
                "count": 1,
                "position": {"region": "center"}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"deeper": True}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 3,
                "position": {"region": "bottom", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["mountains", "valleys", "passes", "dramatic", "elevation", "precise"],
        thumbnail_hint="Mountain range with peaks and valleys"
    ),
    
    TerrainTemplate(
        id="alpine_landscape",
        name="Alpine Landscape",
        description="High-altitude terrain with snow-capped peaks and ridges",
        category="mountain",
        commands=[
            "create a desert biome",
            "add a tall mountain in the center",
            "add a ridge extending from the mountain to the top-left",
            "add a ridge extending from the mountain to the top-right",
            "add two smaller peaks on the left",
            "add two smaller peaks on the right",
            "add a valley in the bottom-center"
        ],
        tags=["mountains", "ridges", "snow", "alpine", "peaks"],
        thumbnail_hint="Snow-capped peaks and ridges"
    ),
    
    TerrainTemplate(
        id="alpine_landscape_precise",
        name="Alpine Landscape (Precise)",
        description="Same as Alpine Landscape but with pre-composed JSON actions",
        category="mountain",
        actions=[
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "ridge",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "ridge",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 2,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 2,
                "position": {"region": "right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "bottom"},
                "modifiers": {}
            }
        ],
        tags=["mountains", "ridges", "snow", "alpine", "peaks", "precise"],
        thumbnail_hint="Snow-capped peaks and ridges"
    ),
    
    # ========================================================================
    # Desert Landscapes
    # ========================================================================
    
    TerrainTemplate(
        id="desert_dunes",
        name="Desert Dunes",
        description="Rolling sand dunes with scattered oases and mesas",
        category="desert",
        commands=[
            "create a desert biome",
            "add rolling dunes across the entire terrain",
            "add a large mesa in the center",
            "add a flat clearing near the center for an oasis",
            "add two smaller mesas on the left",
            "add a valley in the bottom-right"
        ],
        tags=["desert", "dunes", "mesas", "sand", "arid"],
        thumbnail_hint="Rolling sand dunes with mesas"
    ),
    
    TerrainTemplate(
        id="desert_dunes_precise",
        name="Desert Dunes (Precise)",
        description="Same as Desert Dunes but with pre-composed JSON actions",
        category="desert",
        actions=[
            {
                "kind": "add",
                "type": "dunes",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mesa",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mesa",
                "count": 2,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "bottom-right"},
                "modifiers": {}
            }
        ],
        tags=["desert", "dunes", "mesas", "sand", "arid", "precise"],
        thumbnail_hint="Rolling sand dunes with mesas"
    ),
    
    TerrainTemplate(
        id="desert_canyon",
        name="Desert Canyon",
        description="A deep canyon cutting through desert terrain with mesas",
        category="desert",
        commands=[
            "create a desert biome",
            "add rolling dunes in the top half",
            "add a deep canyon from the left-center to the right-center",
            "add a large mesa on the left",
            "add a large mesa on the right",
            "add flat areas near the canyon edges"
        ],
        tags=["desert", "canyon", "mesas", "dramatic"],
        thumbnail_hint="Deep canyon through desert"
    ),
    
    TerrainTemplate(
        id="desert_canyon_precise",
        name="Desert Canyon (Precise)",
        description="Same as Desert Canyon but with pre-composed JSON actions",
        category="desert",
        actions=[
            {
                "kind": "add",
                "type": "dunes",
                "count": 1,
                "position": {"region": "top"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "canyon",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"deeper": True}
            },
            {
                "kind": "add",
                "type": "mesa",
                "count": 1,
                "position": {"region": "left"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "mesa",
                "count": 1,
                "position": {"region": "right"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 2,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["desert", "canyon", "mesas", "dramatic", "precise"],
        thumbnail_hint="Deep canyon through desert"
    ),
    
    # ========================================================================
    # Valley Systems
    # ========================================================================
    
    TerrainTemplate(
        id="river_valley",
        name="River Valley",
        description="A winding valley system with mountains on both sides",
        category="valley",
        commands=[
            "create a desert biome",
            "add a deep valley winding from top-left to bottom-right",
            "add a mountain range on the left side",
            "add a mountain range on the right side",
            "add hills along the valley edges",
            "add a flat zone in the valley bottom"
        ],
        tags=["valleys", "mountains", "rivers", "winding"],
        thumbnail_hint="Winding valley with mountains"
    ),
    
    TerrainTemplate(
        id="river_valley_precise",
        name="River Valley (Precise)",
        description="Same as River Valley but with pre-composed JSON actions",
        category="valley",
        actions=[
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"deeper": True}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 3,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 3,
                "position": {"region": "right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 4,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            }
        ],
        tags=["valleys", "mountains", "rivers", "winding", "precise"],
        thumbnail_hint="Winding valley with mountains"
    ),
    
    TerrainTemplate(
        id="mountain_basin",
        name="Mountain Basin",
        description="A large basin surrounded by mountains with a central clearing",
        category="valley",
        commands=[
            "create a desert biome",
            "add a large basin in the center",
            "add mountains surrounding the basin",
            "add a flat clearing in the basin center",
            "add hills near the basin edges"
        ],
        tags=["basin", "mountains", "clearing", "enclosed"],
        thumbnail_hint="Mountain-encircled basin"
    ),
    
    TerrainTemplate(
        id="mountain_basin_precise",
        name="Mountain Basin (Precise)",
        description="Same as Mountain Basin but with pre-composed JSON actions",
        category="valley",
        actions=[
            {
                "kind": "add",
                "type": "basin",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"wider": True}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 5,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 3,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["basin", "mountains", "clearing", "enclosed", "precise"],
        thumbnail_hint="Mountain-encircled basin"
    ),
    
    # ========================================================================
    # Volcanic Landscapes
    # ========================================================================
    
    TerrainTemplate(
        id="volcanic_field",
        name="Volcanic Field",
        description="Multiple volcanoes with craters and lava flows",
        category="volcanic",
        commands=[
            "create a desert biome",
            "add a large volcano in the center",
            "add a volcano on the left",
            "add a volcano on the right",
            "add a crater near the center",
            "add a deep valley connecting the volcanoes",
            "add hills scattered around"
        ],
        tags=["volcano", "crater", "volcanic", "dramatic"],
        thumbnail_hint="Volcanic field with craters"
    ),
    
    TerrainTemplate(
        id="volcanic_field_precise",
        name="Volcanic Field (Precise)",
        description="Same as Volcanic Field but with pre-composed JSON actions",
        category="volcanic",
        actions=[
            {
                "kind": "add",
                "type": "volcano",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "volcano",
                "count": 1,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "volcano",
                "count": 1,
                "position": {"region": "right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "crater",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"deeper": True}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 4,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["volcano", "crater", "volcanic", "dramatic", "precise"],
        thumbnail_hint="Volcanic field with craters"
    ),
    
    # ========================================================================
    # Walkability & Path Systems
    # ========================================================================
    
    TerrainTemplate(
        id="mountain_path",
        name="Mountain Path",
        description="A path through mountains with features placed around it",
        category="walkability",
        commands=[
            "create a desert biome",
            "add a path from the center to the top-right",
            "add a mountain on the left of the path",
            "add a mountain on the right of the path",
            "add hills along the path edges",
            "add a clearing at the path start"
        ],
        tags=["path", "mountains", "walkability", "navigation"],
        thumbnail_hint="Path winding through mountains"
    ),
    
    TerrainTemplate(
        id="mountain_path_precise",
        name="Mountain Path (Precise)",
        description="Same as Mountain Path but with pre-composed JSON actions showing walkability zones",
        category="walkability",
        actions=[
            {
                "kind": "add",
                "type": "path",
                "count": 1,
                "position": {
                    "start": [256, 256],  # Start at center
                    "end": [400, 100]  # End at top-right
                },
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 3,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            }
        ],
        tags=["path", "mountains", "walkability", "navigation", "precise"],
        thumbnail_hint="Path winding through mountains"
    ),
    
    TerrainTemplate(
        id="trading_route",
        name="Trading Route",
        description="A path connecting settlements with clearings at key points",
        category="walkability",
        commands=[
            "create a desert biome",
            "add a path from bottom-left to top-right",
            "add a flat clearing at the bottom-left",
            "add a flat clearing at the top-right",
            "add a flat clearing in the center",
            "add hills around the path but not blocking it",
            "add a mountain in the top-left"
        ],
        tags=["path", "clearings", "route", "navigation"],
        thumbnail_hint="Trading route with clearings"
    ),
    
    TerrainTemplate(
        id="trading_route_precise",
        name="Trading Route (Precise)",
        description="Same as Trading Route but with pre-composed JSON actions",
        category="walkability",
        actions=[
            {
                "kind": "add",
                "type": "path",
                "count": 1,
                "position": {
                    "start": [100, 400],
                    "end": [400, 100]
                },
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "bottom-left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "top-right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 4,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "top-left"},
                "modifiers": {}
            }
        ],
        tags=["path", "clearings", "route", "navigation", "precise"],
        thumbnail_hint="Trading route with clearings"
    ),
    
    TerrainTemplate(
        id="mountain_pass",
        name="Mountain Pass",
        description="A pass between two mountains with a clear path",
        category="walkability",
        commands=[
            "create a desert biome",
            "add a large mountain on the left",
            "add a large mountain on the right",
            "add a path between the two mountains",
            "add hills on either side of the pass"
        ],
        tags=["pass", "mountains", "path", "corridor"],
        thumbnail_hint="Mountain pass with clear path"
    ),
    
    TerrainTemplate(
        id="mountain_pass_precise",
        name="Mountain Pass (Precise)",
        description="Same as Mountain Pass but with pre-composed JSON actions",
        category="walkability",
        actions=[
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "left"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "right"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "pass",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "path",
                "count": 1,
                "position": {
                    "start": [150, 256],
                    "end": [350, 256]
                },
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 3,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["pass", "mountains", "path", "corridor", "precise"],
        thumbnail_hint="Mountain pass with clear path"
    ),
    
    # ========================================================================
    # Mixed & Complex Landscapes
    # ========================================================================
    
    TerrainTemplate(
        id="diverse_terrain",
        name="Diverse Terrain",
        description="A mix of all terrain types showcasing variety",
        category="mixed",
        commands=[
            "create a desert biome",
            "add a mountain in the top-left",
            "add rolling dunes in the top-right",
            "add a deep valley in the center",
            "add a mesa in the bottom-left",
            "add a volcano in the bottom-right",
            "add hills scattered throughout",
            "add a ridge in the middle"
        ],
        tags=["mixed", "diverse", "showcase", "variety"],
        thumbnail_hint="Diverse terrain with all features"
    ),
    
    TerrainTemplate(
        id="diverse_terrain_precise",
        name="Diverse Terrain (Precise)",
        description="Same as Diverse Terrain but with pre-composed JSON actions",
        category="mixed",
        actions=[
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "top-left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "dunes",
                "count": 1,
                "position": {"region": "top-right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"deeper": True}
            },
            {
                "kind": "add",
                "type": "mesa",
                "count": 1,
                "position": {"region": "bottom-left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "volcano",
                "count": 1,
                "position": {"region": "bottom-right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 5,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "ridge",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            }
        ],
        tags=["mixed", "diverse", "showcase", "variety", "precise"],
        thumbnail_hint="Diverse terrain with all features"
    ),
    
    TerrainTemplate(
        id="peaceful_landscape",
        name="Peaceful Landscape",
        description="Gentle rolling hills with clearings and a valley",
        category="mixed",
        commands=[
            "create a desert biome",
            "add five gentle hills scattered across the terrain",
            "add a shallow valley in the center",
            "add a large flat clearing in the center",
            "add small hills around the edges"
        ],
        tags=["hills", "peaceful", "gentle", "calm"],
        thumbnail_hint="Peaceful rolling hills"
    ),
    
    TerrainTemplate(
        id="peaceful_landscape_precise",
        name="Peaceful Landscape (Precise)",
        description="Same as Peaceful Landscape but with pre-composed JSON actions",
        category="mixed",
        actions=[
            {
                "kind": "add",
                "type": "hill",
                "count": 5,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "flat_zone",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"wider": True}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 4,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["hills", "peaceful", "gentle", "calm", "precise"],
        thumbnail_hint="Peaceful rolling hills"
    ),
    
    TerrainTemplate(
        id="dramatic_cliffs",
        name="Dramatic Cliffs",
        description="Steep cliffs and canyons creating dramatic elevation changes",
        category="mixed",
        commands=[
            "create a desert biome",
            "add a tall mountain in the center",
            "add a cliff face on the left side",
            "add a cliff face on the right side",
            "add a deep canyon in the bottom",
            "add a ravine cutting through the terrain",
            "add hills on the high ground"
        ],
        tags=["cliffs", "canyons", "dramatic", "steep"],
        thumbnail_hint="Dramatic cliffs and canyons"
    ),
    
    TerrainTemplate(
        id="dramatic_cliffs_precise",
        name="Dramatic Cliffs (Precise)",
        description="Same as Dramatic Cliffs but with pre-composed JSON actions",
        category="mixed",
        actions=[
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"taller": True}
            },
            {
                "kind": "add",
                "type": "cliff",
                "count": 1,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "cliff",
                "count": 1,
                "position": {"region": "right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "canyon",
                "count": 1,
                "position": {"region": "bottom"},
                "modifiers": {"deeper": True}
            },
            {
                "kind": "add",
                "type": "ravine",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 3,
                "position": {"region": "top", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["cliffs", "canyons", "dramatic", "steep", "precise"],
        thumbnail_hint="Dramatic cliffs and canyons"
    ),
    
    # ========================================================================
    # Specialized Showcases
    # ========================================================================
    
    TerrainTemplate(
        id="crater_field",
        name="Crater Field",
        description="Multiple impact craters creating a unique landscape",
        category="mixed",
        commands=[
            "create a desert biome",
            "add a large crater in the center",
            "add three medium craters scattered around",
            "add hills between the craters",
            "add a small mountain on the edge"
        ],
        tags=["craters", "impact", "unique", "dramatic"],
        thumbnail_hint="Field of impact craters"
    ),
    
    TerrainTemplate(
        id="crater_field_precise",
        name="Crater Field (Precise)",
        description="Same as Crater Field but with pre-composed JSON actions",
        category="mixed",
        actions=[
            {
                "kind": "add",
                "type": "crater",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"wider": True}
            },
            {
                "kind": "add",
                "type": "crater",
                "count": 3,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 4,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 1,
                "position": {"region": "top-right"},
                "modifiers": {}
            }
        ],
        tags=["craters", "impact", "unique", "dramatic", "precise"],
        thumbnail_hint="Field of impact craters"
    ),
    
    TerrainTemplate(
        id="plateau_landscape",
        name="Plateau Landscape",
        description="Multiple plateaus at different elevations",
        category="mixed",
        commands=[
            "create a desert biome",
            "add a large plateau in the center",
            "add a smaller plateau on the left",
            "add a smaller plateau on the right",
            "add valleys between the plateaus",
            "add hills on the lower ground"
        ],
        tags=["plateaus", "elevated", "layered"],
        thumbnail_hint="Multiple plateaus at different heights"
    ),
    
    TerrainTemplate(
        id="plateau_landscape_precise",
        name="Plateau Landscape (Precise)",
        description="Same as Plateau Landscape but with pre-composed JSON actions",
        category="mixed",
        actions=[
            {
                "kind": "add",
                "type": "plateau",
                "count": 1,
                "position": {"region": "center"},
                "modifiers": {"wider": True}
            },
            {
                "kind": "add",
                "type": "plateau",
                "count": 1,
                "position": {"region": "left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "plateau",
                "count": 1,
                "position": {"region": "right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 2,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 3,
                "position": {"region": "bottom", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["plateaus", "elevated", "layered", "precise"],
        thumbnail_hint="Multiple plateaus at different heights"
    ),
    
    TerrainTemplate(
        id="ridge_network",
        name="Ridge Network",
        description="Interconnected ridges creating natural boundaries",
        category="mixed",
        commands=[
            "create a desert biome",
            "add a ridge from top-left to center",
            "add a ridge from center to top-right",
            "add a ridge from center to bottom",
            "add mountains at the ridge intersections",
            "add valleys between the ridges",
            "add hills in the low areas"
        ],
        tags=["ridges", "network", "interconnected", "boundaries"],
        thumbnail_hint="Network of interconnected ridges"
    ),
    
    TerrainTemplate(
        id="ridge_network_precise",
        name="Ridge Network (Precise)",
        description="Same as Ridge Network but with pre-composed JSON actions",
        category="mixed",
        actions=[
            {
                "kind": "add",
                "type": "ridge",
                "count": 1,
                "position": {"region": "top-left"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "ridge",
                "count": 1,
                "position": {"region": "top-right"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "ridge",
                "count": 1,
                "position": {"region": "bottom"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "mountain",
                "count": 3,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "valley",
                "count": 2,
                "position": {"region": "center", "distribution": "scattered"},
                "modifiers": {}
            },
            {
                "kind": "add",
                "type": "hill",
                "count": 4,
                "position": {"region": "bottom", "distribution": "scattered"},
                "modifiers": {}
            }
        ],
        tags=["ridges", "network", "interconnected", "boundaries", "precise"],
        thumbnail_hint="Network of interconnected ridges"
    ),
]


class TemplateRegistry:
    """Registry for terrain templates."""
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all templates as dictionaries."""
        result = []
        for t in TEMPLATES:
            template_dict = {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "tags": t.tags,
                "thumbnail_hint": t.thumbnail_hint,
                "format": "actions" if t.actions is not None else "commands"
            }
            if t.commands:
                template_dict["command_count"] = len(t.commands)
            if t.actions:
                template_dict["action_count"] = len(t.actions)
            result.append(template_dict)
        return result
    
    @staticmethod
    def get_by_id(template_id: str) -> Optional[TerrainTemplate]:
        """Get a template by ID."""
        for template in TEMPLATES:
            if template.id == template_id:
                return template
        return None
    
    @staticmethod
    def get_by_category(category: str) -> List[Dict]:
        """Get templates by category."""
        result = []
        for t in TEMPLATES:
            if t.category == category:
                template_dict = {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "tags": t.tags,
                    "thumbnail_hint": t.thumbnail_hint,
                    "format": "actions" if t.actions is not None else "commands"
                }
                if t.commands:
                    template_dict["command_count"] = len(t.commands)
                if t.actions:
                    template_dict["action_count"] = len(t.actions)
                result.append(template_dict)
        return result
    
    @staticmethod
    def get_by_tag(tag: str) -> List[Dict]:
        """Get templates by tag."""
        result = []
        for t in TEMPLATES:
            if tag.lower() in [tag_lower.lower() for tag_lower in t.tags]:
                template_dict = {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "tags": t.tags,
                    "thumbnail_hint": t.thumbnail_hint,
                    "format": "actions" if t.actions is not None else "commands"
                }
                if t.commands:
                    template_dict["command_count"] = len(t.commands)
                if t.actions:
                    template_dict["action_count"] = len(t.actions)
                result.append(template_dict)
        return result
    
    @staticmethod
    def get_categories() -> List[str]:
        """Get all unique categories."""
        return sorted(set(t.category for t in TEMPLATES))
    
    @staticmethod
    def apply_template(template_id: str) -> tuple[Optional[List[str]], Optional[List[Dict]]]:
        """
        Get the commands or actions for a template.
        
        Returns:
            Tuple of (commands, actions) where one will be None and the other will have data
        """
        template = TemplateRegistry.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        return template.commands, template.actions
    
    @staticmethod
    def get_template_format(template_id: str) -> str:
        """
        Get the format type of a template.
        
        Returns:
            "commands" or "actions"
        """
        template = TemplateRegistry.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        return "actions" if template.actions is not None else "commands"

