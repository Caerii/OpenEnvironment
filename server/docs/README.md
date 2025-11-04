# 📚 SemanticTerrain Server Documentation

**Last Updated:** November 4, 2025

This directory contains all technical documentation for the SemanticTerrain server.

---

## 📖 Active Documentation

**Essential references for current development:**

### **Quick Start & Context**
- **[CONTEXT_FOR_AI.md](active/CONTEXT_FOR_AI.md)** - Quick reference for AI agents working with the codebase
- **[KNOWN_ISSUES.md](active/KNOWN_ISSUES.md)** - Current bugs, limitations, and TODOs

### **Architecture & Design**
- **[SYSTEM_EXPLANATION.md](active/SYSTEM_EXPLANATION.md)** - Complete architecture deep dive (597 lines)
- **[MASTER_ARCHITECTURE_PLAN.md](active/MASTER_ARCHITECTURE_PLAN.md)** - Long-term roadmap and 7-phase vision
- **[ARCHITECTURE_PRINCIPLES.md](active/ARCHITECTURE_PRINCIPLES.md)** - Core design philosophy and patterns
- **[SEMANTIC_SCENE_REPRESENTATION.md](active/SEMANTIC_SCENE_REPRESENTATION.md)** - Scene graph design (USD-inspired)

### **Research & Standards**
- **[RESEARCH_USD_AND_MCP_ARCHITECTURE.md](active/RESEARCH_USD_AND_MCP_ARCHITECTURE.md)** - Industry research (Pixar USD, MCP, Neural Scene Graphs)
- **[AESTHETIC_GUIDELINES.md](active/AESTHETIC_GUIDELINES.md)** - Visual design principles for terrain generation
- **[COMPLETE_TESTING_GUIDE.md](active/COMPLETE_TESTING_GUIDE.md)** - Testing strategies and examples

### **Implementation Guides**
- **[PRIMITIVE_RECOMMENDATIONS.md](active/PRIMITIVE_RECOMMENDATIONS.md)** - How to implement new terrain primitives
- **[RIDGE_EXAMPLES.md](active/RIDGE_EXAMPLES.md)** - Detailed examples of ridge generation

---

## 🗄️ Archive

**Historical documentation preserved for reference:**

### **Analysis** (`archive/analysis/`)
Deep-dive analyses from earlier development phases:
- Code quality assessments
- Architectural critiques
- Dead code verification
- Technical research

### **Completed Work** (`archive/completed/`)
Completion reports for major milestones:
- **Refactoring reports** (cleanup, feature migration, architectural fixes)
- **Feature completion** (primitives, registry, semantic features, etc.)
- **Phase completion** (MCP integration, scene graph, etc.)

---

## 📂 Documentation Structure

```
server/docs/
├── README.md                    # This file - documentation hub
├── active/                      # Current, relevant docs
│   ├── CONTEXT_FOR_AI.md       # AI quick reference
│   ├── KNOWN_ISSUES.md         # Current issues & TODOs
│   ├── SYSTEM_EXPLANATION.md   # Architecture deep dive
│   ├── MASTER_ARCHITECTURE_PLAN.md
│   ├── ARCHITECTURE_PRINCIPLES.md
│   └── [9 more active docs]
└── archive/                     # Historical reference
    ├── analysis/                # Deep-dive analyses
    │   ├── CODE_SMELLS_ANALYSIS.md
    │   ├── DEAD_CODE_VERIFICATION.md
    │   └── [8 more analyses]
    └── completed/               # Milestone reports
        ├── FINAL_REFACTORING_REPORT.md
        ├── FEATURE_REGISTRY_COMPLETE.md
        └── [20 more completion reports]
```

---

## 🎯 Recommended Reading Order

**For New Developers:**
1. Start: [CONTEXT_FOR_AI.md](active/CONTEXT_FOR_AI.md) - Quick overview
2. Deep dive: [SYSTEM_EXPLANATION.md](active/SYSTEM_EXPLANATION.md) - Full architecture
3. Philosophy: [ARCHITECTURE_PRINCIPLES.md](active/ARCHITECTURE_PRINCIPLES.md) - Why we built it this way
4. Current state: [KNOWN_ISSUES.md](active/KNOWN_ISSUES.md) - What needs work

**For AI Agents:**
1. [CONTEXT_FOR_AI.md](active/CONTEXT_FOR_AI.md) - Complete system context
2. [KNOWN_ISSUES.md](active/KNOWN_ISSUES.md) - Current state
3. Archive docs as needed for historical context

**For Researchers:**
- [RESEARCH_USD_AND_MCP_ARCHITECTURE.md](active/RESEARCH_USD_AND_MCP_ARCHITECTURE.md) - Industry standards
- [SEMANTIC_SCENE_REPRESENTATION.md](active/SEMANTIC_SCENE_REPRESENTATION.md) - Our scene graph design

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
