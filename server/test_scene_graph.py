"""Tests for Phase 2: Semantic Scene Graph Core Structure.

Tests the core scene graph functionality including:
- SceneNode operations
- TerrainSceneGraph management
- SemanticEntity operations
- EntityManager CRUD
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from semantic.scene import SceneNode, TerrainSceneGraph, SemanticEntity, EntityManager, ReferenceResolver


def test_scene_node_basic():
    """Test basic SceneNode operations."""
    print("Testing SceneNode basic operations...")
    
    # Create root node
    root = SceneNode("/World")
    assert root.path == "/World"
    assert root.name == "World"
    assert root.is_root()
    assert root.get_depth() == 0
    
    # Add child
    child = root.add_child("Features")
    assert child.path == "/World/Features"
    assert child.name == "Features"
    assert child.parent == root
    assert child.get_depth() == 1
    assert not child.is_root()
    
    # Get child
    retrieved = root.get_child("Features")
    assert retrieved == child
    
    # Add feature IDs
    child.add_feature_id(1)
    child.add_feature_id(2)
    assert child.feature_ids == [1, 2]
    
    # Remove feature ID
    assert child.remove_feature_id(1) == True
    assert child.feature_ids == [2]
    
    print("  ✅ SceneNode basic operations passed")


def test_scene_node_traversal():
    """Test SceneNode traversal."""
    print("Testing SceneNode traversal...")
    
    root = SceneNode("/World")
    features = root.add_child("Features")
    mountains = features.add_child("Mountains")
    mountain1 = mountains.add_child("Mountain_1")
    mountain2 = mountains.add_child("Mountain_2")
    
    # Depth-first traversal
    nodes = list(root.traverse())
    assert len(nodes) == 5  # root, features, mountains, mountain1, mountain2
    assert nodes[0] == root
    assert nodes[1] == features
    
    # Breadth-first traversal
    nodes_bfs = list(root.traverse(depth_first=False))
    assert len(nodes_bfs) == 5
    assert nodes_bfs[0] == root
    assert nodes_bfs[1] == features
    
    # Get all descendants
    descendants = features.get_all_descendants()
    assert len(descendants) == 3  # mountains, mountain1, mountain2
    
    print("  ✅ SceneNode traversal passed")


def test_scene_node_path_lookup():
    """Test path-based node lookup."""
    print("Testing SceneNode path lookup...")
    
    root = SceneNode("/World")
    features = root.add_child("Features")
    mountains = features.add_child("Mountains")
    mountain1 = mountains.add_child("Mountain_1")
    
    # Absolute path
    found = root.get_child_by_path("/World/Features/Mountains/Mountain_1")
    assert found == mountain1
    
    # Relative path
    found = mountains.get_child_by_path("Mountain_1")
    assert found == mountain1
    
    # Non-existent path
    found = root.get_child_by_path("/World/Features/Valleys")
    assert found is None
    
    print("  ✅ SceneNode path lookup passed")


def test_scene_node_serialization():
    """Test SceneNode serialization."""
    print("Testing SceneNode serialization...")
    
    root = SceneNode("/World")
    features = root.add_child("Features")
    mountains = features.add_child("Mountains")
    mountains.add_feature_id(1)
    mountains.set_data("type", "group")
    
    # Serialize
    data = root.to_dict()
    assert data["path"] == "/World"
    assert len(data["children"]) == 1
    assert data["children"]["Features"]["children"]["Mountains"]["feature_ids"] == [1]
    
    # Deserialize
    restored = SceneNode.from_dict(data)
    assert restored.path == "/World"
    assert restored.get_child("Features").get_child("Mountains").feature_ids == [1]
    
    print("  ✅ SceneNode serialization passed")


def test_terrain_scene_graph():
    """Test TerrainSceneGraph operations."""
    print("Testing TerrainSceneGraph...")
    
    graph = TerrainSceneGraph()
    
    # Check root structure
    assert graph.root.path == "/World"
    assert graph.features_root.path == "/World/Features"
    assert graph.semantics_root.path == "/World/Semantics"
    
    # Add feature group
    group = graph.add_feature_group("Mountains", "the mountains")
    assert group.path == "/World/Features/Mountains"
    assert group.get_data("semantic_label") == "the mountains"
    
    # Get feature group
    retrieved = graph.get_feature_group("Mountains")
    assert retrieved == group
    
    # Add feature
    feature_data = {"id": 1, "type": "mountain", "x": 128, "y": 256}
    feature_node = graph.add_feature(feature_data, "Mountains")
    assert feature_node.feature_ids == [1]
    assert feature_node.get_data("type") == "mountain"
    
    # Find feature by ID
    found = graph.find_feature_by_id(1)
    assert found == feature_node
    
    # Find features by type
    mountains = graph.find_features_by_type("mountain")
    assert len(mountains) == 1
    assert mountains[0] == feature_node
    
    # Get all feature IDs
    feature_ids = graph.get_feature_ids()
    assert 1 in feature_ids
    
    print("  ✅ TerrainSceneGraph passed")


def test_semantic_entity():
    """Test SemanticEntity operations."""
    print("Testing SemanticEntity...")
    
    entity = SemanticEntity("dunes_1", "group", "the dunes")
    entity.add_keywords(["dunes", "desert", "sandy"])
    entity.add_feature_refs([1, 2, 3])
    entity.set_description("Rolling sand dunes")
    entity.set_user_intent("create a desert with rolling dunes")
    
    # Check properties
    assert entity.id == "dunes_1"
    assert entity.type == "group"
    assert entity.label == "the dunes"
    assert len(entity.keywords) == 3
    assert entity.feature_refs == [1, 2, 3]
    
    # Test matching
    assert entity.matches_label("the dunes")
    assert entity.matches_label("dunes")
    assert entity.matches_keyword("sandy")
    assert entity.matches("desert")
    
    # Serialization
    data = entity.to_dict()
    assert data["id"] == "dunes_1"
    assert data["feature_refs"] == [1, 2, 3]
    
    # Deserialization
    restored = SemanticEntity.from_dict(data)
    assert restored.id == "dunes_1"
    assert restored.feature_refs == [1, 2, 3]
    
    print("  ✅ SemanticEntity passed")


def test_entity_manager():
    """Test EntityManager operations."""
    print("Testing EntityManager...")
    
    graph = TerrainSceneGraph()
    
    # Add features first
    feature1 = graph.add_feature({"id": 1, "type": "dunes"}, "Desert_Group")
    feature2 = graph.add_feature({"id": 2, "type": "dunes"}, "Desert_Group")
    
    manager = EntityManager(graph)
    
    # Create and add entity
    entity = SemanticEntity("dunes_1", "group", "the dunes")
    entity.add_keywords(["dunes", "desert"])
    entity.add_feature_refs([1, 2])
    manager.add_entity(entity)
    
    # Find entity
    found = manager.find_entity_by_id("dunes_1")
    assert found is not None
    assert found.label == "the dunes"
    
    # Find by label
    found = manager.find_entity_by_label("the dunes")
    assert found is not None
    
    # Find matching
    matches = manager.find_entities_matching("dunes")
    assert len(matches) >= 1
    
    # Get all entities
    all_entities = manager.get_all_entities()
    assert len(all_entities) == 1
    
    # Check links to feature nodes
    feature_node = graph.find_feature_by_id(1)
    assert feature_node is not None
    semantic_refs = feature_node.get_data("semantic_refs", [])
    assert "dunes_1" in semantic_refs
    
    print("  ✅ EntityManager passed")


def test_integration():
    """Test integration of all components."""
    print("Testing integration...")
    
    graph = TerrainSceneGraph()
    manager = EntityManager(graph)
    
    # Add features
    graph.add_feature({"id": 1, "type": "mountain", "x": 128, "y": 256}, "Mountains")
    graph.add_feature({"id": 2, "type": "mountain", "x": 384, "y": 256}, "Mountains")
    
    # Create entity
    entity = SemanticEntity("mountains_1", "group", "two mountains")
    entity.add_keywords(["mountain", "peak"])
    entity.add_feature_refs([1, 2])
    manager.add_entity(entity)
    
    # Query
    mountains = graph.find_features_by_type("mountain")
    assert len(mountains) == 2
    
    # Find entity
    found = manager.find_entity_by_label("two mountains")
    assert found is not None
    assert len(found.feature_refs) == 2
    
    # Serialize graph
    graph_dict = graph.to_dict()
    assert "root" in graph_dict
    
    # Deserialize
    new_graph = TerrainSceneGraph()
    new_graph.from_dict(graph_dict)
    assert len(new_graph.get_feature_ids()) == 2
    
    print("  ✅ Integration test passed")


def test_reference_resolver_label():
    """Test reference resolution by label."""
    print("Testing ReferenceResolver - Label resolution...")
    
    graph = TerrainSceneGraph()
    manager = EntityManager(graph)
    
    # Add features
    graph.add_feature({"id": 1, "type": "dunes"}, "Desert_Group")
    graph.add_feature({"id": 2, "type": "dunes"}, "Desert_Group")
    
    # Create entity
    entity = SemanticEntity("dunes_1", "group", "the dunes")
    entity.add_feature_refs([1, 2])
    manager.add_entity(entity)
    
    # Resolve by label
    resolver = ReferenceResolver(graph)
    feature_ids = resolver.resolve("the dunes")
    assert feature_ids == [1, 2]
    
    # Resolve without "the"
    feature_ids = resolver.resolve("dunes")
    assert feature_ids == [1, 2]
    
    print("  ✅ ReferenceResolver label resolution passed")


def test_reference_resolver_keyword():
    """Test reference resolution by keyword."""
    print("Testing ReferenceResolver - Keyword resolution...")
    
    graph = TerrainSceneGraph()
    manager = EntityManager(graph)
    
    # Add features
    graph.add_feature({"id": 1, "type": "dunes"}, "Desert_Group")
    
    # Create entity with keywords
    entity = SemanticEntity("desert_1", "scene", "desert scene")
    entity.add_keywords(["desert", "sandy", "arid"])
    entity.add_feature_refs([1])
    manager.add_entity(entity)
    
    # Resolve by keyword
    resolver = ReferenceResolver(graph)
    feature_ids = resolver.resolve("sandy")
    assert feature_ids == [1]
    
    feature_ids = resolver.resolve("arid")
    assert feature_ids == [1]
    
    print("  ✅ ReferenceResolver keyword resolution passed")


def test_reference_resolver_type():
    """Test reference resolution by feature type."""
    print("Testing ReferenceResolver - Type resolution...")
    
    graph = TerrainSceneGraph()
    
    # Add features
    graph.add_feature({"id": 1, "type": "mountain"}, "Mountains")
    graph.add_feature({"id": 2, "type": "mountain"}, "Mountains")
    graph.add_feature({"id": 3, "type": "valley"}, "Valleys")
    
    # Resolve by type
    resolver = ReferenceResolver(graph)
    feature_ids = resolver.resolve("the mountains")
    assert set(feature_ids) == {1, 2}
    
    feature_ids = resolver.resolve("mountain")
    assert set(feature_ids) == {1, 2}
    
    feature_ids = resolver.resolve("valleys")
    assert feature_ids == [3]
    
    print("  ✅ ReferenceResolver type resolution passed")


def test_reference_resolver_ordinal():
    """Test reference resolution with ordinals."""
    print("Testing ReferenceResolver - Ordinal resolution...")
    
    graph = TerrainSceneGraph()
    
    # Add features in order
    graph.add_feature({"id": 1, "type": "mountain"}, "Mountains")
    graph.add_feature({"id": 2, "type": "mountain"}, "Mountains")
    graph.add_feature({"id": 3, "type": "mountain"}, "Mountains")
    
    resolver = ReferenceResolver(graph)
    
    # Test "first"
    feature_ids = resolver.resolve("first mountain")
    assert feature_ids == [1]
    
    # Test "last"
    feature_ids = resolver.resolve("last mountain")
    assert feature_ids == [3]
    
    # Test "second"
    feature_ids = resolver.resolve("second mountain")
    assert feature_ids == [2]
    
    # Test "the last"
    feature_ids = resolver.resolve("the last mountain")
    assert feature_ids == [3]
    
    print("  ✅ ReferenceResolver ordinal resolution passed")


def test_reference_resolver_most_recent():
    """Test reference resolution for most recent."""
    print("Testing ReferenceResolver - Most recent resolution...")
    
    graph = TerrainSceneGraph()
    
    # Add features
    graph.add_feature({"id": 1, "type": "valley"}, "Valleys")
    graph.add_feature({"id": 2, "type": "valley"}, "Valleys")
    
    resolver = ReferenceResolver(graph)
    
    # Test "most recent"
    feature_ids = resolver.resolve("most recent valley")
    assert feature_ids == [2]
    
    # Test "latest"
    feature_ids = resolver.resolve("latest valley")
    assert feature_ids == [2]
    
    print("  ✅ ReferenceResolver most recent resolution passed")


def test_reference_resolver_multi_strategy():
    """Test multi-strategy resolution fallback."""
    print("Testing ReferenceResolver - Multi-strategy fallback...")
    
    graph = TerrainSceneGraph()
    manager = EntityManager(graph)
    
    # Add features
    graph.add_feature({"id": 1, "type": "mountain"}, "Mountains")
    graph.add_feature({"id": 2, "type": "mountain"}, "Mountains")
    
    # Create entity
    entity = SemanticEntity("mountains_1", "group", "two mountains")
    entity.add_keywords(["mountain", "peak"])
    entity.add_feature_refs([1, 2])
    manager.add_entity(entity)
    
    resolver = ReferenceResolver(graph)
    
    # Strategy 1: Label match (should work)
    feature_ids = resolver.resolve("two mountains")
    assert set(feature_ids) == {1, 2}
    
    # Strategy 2: Keyword match (should work)
    feature_ids = resolver.resolve("peak")
    assert set(feature_ids) == {1, 2}
    
    # Strategy 3: Type match (fallback, should work)
    feature_ids = resolver.resolve("mountains")
    assert set(feature_ids) == {1, 2}
    
    # Strategy 4: Ordinal (should work)
    feature_ids = resolver.resolve("last mountain")
    assert feature_ids == [2]
    
    print("  ✅ ReferenceResolver multi-strategy passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("Phase 2: Core Structure + Reference Resolution Tests")
    print("=" * 70)
    print()
    
    try:
        # Phase 2.1 & 2.2: Core Structure
        test_scene_node_basic()
        test_scene_node_traversal()
        test_scene_node_path_lookup()
        test_scene_node_serialization()
        test_terrain_scene_graph()
        test_semantic_entity()
        test_entity_manager()
        test_integration()
        
        # Phase 2.3: Reference Resolution
        test_reference_resolver_label()
        test_reference_resolver_keyword()
        test_reference_resolver_type()
        test_reference_resolver_ordinal()
        test_reference_resolver_most_recent()
        test_reference_resolver_multi_strategy()
        
        print()
        print("=" * 70)
        print("✅ ALL TESTS PASSED! Phase 2.1, 2.2 & 2.3 Complete!")
        print("=" * 70)
        print()
        print("Completed:")
        print("  ✅ Core Structure (Phase 2.1)")
        print("  ✅ Entity System (Phase 2.2)")
        print("  ✅ Reference Resolution (Phase 2.3)")
        print()
        print("Next steps:")
        print("  1. Implement query.py (Phase 2.4)")
        print("  2. Implement serialization.py (Phase 2.5)")
        print("  3. Implement integration.py (Phase 2.6)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

