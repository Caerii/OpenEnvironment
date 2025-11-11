# ReAct Prompt Iteration Plan

## 🎯 **Core Problem**

The ReAct agent's **tool calling architecture is solid** (verified working), but the **prompting and output extraction need refinement** to handle complex terrain generation tasks reliably.

---

## 🔍 **What's Actually Wrong?**

### **✅ What Works (Don't Touch!):**
1. Cerebras tool calling integration ✅
2. Tool schema generation ✅
3. Tool executor and argument injection ✅
4. Conversation history management ✅
5. Simple commands complete successfully ✅

### **❌ What Needs Iteration:**

#### **Issue #1: Stopping Condition Ambiguity** 🚨 CRITICAL
**Symptom:**
- LLM keeps calling tools indefinitely
- Max iterations (5) reached without generating actions
- LLM doesn't know when it's "done" gathering information

**Root Cause:**
```python
# Current system prompt (lines 191-238 in react_agent_v2.py):
"""
1. UNDERSTAND the user's natural language command
2. USE TOOLS to gather information about the current scene
3. REASON about the best way to accomplish the task
4. GENERATE terrain actions when ready
"""
```

**Problem:** "when ready" is too vague! LLM never feels "ready".

**Fix Needed:**
- Add explicit stopping conditions
- Add iteration budget awareness
- Add confidence threshold
- Add "if you have X information, you're done" checklist

---

#### **Issue #2: Output Format Confusion** 🚨 CRITICAL
**Symptom:**
- JSON parsing fails with "Extra data" errors
- LLM wraps JSON in explanatory text
- Actions not extracted from final response

**Example of what LLM does:**
```
I've gathered all the necessary information. Here's the terrain generation plan:

```json
{"actions": [{"kind": "add", "type": "mountain", ...}]}
```

Let me know if you need any adjustments!
```

**Current Extraction Code:**
```python
# Lines 262-298 in react_agent_v2.py
if "```json" in content:
    json_start = content.find("```json") + 7
    json_end = content.find("```", json_start)
    json_str = content[json_start:json_end].strip()
```

**Problem:** Works for code blocks, but LLM adds text before/after.

**Fix Needed:**
- Stronger regex extraction
- Explicit "output ONLY JSON, no text" instruction
- Or use Cerebras structured output if available

---

#### **Issue #3: Tool Selection Logic** 🟡 MEDIUM
**Symptom:**
- LLM calls unnecessary tools
- Redundant information gathering
- Wastes iterations on tools that don't add value

**Example:** For "add 2 mountains", LLM might:
1. Call `query_scene_summary` (unnecessary - simple add doesn't need scene)
2. Call `calculate_position` (unnecessary - no spatial reference)
3. Call `infer_feature_parameters` (could be useful)
4. Finally generate actions

**Problem:** LLM doesn't know which tools are actually needed for which commands.

**Fix Needed:**
- Add command type classification in prompt
- Add examples of when to use each tool
- Add "skip tools if command is straightforward" instruction

---

#### **Issue #4: Parameter Validation** 🟡 MEDIUM
**Symptom:**
```
Tool error: infer_feature_parameters() got multiple values for argument 'feature_type'
```

**Root Cause:** LLM occasionally includes `scene_state` in arguments even though we filter it from schemas.

**Current Fix (in schema.py):**
```python
for param_name, param in sig.parameters.items():
    if param_name == "scene_state":
        continue  # Skip from schema
```

**Problem:** This is already correct! But LLM still sometimes includes it.

**Fix Needed:**
- Add explicit note in tool descriptions: "(scene_state provided automatically)"
- Add parameter validation in executor to drop unexpected args
- Add better error messages

---

## 🛠️ **Iteration Strategy**

### **Phase 1: Fix Stopping Conditions (Week 1, Day 1-2)**

#### **Current Prompt Problems:**
```python
# Too vague:
"4. GENERATE terrain actions when ready"
```

#### **Improved Prompt:**
```python
"""
## STOPPING CONDITIONS (Important!):

Stop calling tools and generate final actions when:

1. **Simple Commands** (no references):
   - "add N <features>" → Generate immediately, no tools needed
   - "create a mountain" → Generate immediately
   
2. **Spatial References** (requires 1-2 tools):
   - "near X" → Call resolve_reference + calculate_position, then generate
   - "between X and Y" → Call resolve_reference + calculate_position, then generate
   
3. **Complex Compositions** (requires 2-3 tools):
   - "surround X with Y" → resolve_reference + calculate_region_positions, then generate
   - "modify recent features" → resolve_temporal_reference + suggest_modification, then generate

MAX ITERATIONS: You have {max_iterations} iterations. Budget wisely!

After iteration 3, you MUST generate actions even if information is imperfect.
"""
```

---

### **Phase 2: Fix Output Format (Week 1, Day 2-3)**

#### **Current Prompt Problems:**
```python
# Lines 210-226 - Too flexible:
"""
## Final Output Format:
When you're ready to generate terrain, output JSON with this structure:
```json
{
  "actions": [...]
}
```
"""
```

#### **Improved Prompt:**
```python
"""
## CRITICAL: Final Output Format

When you're done reasoning (see stopping conditions above):

1. **Do NOT call any more tools**
2. **Output ONLY the JSON below** (no explanations, no text before/after)
3. **Use this EXACT structure:**

```json
{
  "actions": [
    {
      "kind": "add",
      "type": "mountain",
      "x": 100,
      "y": 200,
      "radius": 50,
      "height": 0.8,
      "label": "optional label"
    }
  ]
}
```

**IMPORTANT:**
- ❌ BAD: "Here's the plan: ```json...``` Let me know if..."
- ✅ GOOD: Just the JSON, nothing else

If you output text before/after the JSON, parsing will FAIL.
"""
```

---

### **Phase 3: Improve Tool Selection (Week 1, Day 3-4)**

#### **Add Command Classification:**
```python
"""
## Tool Usage Guidelines:

### Type 1: Simple Direct Commands
**Pattern:** "add N <feature>", "create a <feature>"
**Tools Needed:** NONE (generate immediately)
**Example:** "add 2 mountains" → No tools, just generate actions

### Type 2: Spatial Reference Commands
**Pattern:** "add X near/between/around Y"
**Tools Needed:** 
  1. resolve_reference (find Y)
  2. calculate_position (compute X position)
**Example:** "add valley near the peak"
  → resolve_reference("the peak")
  → calculate_position(relationship="near", reference_ids=[...])
  → generate actions

### Type 3: Modification Commands
**Pattern:** "make X taller/wider", "modify recent features"
**Tools Needed:**
  1. resolve_reference OR resolve_temporal_reference
  2. suggest_modification
**Example:** "make the mountains taller"
  → resolve_reference("the mountains")
  → suggest_modification(feature_ids=[...], modification_type="taller")
  → generate actions

### Type 4: Complex Compositions
**Pattern:** "surround X with Y", "create N features in a pattern"
**Tools Needed:**
  1-2. Reference resolution
  3. calculate_region_positions
**Example:** "surround the valley with 5 cliffs"
  → resolve_reference("the valley")
  → calculate_region_positions(count=5, pattern="circular")
  → generate actions

**RULE:** Use the MINIMUM tools needed for your command type!
"""
```

---

### **Phase 4: Better Error Handling (Week 1, Day 4-5)**

#### **Add Tool Error Recovery:**
```python
"""
## Handling Tool Errors:

If a tool returns an error:
1. Check if the error is recoverable (e.g., "entity not found" → try different reference)
2. If not recoverable, proceed with best-effort action generation
3. Do NOT waste iterations retrying the same failed tool

Example:
- resolve_reference("the peak") → {"error": "No entity found"}
- Response: Generate action with default position instead of blocking
"""
```

---

## 📊 **Prompt Evaluation Criteria**

After each iteration, test with these scenarios:

### **Test Suite:**

1. **Simple Direct** (should complete in 1 iteration, 0 tools):
   - "add 2 mountains"
   - "create a valley"
   - "add 3 dunes"

2. **Spatial Reference** (should complete in 2-3 iterations, 1-2 tools):
   - "add valley near the peak"
   - "create mountain between the dunes"
   - "add cliff north of the valley"

3. **Modification** (should complete in 2-3 iterations, 1-2 tools):
   - "make the mountains taller"
   - "widen recent valleys"
   - "steepen the cliffs"

4. **Complex Composition** (should complete in 3-4 iterations, 2-3 tools):
   - "surround the valley with 5 cliffs"
   - "create a circular pattern of 8 mountains"
   - "add mountains between each pair of dunes"

### **Success Metrics:**
- ✅ **Completion rate:** >90% should generate valid actions
- ✅ **Iteration count:** Simple=1, Spatial=2-3, Complex=3-4
- ✅ **Tool efficiency:** No redundant tool calls
- ✅ **JSON extraction:** 100% success rate

---

## 🧪 **Iteration Process**

### **Step 1: Update Prompts**
Edit `server/semantic/react_agent_v2.py`:
- `_build_system_prompt()` (lines 189-238)
- `_build_user_prompt()` (lines 240-254)

### **Step 2: Test**
```bash
cd server
$env:CEREBRAS_API_KEY='csk-w55m3494mx3tr62wnm9fc64e9wp5nfdhm644pxrhpjt5xmhd'
uv run pytest tests/semantic/test_react_integration.py -v -s
```

### **Step 3: Analyze Failures**
Look at:
- Reasoning trace (what tools were called?)
- Iteration count (how many before stopping?)
- Final output (did JSON parse correctly?)

### **Step 4: Iterate**
Adjust prompts based on failure patterns.

### **Step 5: Deploy**
Once test suite passes, enable in production.

---

## 🎯 **Specific Prompt Changes to Make**

### **Change #1: System Prompt** (lines 189-238)

**Add after line 203:**
```python
## COMMAND TYPE CLASSIFICATION:
Classify the command first, then use appropriate tools:

1. SIMPLE (no tools): "add N features" → Generate immediately
2. SPATIAL (1-2 tools): "near X", "between X and Y" → Resolve + Calculate
3. MODIFY (1-2 tools): "make X taller" → Resolve + Suggest
4. COMPLEX (2-3 tools): "surround X with Y" → Resolve + Calculate pattern

MAX ITERATIONS: You have 5 iterations. Budget wisely!
After 3 iterations, you MUST generate actions.
```

**Replace lines 210-226 with:**
```python
## FINAL OUTPUT (CRITICAL):
When ready, output ONLY this JSON structure (no text before/after):

```json
{
  "actions": [
    {
      "kind": "add",
      "type": "mountain",
      "x": 100,
      "y": 200,
      "height": 0.8
    }
  ]
}
```

❌ BAD: "Here's the plan: ```json...``` Any questions?"
✅ GOOD: Just the raw JSON block

If you add text, parsing FAILS.
```

---

### **Change #2: Improve JSON Extraction** (lines 256-298)

**Replace entire `_extract_actions_from_response` with:**
```python
def _extract_actions_from_response(self, content: Optional[str]) -> List[Dict]:
    """Extract actions from LLM response (robust version)."""
    if not content:
        return []
    
    import re
    
    try:
        # Strategy 1: Look for ```json blocks with regex
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Strategy 2: Look for generic ``` blocks
            json_match = re.search(r'```\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # Strategy 3: Find JSON object directly
                json_match = re.search(r'\{.*?"actions".*?\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return []
        
        # Parse JSON
        parsed = json.loads(json_str)
        
        # Extract actions array
        if "actions" in parsed:
            return parsed["actions"]
        elif isinstance(parsed, list):
            return parsed
        else:
            return []
    
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}")
        logger.debug(f"Content was: {content[:200]}...")
        return []
    except Exception as e:
        logger.error(f"Error extracting actions: {e}")
        return []
```

---

### **Change #3: Add Iteration Budget Awareness** (lines 96-159)

**Add after line 98:**
```python
# Add iteration count to messages for LLM awareness
if iteration >= 3:
    # Inject urgency after 3 iterations
    conversation.append({
        "role": "user",
        "content": f"⚠️ ITERATION {iteration}/5 - Please generate final actions NOW."
    })
```

---

## 🚀 **Expected Outcomes**

### **After Phase 1 (Stopping Conditions):**
- Simple commands complete in 1 iteration
- Complex commands complete within 4 iterations
- No more "max iterations reached" failures

### **After Phase 2 (Output Format):**
- 100% JSON extraction success rate
- No "Extra data" errors
- Clean action parsing

### **After Phase 3 (Tool Selection):**
- 50% reduction in unnecessary tool calls
- Faster completion times (fewer API calls)
- More efficient reasoning

### **After Phase 4 (Error Handling):**
- Graceful degradation on tool failures
- No crashes on missing references
- Always generates some output

---

## 📝 **Summary**

### **What to Iterate:**
1. 🚨 **CRITICAL:** System prompt - stopping conditions
2. 🚨 **CRITICAL:** Output format instructions
3. 🟡 **MEDIUM:** Tool selection guidelines
4. 🟡 **MEDIUM:** JSON extraction robustness
5. 🟢 **LOW:** Error recovery strategies

### **What NOT to Touch:**
- ✅ Tool calling architecture (works!)
- ✅ Schema generation (correct!)
- ✅ Tool executor (solid!)
- ✅ Conversation management (good!)

### **Timeline:**
- Week 1, Day 1-2: Stopping conditions
- Week 1, Day 2-3: Output format
- Week 1, Day 3-4: Tool selection
- Week 1, Day 4-5: Error handling
- Week 1, Day 5-7: Testing & polish

**Estimated time to production-ready: 5-7 days of prompt iteration**

---

The core system is 75% done! Just need to tune the prompts to guide the LLM better. 🎯

