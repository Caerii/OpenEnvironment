# API Reference

Complete API endpoint documentation for the Semantic Terrain system.

---

## Base URL

```
http://localhost:8001
```

---

## Core Endpoints

### Generate Terrain

**POST** `/api/generate`

Generate terrain from a natural language command.

**Request:**
```json
{
  "text": "create a desert with rolling dunes and two mountains on the left",
  "voxel": false,
  "voxel_resolution": 256
}
```

**Response:**
```json
{
  "ok": true,
  "state": {
    "seed": 42,
    "features": [...],
    "semantic_scene": {...}
  },
  "assets": {
    "heightmap": "/assets/heightmap_1234567890.png",
    "splatmap": "/assets/splatmap_1234567890.png"
  }
}
```

### Modify Terrain

**POST** `/api/modify`

Modify existing terrain (alias for generate).

**Request:** Same as `/api/generate`

**Response:** Same as `/api/generate`

### Get State

**GET** `/api/state`

Get current terrain state.

**Response:**
```json
{
  "seed": 42,
  "features": [...],
  "semantic_scene": {...}
}
```

### Reset Terrain

**POST** `/api/reset`

Reset terrain to base state.

**Request:**
```json
{
  "text": "",
  "voxel": false
}
```

**Response:** Same as `/api/generate`

### Regenerate Terrain

**POST** `/api/regenerate`

Rebuild terrain from current state.

**Request:**
```json
{
  "text": "",
  "voxel": false,
  "voxel_resolution": 256
}
```

**Response:** Same as `/api/generate`

---

## Template Endpoints

### List Templates

**GET** `/api/templates`

List all available terrain templates.

**Query Parameters:**
- `category` (optional) - Filter by category
- `tag` (optional) - Filter by tag

**Response:**
```json
{
  "templates": [
    {
      "id": "desert_oasis",
      "name": "Desert Oasis",
      "category": "desert",
      "tags": ["desert", "oasis"],
      "description": "..."
    }
  ]
}
```

### Get Template

**GET** `/api/templates/{template_id}`

Get details for a specific template.

**Response:**
```json
{
  "id": "desert_oasis",
  "name": "Desert Oasis",
  "category": "desert",
  "description": "...",
  "actions": [...]
}
```

### Apply Template

**POST** `/api/templates/{template_id}/apply`

Apply a terrain template.

**Request:**
```json
{
  "text": "",
  "voxel": false
}
```

**Response:** Same as `/api/generate`

---

## Multi-Agent Endpoints

### Design with Multi-Agent

**POST** `/api/design/multi-agent`

Run the multi-agent terrain design workflow.

**Request:**
```json
{
  "command": "design a complex mountain valley system",
  "max_rounds": 6,
  "profile": "standard"
}
```

**Response:**
```json
{
  "ok": true,
  "actions": [...],
  "quality_info": {
    "overall_score": 8.5,
    "composition_score": 9.0,
    "texture_score": 8.0
  },
  "transcript": "..."
}
```

---

## MCP Endpoints

### Get MCP Info

**GET** `/api/mcp`

Get MCP server information and capabilities.

**Response:**
```json
{
  "name": "Semantic Terrain MCP Server",
  "version": "1.0.0",
  "capabilities": [...]
}
```

### List MCP Tools

**GET** `/api/mcp/tools`

List all available MCP tools.

**Query Parameters:**
- `category` (optional) - Filter by category

**Response:**
```json
{
  "tools": [
    {
      "name": "add_feature",
      "category": "generation",
      "description": "..."
    }
  ]
}
```

### Get MCP Tool

**GET** `/api/mcp/tools/{tool_name}`

Get details for a specific MCP tool.

**Response:**
```json
{
  "name": "add_feature",
  "description": "...",
  "parameters": [...]
}
```

### Call MCP Tool

**POST** `/api/mcp/tools/{tool_name}/call`

Execute an MCP tool with provided arguments.

**Request:**
```json
{
  "arguments": {
    "type": "mountain",
    "position": {"region": "left"}
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {...}
}
```

### List MCP Resources

**GET** `/api/mcp/resources`

List all available MCP resources.

**Response:**
```json
{
  "resources": [
    {
      "uri": "terrain://state",
      "name": "Terrain State",
      "description": "..."
    }
  ]
}
```

### Get MCP Resource

**GET** `/api/mcp/resources/{resource_uri:path}`

Get a specific MCP resource.

**Response:**
```json
{
  "uri": "terrain://state",
  "contents": {...}
}
```

### List MCP Prompts

**GET** `/api/mcp/prompts`

List all available MCP prompts.

**Response:**
```json
{
  "prompts": [
    {
      "name": "generate_terrain",
      "description": "..."
    }
  ]
}
```

### Get MCP Prompt

**GET** `/api/mcp/prompts/{prompt_name}`

Get a specific MCP prompt template.

**Response:**
```json
{
  "name": "generate_terrain",
  "description": "...",
  "template": "..."
}
```

---

## Status Endpoints

### Get Status

**GET** `/api/status`

Get server status including API key availability.

**Response:**
```json
{
  "status": "running",
  "api_keys": {
    "cerebras": true,
    "together": false,
    "gemini": false
  },
  "version": "1.0.0"
}
```

---

## Assets

### Serve Assets

**GET** `/assets/*`

Serve generated heightmaps, splatmaps, and voxel meshes.

**Examples:**
- `/assets/heightmap_1234567890.png` - Heightmap image
- `/assets/splatmap_1234567890.png` - Splatmap image
- `/assets/voxel_1234567890.obj` - Voxel mesh (if generated)

---

## Error Responses

All endpoints may return error responses:

```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

---

## Authentication

Currently no authentication is required. Consider adding authentication for production use.

---

See also:
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Parsing Strategies](PARSING_STRATEGIES.md) - How commands are parsed
- [Examples](EXAMPLES.md) - API usage examples

