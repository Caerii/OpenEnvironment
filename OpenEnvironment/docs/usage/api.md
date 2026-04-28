# API Reference

Base URL: `http://localhost:8001`

All endpoints accept and return JSON. The `Command` model used by most endpoints:

```json
{
  "text": "create a desert with dunes",
  "voxel": false,
  "voxel_resolution": 256,
  "seed": 42,
  "biome": "desert"
}
```

All fields are optional. `text` defaults to `""`, `voxel` to `false`, `seed` to `-1` (auto).

---

## Terrain

### POST /api/generate

Generate terrain from natural language.

```json
// Response
{
  "ok": true,
  "state": { "seed": 42, "features": [...], "semantic_scene": {...} },
  "assets": {
    "height8": "/assets/height8_123.png",
    "height16": "/assets/height16_123.png",
    "splat": "/assets/splat_123.png",
    "voxel_obj": "/assets/voxel_123.obj"  // only if voxel=true
  }
}
```

### POST /api/modify

Same as `/api/generate`. Alias for clarity in the frontend.

### GET /api/state

Returns current terrain state JSON (features, scene graph, seed, action history).

### POST /api/reset

Resets terrain. Generates a fresh procedurally-interesting default terrain based on seed. Accepts `seed` and `biome` in the body.

### POST /api/regenerate

Rebuilds terrain from current state without parsing any new command. Useful after external state changes or to toggle voxel mode.

---

## Templates

### GET /api/templates

List templates. Optional query params: `category`, `tag`.

```json
{
  "ok": true,
  "templates": [{ "id": "desert_oasis", "name": "Desert Oasis", "category": "desert", ... }],
  "categories": ["desert", "mountain", ...],
  "count": 16
}
```

### GET /api/templates/{id}

Get template details including its commands or actions.

### POST /api/templates/{id}/apply

Apply a template. Accepts optional `seed` and `biome` in body. Returns same shape as `/api/generate`.

---

## Multi-Agent (experimental)

### POST /api/design/multi-agent

Runs an AG2-based artist/critic/judge workflow. Slower but aims for higher quality.

```json
// Request
{ "command": "design a complex mountain valley system", "max_rounds": 6 }

// Response
{ "ok": true, "state": {...}, "assets": {...} }
```

---

## MCP (Model Context Protocol)

### GET /api/mcp

Server info and capabilities.

### GET /api/mcp/tools

List available tools. Optional `category` query param.

### GET /api/mcp/tools/{name}

Tool schema (parameters, description).

### POST /api/mcp/tools/{name}/call

Execute a tool. Body: `{ "arguments": {...} }`. Returns execution result with updated state and assets.

### GET /api/mcp/resources

List resources (current state, assets, templates).

### GET /api/mcp/resources/{uri}

Fetch a resource by URI (`state://current`, `asset://filename`, `template://id`).

### GET /api/mcp/prompts

List prompt templates.

### GET /api/mcp/prompts/{name}

Get a prompt template with its message content.

---

## Status

### GET /api/status

```json
{
  "ok": true,
  "cerebras_api_key_configured": true,
  "llm_parser_available": true,
  "server_ready": true
}
```

---

## Static assets

### GET /assets/*

Serves generated PNGs, OBJ meshes, and BIN files from `web/public/assets/`.
