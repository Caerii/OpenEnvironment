# Development Guide

Guide for developers working on the Semantic Terrain system.

---

## Project Structure

```
SemanticTerrain/
├── server/                 # Backend (FastAPI)
│   ├── api/               # API controllers
│   │   └── controllers/  # Route handlers
│   ├── core/              # Core utilities
│   ├── domain/            # Domain models
│   ├── engine/            # Terrain generation engine
│   │   ├── builder.py     # TerrainBuilder
│   │   ├── commands.py    # Command pattern
│   │   ├── feature_registry.py  # Feature registry
│   │   ├── stamping.py    # Feature stamping
│   │   ├── splatmap.py    # Texture generation
│   │   └── templates.py   # Template system
│   ├── primitives/         # Terrain feature generators
│   ├── semantic/          # Semantic layer
│   │   ├── narrative/     # Narrative pipeline
│   │   ├── llm/           # LLM clients
│   │   ├── tools/         # Tool functions
│   │   ├── scene/         # Scene graph
│   │   ├── evaluation.py  # Quality evaluation
│   │   └── parser.py      # SemanticParser
│   ├── services/          # Business logic services
│   ├── main.py           # FastAPI app
│   ├── orchestration.py  # Command orchestration
│   └── terrain.py        # Main terrain generator
├── web/                   # Frontend (React)
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── shaders/      # GLSL shaders
│   │   └── api.ts        # API client
│   └── public/          # Static assets
└── docs/                 # Documentation (this folder)
```

---

## Adding New Features

### New Terrain Primitive

1. **Create Generator** in `server/primitives/`:
   ```python
   # server/primitives/my_feature.py
   def generate_my_feature(x, y, radius, height, seed):
       # Generate heightmap stamp
       return stamp
   ```

2. **Register in Feature Registry** (`server/engine/feature_registry.py`):
   ```python
   registry.register("my_feature", generate_my_feature, defaults={...})
   ```

3. **Add to Tool Registry** (`server/semantic/tool_registry.py`):
   ```python
   add_tool("my_feature", category=ToolCategory.GENERATION, ...)
   ```

### New API Endpoint

1. **Create Controller Method** (`server/api/controllers/terrain_controller.py`):
   ```python
   def my_endpoint(self, request: MyRequest) -> Dict:
       # Implementation
       return {"ok": True, "result": ...}
   ```

2. **Add Route** (`server/main.py`):
   ```python
   @app.post("/api/my-endpoint")
   def my_endpoint(request: MyRequest):
       return terrain_controller.my_endpoint(request)
   ```

3. **Update Frontend** (`web/src/api.ts`):
   ```typescript
   export async function myEndpoint(data: MyRequest) {
     return api.post('/api/my-endpoint', data);
   }
   ```

### New Parsing Strategy

1. **Create Parser** (`server/semantic/`):
   ```python
   class MyParser:
       def parse(self, command: str, scene_state: Dict) -> Dict:
           # Parse logic
           return {"actions": [...]}
   ```

2. **Add to Orchestration** (`server/orchestration.py`):
   ```python
   def parse_command_to_actions(...):
       # Try MyParser
       try:
           parser = MyParser()
           return parser.parse(command, state)
       except:
           # Fallback
   ```

### New Template

1. **Add Template** (`server/engine/templates.py`):
   ```python
   TEMPLATES = {
       "my_template": {
           "name": "My Template",
           "category": "custom",
           "actions": [
               {"kind": "add", "type": "mountain", ...}
           ]
       }
   }
   ```

---

## Testing

### Running Tests

```bash
# Backend tests
cd server
pytest tests/

# Specific test file
pytest tests/integration/test_end_to_end_flow.py

# With coverage
pytest --cov=server tests/
```

### Writing Tests

```python
# tests/integration/test_my_feature.py
def test_my_feature():
    # Setup
    state = {"features": [], "seed": 42}
    
    # Execute
    actions = [{"kind": "add", "type": "my_feature", ...}]
    heightmap, state, splatmap = apply_actions("", state, direct_actions=actions)
    
    # Assert
    assert heightmap is not None
    assert len(state["features"]) == 1
```

---

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Use meaningful variable names

### TypeScript

- Use TypeScript strict mode
- Follow ESLint rules
- Use meaningful variable names
- Document complex functions

---

## Debugging

### Backend Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Frontend Debugging

```typescript
// Use browser console
console.log("Debug message");
console.error("Error message");

// React DevTools for component debugging
```

---

## Performance Optimization

### Backend

- Use NumPy vectorization
- Cache expensive computations
- Profile with `cProfile`
- Optimize hot paths

### Frontend

- Use React.memo for expensive components
- Optimize shader performance
- Use Web Workers for heavy computations
- Profile with Chrome DevTools

---

## Contributing

### Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

### Pull Request Guidelines

- Clear description of changes
- Link to related issues
- Include tests
- Update documentation
- Follow code style

---

## Common Tasks

### Adding a New LLM Provider

1. **Create Client** (`server/semantic/llm/clients.py`):
   ```python
   class MyLLMClient(LLMClient):
       def chat(self, messages, ...):
           # Implementation
   ```

2. **Add to Factory** (`server/semantic/llm/__init__.py`):
   ```python
   def create_llm_client():
       if os.getenv("MY_API_KEY"):
           return MyLLMClient()
       # Fallback
   ```

### Adding a New Quality Metric

1. **Add Metric Function** (`server/semantic/evaluation.py`):
   ```python
   def compute_my_metric(features):
       # Calculate metric
       return score
   ```

2. **Add to Rubric** (`server/semantic/evaluation.py`):
   ```python
   QUALITY_RUBRIC = {
       "my_metric": {
           "weight": 0.1,
           "threshold": 0.8
       }
   }
   ```

---

## Troubleshooting

### Import Errors

- Check PYTHONPATH
- Verify virtual environment
- Check relative imports

### API Errors

- Check API key configuration
- Verify endpoint URLs
- Check CORS settings

### Generation Issues

- Check seed values
- Verify feature parameters
- Check state consistency

---

See also:
- [Architecture](ARCHITECTURE.md) - System architecture
- [API Reference](API_REFERENCE.md) - API documentation
- [SETUP.md](../SETUP.md) - Setup instructions

