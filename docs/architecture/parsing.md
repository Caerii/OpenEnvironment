# Parsing Strategies

Commands go through a cascade. The first strategy that succeeds wins.

## Cascade order

```python
# orchestration.py :: parse_command_to_actions()
1. Direct actions      -- pre-structured JSON passed via API (skips parsing)
2. Narrative pipeline  -- default for most commands
3. SemanticParser      -- LLM + scene graph context (fallback if narrative fails)
4. CommandParser       -- regex-based (fallback if no API key)
```

The multi-agent workflow is a separate endpoint (`/api/design/multi-agent`), not part of the cascade.

## 1. Narrative pipeline (default)

**Files:** `semantic/narrative/`

Turns a command into a story, then into terrain.

1. **Archetype matching** -- classifies command as desert, mountain, valley, etc.
2. **Narrative generation** -- creates a `TerrainNarrative` with mood, story, aesthetic goals
3. **Composition** -- generates focal point + supporting + accent features with positions
4. **Action conversion** -- converts composition to action dicts
5. **Quality check** -- computes feature metrics and aesthetic quality score

Best for: creative commands ("dramatic mountain landscape", "balanced desert with scattered dunes").

## 2. SemanticParser

**File:** `semantic/parser.py`

Uses an LLM (Cerebras/Together/Gemini) to parse the command with full scene context.

- Receives current scene graph state so it can resolve references ("the dunes", "near the mountains")
- Can invoke the ReAct agent (V2) for multi-step reasoning when `use_react=True`
- Returns structured action dicts

Best for: commands that reference existing features or need spatial reasoning.

## 3. Regex fallback (CommandParser)

**File:** `parsing.py`

Pattern-matching parser. No LLM required.

- Extracts feature types, counts, positions, modifiers from text
- Handles "add two mountains on the left", "remove the valley", etc.
- Limited: no reference resolution, no spatial reasoning, no aesthetic goals

Best for: simple commands when no API key is available.

## Comparison

| | Needs LLM | Reference resolution | Quality eval | Complexity |
|---|---|---|---|---|
| Narrative | Yes | Via scene graph | Yes | High |
| SemanticParser | Yes | Yes (scene context) | No | Medium |
| Regex | No | No | No | Low |
