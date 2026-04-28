# Semantic Layer

LLM-powered natural language understanding for terrain commands.

## Components

- `parser.py` -- `SemanticParser`: LLM parsing with scene context
- `react_agent_v2.py` -- ReAct reasoning agent with tool calling
- `narrative/` -- story-driven generation (archetypes, composition, aesthetic goals)
- `scene/` -- scene graph (entity management, reference resolution, spatial queries)
- `evaluation/` -- quality metrics (feature metrics, texture metrics, rubrics)
- `llm/` -- provider-agnostic LLM clients (Cerebras, Together, Gemini)
- `tools/` -- tool functions for ReAct agent (query, spatial, quality)
- `tool_registry.py` -- MCP-style tool schema registry

## LLM setup

Set `CEREBRAS_API_KEY` in `server/.env`. Without it, the system falls back to regex parsing. Supports `TOGETHER_API_KEY` and `GEMINI_API_KEY` as alternatives via the `LLM_PROVIDER` env var.
