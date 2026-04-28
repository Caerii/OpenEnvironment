# Examples

## Natural language commands

### Adding features

```
create a desert with rolling dunes and two mountains on the left
add a valley in the center
add three hills scattered on the right
add a cliff on the top edge
```

### Modifying features

```
make the mountain taller
make the valley deeper
make the dunes wider
```

### Removing features

```
remove the first hill
remove the dunes
```

### Spatial references

```
add a hill next to the dunes
add a valley between the mountains
add a mesa north of the crater
```

### Narrative / aesthetic commands

These trigger the narrative pipeline for richer composition:

```
create a dramatic mountain landscape
design a balanced desert with scattered dunes
build a volcanic field with multiple craters
```

## Command anatomy

```
[action] [count] [type] [position] [modifiers]
```

- **action**: add, remove, make/modify
- **count**: one, two, three, ... or a number
- **type**: mountain, hill, valley, dunes, cliff, mesa, canyon, ridge, volcano, crater, basin, plateau, mound, pinnacle, spur, terraces, ravine, pass, slope, flat_zone, path, clearing
- **position**: left, right, center, top, bottom, top-left, top-right, bottom-left, bottom-right, or `at (x, y)`
- **modifiers**: taller, deeper, wider, or percentage ("50% taller")

## API usage

### Python

```python
import requests

# Generate
r = requests.post("http://localhost:8001/api/generate", json={
    "text": "create a desert with rolling dunes",
    "seed": 42
})
data = r.json()
print(data["assets"]["height8"])  # /assets/height8_xxx.png

# Modify
requests.post("http://localhost:8001/api/modify", json={
    "text": "add two mountains on the left"
})

# Reset
requests.post("http://localhost:8001/api/reset", json={"seed": 99})

# Apply template
requests.post("http://localhost:8001/api/templates/desert_oasis/apply")
```

### curl

```bash
# Generate
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "create a mountain range with deep valleys"}'

# List templates
curl http://localhost:8001/api/templates

# Check status
curl http://localhost:8001/api/status
```
