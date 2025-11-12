# Next Steps Roadmap - Complete the System

## ✅ What We've Accomplished

1. **Quality Evaluation & Refinement System** ✅
   - Quality evaluation tools (`evaluate_terrain_quality`)
   - Refinement tools (`refine_composition`)
   - Iterative refinement loop (up to 5 iterations)
   - Quality threshold (0.8)

2. **Quality History Logging** ✅
   - Logs all quality improvements to `logs/quality_history.jsonl`
   - Tracks initial/final scores, improvements, refinements

3. **Model Configuration** ✅
   - Gemini 2.5 Flash Image for visual critique (images + text)
   - Together llama-3.3-70b for ReAct agent (65k context)
   - Optimal model selection for each use case

4. **Together.AI Integration** ✅
   - Fixed role alternation issues
   - Working with multi-agent workflow

5. **Parser System** ✅ (Updated Nov 2025)
   - Narrative pipeline is PRIMARY parser
   - SemanticParser as fallback
   - CommandParser as final fallback

6. **Walkability Infrastructure** ✅ (Updated Nov 2025)
   - Primitives implemented (flat_zone, path, clearing)
   - Constraint system implemented
   - Builder integration complete
   - ⚠️ Enforcement integration pending

---

## 🚨 Critical Next Steps (Must Fix)

### **1. Terrain Rendering Imports** ⚠️ PARTIALLY WORKING

**Status:** `_render_terrain_preview()` in `quality_tools.py` has fallback import handling

**Current State:**
- Uses bootstrap to ensure proper import environment
- Multiple fallback strategies for different runtime contexts
- Handles both package and direct imports
- May still fail in some edge cases (needs testing)

**Impact:**
- Should work in most contexts, but may default to fallback texture metrics (0.120 score) if rendering fails
- Quality evaluation may be limited if rendering fails

**Files:**
- `server/semantic/tools/quality_tools.py` (line 386-450)

---

### **2. Fix Narrative Tool Import Error** 🚨 HIGH PRIORITY

**Problem:** `generate_narrative_composition` fails with bootstrap import error

**Impact:**
- ReAct agent can't use narrative tool (best quality path)
- Falls back to manual action generation
- Lower quality outputs

**Fix Needed:**
```python
# In server/semantic/narrative/generation.py
# Fix: from ...bootstrap import ensure_bootstrapped
# Current: Relative import fails
# Solution: Fix import path or make bootstrap optional
```

**Files:**
- `server/semantic/narrative/generation.py` (line 12)
- `server/semantic/tools/narrative_tools.py` (line 94)

---

## ⚠️ Important Next Steps (Should Do)

### **3. Test End-to-End Workflow** ⚠️ MEDIUM PRIORITY

**What to Test:**
1. ReAct agent with quality refinement
2. Multi-agent workflow with Gemini visual critique
3. Quality history logging
4. Verify improvements are actually happening

**Commands to Test:**
```bash
# Test ReAct with quality refinement
uv run python tools/test_quality_refinement.py

# Test multi-agent workflow
uv run python tools/evaluate_multi_agent_quality.py --rounds 3 --iterations 2

# Check quality history
cat logs/quality_history.jsonl | tail -20
```

---

### **4. Monitor Quality Improvements** ⚠️ MEDIUM PRIORITY

**What to Monitor:**
- Quality scores over time
- Refinement effectiveness
- Common warning patterns
- Improvement rates

**Tools:**
- `logs/quality_history.jsonl` - Quality progression
- `logs/react_sessions/` - ReAct agent logs
- `logs/multi_agent_sessions/` - Multi-agent logs

**Analysis:**
- Are scores improving?
- Which refinements work best?
- What warnings are most common?
- How many iterations needed to reach 0.8?

---

### **5. Improve Refinement Heuristics** ⚠️ MEDIUM PRIORITY

**Current:** Simple heuristics (add features, spread positions, vary heights)

**Improvements:**
- **LLM-guided refinements**: Use LLM to suggest specific improvements
- **Smarter placement**: Use golden ratio, rule of thirds for new features
- **Texture-aware**: Add features that improve texture distribution
- **Context-aware**: Consider existing features when refining

**Example:**
```python
# Instead of random feature addition:
refined = _add_supporting_features(actions)

# Use LLM to suggest:
prompt = f"Quality warnings: {warnings}. Suggest 2-3 specific improvements."
suggestions = llm_client.chat(prompt)
# Parse and apply intelligently
```

---

## 💡 Optional Enhancements (Nice to Have)

### **6. Gemini 2.5 Pro for Complex Reasoning** 💡 OPTIONAL

**Use Case:** Advanced reasoning tasks, complex quality evaluation

**Benefits:**
- 1M context (vs 65k for Together)
- Thinking capabilities
- Function calling supported
- Code execution

**Consideration:**
- Currently Together.ai works well for ReAct
- Gemini 2.5 Pro could be alternative if needed
- May be slower/more expensive

**Implementation:**
- Add option to use Gemini 2.5 Pro for ReAct agent
- Compare performance vs Together
- Use for complex reasoning tasks

---

### **7. Quality Visualization Dashboard** 💡 OPTIONAL

**Features:**
- Quality score trends over time
- Before/after comparisons
- Refinement effectiveness charts
- Warning pattern analysis

**Tools:**
- matplotlib/plotly for visualization
- Web dashboard (optional)
- Quality reports

---

### **8. Advanced Refinement Strategies** 💡 OPTIONAL

**Ideas:**
- **Multi-strategy refinement**: Try multiple approaches, pick best
- **Learning from history**: Use past refinements to guide future ones
- **A/B testing**: Compare refinement strategies
- **Adaptive heuristics**: Adjust based on success rates

---

## 📋 Implementation Priority

### **Phase 1: Critical Fixes** (Do First)
1. ✅ Fix terrain rendering imports
2. ✅ Fix narrative tool imports
3. ✅ Test end-to-end workflow

### **Phase 2: Validation** (Do Next)
4. ✅ Monitor quality improvements
5. ✅ Analyze quality history
6. ✅ Verify system works correctly

### **Phase 3: Enhancements** (Do Later)
7. ✅ Improve refinement heuristics
8. ✅ Add quality visualization
9. ✅ Consider Gemini 2.5 Pro for reasoning

---

## 🎯 Expected Outcomes

After fixing critical issues:

1. **Quality scores improve** from 0.06 → 0.80+
2. **Texture metrics accurate** (not default 0.120)
3. **Narrative tool works** (best quality path enabled)
4. **Refinement effective** (iterative improvements)
5. **Quality history tracked** (data for analysis)

---

## 🚀 Ready to Proceed

**Current Status:**
- ✅ Quality evaluation system implemented
- ✅ Refinement system implemented
- ✅ Quality logging implemented
- ✅ Models configured optimally
- ⚠️ Import issues need fixing (blocks full functionality)

**Next Action:** Fix import issues, then test end-to-end!

