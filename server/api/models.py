"""Request/Response models for API."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict


class Command(BaseModel):
    """Command model for terrain generation requests."""
    text: str = Field(default="", max_length=1000, description="Natural language command for terrain generation")
    actions: Optional[List[Dict]] = Field(default=None, description="Direct JSON actions array (for compositional calls)")
    voxel: bool = Field(default=False, description="Generate voxel terrain instead of heightmap")
    voxel_resolution: int = Field(default=256, ge=128, le=2048, description="Voxel grid resolution (128-2048)")
    seed: Optional[int] = Field(default=None, description="Random seed for terrain generation (-1 = auto-generate random seed)")
    biome: Optional[str] = Field(default=None, description="Base biome type (flat, desert, forest, arctic)")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if v is None:
            return ""
        return str(v).strip()


