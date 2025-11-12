# Comprehensive Test Plan - Narrative-ReAct Integration

## Test Suites

### **1. Narrative Extraction Edge Cases**
- **Simple commands:** "create a mountain", "add dunes"
- **Moderate commands:** "create dramatic mountains with valleys"
- **Complex commands:** Multi-feature descriptions
- **Edge cases:** Very vague, ambiguous, conflicting goals, repetitive, empty

**Expected:** All commands should extract narrative successfully, handling edge cases gracefully.

---

### **2. Spatial Constraints Edge Cases**
- **Clustering values:** 0.0, 0.1, 0.5, 0.9, 1.0
- **Alignment values:** None, 0°, 45°, 90°, 180°, 270°, 360°

**Expected:** 
- Higher clustering → smaller offsets
- Alignment affects direction of placement
- Edge cases handled gracefully

---

### **3. Iterative Quality Refinement**
- **Max iterations:** 10
- **Command:** "create dramatic mountains with valleys and cliffs"
- **Process:** Evaluate → Refine → Re-evaluate → Repeat

**Expected:**
- Quality improves over iterations
- Reaches target quality (0.8) within reasonable iterations
- Refinement makes meaningful changes

---

### **4. Long Run Quality Progression**
- **Commands:** 6 moderate/complex commands
- **Iterations per command:** 5
- **Full ReAct flow:** Narrative extraction → ReAct reasoning → Quality evaluation

**Expected:**
- Consistent quality across commands
- Narrative extraction working in all cases
- Quality scores improving or maintaining high levels

---

### **5. Archetype Coverage**
- **Archetypes:** Ancient Uplift, Wind Architect, Water's Legacy, Volcanic, Glacial
- **Test:** Commands that should trigger each archetype

**Expected:**
- High match rate between expected and actual archetypes
- All archetypes properly handled

---

## Quality Metrics Tracked

### **Per Iteration:**
- Overall quality score
- Composition score
- Texture score
- Warning count
- Actions count
- Tool calls
- ReAct iterations
- Elapsed time

### **Per Command:**
- Average score
- Best score
- Narrative extraction success
- Constraint application

### **Overall:**
- Success rates
- Quality improvements
- Edge case handling
- Performance metrics

---

## Expected Outcomes

### **Quality Improvements:**
- Initial scores: 0.6-0.8
- After refinement: 0.75-0.85+
- Consistent quality across different commands

### **Edge Case Handling:**
- Vague commands: Extract reasonable narrative
- Conflicting goals: Handle gracefully
- Empty commands: Return appropriate response

### **Performance:**
- Narrative extraction: < 1s per command
- Quality evaluation: < 2s per evaluation
- Full ReAct flow: < 10s per command

---

## Success Criteria

### **Must Have:**
- ✅ Narrative extraction: > 90% success rate
- ✅ Quality improvement: +0.1-0.2 over iterations
- ✅ Edge cases: Graceful handling (no crashes)
- ✅ Archetype coverage: > 80% match rate

### **Nice to Have:**
- ✅ Quality scores consistently > 0.75
- ✅ Refinement reaches 0.8 within 5 iterations
- ✅ All archetypes properly matched
- ✅ Performance within acceptable limits

---

## Test Execution

Run comprehensive test suite:
```bash
cd server
uv run python tools/test_comprehensive_narrative_react.py
```

Results saved to:
- `logs/comprehensive_test_results.json` - Detailed results
- `logs/comprehensive_test_output.log` - Full output log

---

## Analysis

After tests complete, analyze:
1. Quality progression over iterations
2. Edge case handling success
3. Archetype matching accuracy
4. Performance bottlenecks
5. Areas for improvement

