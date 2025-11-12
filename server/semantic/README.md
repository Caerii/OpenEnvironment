# Semantic Terrain - LLM Integration

This module provides intelligent natural language understanding for terrain generation commands using Cerebras/Qwen-3-Coder.

## Setup

1. Add your Cerebras API key to `server/.env`:
   ```
   CEREBRAS_API_KEY=your_api_key_here
   ```

2. Install dependencies:
   ```bash
   cd server
   uv sync
   ```

## Architecture

- **`semantic/parser.py`** - `SemanticParser` class using Cerebras SDK
  - Uses Qwen-3-Coder-480B model for structured JSON output
  - Falls back to regex parser if LLM unavailable
  - Handles multiple actions in a single command
  - Extracts percentages, coordinates, and complex modifiers

## Integration

The parser is automatically used in `terrain.py` via `apply_actions()`:
- Tries semantic parser first
- Falls back to regex parser on error
- Processes all actions from LLM response (not just first)

## Features

- **Multi-action parsing**: "add two mountains and a valley" → 2 separate actions
- **Percentage extraction**: "50% taller" → `height_percent: 50`
- **Context awareness**: "the mountain" refers to most recent mountain
- **Robust fallback**: Works even if API key missing or LLM fails

