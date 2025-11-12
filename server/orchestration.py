"""
Helper functions for terrain generation orchestration.

These functions break down the complex apply_actions() workflow into
clear, single-purpose steps that are easy to understand and test.
"""
import logging
from typing import Dict, List, Tuple, Optional, Set

from .semantic.narrative.utils import run_narrative_pipeline

logger = logging.getLogger(__name__)


def init_scene_graph(state: Dict):
    """
    Initialize or load scene graph from state.
    
    Args:
        state: Terrain state dictionary
    
    Returns:
        TerrainSceneGraph instance or None if initialization fails
    """
    try:
        from .semantic.scene import TerrainSceneGraph, SceneGraphSerializer
        
        if "semantic_scene" in state:
            scene_graph = SceneGraphSerializer.from_dict(state["semantic_scene"])
        else:
            scene_graph = TerrainSceneGraph()
            state["semantic_scene"] = SceneGraphSerializer.to_dict(scene_graph)
        
        return scene_graph
        
    except (ValueError, KeyError, AttributeError, ImportError) as e:
        logger.warning(f"Scene graph initialization failed: {e}, continuing without scene graph")
        return None


def parse_command_to_actions(
    command: str,
    state: Dict,
    direct_actions: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Parse command into list of action dictionaries.
    
    Handles three cases:
    1. Direct actions (pre-structured JSON)
    2. Empty command (rebuild from state only)
    3. Natural language command (use parser)
    
    Args:
        command: Natural language command string
        state: Terrain state for context
        direct_actions: Optional pre-structured actions
    
    Returns:
        List of action dictionaries
    """
    # Case 1: Direct JSON actions (compositional API calls)
    if direct_actions is not None:
        return direct_actions
    
    # Case 2: Empty command - just rebuild, no new actions
    if not command or not command.strip():
        return []
    
    try:
        actions, metadata = run_narrative_pipeline(command, state)
        if actions:
            if isinstance(state, dict):
                state["_debug_last_parser"] = "narrative"
                state["_last_narrative_meta"] = metadata
            logger.info("Narrative pipeline executed with %d actions", len(actions))
            return actions
    except Exception as narrative_exc:
        logger.warning(
            "Narrative pipeline exception for '%s': %s",
            command[:60], narrative_exc,
            exc_info=True
        )
 
    # FIX: Use SemanticParser (advanced with scene graph context) instead of CommandParser
    try:
        from .semantic.parser import SemanticParser
        parser = SemanticParser()
        parsed = parser.parse(command, scene_state=state)  # Pass scene_state for full context!
        if isinstance(state, dict):
            state["_debug_last_parser"] = "semantic"
        return parsed.get("actions", [])
    except ValueError as e:
        # SemanticParser unavailable (no API key) - graceful fallback to CommandParser
        logger.info(f"SemanticParser unavailable ({e}), falling back to CommandParser")
        try:
            from .parsing import CommandParser
            parser = CommandParser()
            parsed = parser.parse(command, context=state)
            if isinstance(state, dict):
                state["_debug_last_parser"] = "regex"
            return parsed.get("actions", [])
        except (ImportError, ValueError, KeyError) as e2:
            logger.warning(f"All parsers failed: {e2}, returning no actions")
            return []
    except (ImportError, KeyError) as e:
        # SemanticParser import/execution failed - fall back to CommandParser
        logger.warning(f"SemanticParser failed ({e}), falling back to CommandParser")
        try:
            from .parsing import CommandParser
            parser = CommandParser()
            parsed = parser.parse(command, context=state)
            if isinstance(state, dict):
                state["_debug_last_parser"] = "regex"
            return parsed.get("actions", [])
        except (ImportError, ValueError, KeyError) as e2:
            logger.warning(f"All parsers failed: {e2}, returning no actions")
            return []
    
    # OLD IMPLEMENTATION (kept for reference):
    # try:
    #     from .parsing import CommandParser
    #     parser = CommandParser()
    #     parsed = parser.parse(command, context=state)
    #     return parsed.get("actions", [])
    # except (ImportError, ValueError, KeyError) as e:
    #     logger.warning(f"Command parsing failed: {e}, returning no actions")
    #     return []


def partition_actions(actions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Partition actions into remove/modify vs add.
    
    Remove and modify actions must execute first (they operate on existing features).
    Add actions execute after (they create new features).
    
    Args:
        actions: List of action dictionaries
    
    Returns:
        Tuple of (remove_modify_actions, add_actions)
    """
    remove_modify = [a for a in actions if a.get("kind") in ("remove", "modify")]
    add = [a for a in actions if a.get("kind") == "add"]
    return remove_modify, add


def resolve_removal_targets(
    actions: List[Dict],
    scene_graph,
    feature_state
) -> List[int]:
    """
    Resolve which feature IDs will be removed.
    
    Uses scene graph for reference resolution (e.g., "remove the dunes").
    Tracks IDs for later scene graph cleanup.
    
    Args:
        actions: List of remove actions
        scene_graph: TerrainSceneGraph instance (may be None)
        feature_state: FeatureState manager
    
    Returns:
        List of feature IDs that will be removed
    """
    removed_ids = []
    
    if not scene_graph:
        return removed_ids
    
    from .semantic.scene import SceneGraphIntegrator
    
    for action_dict in actions:
        if action_dict.get("kind") != "remove":
            continue
        
        # Try to resolve target_feature_ids using scene graph
        target_ids = SceneGraphIntegrator.resolve_target_features(scene_graph, action_dict)
        if target_ids:
            action_dict["target_feature_ids"] = target_ids
            removed_ids.extend(target_ids)
        else:
            # Fallback: track by type (will remove most recent)
            feature_type = action_dict.get("type")
            if feature_type:
                existing = feature_state.list_features()
                matching = [f for f in existing if f.get("type") == feature_type]
                if matching:
                    removed_ids.append(matching[-1].get("id"))
    
    return removed_ids


def execute_state_actions(
    actions: List[Dict],
    feature_state,
    seed: int
) -> Set[int]:
    """
    Execute remove/modify actions (state-only operations).
    
    Args:
        actions: List of remove/modify action dictionaries
        feature_state: FeatureState manager
        seed: Random seed
    
    Returns:
        Set of feature IDs that were actually removed
    """
    from .engine.commands import create_command_from_dict
    
    # Get feature IDs before removal
    features_before = feature_state.list_features()
    ids_before = {f.get("id") for f in features_before if "id" in f}
    
    # Execute each action
    for action_dict in actions:
        try:
            command = create_command_from_dict(action_dict)
            command.execute(None, feature_state, seed)  # Builder=None for state-only ops
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to execute action {action_dict.get('kind')}: {e}")
    
    # Get feature IDs after removal to determine what was actually removed
    features_after = feature_state.list_features()
    ids_after = {f.get("id") for f in features_after if "id" in f}
    
    return ids_before - ids_after


def cleanup_scene_graph(scene_graph, removed_feature_ids: List[int]):
    """
    Remove scene graph entities for deleted features.
    
    Args:
        scene_graph: TerrainSceneGraph instance (may be None)
        removed_feature_ids: List of feature IDs that were removed
    """
    if not scene_graph or not removed_feature_ids:
        return
    
    try:
        from .semantic.scene import SceneGraphIntegrator
        SceneGraphIntegrator.cleanup_for_removed_features(
            scene_graph,
            list(set(removed_feature_ids))  # Deduplicate
        )
    except (ImportError, AttributeError, ValueError) as e:
        logger.warning(f"Scene graph cleanup failed: {e}")


def execute_add_actions(
    actions: List[Dict],
    builder,
    feature_state,
    scene_graph,
    seed: int,
    command: str
) -> List[Dict]:
    """
    Execute add actions (create and apply new features).
    
    Args:
        actions: List of add action dictionaries
        builder: TerrainBuilder instance
        feature_state: FeatureState manager
        scene_graph: TerrainSceneGraph instance (may be None)
        seed: Random seed
        command: Original user command (for scene graph metadata)
    
    Returns:
        List of created feature info dicts (for scene graph integration)
    """
    from .engine.commands import create_command_from_dict
    
    created_features = []
    
    for action_dict in actions:
        # Track features before
        features_before = len(feature_state.list_features())
        
        try:
            # Execute command (creates and applies features)
            command_obj = create_command_from_dict(action_dict)
            command_obj.execute(builder, feature_state, seed)
            
            # Get newly created features
            features_after = feature_state.list_features()
            new_features = features_after[features_before:]
            
            if new_features and scene_graph:
                feature_ids = [f.get("id") for f in new_features if "id" in f]
                if feature_ids:
                    created_features.append({
                        "action": action_dict,
                        "feature_ids": feature_ids,
                        "feature_data": new_features,
                        "command": command
                    })
        
        except (ValueError, KeyError, TypeError, ImportError) as e:
            logger.warning(f"Failed to execute add action: {e}")
    
    return created_features


def update_scene_graph_for_additions(scene_graph, created_features: List[Dict]):
    """
    Create scene graph entities for newly added features.
    
    Args:
        scene_graph: TerrainSceneGraph instance (may be None)
        created_features: List of feature info dicts from execute_add_actions()
    """
    if not scene_graph or not created_features:
        return
    
    from .semantic.scene import SceneGraphIntegrator
    
    for item in created_features:
        try:
            SceneGraphIntegrator.update_scene_graph_for_action(
                scene_graph,
                item["action"],
                item["feature_ids"],
                item["command"],  # command (str) comes before feature_data_list
                feature_data_list=item["feature_data"]
            )
        except (ValueError, AttributeError, ImportError) as e:
            logger.warning(f"Failed to create scene graph entity: {e}")


def build_final_terrain(feature_state, base_biome_fn, seed: int):
    """
    Build final terrain from all features in state.
    
    Args:
        feature_state: FeatureState with all features
        base_biome_fn: Base biome generation function
        seed: Random seed
    
    Returns:
        Tuple of (heightmap, splatmap)
    """
    from .engine.builder import TerrainBuilder
    from .terrain import _apply_feature_to_builder
    
    # Create fresh builder
    builder = TerrainBuilder(base_biome_fn, seed)
    
    # Apply all features
    for feat in feature_state.list_features():
        try:
            _apply_feature_to_builder(builder, feat, seed)
        except (ValueError, KeyError, ImportError) as e:
            logger.warning(f"Failed to apply feature {feat.get('type')}: {e}")
    
    # Generate outputs
    heightmap = builder.get_heightmap()
    # FIX: Method name was get_splatmap() but actual method is build_splatmap()
    splatmap = builder.build_splatmap()  # FIXED: was get_splatmap()
    
    return heightmap, splatmap

