# Terrain Template System

## Overview

The template system provides curated terrain environments that showcase the system's capabilities. Templates are predefined configurations that can be instantly applied to demonstrate what's possible.

Templates support **two formats**:
1. **Natural Language Commands** - Flexible, semantic parsing (e.g., "add a large mountain in the top-left")
2. **Pre-Composed JSON Actions** - Precise, deterministic, bypasses parser (e.g., `{"kind": "add", "type": "mountain", ...}`)

Both formats generate the same terrain types, but JSON actions provide exact control and deterministic results, while commands leverage the semantic parser for natural language understanding.

## Features

- **16+ curated templates** showcasing different terrain types
- **Two template formats**:
  - **Natural language commands** - Flexible, goes through semantic parser
  - **Pre-composed JSON actions** - Precise, deterministic, bypasses parser
- **Category-based organization** (mountain, desert, valley, volcanic, walkability, mixed)
- **Tag-based filtering** for easy discovery
- **RESTful API** for frontend integration
- **One-click application** - instant terrain generation

## Template Categories

### Mountain Landscapes
- **Mountain Range**: Dramatic peaks with valleys and passes
- **Alpine Landscape**: Snow-capped peaks with ridges

### Desert Landscapes
- **Desert Dunes**: Rolling sand dunes with mesas and oases
- **Desert Canyon**: Deep canyon through desert terrain

### Valley Systems
- **River Valley**: Winding valley with mountains on both sides
- **Mountain Basin**: Enclosed basin surrounded by mountains

### Volcanic Landscapes
- **Volcanic Field**: Multiple volcanoes with craters

### Walkability & Path Systems
- **Mountain Path**: Path through mountains (showcases walkability zones)
- **Trading Route**: Path connecting settlements with clearings
- **Mountain Pass**: Pass between mountains with clear path

### Mixed & Complex
- **Diverse Terrain**: Showcase of all feature types
- **Peaceful Landscape**: Gentle rolling hills
- **Dramatic Cliffs**: Steep elevation changes
- **Crater Field**: Multiple impact craters
- **Plateau Landscape**: Multiple plateaus at different elevations
- **Ridge Network**: Interconnected ridges

## API Endpoints

### List Templates
```
GET /api/templates
GET /api/templates?category=mountain
GET /api/templates?tag=dramatic
```

Response:
```json
{
  "ok": true,
  "templates": [
    {
      "id": "mountain_range",
      "name": "Mountain Range",
      "description": "A dramatic mountain range...",
      "category": "mountain",
      "tags": ["mountains", "valleys", "passes"],
      "thumbnail_hint": "Mountain range with peaks and valleys",
      "format": "commands",
      "command_count": 6
    },
    {
      "id": "mountain_range_precise",
      "name": "Mountain Range (Precise)",
      "description": "Same as Mountain Range but with pre-composed JSON actions",
      "category": "mountain",
      "tags": ["mountains", "valleys", "passes", "precise"],
      "thumbnail_hint": "Mountain range with peaks and valleys",
      "format": "actions",
      "action_count": 5
    }
  ],
  "categories": ["mountain", "desert", "valley", ...],
  "count": 18
}
```

### Get Template Details
```
GET /api/templates/{template_id}
```

Response (commands format):
```json
{
  "ok": true,
  "template": {
    "id": "mountain_range",
    "name": "Mountain Range",
    "description": "...",
    "category": "mountain",
    "tags": [...],
    "format": "commands",
    "commands": [
      "create a desert biome",
      "add a large mountain in the top-left",
      ...
    ],
    "command_count": 6
  }
}
```

Response (actions format):
```json
{
  "ok": true,
  "template": {
    "id": "mountain_range_precise",
    "name": "Mountain Range (Precise)",
    "description": "...",
    "category": "mountain",
    "tags": [...],
    "format": "actions",
    "actions": [
      {
        "kind": "add",
        "type": "mountain",
        "count": 1,
        "position": {"region": "top-left"},
        "modifiers": {"taller": true}
      },
      ...
    ],
    "action_count": 5
  }
}
```

### Apply Template
```
POST /api/templates/{template_id}/apply
```

Response:
```json
{
  "ok": true,
  "template_id": "mountain_range",
  "template_name": "Mountain Range",
  "state": {...},
  "assets": {
    "height8": "/assets/height_1234567890_8.png",
    "height16": "/assets/height_1234567890_16.png",
    "splat": "/assets/splat_1234567890.png"
  }
}
```

## Frontend Integration

### TypeScript API

```typescript
import { listTemplates, getTemplate, applyTemplate } from './api'

// List all templates
const { templates, categories } = await listTemplates()

// Filter by category
const mountainTemplates = await listTemplates('mountain')

// Filter by tag
const dramaticTemplates = await listTemplates(undefined, 'dramatic')

// Get template details
const template = await getTemplate('mountain_range')

// Apply template
const result = await applyTemplate('mountain_range')
// Result contains state and asset URLs
```

### React Component Example

```tsx
function TemplateSelector() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  
  useEffect(() => {
    listTemplates(selectedCategory || undefined).then(res => {
      setTemplates(res.templates)
    })
  }, [selectedCategory])
  
  const handleApply = async (templateId: string) => {
    const result = await applyTemplate(templateId)
    // Update terrain viewer with new assets
    updateTerrain(result.assets)
  }
  
  return (
    <div>
      <CategoryFilter 
        categories={categories}
        selected={selectedCategory}
        onChange={setSelectedCategory}
      />
      <TemplateGrid 
        templates={templates}
        onSelect={handleApply}
      />
    </div>
  )
}
```

## Template Design Principles

### 1. **Showcase Capabilities**
Each template demonstrates specific system features:
- Feature combinations
- Walkability zones
- Semantic relationships
- Visual variety

### 2. **Visual Distinctness**
Templates are visually distinct and memorable:
- Different elevation profiles
- Different feature densities
- Different spatial arrangements

### 3. **Progressive Complexity**
Templates range from simple to complex:
- **Simple**: Peaceful Landscape (5 hills)
- **Medium**: Mountain Path (path + mountains)
- **Complex**: Diverse Terrain (all features)

### 4. **Real-World Inspiration**
Templates are inspired by real terrain:
- Mountain ranges
- Desert landscapes
- Volcanic fields
- Trading routes

## Adding New Templates

Templates are defined in `server/engine/templates.py`:

### Using Natural Language Commands

```python
TerrainTemplate(
    id="my_template",
    name="My Template",
    description="A description of what this showcases",
    category="mixed",
    commands=[
        "create a desert biome",
        "add a mountain in the center",
        # ... more commands
    ],
    tags=["mountains", "dramatic"],
    thumbnail_hint="Description for thumbnail generation"
)
```

### Using Pre-Composed JSON Actions

```python
TerrainTemplate(
    id="my_template_precise",
    name="My Template (Precise)",
    description="Same template with deterministic JSON actions",
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
            "type": "hill",
            "count": 3,
            "position": {"region": "bottom", "distribution": "scattered"},
            "modifiers": {}
        }
    ],
    tags=["mountains", "dramatic", "precise"],
    thumbnail_hint="Description for thumbnail generation"
)
```

**Best Practices:**
- **Commands format**: More flexible, goes through semantic parser, can handle natural language variations
- **Actions format**: More precise and deterministic, bypasses parser, exact control over parameters
- Keep commands/actions simple and clear
- Test templates to ensure they generate correctly
- Add descriptive tags for discoverability (use "precise" tag for action-based templates)
- Choose appropriate category
- **For paths**: Use actions format with `"position": {"start": [x1, y1], "end": [x2, y2]}`

**When to use each format:**
- **Commands**: When you want natural language flexibility and semantic relationships
- **Actions**: When you need precise, deterministic generation (e.g., for testing, reproducible results)

## Template Showcase Ideas

### Future Template Ideas

1. **Island Paradise**: Hills with surrounding flat zones (beaches)
2. **Crater Lake**: Large crater with flat center (water)
3. **Mountain Fortress**: Mountains with clearings (defensible positions)
4. **Desert Oasis**: Dunes with central clearing and surrounding hills
5. **Ridge Trail**: Ridge network with path along the top
6. **Valley Settlement**: Valley with multiple clearings (settlements)
7. **Volcanic Caldera**: Large volcano with crater and surrounding terrain
8. **Terraced Hills**: Multiple terraces creating stepped landscape

## Usage Examples

### Command Line (curl)

```bash
# List all templates
curl http://localhost:8001/api/templates

# List mountain templates
curl http://localhost:8001/api/templates?category=mountain

# Get template details
curl http://localhost:8001/api/templates/mountain_range

# Apply template
curl -X POST http://localhost:8001/api/templates/mountain_range/apply
```

### Programmatic (Python)

```python
from server.engine.templates import TemplateRegistry

# List templates
templates = TemplateRegistry.get_all()

# Get template commands
commands = TemplateRegistry.apply_template("mountain_range")

# Apply commands
for cmd in commands:
    result = apply_actions(cmd, state)
```

## Benefits

1. **Showcase System**: Instantly demonstrate capabilities
2. **User Onboarding**: Help users understand what's possible
3. **Quick Start**: Get started with interesting terrain immediately
4. **Inspiration**: Show users what they can create
5. **Testing**: Test system with known-good configurations

## Integration with Walkability Zones

Several templates showcase walkability zones:
- **Mountain Path**: Path through mountains
- **Trading Route**: Path with clearings
- **Mountain Pass**: Pass between mountains

These templates demonstrate the proactive terrain design approach where paths are created first, then features are placed around them.

