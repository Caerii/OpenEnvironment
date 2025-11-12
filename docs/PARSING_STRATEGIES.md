# Parsing Strategies

The Semantic Terrain system supports multiple parsing strategies, automatically selecting the best approach based on command complexity and available resources.

---

## Strategy Selection

The system tries parsing strategies in this order:

1. **Narrative Pipeline** (Default) - Story-driven generation
2. **SemanticParser** - LLM-powered with scene graph
3. **ReAct Agent** - Tool-calling reasoning
4. **Multi-Agent Workflow** - Artist/Critic collaboration
5. **Regex Fallback** - Basic parsing without LLM

Each strategy has different capabilities and use cases.

---

## 1. Narrative Pipeline (Default)

**Purpose:** Story-driven terrain generation with aesthetic goals

### Process

1. **Archetype Matching** - Identifies terrain archetype (desert, mountain, valley, etc.)
2. **Story Generation** - Creates narrative context
3. **Composition Generation** - Generates focal, supporting, and accent features
4. **Action Conversion** - Converts composition to structured actions

### Features

- Archetype-based feature selection
- Aesthetic goals (drama, balance, harmony)
- Focal point emphasis
- Natural feature relationships
- Story-driven composition

### Example

```
Command: "create a dramatic mountain landscape"
→ Archetype: Mountain
→ Story: "A dramatic mountain range with deep valleys..."
→ Composition: 
  - Focal: Large mountain (center)
  - Supporting: 3-4 peaks (surrounding)
  - Accent: Deep valleys (between peaks)
→ Actions: [add mountain, add mountain, add valley, ...]
```

### When to Use

- Complex, artistic terrain generation
- Commands with aesthetic goals ("dramatic", "balanced", "harmonious")
- Narrative-driven requests ("create a story of...")
- Default for most commands

---

## 2. SemanticParser

**Purpose:** LLM-powered parsing with scene graph context

### Process

1. **Tool Registry** - Uses MCP-style tool registry for available features
2. **Scene Context** - Incorporates current scene graph state
3. **LLM Parsing** - Uses Cerebras/Together/Gemini for understanding
4. **Action Extraction** - Converts LLM response to structured actions

### Features

- Context-aware parsing
- Reference resolution ("the dunes" → feature IDs)
- Spatial queries ("find features near X")
- Tool-based feature discovery
- Scene graph integration

### Example

```
Command: "add two mountains next to the dunes"
→ Scene Graph: Finds "dunes" entity → Feature IDs [3, 4]
→ Spatial Resolver: Calculates positions near dunes
→ Actions: [add mountain at (x1, y1), add mountain at (x2, y2)]
```

### When to Use

- Commands with references to existing features
- Spatial relationship queries
- Complex spatial reasoning
- When narrative pipeline doesn't match

---

## 3. ReAct Agent

**Purpose:** Tool-calling reasoning agent for complex commands

### Process

1. **Reasoning Loop** - Iterative thinking and tool use
2. **Tool Calls** - Uses available tools (query, spatial, quality, etc.)
3. **Quality Evaluation** - Assesses terrain quality during reasoning
4. **Refinement** - Iteratively improves actions

### Features

- Multi-step reasoning
- Tool-based exploration
- Quality-aware generation
- Iterative refinement
- Context building through tool use

### Example

```
Command: "create a balanced desert with good texture coverage"
→ Reasoning: "I need to check texture coverage..."
→ Tool Call: analyze_texture_feature_relationship()
→ Reasoning: "I see gaps, let me adjust..."
→ Tool Call: modify_feature_parameters()
→ Actions: [refined actions with better coverage]
```

### When to Use

- Commands requiring quality evaluation
- Complex multi-step reasoning
- Quality-focused requests
- When other strategies fail

---

## 4. Multi-Agent Workflow

**Purpose:** Collaborative terrain design with multiple perspectives

### Process

1. **Artist** - Creates initial terrain plan
2. **Critic** - Evaluates plan and provides feedback
3. **Integrator** - Incorporates critique and refines
4. **Judge** - Provides final quality score

### Features

- Multiple agent perspectives
- Iterative refinement
- Quality-focused collaboration
- Visual evaluation (optional Gemini feedback)
- High-quality output

### Example

```
Command: "design a complex mountain valley system"
→ Artist: Creates initial plan with 5 features
→ Critic: "Texture coverage is low, add more features"
→ Integrator: Adds 3 more features, adjusts positions
→ Judge: "Quality score: 8.5/10, good composition"
→ Final Actions: [8 refined actions]
```

### When to Use

- High-quality terrain requirements
- Complex multi-feature designs
- When quality is critical
- Via `/api/design/multi-agent` endpoint

---

## 5. Regex Fallback

**Purpose:** Basic parsing without LLM (no API key required)

### Process

- Pattern matching for common commands
- Simple feature extraction
- Basic position resolution

### Features

- No API key required
- Fast parsing
- Basic command support

### Limitations

- No reference resolution
- No complex spatial reasoning
- Limited modifier support
- No quality evaluation

### Example

```
Command: "add mountain left"
→ Pattern Match: "add" + "mountain" + "left"
→ Action: {kind: "add", type: "mountain", position: {region: "left"}}
```

### When to Use

- No LLM API key available
- Simple commands
- Fallback when LLM fails
- Testing without API costs

---

## Strategy Comparison

| Strategy | LLM Required | Quality Eval | Reference Resolution | Complexity | Use Case |
|----------|--------------|--------------|---------------------|------------|----------|
| Narrative Pipeline | ✅ | ✅ | ✅ | High | Default, artistic |
| SemanticParser | ✅ | ❌ | ✅ | Medium | References, spatial |
| ReAct Agent | ✅ | ✅ | ✅ | Very High | Quality-focused |
| Multi-Agent | ✅ | ✅ | ✅ | Very High | High-quality designs |
| Regex Fallback | ❌ | ❌ | ❌ | Low | Simple, fallback |

---

## Implementation Details

### Strategy Selection Logic

```python
# In orchestration.py
def parse_command_to_actions(command, state, direct_actions):
    # 1. Direct actions (pre-structured JSON)
    if direct_actions:
        return direct_actions
    
    # 2. Narrative pipeline (default)
    try:
        actions, metadata = run_narrative_pipeline(command, state)
        if actions:
            return actions
    except Exception:
        pass
    
    # 3. SemanticParser (LLM + scene graph)
    try:
        parser = SemanticParser()
        parsed = parser.parse(command, scene_state=state)
        return parsed.get("actions", [])
    except ValueError:
        # No API key, fall back to regex
        pass
    
    # 4. Regex fallback
    parser = CommandParser()
    return parser.parse(command, context=state).get("actions", [])
```

### Custom Strategy Selection

You can force a specific strategy by:

1. **Narrative Pipeline** - Use narrative-focused commands
2. **SemanticParser** - Use reference-based commands
3. **ReAct Agent** - Use quality-focused commands
4. **Multi-Agent** - Use `/api/design/multi-agent` endpoint
5. **Regex** - Simple commands without LLM

---

## Best Practices

### For Narrative Pipeline
- Use descriptive, aesthetic language
- Include archetype hints ("desert", "mountain", "valley")
- Mention aesthetic goals ("dramatic", "balanced")

### For SemanticParser
- Reference existing features ("the dunes", "first mountain")
- Use spatial relationships ("next to", "near", "between")
- Leverage scene graph context

### For ReAct Agent
- Include quality requirements ("good coverage", "balanced")
- Request iterative refinement
- Use quality-focused language

### For Multi-Agent
- Use `/api/design/multi-agent` endpoint
- Provide clear design goals
- Allow multiple refinement rounds

### For Regex Fallback
- Use simple, direct commands
- Avoid references or complex relationships
- Stick to basic feature types and positions

---

See also:
- [Architecture](ARCHITECTURE.md) - System architecture overview
- [Quality Evaluation](QUALITY_EVALUATION.md) - Quality system details
- [Scene Graph](SCENE_GRAPH.md) - Reference resolution system

