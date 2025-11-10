"""FastAPI application entry point with controller-service architecture."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import os
import logging

from .bootstrap import ensure_bootstrapped

ensure_bootstrapped()

# FIX: Load .env file before anything else to ensure CEREBRAS_API_KEY is available
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Paths configuration
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "public", "assets"))
TEXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "public", "textures"))
STATE_PATH = os.path.join(OUT_DIR, "terrain_state.json")

# Initialize services
from .services import (
    StateService,
    TextureService,
    AssetService,
    TerrainService,
    TemplateService,
    MCPService
)

state_service = StateService(STATE_PATH)
texture_service = TextureService(TEXTURES_DIR)
asset_service = AssetService(OUT_DIR)
terrain_service = TerrainService(state_service, asset_service)
template_service = TemplateService(terrain_service)
mcp_service = MCPService(terrain_service, asset_service, state_service)

# Initialize controllers
from .api.controllers import (
    TerrainController,
    TemplateController,
    MCPController,
    StatusController
)

terrain_controller = TerrainController(terrain_service, asset_service)
template_controller = TemplateController(template_service, asset_service)
mcp_controller = MCPController(mcp_service)
status_controller = StatusController()

# Import models
from .api.models import Command
from typing import Dict

# ============================================================================
# Terrain Generation Endpoints
# ============================================================================

@app.post("/api/generate")
def generate(cmd: Command) -> Dict:
    """Generate terrain from command."""
    return terrain_controller.generate(cmd)

@app.post("/api/modify")
def modify(cmd: Command) -> Dict:
    """Modify terrain (alias for generate)."""
    return terrain_controller.modify(cmd)

@app.get("/api/state")
def get_state() -> Dict:
    """Get current terrain state."""
    try:
        return state_service.get_state()
    except Exception as e:
        from fastapi import HTTPException
        error_msg = f"Failed to read state: {str(e)}"
        logger.error(f"ERROR in /api/state: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/reset")
def reset(cmd: Command = Command()) -> Dict:
    """Reset terrain to base state."""
    return terrain_controller.reset(cmd)

@app.post("/api/regenerate")
def regenerate(cmd: Command = Command(text="", voxel=False, voxel_resolution=256)) -> Dict:
    """Regenerate terrain from current state."""
    return terrain_controller.regenerate(cmd)


# ============================================================================
# Template System
# ============================================================================

@app.get("/api/templates")
def list_templates(category: Optional[str] = None, tag: Optional[str] = None) -> Dict:
    """List all available terrain templates."""
    return template_controller.list_templates(category, tag)

@app.get("/api/templates/{template_id}")
def get_template(template_id: str) -> Dict:
    """Get details for a specific template."""
    return template_controller.get_template(template_id)

@app.post("/api/templates/{template_id}/apply")
async def apply_template(template_id: str, cmd: Command = Command()) -> Dict:
    """Apply a terrain template."""
    return template_controller.apply_template(template_id, cmd)


# ============================================================================
# MCP (Model Context Protocol) Server Endpoints
# ============================================================================

@app.get("/api/mcp")
def mcp_info() -> Dict:
    """Get MCP server information and capabilities."""
    return mcp_controller.get_info()

@app.get("/api/mcp/tools")
def list_mcp_tools(category: Optional[str] = None) -> Dict:
    """List all available MCP tools."""
    return mcp_controller.list_tools(category)


@app.get("/api/mcp/tools/{tool_name}")
def get_mcp_tool(tool_name: str) -> Dict:
    """Get details for a specific MCP tool."""
    return mcp_controller.get_tool(tool_name)

@app.post("/api/mcp/tools/{tool_name}/call")
def call_mcp_tool(tool_name: str, arguments: Dict) -> Dict:
    """Execute an MCP tool with provided arguments."""
    return mcp_controller.call_tool(tool_name, arguments)


@app.get("/api/mcp/resources")
def list_mcp_resources() -> Dict:
    """List all available MCP resources."""
    return mcp_controller.list_resources()

@app.get("/api/mcp/resources/{resource_uri:path}")
def get_mcp_resource(resource_uri: str) -> Dict:
    """Get a specific MCP resource."""
    return mcp_controller.get_resource(resource_uri)

@app.get("/api/mcp/prompts")
def list_mcp_prompts() -> Dict:
    """List all available MCP prompts."""
    return mcp_controller.list_prompts()

@app.get("/api/mcp/prompts/{prompt_name}")
def get_mcp_prompt(prompt_name: str) -> Dict:
    """Get a specific MCP prompt template."""
    return mcp_controller.get_prompt(prompt_name)


@app.get("/api/status")
def get_status() -> Dict:
    """Get server status including API key availability."""
    return status_controller.get_status()


# Serve the /public/assets folder under /assets
app.mount("/assets", StaticFiles(directory=OUT_DIR), name="assets")

