# Usage Examples

Comprehensive examples of using the Semantic Terrain system.

---

## Basic Terrain Generation

### Simple Commands

```
create a desert with rolling dunes
add a mountain on the left
add three hills on the right
create a valley in the center
```

### Complex Compositions

```
create a desert biome
add a large mountain in the top-left
add a large mountain in the top-right
add a mountain pass between the two mountains
add a deep valley in the center
add three hills scattered in the bottom half
```

---

## Modifying Existing Features

### Reference-Based Modifications

```
make the mountain taller
make the valley deeper
remove the first hill
make the dunes wider
```

### Spatial References

```
add a hill next to the dunes
make the mountains taller
add a valley between the mountains
```

---

## Narrative-Driven Generation

### Aesthetic Goals

```
create a dramatic mountain landscape
design a balanced desert with scattered dunes
build a harmonious valley system
```

### Story-Based

```
create a story of a mountain range with deep valleys
design a desert oasis with surrounding dunes
build a volcanic field with multiple craters
```

---

## Quality-Aware Generation

### Quality Requirements

```
create a desert with good texture coverage
design a balanced mountain valley system
build terrain with natural feature spacing
```

### Refinement Requests

```
create a desert and refine for better texture coverage
design a mountain landscape and improve spacing
```

---

## Walkability Zones

### Path Creation

```
add a path from the center to the top-right
add a flat clearing near the center
add mountains on the left and right of the path
```

### Trading Routes

```
create a trading route from bottom-left to top-right
add flat zones along the route
add mountains on both sides for protection
```

---

## Template Usage

### Apply Template

```bash
curl -X POST http://localhost:8001/api/templates/desert_oasis/apply \
  -H "Content-Type: application/json" \
  -d '{"text": "", "voxel": false}'
```

### List Templates

```bash
curl http://localhost:8001/api/templates
```

---

## Multi-Agent Workflow

### Design Request

```bash
curl -X POST http://localhost:8001/api/design/multi-agent \
  -H "Content-Type: application/json" \
  -d '{
    "command": "design a complex mountain valley system",
    "max_rounds": 6,
    "profile": "standard"
  }'
```

### Response

```json
{
  "ok": true,
  "actions": [
    {"kind": "add", "type": "mountain", ...},
    {"kind": "add", "type": "valley", ...}
  ],
  "quality_info": {
    "overall_score": 8.5,
    "composition_score": 9.0,
    "texture_score": 8.0
  }
}
```

---

## API Usage Examples

### Generate Terrain

```python
import requests

response = requests.post(
    "http://localhost:8001/api/generate",
    json={
        "text": "create a desert with rolling dunes",
        "voxel": False
    }
)

result = response.json()
print(f"Heightmap: {result['assets']['heightmap']}")
print(f"Splatmap: {result['assets']['splatmap']}")
```

### Modify Terrain

```python
response = requests.post(
    "http://localhost:8001/api/modify",
    json={
        "text": "make the dunes taller",
        "voxel": False
    }
)
```

### Get State

```python
response = requests.get("http://localhost:8001/api/state")
state = response.json()
print(f"Features: {len(state['features'])}")
```

### Reset Terrain

```python
response = requests.post(
    "http://localhost:8001/api/reset",
    json={"text": "", "voxel": False}
)
```

---

## Frontend Integration

### React Example

```typescript
import { generateTerrain } from './api';

async function handleGenerate() {
  const result = await generateTerrain({
    text: "create a desert with rolling dunes",
    voxel: false
  });
  
  // Update 3D viewer with new terrain
  updateViewer(result.assets.heightmap, result.assets.splatmap);
}
```

---

## Advanced Examples

### Iterative Refinement

```python
# Generate initial terrain
response = requests.post(
    "http://localhost:8001/api/generate",
    json={"text": "create a desert", "voxel": False}
)

# Refine for better quality
response = requests.post(
    "http://localhost:8001/api/design/multi-agent",
    json={
        "command": "improve texture coverage",
        "max_rounds": 3
    }
)
```

### Template with Modifications

```python
# Apply template
response = requests.post(
    "http://localhost:8001/api/templates/desert_oasis/apply",
    json={"text": "", "voxel": False}
)

# Modify template result
response = requests.post(
    "http://localhost:8001/api/modify",
    json={"text": "add more dunes", "voxel": False}
)
```

---

## Command Patterns

### Feature Addition

```
add [count] [type] [position] [modifiers]
```

Examples:
- `add two mountains on the left`
- `add three hills scattered on the right`
- `add a large valley in the center`

### Feature Modification

```
make [reference] [modifier]
```

Examples:
- `make the mountain taller`
- `make the valley deeper`
- `make the dunes wider`

### Feature Removal

```
remove [reference]
```

Examples:
- `remove the first hill`
- `remove the mountains`
- `remove the dunes`

### Spatial Queries

```
find [what] [where]
what's [where]
```

Examples:
- `find features near the dunes`
- `what's in the center?`
- `find mountains on the left`

---

See also:
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Parsing Strategies](PARSING_STRATEGIES.md) - How commands are parsed
- [Architecture](ARCHITECTURE.md) - System architecture

