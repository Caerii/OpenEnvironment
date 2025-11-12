# Testing Guide

**Last Updated:** November 11, 2025

This document describes the test suite for Semantic Terrain, including what each test covers and how to run them.

**⚠️ Important:** Some tests may not work for various reasons (missing API keys, optional dependencies, import context issues, experimental features). See [Tests That May Not Work](#⚠️-tests-that-may-not-work) section below for details.

---

## 📋 Test Organization

The test suite is organized into two main directories:

### 1. **`server/tests/`** - Unit & Integration Tests
Structured test suite using pytest, organized by component:
- `tests/core/` - Core utilities (geometry, positioning)
- `tests/domain/` - Domain models (Feature, Position, etc.)
- `tests/engine/` - Engine components (renderers, feature registry)
- `tests/features/` - Feature implementations (mountains, base features)
- `tests/semantic/` - Semantic layer (narrative, ReAct, evaluation, context)
- `tests/integration/` - End-to-end integration tests

### 2. **`server/tools/`** - Manual Test Scripts
Standalone test scripts for specific features and workflows:
- Phase 1 & Phase 2 fixes validation
- Quality evaluation and refinement
- Multi-agent workflow testing
- Rubric evolution testing
- Full workflow integration tests

---

## 🧪 Test Categories

### Unit Tests

#### **Core Utilities** (`tests/core/`)
- **`test_geometry.py`** - Geometry utilities
  - Position calculations
  - Region definitions (center, left, right, etc.)
  - Circle/radius calculations
  - Geometry integration tests

#### **Domain Models** (`tests/domain/`)
- **`test_models.py`** - Domain model validation
  - `Position` model (absolute, region-based, relative)
  - `FeatureParameters` validation
  - `Feature` dataclass (typed features)
  - `TerrainState` serialization

#### **Engine Components** (`tests/engine/`)
- **`test_renderers.py`** - Feature renderer system ⚠️ **Experimental**
  - RendererRegistry registration
  - Mountain, Valley, Dunes, Cliff, Plateau, Canyon renderers
  - BlendingMode correctness
  - Parameter handling
  - **Note:** Tests experimental `RendererRegistry`, production uses `FeatureRegistry`

- **`test_feature_registry_bridge.py`** - Feature registry bridge
  - Bridge between dict-based and typed features
  - Backward compatibility
  - Feature creation and conversion

- **`test_create_feature_typed.py`** - Typed feature creation
  - Creating typed `Feature` instances
  - Stamp generation with typed features

#### **Feature Implementations** (`tests/features/`)
- **`test_feature_base.py`** - Base feature functionality
  - Feature type validation
  - Feature identity and uniqueness
  - Feature geometry calculations
  - Feature appearance properties
  - Feature ABC (abstract base class)
  - Feature integration tests

- **`test_mountain.py`** - Mountain feature specific tests
  - Mountain parameter validation
  - Mountain generation and stamping

#### **Semantic Layer** (`tests/semantic/`)

- **`test_narrative_generation.py`** - Narrative-driven generation
  - Narrative → typed Feature pipeline
  - Focal point, supporting, and accent features
  - Narrative composition validation

- **`test_narrative_generation_simple.py`** - Simplified narrative tests
  - Basic narrative extraction
  - Simple narrative → features

- **`test_narrative_tool.py`** - Narrative tool for ReAct agent
  - Tool integration
  - Narrative extraction from commands

- **`test_parse_command_to_actions_narrative.py`** - Narrative pipeline parsing
  - Verifies narrative pipeline is default for aesthetic commands
  - Command → actions via narrative pipeline

- **`test_context_helpers.py`** - Context helper functions
  - Scene summarization (empty, with features)
  - Recent actions summarization
  - Aesthetic goal inference from commands
  - Aesthetic goal inference from metadata

- **`test_evaluation.py`** - Quality evaluation system
  - Feature metrics calculation (spacing, distribution, hierarchy)
  - Aesthetic quality scoring
  - Texture metrics and rubric evaluation

- **`test_react_integration.py`** - ReAct agent integration
  - Tool schema validation
  - ReAct agent initialization and execution
  - Tool calling and reasoning

- **`test_react_prompts.py`** - ReAct prompt building
  - System prompt context injection
  - User prompt with feature counts

- **`test_tools_basic.py`** - Basic tool functionality
  - Query tools (scene queries, spatial queries)
  - Spatial tools (find features, spatial constraints)

- **`test_multi_agent_service.py`** - Multi-agent service
  - Design workflow execution
  - Action application
  - Error handling

- **`test_multi_agent_tools.py`** - Multi-agent tools
  - Scene preview rendering
  - Scene action evaluation
  - Scene plan visual scoring

### Integration Tests

#### **`tests/integration/`**

- **`test_end_to_end_flow.py`** - Complete pipeline tests
  - Simple command → terrain generation
  - Feature creation (dict-based, not typed)
  - Narrative integration
  - Type system gaps identification

- **`test_narrative_flow.py`** - Narrative pipeline flow
  - End-to-end narrative generation
  - Narrative → actions → terrain

- **`test_api_narrative_flow.py`** - API endpoint narrative flow
  - `/api/generate` endpoint uses narrative pipeline
  - FastAPI TestClient integration

- **`test_api_multi_agent.py`** - Multi-agent API endpoint
  - `/api/design/multi-agent` endpoint testing
  - Multi-agent workflow via API

---

## 🔧 Manual Test Scripts (`server/tools/`)

These are standalone scripts for testing specific features and workflows:

### Phase 1 & Phase 2 Fixes
- **`test_phase1_phase2_fixes.py`** - Systematic validation of Phase 1 & 2 fixes
  - **Phase 1 Tests:**
    - Archetype matching (feature combinations)
    - Context rubric uses archetype + goals
    - Refinement priority (texture first)
  - **Phase 2 Tests:**
    - Texture-to-feature mapping
    - Parameter modification
    - Integration refinement using new tools
  - **Output:** Exports terrain textures to `sample_images/` folder
  - **Results:** Saves JSON results to `logs/test_phase1_phase2_results.json`

### Quality Evaluation
- **`test_quality_direct.py`** - Direct quality evaluation testing
  - Quality metrics calculation
  - Rubric evaluation

- **`test_quality_refinement.py`** - Quality refinement system
  - Iterative refinement workflow
  - Parameter adjustment based on quality feedback

- **`test_quality_logging.py`** - Quality logging and tracking
  - Quality history logging
  - Quality progression tracking

### Narrative & ReAct Integration
- **`test_narrative_react_integration.py`** - Narrative + ReAct agent integration
  - Narrative extraction from commands
  - Spatial tool constraints
  - Quality evaluation with narrative
  - Full ReAct flow with narrative

- **`test_comprehensive_narrative_react.py`** - Comprehensive narrative/ReAct tests
  - Narrative extraction edge cases
  - Spatial constraints edge cases
  - Quality iterative refinement
  - Long-run quality progression
  - Archetype coverage

- **`test_full_workflow.py`** - Full ReAct workflow test
  - Complete ReAct agent workflow
  - Quality refinement and logging

### Multi-Agent Workflow
- **`test_multi_agent_simple.py`** - Simple multi-agent workflow test
  - Basic multi-agent design workflow
  - Action generation and application

### Rubric Evolution
- **`test_rubric_evolution.py`** - Rubric evolution system ⚠️ **Experimental**
  - Context rubric generation
  - Rubric evolution from terrain analysis
  - **Requires:** `google-genai` package and Gemini API key

- **`test_rubric_evolution_real_data.py`** - Rubric evolution with real data
  - Context rubrics integration
  - Rubric evolution from real terrain data
  - **Requires:** `google-genai` package and Gemini API key

### Context & Rubric Impact
- **`test_context_rubric_impact.py`** - Context rubric impact testing
  - How context rubrics affect quality evaluation
  - Rubric adaptation based on context

### Module Refactoring
- **`test_refactored_modules.py`** - Refactored module validation
  - Import validation
  - Config module testing
  - State initializer testing
  - Warning types validation
  - Archetype matcher testing
  - Quality tools integration
  - Narrative pipeline integration

---

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies (from server/ directory)
cd server
uv sync --all-extras  # Includes pytest and dev dependencies
```

### Run All Tests
```bash
# From server/ directory using uv
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=server --cov-report=html

# Alternative: If pytest is installed globally
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/core/ tests/domain/ tests/engine/ tests/features/ -v

# Semantic layer tests
uv run pytest tests/semantic/ -v

# Integration tests
uv run pytest tests/integration/ -v

# Specific test file
uv run pytest tests/semantic/test_narrative_generation.py -v

# Specific test class or function
uv run pytest tests/semantic/test_narrative_generation.py::TestGenerateFromNarrative -v
uv run pytest tests/semantic/test_narrative_generation.py::TestGenerateFromNarrative::test_generates_typed_features -v
```

### Run Manual Test Scripts
```bash
# From server/ directory using uv
cd server

# Phase 1 & 2 fixes
uv run python tools/test_phase1_phase2_fixes.py

# Quality evaluation
uv run python tools/test_quality_direct.py
uv run python tools/test_quality_refinement.py

# Narrative/ReAct integration
uv run python tools/test_narrative_react_integration.py
uv run python tools/test_comprehensive_narrative_react.py

# Full workflow
uv run python tools/test_full_workflow.py

# Multi-agent (requires API keys)
uv run python tools/test_multi_agent_simple.py

# Rubric evolution (requires Gemini API key)
uv run python tools/test_rubric_evolution.py
uv run python tools/test_rubric_evolution_real_data.py

# Alternative: If running from tools/ directory
cd tools
uv run python test_phase1_phase2_fixes.py
```

---

## 📊 Test Coverage

### Production Features (Well Tested)
- ✅ Narrative pipeline - Comprehensive tests
- ✅ Feature generation - Unit and integration tests
- ✅ Quality evaluation - Direct and refinement tests
- ✅ Context helpers - Unit tests
- ✅ Domain models - Type validation tests
- ✅ Geometry utilities - Core tests

### Experimental Features (Partially Tested)
- ⚠️ RendererRegistry - Tests exist but system not in production
- ⚠️ Multi-agent workflow - Tests exist but has edge cases
- ⚠️ Rubric evolution - Tests exist but requires optional dependency
- ⚠️ ReAct agent - Integration tests exist but experimental

### Missing Tests
- ❌ Configuration system - No tests (system exists but not used)
- ❌ Slope erosion - No tests (function exists but never called)
- ❌ Asset cleanup - No tests
- ❌ State lock - No tests (critical but untested)
- ❌ Bootstrap system - No tests

---

## ⚠️ Tests That May Not Work

**Important:** Some tests may fail or not work for various reasons. This is expected and documented below.

### Tests That May Fail

#### Import Context Issues
- **Affected:** Narrative tool tests, some integration tests
- **Reason:** Tests run in different import context than production
- **Symptoms:** `ImportError`, `ModuleNotFoundError`, or import-related failures
- **Workaround:** 
  - Use `uv run` to ensure proper environment
  - Run from repo root with `PYTHONPATH` set
  - Use `server.bootstrap.ensure_bootstrapped()` in test setup

#### Missing API Keys
- **Affected:** Tests requiring LLM API keys
  - `test_multi_agent_simple.py`
  - `test_rubric_evolution.py`
  - `test_rubric_evolution_real_data.py`
  - `test_full_workflow.py`
  - `test_narrative_react_integration.py`
  - `test_comprehensive_narrative_react.py`
- **Reason:** Tests require valid API keys in `.env` file
- **Symptoms:** `ValueError`, `APIError`, or "Failed to create LLM client" messages
- **Workaround:** 
  - Add required API keys to `server/.env`
  - See [ENV_TEMPLATE.md](../ENV_TEMPLATE.md) for required keys
  - Skip tests if API keys unavailable: `uv run pytest tests/ -k "not multi_agent"`

#### Missing Optional Dependencies
- **Affected:** Rubric evolution tests
- **Reason:** Requires `google-genai` package (optional dependency)
- **Symptoms:** `ImportError: No module named 'google.genai'`
- **Workaround:** 
  - Install: `uv add google-genai`
  - Or skip: `uv run pytest tests/ -k "not rubric_evolution"`

#### Experimental Feature Tests
- **Affected:** 
  - `test_renderers.py` - Tests `RendererRegistry` (experimental, not in production)
  - `test_api_multi_agent.py` - Tests experimental multi-agent endpoint
- **Reason:** Tests cover experimental features with edge cases
- **Symptoms:** Tests may pass but features not used in production
- **Note:** These tests validate experimental code, not production pipeline

#### Environment-Specific Issues
- **Affected:** File I/O tests, path-dependent tests
- **Reason:** Different file systems, path separators (Windows vs Unix)
- **Symptoms:** `FileNotFoundError`, path-related errors
- **Workaround:** 
  - Use `tmp_path` fixtures where available
  - Check path separators in test code
  - Run from correct directory

#### Flaky/Non-Deterministic Tests
- **Affected:** Some integration tests with LLM calls
- **Reason:** LLM responses may vary, timing issues
- **Symptoms:** Intermittent failures, different results on rerun
- **Workaround:** 
  - Rerun failed tests
  - Use fixed seeds where available
  - Mock LLM calls in unit tests

### How to Handle Failing Tests

1. **Check if test is expected to fail:**
   - Review this section for known issues
   - Check test file comments for requirements
   - Verify environment setup (API keys, dependencies)

2. **Skip problematic tests:**
   ```bash
   # Skip tests requiring API keys
   uv run pytest tests/ -k "not multi_agent and not rubric_evolution"
   
   # Skip specific test file
   uv run pytest tests/ --ignore=tests/semantic/test_multi_agent_service.py
   ```

3. **Run only working tests:**
   ```bash
   # Run only unit tests (less likely to have issues)
   uv run pytest tests/core/ tests/domain/ tests/engine/ tests/features/ -v
   
   # Run only semantic tests without LLM dependencies
   uv run pytest tests/semantic/test_context_helpers.py tests/semantic/test_evaluation.py -v
   ```

4. **Report issues:**
   - If test failure is unexpected, check code comments
   - Verify against actual code (source of truth)
   - Some tests may be outdated - code takes precedence

---

## 📝 Writing New Tests

### Test Structure
```python
"""Test description."""
import pytest
from server.module import Function

class TestFeature:
    """Test class description."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = Function()
        assert result is not None
    
    def test_edge_case(self):
        """Test edge case."""
        with pytest.raises(ValueError):
            Function(invalid_input)
```

### Test Organization
- **Unit tests:** One test file per module
- **Integration tests:** Test complete workflows
- **Manual scripts:** For complex workflows requiring manual inspection

### Best Practices
1. **Use descriptive test names** - `test_feature_does_x_when_y`
2. **Test one thing per test** - Single assertion focus
3. **Use fixtures** - For common setup/teardown
4. **Mock external dependencies** - LLM calls, file I/O
5. **Test edge cases** - Empty inputs, invalid inputs, boundary conditions

---

## 🔗 Related Documentation

- **[Development Guide](DEVELOPMENT.md)** - Development setup and guidelines
- **[Architecture](ARCHITECTURE.md)** - System architecture and components
- **[Undocumented Features](UNDOCUMENTED_FEATURES.md)** - Experimental features and broken integrations

---

## 📈 Test Statistics

**Total Test Files:** ~38 test files
- **Unit Tests:** ~25 files
- **Integration Tests:** ~4 files
- **Manual Test Scripts:** ~13 files

**Test Categories:**
- Core utilities: 1 file
- Domain models: 1 file
- Engine components: 3 files
- Features: 2 files
- Semantic layer: 12 files
- Integration: 4 files
- Manual scripts: 13 files

---

*For questions or issues with tests, check the code comments in test files or refer to the actual implementation in the codebase (source of truth).*

