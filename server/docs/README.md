# 📚 SemanticTerrain Server Documentation

**Last Updated:** November 11, 2025

This directory contains all technical documentation for the SemanticTerrain server.

---

## 📖 Active Documentation

**Essential references for current development, organized by topic:**

### **Quick Start & Context** (Root Level)
- **[CONTEXT_FOR_AI.md](active/CONTEXT_FOR_AI.md)** - Quick reference for AI agents working with the codebase
- **[KNOWN_ISSUES.md](active/KNOWN_ISSUES.md)** - Current bugs, limitations, and TODOs
- **[SYSTEM_EXPLANATION.md](active/SYSTEM_EXPLANATION.md)** - Complete architecture deep dive (597 lines)

### **Architecture & Design** (`active/architecture/`)
Core architectural documentation:
- **[CURRENT_ARCHITECTURE_STATUS.md](active/architecture/CURRENT_ARCHITECTURE_STATUS.md)** ⭐ **START HERE** - Actual current state (verified Nov 2025)
- **[MASTER_ARCHITECTURE_PLAN.md](active/architecture/MASTER_ARCHITECTURE_PLAN.md)** - Long-term roadmap and 7-phase vision
- **[ARCHITECTURE_PRINCIPLES.md](active/architecture/ARCHITECTURE_PRINCIPLES.md)** - Core design philosophy and patterns
- **[SEMANTIC_SCENE_REPRESENTATION.md](active/architecture/SEMANTIC_SCENE_REPRESENTATION.md)** - Scene graph design (USD-inspired)
- **[ENCAPSULATION_DESIGN.md](active/architecture/ENCAPSULATION_DESIGN.md)** - Encapsulation patterns and design decisions

### **Model Strategy & Configuration** (`active/models/`)
LLM model selection and configuration:
- **[GEMINI_MODEL_STRATEGY.md](active/models/GEMINI_MODEL_STRATEGY.md)** - Optimal Gemini model configuration for visual critique
- **[MODEL_RECOMMENDATIONS.md](active/models/MODEL_RECOMMENDATIONS.md)** - LLM model recommendations and comparisons
- **[GEMINI_2_FLASH_RECOMMENDATION.md](active/models/GEMINI_2_FLASH_RECOMMENDATION.md)** - Gemini 2.5 Flash Image usage guide
- **[LLM_PARAMETER_CONTEXT_ANALYSIS.md](active/models/LLM_PARAMETER_CONTEXT_ANALYSIS.md)** - Context length analysis for LLM parameters
- **[LLM_PARAMETER_CONTEXT_COMPLETE.md](active/models/LLM_PARAMETER_CONTEXT_COMPLETE.md)** - Context length implementation completion

### **Roadmap & Planning** (`active/roadmap/`)
Current development priorities and next steps:
- **[NEXT_STEPS_ROADMAP.md](active/roadmap/NEXT_STEPS_ROADMAP.md)** - Current development roadmap and priorities
- **[NEXT_STEPS_DETAILED.md](active/roadmap/NEXT_STEPS_DETAILED.md)** - Detailed next steps and implementation plans
- **[FURTHER_IMPROVEMENTS_NEEDED.md](active/roadmap/FURTHER_IMPROVEMENTS_NEEDED.md)** - Critical improvements and enhancements needed

### **Performance & Optimization** (`active/performance/`)
Performance analysis and optimization work (18 documents):
- **[PERFORMANCE_ANALYSIS.md](active/performance/PERFORMANCE_ANALYSIS.md)** - Comprehensive performance analysis
- **[PERFORMANCE_FINAL_REPORT.md](active/performance/PERFORMANCE_FINAL_REPORT.md)** - Final performance report
- **[OPTIMIZATION_SUMMARY.md](active/performance/OPTIMIZATION_SUMMARY.md)** - Optimization implementation summary
- **[DEEP_PERFORMANCE_ANALYSIS.md](active/performance/DEEP_PERFORMANCE_ANALYSIS.md)** - Deep-dive performance analysis
- **[SYSTEMATIC_PERFORMANCE_PROFILING.md](active/performance/SYSTEMATIC_PERFORMANCE_PROFILING.md)** - Systematic profiling methodology
- **[BOTTLENECK_FIXES_COMPLETE.md](active/performance/BOTTLENECK_FIXES_COMPLETE.md)** - Bottleneck fixes completion report
- *See `active/performance/` directory for full list (18 documents)*

### **Features & Implementation** (`active/features/`)
Feature-specific documentation and guides:
- **[WALKABILITY_ZONE_ARCHITECTURE.md](active/features/WALKABILITY_ZONE_ARCHITECTURE.md)** - Walkability zone system architecture
- **[TEMPLATE_SYSTEM.md](active/features/TEMPLATE_SYSTEM.md)** - Terrain template system guide
- **[PRIMITIVE_RECOMMENDATIONS.md](active/features/PRIMITIVE_RECOMMENDATIONS.md)** - How to implement new terrain primitives
- **[RIDGE_EXAMPLES.md](active/features/RIDGE_EXAMPLES.md)** - Detailed examples of ridge generation
- **[PLACEHOLDER_RECOMMENDATIONS.md](active/features/PLACEHOLDER_RECOMMENDATIONS.md)** - Placeholder system recommendations
- *See `active/features/` directory for full list (9 documents)*

### **Research & Standards** (`active/research/`)
Industry research and design standards:
- **[RESEARCH_USD_AND_MCP_ARCHITECTURE.md](active/research/RESEARCH_USD_AND_MCP_ARCHITECTURE.md)** - Industry research (Pixar USD, MCP, Neural Scene Graphs)
- **[AESTHETIC_GUIDELINES.md](active/research/AESTHETIC_GUIDELINES.md)** - Visual design principles for terrain generation

### **Testing** (`active/testing/`)
Testing strategies and guides:
- **[COMPLETE_TESTING_GUIDE.md](active/testing/COMPLETE_TESTING_GUIDE.md)** - Complete testing guide with examples

### **Integration** (`active/integration/`)
**Note:** Integration docs have been archived. See `archive/completed/` for historical integration fixes. Current integration status is documented in `CURRENT_ARCHITECTURE_STATUS.md`.

---

## 🗄️ Archive

**Historical documentation preserved for reference:**

### **Analysis** (`archive/analysis/`)
Deep-dive analyses from earlier development phases:
- Code quality assessments and architectural critiques
- System analysis documents (comprehensive, critical, gaps analysis)
- Type system and integration analyses
- ReAct implementation critiques and planning
- Semantic context requirements and solutions
- Technical feasibility and vision documents
- Status reports and honest assessments

**Recent additions:** 
- 30+ analysis documents moved from root directory (Nov 2025)
- Planning documents from `old_ai_generated_docs/` (Nov 2025):
  - `ARCHITECTURE_CONNECTION_MAP.md` - Component connection mapping
  - `BRITTLE_PATTERNS_ANALYSIS.md` - Brittle pattern identification
  - `DEEP_GENERATE_PATHWAY_ANALYSIS.md` - Generation pathway analysis
  - `ROOT_CAUSE_ANALYSIS.md` - Root cause analysis of architectural issues

### **Completed Work** (`archive/completed/`)
Completion reports for major milestones:
- **Refactoring reports** (cleanup, feature migration, architectural fixes)
- **Feature completion** (primitives, registry, semantic features, etc.)
- **Phase completion** (MCP integration, scene graph, etc.)
- **Implementation reports** (narrative tools, ReAct agent, quality improvements)
- **Fix summaries** (context length, auto-refresh, semantic fixes)
- **Implementation plans** (critical action plans, prioritized fixes, encapsulation)

**Recent additions:** 
- 24+ completion reports moved from root directory (Nov 2025)
- Planning documents from `old_ai_generated_docs/` (Nov 2025):
  - `CRITICAL_ACTION_PLAN.md` - Prioritized critical fixes (mostly implemented)
  - `ENCAPSULATION_COMPLETE.md` - Encapsulation refactoring summary
  - `PRIORITIZED_FIX_PLAN.md` - Prioritized fix plan
  - `QUICK_FIX_REFERENCE.md` - Quick reference for code changes (outdated)
  - `TESTING_SUMMARY.md`, `TESTING_CHECKLIST.md` - Testing documentation

---

## 📂 Documentation Structure

```
server/docs/
├── README.md                    # This file - documentation hub
├── active/                      # Current, relevant docs (organized by topic)
│   ├── CONTEXT_FOR_AI.md       # AI quick reference (root level)
│   ├── KNOWN_ISSUES.md         # Current issues & TODOs (root level)
│   ├── SYSTEM_EXPLANATION.md   # Architecture deep dive (root level)
│   ├── architecture/           # Architecture & design docs (5 files)
│   ├── models/                 # LLM model strategy & config (5 files)
│   ├── roadmap/                # Current planning & next steps (3 files)
│   ├── performance/            # Performance & optimization (18 files)
│   ├── features/               # Feature-specific guides (9 files)
│   ├── research/               # Industry research & standards (2 files)
│   ├── testing/                # Testing guides (1 file)
│   └── integration/            # Integration fixes & tests (2 files)
└── archive/                     # Historical reference
    ├── analysis/                # Deep-dive analyses
    │   ├── CODE_SMELLS_ANALYSIS.md
    │   ├── DEAD_CODE_VERIFICATION.md
    │   └── [30+ analysis documents]
    └── completed/               # Milestone reports
        ├── FINAL_REFACTORING_REPORT.md
        ├── FEATURE_REGISTRY_COMPLETE.md
        └── [40+ completion reports]
```

---

## 🎯 Recommended Reading Order

**For New Developers:**
1. Start: [CONTEXT_FOR_AI.md](active/CONTEXT_FOR_AI.md) - Quick overview
2. Current state: [CURRENT_ARCHITECTURE_STATUS.md](active/architecture/CURRENT_ARCHITECTURE_STATUS.md) - What's actually implemented
3. Deep dive: [SYSTEM_EXPLANATION.md](active/SYSTEM_EXPLANATION.md) - Full architecture
4. Issues: [KNOWN_ISSUES.md](active/KNOWN_ISSUES.md) - What needs work

**For AI Agents:**
1. [CONTEXT_FOR_AI.md](active/CONTEXT_FOR_AI.md) - Complete system context
2. [KNOWN_ISSUES.md](active/KNOWN_ISSUES.md) - Current state
3. Archive docs as needed for historical context

**For Researchers:**
- [RESEARCH_USD_AND_MCP_ARCHITECTURE.md](active/research/RESEARCH_USD_AND_MCP_ARCHITECTURE.md) - Industry standards
- [SEMANTIC_SCENE_REPRESENTATION.md](active/architecture/SEMANTIC_SCENE_REPRESENTATION.md) - Our scene graph design

**For Performance Engineers:**
- [PERFORMANCE_ANALYSIS.md](active/performance/PERFORMANCE_ANALYSIS.md) - Start here
- [SYSTEMATIC_PERFORMANCE_PROFILING.md](active/performance/SYSTEMATIC_PERFORMANCE_PROFILING.md) - Profiling methodology
- [OPTIMIZATION_SUMMARY.md](active/performance/OPTIMIZATION_SUMMARY.md) - Optimization work completed

---

## ✅ Documentation Standards

**Active Docs:**
- Must be current and accurate
- Updated when architecture changes
- Focused on "why" not just "what"

**Archive:**
- Historical reference only
- Milestone completion reports
- Analysis documents from past work
- NOT updated, preserved as-is

**When in doubt:**
- Active = "I need this to understand the current system"
- Archive = "Interesting history, but not critical to current work"
