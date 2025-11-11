# LLM Parameter Context Analysis

## Current State

### ✅ What Works Well

1. **Tool Registry**: Comprehensive parameter schemas with:
   - Min/max constraints
   - Default values
   - Type information
   - Descriptions

2. **Scene Graph Context**: Rich semantic context about existing entities

3. **Basic Modifiers**: LLM can set `taller`, `deeper`, `wider`, `height_percent`, `depth_percent`, `width_percent`

### ❌ Critical Gaps

1. **Insufficient Tool Parameter Context**:
   - `_generate_compact_tool_context()` only shows **80-character truncated descriptions**
   - **NO parameter details** (ranges, defaults, constraints) are exposed
   - LLM cannot see what parameters each primitive supports
   - LLM cannot make informed parameter choices

2. **Limited Parameter Awareness**:
   - LLM only knows about generic modifiers (`height_percent`, etc.)
   - Doesn't know primitive-specific parameters:
     - Mountains: `height` (0.1-1.0, default 0.75), `radius` (20-100, default 56)
     - Valleys: `depth` (0.1-1.0, default 0.55), `radius` (30-100, default 64)
     - Dunes: `amplitude` (0.02-0.3, default 0.08), `frequency` (5.0-50.0, default 18.0)
     - Cliffs: `length`, `height`, `orientation`, `steepness`
     - And many more...

3. **No Parameter Judgment**:
   - LLM cannot intelligently choose parameters based on context
   - Cannot understand parameter relationships (e.g., "tall mountain" → height=0.9)
   - Cannot adapt parameters to user intent (e.g., "gentle hill" → height=0.3, radius=60)

## Impact

**Without parameter context, the LLM:**
- Uses generic modifiers instead of precise values
- Cannot optimize parameters for user intent
- Cannot understand what "tall", "deep", "wide" mean in concrete terms
- Cannot make context-aware parameter choices

## Recommended Solution

Enhance `_generate_compact_tool_context()` to include **full parameter schemas** for each tool:

```python
def _generate_detailed_tool_context(self) -> str:
    """Generate detailed tool context with full parameter information."""
    lines = ["\n=== AVAILABLE TOOLS WITH PARAMETERS ===\n"]
    
    primitives = self.tool_registry.get_tools_by_category(ToolCategory.PRIMITIVE)
    for tool in primitives:
        lines.append(f"\n{tool.name}: {tool.description}")
        lines.append("  Parameters:")
        for param in tool.parameters:
            req = " (required)" if param.required else " (optional)"
            default = f" [default: {param.default}]" if param.default is not None else ""
            min_max = ""
            if param.minimum is not None and param.maximum is not None:
                min_max = f" [range: {param.minimum}-{param.maximum}]"
            lines.append(f"    - {param.name} ({param.type}){req}{default}{min_max}: {param.description}")
    
    return "\n".join(lines)
```

This would allow the LLM to:
1. **See all available parameters** for each primitive
2. **Understand parameter ranges** and choose appropriate values
3. **Make intelligent judgments** based on user intent (e.g., "tall" → height=0.9)
4. **Use context-appropriate defaults** when user doesn't specify

## Parameter Mapping

The LLM should map user intent to concrete parameters:

| User Intent | Parameter Choice |
|------------|------------------|
| "tall mountain" | height: 0.9 (near max) |
| "gentle hill" | height: 0.3, radius: 60 (lower, wider) |
| "deep valley" | depth: 0.8 (near max) |
| "wide plateau" | width: 120, length: 150 (large) |
| "steep cliff" | steepness: 0.95 (near max) |
| "rolling dunes" | amplitude: 0.12, frequency: 18 (moderate) |

## Implementation Priority

**HIGH**: This is critical for intelligent terrain generation. Without parameter context, the LLM is essentially "guessing" at parameter values rather than making informed choices.


