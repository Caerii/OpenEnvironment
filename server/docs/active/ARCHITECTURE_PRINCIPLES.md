# Terrain Engine Architecture Principles

## Core Principles

### 1. **Feature as First-Class Citizen**

Features are not dictionaries or strings—they are **objects with behavior**.

✅ **Good:**
```python
class MountainFeature(Feature):
    def generate_stamp(self, terrain, seed):
        return generate_mountain(...)
    
    def get_blending_mode(self):
        return BlendingMode.MAX
```

❌ **Bad:**
```python
if ftype == "mountain":
    # logic here
```

### 2. **Separation of Concerns**

- **Primitives**: Generate stamps (pure functions)
- **Features**: Encapsulate behavior (classes)
- **Engine**: Blend stamps (stateless)
- **Orchestrator**: Coordinate (thin layer)

### 3. **Configuration over Code**

Magic numbers should be in configuration, not code.

✅ **Good:**
```python
config.mountains.default_height = 0.75
config.mountains.height_variation = 0.15
```

❌ **Bad:**
```python
height = 0.75  # Hardcoded!
```

### 4. **Single Source of Truth**

Feature parameters come from **one place** (config or feature class), not scattered.

### 5. **Deterministic by Default**

Same seed + same state = same result. Always.

### 6. **Fail Fast**

Validate inputs early, fail loudly with clear errors.

### 7. **Extensibility First**

Design for adding features without modifying core code.

---

## Design Patterns Required

### Strategy Pattern
- Feature types as strategies
- Enables polymorphism
- Easy to add new types

### Factory Pattern
- Centralized feature creation
- Consistent initialization
- Type safety

### Builder Pattern
- Fluent feature configuration
- Validation during construction
- Clear parameter defaults

### Registry Pattern
- Feature type registration
- Plugin system
- Dynamic feature loading

---

## Architecture Layers

```
┌─────────────────────────────────────┐
│   API Layer (main.py)               │
│   - HTTP endpoints                  │
│   - Request/response                 │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Orchestrator (terrain.py)         │
│   - Coordinates systems              │
│   - Thin, declarative                │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Feature System                    │
│   - Feature classes                  │
│   - Feature registry                 │
│   - Feature factory                  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Engine Layer                      │
│   - Blending engine                  │
│   - Splatmap generator               │
│   - Spatial resolver                 │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Primitives Layer                  │
│   - Stamp generators                 │
│   - Pure functions                   │
└─────────────────────────────────────┘
```

---

## State Management Principles

1. **Immutable State**: Never mutate state directly
2. **Versioned Schema**: State has version numbers
3. **Validation**: Validate on load/save
4. **Migration**: Support schema evolution
5. **Serialization**: Clean, readable format

---

## Performance Principles

1. **Single Pass**: Never rebuild twice
2. **Cache Aggressively**: Base terrain, stamps, etc.
3. **Vectorize**: Use NumPy operations
4. **Lazy Evaluation**: Compute only what's needed
5. **Incremental Updates**: Only rebuild what changed

---

## Aesthetic Principles

1. **Variation**: ±15% randomness by default
2. **Natural Spacing**: Poisson disk, not grids
3. **Proportional**: Features relate to each other
4. **Smooth Blending**: 40px+ feathering
5. **Context Aware**: Features adapt to surroundings

---

## Error Handling Principles

1. **Fail Fast**: Validate early
2. **Clear Messages**: Tell user what went wrong
3. **Graceful Degradation**: Fallback when possible
4. **Logging**: Comprehensive logs for debugging
5. **Recovery**: Undo on error if possible

---

## Testing Principles

1. **Unit Tests**: Test features in isolation
2. **Integration Tests**: Test system integration
3. **Property Tests**: Test invariants (determinism, etc.)
4. **Performance Tests**: Benchmark critical paths
5. **Visual Tests**: Compare generated terrains

---

## Documentation Principles

1. **API Docs**: Every public function documented
2. **Architecture Docs**: System design explained
3. **Examples**: Working code examples
4. **Migration Guides**: How to upgrade
5. **Troubleshooting**: Common issues and fixes

---

## Versioning Principles

1. **Semantic Versioning**: MAJOR.MINOR.PATCH
2. **Breaking Changes**: New major version
3. **Deprecation**: Warn before removing
4. **Migration Tools**: Help users upgrade
5. **Backward Compatibility**: Support old formats

---

## Security Principles

1. **Input Validation**: Validate all inputs
2. **Bounds Checking**: Prevent array overflows
3. **Resource Limits**: Prevent DoS
4. **Sanitization**: Clean user input
5. **Principle of Least Privilege**: Minimal permissions

---

## Extensibility Checklist

When adding a new feature type, you should only need to:

- [ ] Create feature class (e.g., `CanyonFeature`)
- [ ] Create primitive function (e.g., `generate_canyon`)
- [ ] Register in FeatureRegistry
- [ ] Add to parser schema
- [ ] Add config defaults

**You should NOT need to:**
- ❌ Modify orchestrator
- ❌ Add if/elif chains
- ❌ Change core logic
- ❌ Break existing features

---

## Code Quality Metrics

### Complexity
- Cyclomatic complexity < 10 per function
- Max nesting depth: 3
- Function length: < 50 lines

### Test Coverage
- Unit tests: > 80%
- Integration tests: > 60%
- Critical paths: 100%

### Performance
- Generation time: < 1 second (512×512)
- Memory usage: < 100MB
- Cache hit rate: > 80%

### Maintainability
- Code duplication: < 5%
- Magic numbers: 0 (all in config)
- Documentation coverage: > 90%

---

## Future-Proofing Checklist

- [ ] Can add features without modifying core?
- [ ] Can change algorithms without breaking API?
- [ ] Can optimize performance without changing behavior?
- [ ] Can extend functionality via plugins?
- [ ] Can handle 10x more features?
- [ ] Can support different terrain sizes?
- [ ] Can support different biomes?
- [ ] Can support different output formats?

---

## Red Flags (Anti-Patterns)

❌ **If/elif chains longer than 3**
❌ **Magic numbers in code**
❌ **Functions longer than 50 lines**
❌ **Multiple rebuilds**
❌ **No validation**
❌ **No error handling**
❌ **Hardcoded paths**
❌ **Global state**
❌ **Tight coupling**
❌ **No tests**

---

## Green Flags (Good Patterns)

✅ **Feature registry**
✅ **Configuration system**
✅ **Validation everywhere**
✅ **Clear error messages**
✅ **Comprehensive tests**
✅ **Single responsibility**
✅ **Dependency injection**
✅ **Interface-based design**
✅ **Documentation**
✅ **Performance monitoring**

---

This document defines the **principles** that guide architectural decisions. Refer to `ARCHITECTURAL_CRITIQUE.md` for specific issues and fixes.

