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


class MultiAgentRequest(BaseModel):
    """Request payload for multi-agent terrain design."""

    text: str = Field(..., description="User brief guiding the multi-agent terrain design")
    profile: Optional[str] = Field(
        default=None,
        description="Prompt profile name for LLM configuration (e.g., compact, standard, omni)",
    )
    max_rounds: int = Field(
        default=6,
        ge=1,
        le=12,
        description="Maximum number of conversation rounds for the agent loop",
    )


