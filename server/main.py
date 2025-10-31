from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
import os, json, time, traceback
from PIL import Image
from .terrain import apply_actions, to_png_16bit_gray, to_png_8bit_gray, to_png_rgba
from .primitives.base import base_flat
from .engine.state_lock import atomic_read_state, atomic_write_state
from .engine.cleanup import cleanup_old_assets, cleanup_temp_files
from .engine.voxel import heightmap_to_voxels, export_voxels_mesh, export_voxels_binary

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "public", "assets"))
TEXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "public", "textures"))
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TEXTURES_DIR, exist_ok=True)
STATE_PATH = os.path.join(OUT_DIR, "terrain_state.json")

# Init state using atomic write
if not os.path.exists(STATE_PATH):
    atomic_write_state({"features": [], "seed": 0}, STATE_PATH, backup=False)

def create_placeholder_texture(name: str, color: tuple):
    """Create a solid color placeholder texture (512x512)."""
    path = os.path.join(TEXTURES_DIR, f"{name}.jpg")
    if not os.path.exists(path):
        # Create solid color image (R, G, B)
        img = Image.new('RGB', (512, 512), color)
        img.save(path, 'JPEG', quality=85)
        print(f"Created placeholder texture: {path}")

def ensure_placeholder_textures():
    """Ensure all required placeholder textures exist."""
    textures = {
        "grass": (76, 175, 80),      # #4CAF50 - bright green
        "rock": (128, 128, 128),      # #808080 - gray
        "sand": (210, 180, 140),      # #D2B48C - tan/beige
        "snow": (255, 255, 255),      # #FFFFFF - white
    }
    for name, color in textures.items():
        create_placeholder_texture(name, color)

# Create placeholder textures on startup
ensure_placeholder_textures()

class Command(BaseModel):
    text: str = Field(default="", max_length=1000, description="Natural language command for terrain generation")
    actions: Optional[List[Dict]] = Field(default=None, description="Direct JSON actions array (for compositional calls)")
    voxel: bool = Field(default=False, description="Generate voxel terrain instead of heightmap")
    voxel_resolution: int = Field(default=256, ge=128, le=2048, description="Voxel grid resolution (128-2048)")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if v is None:
            return ""
        return str(v).strip()

def save_outputs(h, splat, tag, voxel_mode=False, voxel_resolution=256):
    """Save terrain outputs with error handling."""
    try:
        # 16-bit for Unity, 8-bit for web viewer (WebGL commonly samples 8-bit)
        path_h16 = os.path.join(OUT_DIR, f"height_{tag}_16.png")
        path_h8  = os.path.join(OUT_DIR, f"height_{tag}_8.png")
        path_s   = os.path.join(OUT_DIR, f"splat_{tag}.png")

        to_png_16bit_gray(h, path_h16)
        to_png_8bit_gray(h, path_h8)
        to_png_rgba(splat, path_s)
        
        urls = {
            "height16": f"/assets/height_{tag}_16.png",
            "height8":  f"/assets/height_{tag}_8.png",
            "splat":    f"/assets/splat_{tag}.png"
        }
        
        # Generate voxel data if requested
        if voxel_mode:
            print(f"Generating voxel grid with resolution: {voxel_resolution}³ ({voxel_resolution**3:,} voxels)")
            voxel_grid = heightmap_to_voxels(h, resolution=voxel_resolution, height_scale=50.0)
            voxel_obj_path = os.path.join(OUT_DIR, f"voxel_{tag}.obj")
            voxel_bin_path = os.path.join(OUT_DIR, f"voxel_{tag}.bin")
            
            export_voxels_mesh(voxel_grid, voxel_obj_path)
            export_voxels_binary(voxel_grid, voxel_bin_path)
            
            urls["voxel_obj"] = f"/assets/voxel_{tag}.obj"
            urls["voxel_bin"] = f"/assets/voxel_{tag}.bin"
        
        return urls
    except Exception as e:
        error_msg = f"Failed to save outputs: {str(e)}"
        print(f"ERROR in save_outputs: {error_msg}")
        raise IOError(error_msg) from e

@app.post("/api/generate")
def generate(cmd: Command):
    """Generate terrain from command with error handling."""
    try:
        # Atomic read state
        state = atomic_read_state(STATE_PATH)
        
        # Generate terrain - support both text and direct actions
        if cmd.actions:
            # Direct JSON actions (compositional calls)
            h, state, splat = apply_actions("", state, direct_actions=cmd.actions)
        else:
            # Natural language command
            h, state, splat = apply_actions(cmd.text, state)
        
        # Atomic write state
        atomic_write_state(state, STATE_PATH)
        
        # Save outputs
        tag = str(int(time.time()))
        urls = save_outputs(h, splat, tag, voxel_mode=cmd.voxel, voxel_resolution=cmd.voxel_resolution)
        
        # Periodic cleanup (every 10th generation to avoid overhead)
        import random
        if random.randint(1, 10) == 1:
            cleanup_old_assets(OUT_DIR)
            cleanup_temp_files(OUT_DIR)
        
        return {"ok": True, "state": state, "assets": urls}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        error_msg = f"Generation failed: {str(e)}"
        print(f"ERROR in /api/generate: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/modify")
def modify(cmd: Command):
    """Modify terrain (alias for generate)."""
    return generate(cmd)

@app.get("/api/state")
def get_state():
    """Get current terrain state."""
    try:
        return atomic_read_state(STATE_PATH)
    except Exception as e:
        error_msg = f"Failed to read state: {str(e)}"
        print(f"ERROR in /api/state: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/reset")
def reset():
    """Reset terrain to perfectly flat base state."""
    try:
        state = {"features": [], "seed": 0}
        
        # Atomic write state
        atomic_write_state(state, STATE_PATH)
        
        # Generate perfectly flat base terrain
        h, state, splat = apply_actions("", state, base_biome_fn=base_flat)
        
        # Save outputs
        tag = str(int(time.time()))
        urls = save_outputs(h, splat, tag, voxel_mode=False)
        
        return {"ok": True, "state": state, "assets": urls}
    
    except Exception as e:
        error_msg = f"Reset failed: {str(e)}"
        print(f"ERROR in /api/reset: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/regenerate")
def regenerate(cmd: Command = Command(text="", voxel=False, voxel_resolution=256)):
    """Regenerate terrain from current state (for auto-load on refresh)."""
    try:
        # Atomic read state
        state = atomic_read_state(STATE_PATH)
        
        # Regenerate from current state
        h, state, splat = apply_actions("", state)  # Empty command = rebuild from state
        
        # Save outputs (with voxel support)
        tag = str(int(time.time()))
        urls = save_outputs(h, splat, tag, voxel_mode=cmd.voxel, voxel_resolution=cmd.voxel_resolution)
        
        return {"ok": True, "state": state, "assets": urls}
    
    except Exception as e:
        error_msg = f"Regeneration failed: {str(e)}"
        print(f"ERROR in /api/regenerate: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

# Serve the /public/assets folder under /assets
app.mount("/assets", StaticFiles(directory=OUT_DIR), name="assets")

