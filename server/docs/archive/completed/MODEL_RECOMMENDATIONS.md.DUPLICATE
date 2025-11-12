# LLM Model Recommendations for Terrain Generation

## 🎯 Current Situation

**Current Default:** `llama3.1-8b` (8k context) - **TOO SMALL**

**Problem:** 
- 8k context is limiting for ReAct agent with:
  - Multiple tool schemas (17 tools)
  - Quality evaluation prompts
  - Refinement iterations
  - Conversation history

**Impact:**
- Context compression needed (loses information)
- May hit token limits during refinement
- Lower quality reasoning with compressed prompts

---

## ✅ Recommended Models

### **Option 1: Together.ai - `llama-3.3-70b`** ⭐ BEST CHOICE

**Specs:**
- **Context:** 65,536 tokens (8x more than current)
- **Parameters:** 70B (excellent reasoning)
- **Rate Limits:** 30 req/min, 900 req/hour, 14,400 req/day
- **Token Limits:** 64k/min, 1M/hour, 1M/day

**Why This Model:**
- ✅ **65k context** - Can handle full ReAct workflow without compression
- ✅ **Strong reasoning** - Better tool selection and quality evaluation
- ✅ **Good rate limits** - Sufficient for iterative refinement
- ✅ **Proven performance** - Latest Llama 3.3 model

**Setup:**
```bash
# In .env file:
LLM_PROVIDER=together
TOGETHER_MODEL=llama-3.3-70b
TOGETHER_API_KEY=your_key_here
```

---

### **Option 2: Together.ai - `qwen-3-32b`** ⭐ GOOD ALTERNATIVE

**Specs:**
- **Context:** 65,536 tokens
- **Parameters:** 32B (good balance)
- **Rate Limits:** Same as llama-3.3-70b
- **Token Limits:** Same as llama-3.3-70b

**Why This Model:**
- ✅ **65k context** - Same benefits as llama-3.3-70b
- ✅ **Smaller/faster** - May be faster than 70B
- ✅ **Good reasoning** - Still excellent for ReAct

**Setup:**
```bash
LLM_PROVIDER=together
TOGETHER_MODEL=qwen-3-32b
TOGETHER_API_KEY=your_key_here
```

---

### **Option 3: Cerebras - Larger Models** ⚠️ CHECK AVAILABILITY

**If staying with Cerebras, check if these are available:**
- `qwen-3-32b` - 32B parameters, likely 65k context
- `gpt-oss-120b` - 120B parameters, very powerful
- `llama-3.3-70b` - If Cerebras offers it

**Current:** `llama3.1-8b` (8k context) - **NOT RECOMMENDED**

**Setup:**
```bash
LLM_PROVIDER=cerebras
CEREBRAS_MODEL=qwen-3-32b  # or gpt-oss-120b if available
CEREBRAS_API_KEY=your_key_here
```

---

## 📊 Comparison

| Model | Context | Parameters | Reasoning | Speed | Cost | Recommendation |
|-------|---------|------------|-----------|-------|------|----------------|
| **llama-3.3-70b** (Together) | 65k | 70B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ BEST |
| **qwen-3-32b** (Together) | 65k | 32B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ EXCELLENT |
| **qwen-3-235b** (Together) | 65k | 235B | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ OVERKILL |
| **llama3.1-8b** (Current) | 8k | 8B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ TOO SMALL |

---

## 🚀 Migration Steps

### Step 1: Update Default Model

Already updated in `server/semantic/llm/factory.py`:
- Together default: `llama-3.3-70b` (was `meta-llama/Llama-3.1-70B-Instruct-Turbo`)

### Step 2: Set Environment Variable

```bash
# In server/.env:
LLM_PROVIDER=together
TOGETHER_MODEL=llama-3.3-70b
```

### Step 3: Test

```bash
cd server
uv run python tools/test_quality_direct.py
```

### Step 4: Monitor Quality Improvements

Check `logs/quality_history.jsonl` to see if quality scores improve with larger model.

---

## 💡 Why Larger Context Matters

### Current (8k context):
```
System Prompt: ~500 tokens
Tool Schemas (17 tools): ~3000 tokens
Scene Summary: ~200 tokens (compressed)
Recent Actions: ~100 tokens (compressed)
User Command: ~50 tokens
Conversation History: ~1000 tokens
---
Total: ~4850 tokens (60% of 8k limit)
```

**Problem:** Can't include full conversation history or detailed context

### With 65k context:
```
System Prompt: ~500 tokens
Tool Schemas (17 tools): ~3000 tokens
Full Scene Summary: ~1000 tokens (uncompressed)
Full Action History: ~500 tokens (uncompressed)
User Command: ~50 tokens
Full Conversation History: ~5000 tokens
Quality Evaluation Context: ~2000 tokens
---
Total: ~12,050 tokens (18% of 65k limit)
```

**Benefit:** Can include full context, better reasoning, no compression needed

---

## 🎯 Expected Improvements

With `llama-3.3-70b` (65k context):

1. **Better Tool Selection** - More context = better tool choice
2. **Better Quality Evaluation** - Can reason about full scene
3. **Better Refinement** - Can consider full context when refining
4. **No Context Compression** - Full information available
5. **Higher Quality Scores** - Better reasoning = better terrain

---

## 📝 Recommendation

**Switch to Together.ai with `llama-3.3-70b`:**

1. ✅ You already have Together.ai API key
2. ✅ 65k context is perfect for our workflow
3. ✅ 70B parameters = excellent reasoning
4. ✅ Good rate limits for iterative refinement
5. ✅ Already tested and working (we fixed Together.AI role alternation)

**Action:** Update `.env` file:
```bash
LLM_PROVIDER=together
TOGETHER_MODEL=llama-3.3-70b
```

