# 🚀 **DETAILED NEXT STEPS**

## **How to Actually Complete the Integration**

**Based on:** CRITICAL_GAPS_ANALYSIS.md  
**Goal:** Connect typed Features and narrative system to production pipeline  
**Time:** 5-7 hours

---

## 📋 **PHASE 3: Bridge the Type Gap**

### **Task 3.1: Fix `FeatureState.add_feature`** (30 min)

**File:** `server/semantic/state_manager.py`

**Current Code:**
```python
def add_feature(self, feat: Dict):
    """Add feature (expects dict)."""
    if "id" not in feat:
        feat["id"] = self._generate_id()
    # ...
    self.state["features"].append(feat)
```

**New Code:**
```python
from typing import Union
from domain.models import Feature

def add_feature(self, feat: Union[Feature, Dict]):
    """Add feature (accepts Feature or dict for migration)."""
    # Convert Feature → dict if needed
    if isinstance(feat, Feature):
        feat_dict = feat.to_dict()
    else:
        feat_dict = feat
    
    # Assign ID if missing
    if "id" not in feat_dict:
        feat_dict["id"] = self._generate_id()
    else:
        feat_id = feat_dict["id"]
        if feat_id >= self.next_id:
            self.next_id = feat_id + 1
    
    self.state["features"].append(feat_dict)
```

**Test:**
```python
# tests/semantic/test_state_manager_bridge.py
def test_add_feature_accepts_typed_feature():
    state = {"features": [], "seed": 42}
    fs = FeatureState(state)
    
    feat = Feature(
        id=1,
        type="mountain",
        position=Position(x=256, y=256),
        parameters=FeatureParameters(height=0.8),
        metadata={}
    )
    
    fs.add_feature(feat)  # Should not crash!
    
    stored = fs.get_feature(1)
    assert stored["type"] == "mountain"
```

---

### **Task 3.2: Fix `_apply_feature_to_builder`** (30 min)

**File:** `server/engine/commands.py`

**Current Code:**
```python
def _apply_feature_to_builder(builder: TerrainBuilder, feat: Dict, seed: int):
    """Apply feature dict to builder."""
    ftype = feat.get("type")
    # ...
```

**New Code:**
```python
from typing import Union
from domain.models import Feature

def _apply_feature_to_builder(builder: TerrainBuilder, feat: Union[Feature, Dict], seed: int):
    """Apply feature (Feature or dict) to builder."""
    from ..engine.feature_registry import FeatureRegistry
    
    # Convert Feature → dict if needed (for current implementation)
    if isinstance(feat, Feature):
        feat_dict = feat.to_dict()
    else:
        feat_dict = feat
    
    ftype = feat_dict.get("type")
    
    if not ftype:
        logger.warning(f"Feature missing type field: {feat_dict}")
        return
    
    if not FeatureRegistry.has_generator(ftype):
        logger.warning(f"Unknown feature type '{ftype}', skipping.")
        return
    
    # Generate stamp using registry
    try:
        stamp = FeatureRegistry.generate_stamp(ftype, feat_dict, seed)
        mode = FeatureRegistry.get_blending_mode(ftype)
        
        # Special handling for dunes
        if ftype == "dunes":
            from ..primitives.dunes import generate_dune_mask
            box = (feat_dict["x0"], feat_dict["y0"], feat_dict["x1"], feat_dict["y1"])
            dune_mask = generate_dune_mask(box)
            builder.apply_feature(stamp, mode, dune_mask_slice=dune_mask, mask_bounds=box,
                                feature_type=ftype, feature_params=feat_dict)
        else:
            builder.apply_feature(stamp, mode, feature_type=ftype, feature_params=feat_dict)
            FeatureRegistry.apply_special_effects(ftype, builder, feat_dict, stamp, seed)
        
    except Exception as e:
        logger.error(f"Error applying feature '{ftype}': {e}", exc_info=True)
```

**Test:**
```python
# tests/engine/test_commands_bridge.py
def test_apply_feature_to_builder_accepts_typed_feature():
    builder = TerrainBuilder(base_desert, 42)
    
    feat = Feature(
        id=1,
        type="mountain",
        position=Position(x=256, y=256),
        parameters=FeatureParameters(height=0.8, radius=40),
        metadata={}
    )
    
    _apply_feature_to_builder(builder, feat, 42)  # Should not crash!
    
    h, _, _ = builder.finalize()
    assert h[256, 256] > 0.5  # Mountain should be there
```

---

### **Task 3.3: Update `AddFeatureCommand`** (20 min)

**File:** `server/engine/commands.py`

**Current:** Already uses `FeatureRegistry.create_feature`, which returns Feature!

**But:** Passes result to `feature_state.add_feature()`, which we just fixed.

**Verify:** Test that the full flow works:

```python
# tests/engine/test_commands_integration.py
def test_add_feature_command_with_typed_features():
    state = {"features": [], "seed": 42}
    feature_state = FeatureState(state)
    builder = TerrainBuilder(base_desert, 42)
    
    cmd = AddFeatureCommand(
        feature_type="mountain",
        position={"x": 256, "y": 256},
        modifiers={"taller": True},
        count=1
    )
    
    cmd.execute(builder, feature_state, 42)
    
    # Feature should be stored (as dict in current implementation)
    features = feature_state.list_features()
    assert len(features) == 1
    assert features[0]["type"] == "mountain"
    
    # Builder should have applied it
    h, _, _ = builder.finalize()
    assert h[256, 256] > 0.7  # Tall mountain
```

---

## 📋 **PHASE 4: Connect Narrative System**

### **Task 4.1: Create `composition_to_actions` Converter** (1 hour)

**File:** `server/semantic/narrative/converters.py` (**NEW**)

```python
"""
Converters between narrative types and action dicts.
"""

from typing import Dict, List
from .types import FeatureComposition, TerrainNarrative
from ...domain.models import Feature, FeatureParameters


def composition_to_actions(composition: FeatureComposition) -> List[Dict]:
    """
    Convert FeatureComposition → action dicts for main pipeline.
    
    This is the BRIDGE between narrative system and terrain generation.
    
    Args:
        composition: Generated feature composition with typed Features
    
    Returns:
        List of action dicts for execute_add_actions()
    
    Example:
        composition = generate_from_narrative(narrative, {}, seed=42)
        actions = composition_to_actions(composition)
        # Now actions can be passed to execute_add_actions()
    """
    actions = []
    
    # Add focal point (hero feature)
    if composition.focal_point:
        actions.append(_feature_to_action(composition.focal_point, label="focal"))
    
    # Add supporting features (context)
    for i, feat in enumerate(composition.supporting_features):
        actions.append(_feature_to_action(feat, label=f"supporting_{i}"))
    
    # Add accent features (visual interest)
    for i, feat in enumerate(composition.accent_features):
        actions.append(_feature_to_action(feat, label=f"accent_{i}"))
    
    # Add background features (if any)
    for i, feat in enumerate(composition.background_features):
        actions.append(_feature_to_action(feat, label=f"background_{i}"))
    
    # Add foreground features (if any)
    for i, feat in enumerate(composition.foreground_features):
        actions.append(_feature_to_action(feat, label=f"foreground_{i}"))
    
    return actions


def _feature_to_action(feat: Feature, label: str = "") -> Dict:
    """
    Convert single Feature → action dict.
    
    Args:
        feat: Typed Feature instance
        label: Optional label for scene graph tracking
    
    Returns:
        Action dict compatible with AddFeatureCommand
    """
    action = {
        "kind": "add",
        "type": feat.type,
        "position": _position_to_dict(feat.position),
        "modifiers": _params_to_modifiers(feat.parameters),
        "count": 1
    }
    
    # Add label if provided (for scene graph)
    if label:
        action["label"] = label
    
    return action


def _position_to_dict(position) -> Dict:
    """Convert Position → position dict."""
    if position.is_absolute():
        return {"x": position.x, "y": position.y}
    elif position.is_region():
        return {"region": position.region}
    elif position.is_relative():
        return {
            "relative_to": position.relative_to,
            "offset_x": position.offset_x,
            "offset_y": position.offset_y
        }
    else:
        # Default to center
        return {"region": "center"}


def _params_to_modifiers(params: FeatureParameters) -> Dict:
    """
    Convert FeatureParameters → modifier dict.
    
    Translates typed parameters back to modifier format for variation engine.
    """
    modifiers = {}
    
    # Standard parameters
    if params.height is not None:
        modifiers["height"] = params.height
    if params.depth is not None:
        modifiers["depth"] = params.depth
    if params.radius is not None:
        modifiers["radius"] = params.radius
    if params.steepness is not None:
        modifiers["steepness"] = params.steepness
    
    # Extra parameters (stored in params dict)
    modifiers.update(params.params)
    
    return modifiers


def actions_to_composition(actions: List[Dict], seed: int = 42) -> FeatureComposition:
    """
    REVERSE: Convert action dicts → FeatureComposition.
    
    Useful for round-trip testing and for converting old actions to new format.
    """
    from ...engine.feature_registry import FeatureRegistry
    
    focal = None
    supporting = []
    accents = []
    
    for i, action in enumerate(actions):
        # Create feature using registry
        ftype = action["type"]
        pos = action["position"]
        modifiers = action.get("modifiers", {})
        
        cx = pos.get("x", 256)
        cy = pos.get("y", 256)
        
        feat = FeatureRegistry.create_feature(ftype, cx, cy, modifiers, seed + i)
        
        # Categorize based on label or order
        label = action.get("label", "")
        if "focal" in label or i == 0:
            focal = feat
        elif "supporting" in label or i < 4:
            supporting.append(feat)
        else:
            accents.append(feat)
    
    return FeatureComposition(
        focal_point=focal,
        supporting_features=supporting,
        accent_features=accents,
        background_features=[],
        foreground_features=[],
        depth_layers=[],
        negative_space_zones=[],
        golden_ratio_used=False,
        rule_of_thirds_used=False,
        leading_lines=[],
        rhythmic_elements=[],
        variation_pattern="organic"
    )
```

**Test:**
```python
# tests/semantic/test_converters.py
def test_composition_to_actions_conversion():
    """Test that FeatureComposition converts to valid actions."""
    from semantic.narrative.generation import generate_from_narrative
    from semantic.narrative.converters import composition_to_actions
    
    # Generate composition
    narrative = create_minimal_narrative()
    composition = generate_from_narrative(narrative, {}, seed=42)
    
    # Convert to actions
    actions = composition_to_actions(composition)
    
    # Should have actions for focal + supporting + accents
    assert len(actions) >= 3
    
    # All should be valid action dicts
    for action in actions:
        assert "kind" in action
        assert action["kind"] == "add"
        assert "type" in action
        assert "position" in action
        assert "modifiers" in action
```

---

### **Task 4.2: Create `NarrativeParser`** (1.5 hours)

**File:** `server/semantic/narrative_parser.py` (**NEW**)

```python
"""
Narrative-driven parser for intelligent terrain generation.

This parser uses the narrative system to generate high-quality, coherent
terrain compositions instead of simple feature-by-feature addition.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NarrativeParser:
    """
    Parser that uses narrative system for intelligent generation.
    
    Flow:
        command → narrative → composition → actions
    
    This is the MAIN INTEGRATION POINT between narrative AI and terrain generation.
    """
    
    def __init__(self):
        """Initialize narrative parser."""
        self.use_narrative = True  # Can be disabled for debugging
    
    def parse(self, command: str, scene_state: Optional[Dict] = None) -> Dict:
        """
        Parse command using narrative system.
        
        Args:
            command: Natural language command
            scene_state: Current scene state (for context)
        
        Returns:
            {"actions": [action_dicts], "narrative": narrative_obj}
        """
        if not self.use_narrative:
            # Fallback to simple parser
            return self._simple_parse(command)
        
        try:
            # Step 1: Develop narrative
            logger.info(f"Developing narrative for: {command[:50]}...")
            narrative = self._develop_narrative(command, scene_state)
            
            # Step 2: Generate features
            logger.info(f"Generating features from narrative (archetype: {narrative.archetype.name})")
            composition = self._generate_composition(narrative, scene_state)
            
            # Step 3: Convert to actions
            logger.info(f"Converting composition to actions...")
            actions = self._composition_to_actions(composition)
            
            logger.info(f"Narrative parser generated {len(actions)} actions")
            
            return {
                "actions": actions,
                "narrative": narrative,  # Include for debugging/refinement
                "composition": composition  # Include for iteration
            }
        
        except Exception as e:
            logger.warning(f"Narrative parsing failed: {e}, falling back to simple parser")
            return self._simple_parse(command)
    
    def _develop_narrative(self, command: str, scene_state: Optional[Dict]) -> 'TerrainNarrative':
        """Step 1: Command → narrative."""
        from .narrative.narrative_dev import develop_terrain_narrative
        
        if scene_state is None:
            scene_state = {}
        
        return develop_terrain_narrative(command, scene_state)
    
    def _generate_composition(self, narrative: 'TerrainNarrative', scene_state: Dict) -> 'FeatureComposition':
        """Step 2: Narrative → typed features."""
        from .narrative.generation import generate_from_narrative
        
        # Use narrative's seed if available
        seed = getattr(narrative, 'seed', 42)
        
        return generate_from_narrative(narrative, scene_state, seed=seed)
    
    def _composition_to_actions(self, composition: 'FeatureComposition') -> List[Dict]:
        """Step 3: Features → actions."""
        from .narrative.converters import composition_to_actions
        
        return composition_to_actions(composition)
    
    def _simple_parse(self, command: str) -> Dict:
        """Fallback to simple parsing."""
        from .parsing import CommandParser
        
        parser = CommandParser()
        return parser.parse(command, context={})


def should_use_narrative(command: str) -> bool:
    """
    Determine if command should use narrative system.
    
    Narrative system is better for:
    - Creative/aesthetic requests ("dramatic", "beautiful", "epic")
    - Vague directions ("make it interesting")
    - Complex scenes ("mountain range with valleys")
    
    Simple parser is better for:
    - Precise commands ("add 3 mountains at 256,256")
    - Modifications ("make the mountain taller")
    - Removals ("remove the last mountain")
    """
    # Narrative keywords
    narrative_keywords = [
        "dramatic", "beautiful", "epic", "vast", "rugged", "smooth",
        "interesting", "varied", "diverse", "natural", "realistic",
        "landscape", "scene", "terrain", "composition"
    ]
    
    # Simple command keywords
    simple_keywords = [
        "add", "remove", "delete", "modify", "make", "taller", "shorter",
        "wider", "narrower", "at", "near", "between"
    ]
    
    cmd_lower = command.lower()
    
    # Check for narrative keywords
    has_narrative = any(kw in cmd_lower for kw in narrative_keywords)
    
    # Check for specific positioning or modification
    has_simple = any(kw in cmd_lower for kw in simple_keywords)
    
    # If both, prefer narrative (more intelligent)
    if has_narrative:
        return True
    
    # If simple keywords only, use simple parser
    if has_simple and not has_narrative:
        return False
    
    # Default: use narrative for richer results
    return True
```

**Test:**
```python
# tests/semantic/test_narrative_parser.py
def test_narrative_parser_generates_actions():
    """Test that NarrativeParser generates valid actions."""
    parser = NarrativeParser()
    
    result = parser.parse("create dramatic mountains", scene_state={})
    
    # Should return actions
    assert "actions" in result
    assert len(result["actions"]) >= 1
    
    # Should include narrative for debugging
    assert "narrative" in result
    assert "composition" in result
    
    # Actions should be valid
    for action in result["actions"]:
        assert action["kind"] == "add"
        assert "type" in action
        assert "position" in action
```

---

### **Task 4.3: Integrate with ReAct Agent** (1 hour)

**File:** `server/semantic/react_agent_v2.py`

**Add method:**
```python
def _should_use_narrative(self, command: str) -> bool:
    """Determine if command warrants narrative generation."""
    from .narrative_parser import should_use_narrative
    return should_use_narrative(command)

def _generate_with_narrative(self, command: str, scene_state: Dict) -> List[Dict]:
    """Generate actions using narrative system."""
    from .narrative_parser import NarrativeParser
    
    parser = NarrativeParser()
    result = parser.parse(command, scene_state)
    
    return result["actions"]
```

**Update `solve` method:**
```python
def solve(self, command: str, scene_state: Dict) -> Dict:
    """
    ReAct loop with narrative integration.
    """
    # Check if we should use narrative system
    if self._should_use_narrative(command):
        logger.info("Using narrative system for intelligent generation")
        try:
            actions = self._generate_with_narrative(command, scene_state)
            return {
                "success": True,
                "actions": actions,
                "iterations": 1,
                "total_tool_calls": 0,
                "method": "narrative"
            }
        except Exception as e:
            logger.warning(f"Narrative generation failed: {e}, using ReAct loop")
    
    # Fall back to ReAct loop for complex queries
    # ... existing ReAct logic ...
```

---

## 📋 **PHASE 5: Test End-to-End**

### **Task 5.1: Integration Test** (1 hour)

**File:** `server/tests/integration/test_narrative_integration.py` (**NEW**)

```python
"""
End-to-end integration tests for narrative system.
"""

import pytest
from terrain import apply_actions


class TestNarrativeIntegration:
    """Test complete flow: command → narrative → features → terrain."""
    
    def test_narrative_command_generates_terrain(self):
        """Test that narrative commands produce valid terrain."""
        state = {"features": [], "seed": 42}
        
        # Use narrative-friendly command
        heightmap, updated_state, splatmap = apply_actions(
            "create a dramatic mountain landscape",
            state,
            seed=42
        )
        
        # Should produce valid outputs
        assert heightmap.shape == (512, 512)
        assert splatmap.shape == (512, 512, 4)
        
        # Should have features (focal + supporting + accents)
        assert len(updated_state["features"]) >= 3
        
        # Mountains should be tall (dramatic)
        max_height = heightmap.max()
        assert max_height > 0.7, "Dramatic mountains should be tall!"
    
    def test_narrative_uses_typed_features(self):
        """Verify that narrative path uses typed Features internally."""
        from semantic.narrative_parser import NarrativeParser
        from domain.models import Feature
        
        parser = NarrativeParser()
        result = parser.parse("epic mountains", scene_state={})
        
        # Composition should have typed Features
        composition = result["composition"]
        assert isinstance(composition.focal_point, Feature)
        
        # Actions should be valid dicts
        actions = result["actions"]
        assert all(isinstance(a, dict) for a in actions)
```

---

## ✅ **Success Criteria:**

After completing all phases:

1. ✅ `FeatureState.add_feature(Feature(...))` works
2. ✅ `_apply_feature_to_builder(builder, Feature(...), seed)` works
3. ✅ `composition_to_actions(composition)` converter works
4. ✅ `NarrativeParser.parse(command)` generates valid actions
5. ✅ End-to-end: "dramatic mountains" → terrain with 3+ features
6. ✅ All 80+ tests still passing
7. ✅ Narrative system actually called in production

---

## 📊 **Timeline:**

| Phase | Tasks | Time | Status |
|-------|-------|------|--------|
| **Phase 3** | Fix type bridges | 1.5h | ⏳ Pending |
| **Phase 4** | Connect narrative | 3.5h | ⏳ Pending |
| **Phase 5** | Test integration | 1h | ⏳ Pending |
| **TOTAL** | 7 tasks | **6h** | ⏳ **Not Started** |

---

## 🎯 **After This, We'll Have:**

- ✅ Typed Features used in production
- ✅ Narrative system connected to pipeline
- ✅ `generate_from_narrative` actually called
- ✅ End-to-end type safety
- ✅ True "hybrid approach" working

**Then we can move to Week 2-4 narrative tools with confidence!**

---

**Ready to proceed?** 🚀

##
