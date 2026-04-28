# Testing

## Running tests

```bash
cd server

# All tests
uv run pytest tests/ -v

# By layer
uv run pytest tests/core/ -v
uv run pytest tests/domain/ -v
uv run pytest tests/engine/ -v
uv run pytest tests/features/ -v
uv run pytest tests/semantic/ -v
uv run pytest tests/integration/ -v

# Single file
uv run pytest tests/semantic/test_evaluation.py -v

# Skip tests that need API keys
uv run pytest tests/ -k "not multi_agent and not rubric_evolution"
```

## Test layout

### `server/tests/` -- pytest suite

| Directory | What it tests |
|-----------|--------------|
| `tests/core/` | Geometry utilities, position calculations |
| `tests/domain/` | `Feature`, `Position`, `FeatureParameters` dataclasses |
| `tests/engine/` | `FeatureRegistry` bridge, typed feature creation, renderers (experimental) |
| `tests/features/` | Feature base class, mountain-specific tests |
| `tests/semantic/` | Narrative generation, evaluation, ReAct agent, context helpers, tools, multi-agent |
| `tests/integration/` | End-to-end flow, narrative flow, API endpoints |

### `server/tools/` -- manual scripts

Standalone scripts for testing workflows that need API keys or manual inspection. Run with `uv run python tools/<script>.py` from the `server/` directory.

Notable scripts:
- `test_phase1_phase2_fixes.py` -- validates quality evaluation pipeline, exports sample images
- `test_quality_refinement.py` -- iterative refinement workflow
- `test_narrative_react_integration.py` -- narrative + ReAct agent together
- `test_full_workflow.py` -- complete ReAct workflow with quality logging
- `test_multi_agent_simple.py` -- multi-agent design workflow (needs API key)

## What's well-tested

- Narrative pipeline (generation, archetypes, composition)
- Feature metrics and quality evaluation
- Context helpers (scene summarization, goal inference)
- Domain models and geometry
- Feature registry bridge

## What needs API keys

Tests in `tests/semantic/test_react_integration.py`, `test_multi_agent_service.py`, and most `tools/` scripts require a valid LLM API key in `server/.env`. They'll fail with `ValueError` or API errors if the key is missing.

## What's experimental

- `tests/engine/test_renderers.py` -- tests `RendererRegistry` which isn't used in production
- `tests/integration/test_api_multi_agent.py` -- multi-agent endpoint has edge cases
- `tools/test_rubric_evolution.py` -- requires `google-genai` package
