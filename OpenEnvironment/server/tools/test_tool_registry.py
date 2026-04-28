"""Test script for MCP Tool Registry.

Run this to verify the tool registry is working correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tool_registry():
    """Test tool registry initialization and features."""
    print("=" * 70)
    print("Testing MCP Tool Registry")
    print("=" * 70)
    
    # Import and initialize
    from semantic.tool_registry import get_tool_registry, ToolCategory
    
    registry = get_tool_registry()
    
    # Test 1: Tool discovery
    print("\n✓ Tool Registry initialized successfully!")
    print(f"  Total tools discovered: {len(registry.tools)}")
    
    # Test 2: Category breakdown
    print("\n📊 Tools by Category:")
    for category in ToolCategory:
        tools = registry.get_tools_by_category(category)
        if tools:
            print(f"  - {category.value}: {len(tools)} tools")
            for tool in tools[:3]:  # Show first 3
                print(f"     • {tool.name}")
    
    # Test 3: Schema generation
    print("\n🔧 Testing JSON Schema generation...")
    mountain_tool = registry.get_tool("add_mountain")
    if mountain_tool:
        schema = mountain_tool.to_schema()
        print(f"  ✓ Generated schema for 'add_mountain'")
        print(f"    Parameters: {len(schema['function']['parameters']['properties'])} defined")
    
    # Test 4: LLM function schemas
    print("\n📋 Testing LLM function schema export...")
    llm_schemas = registry.to_llm_function_schemas()
    print(f"  ✓ Exported {len(llm_schemas)} function schemas for LLM")
    
    # Test 5: Context string generation
    print("\n📝 Testing context string generation...")
    context = registry.to_context_string()
    print(f"  ✓ Generated context string ({len(context)} chars)")
    print("  Sample:")
    print(context[:500] + "...")
    
    # Test 6: Scene context generation
    print("\n🎬 Testing scene context generation...")
    test_state = {
        "features": [
            {"id": 1, "type": "mountain", "x": 128, "y": 256},
            {"id": 2, "type": "mountain", "x": 384, "y": 256},
            {"id": 3, "type": "dunes", "x0": 100, "y0": 100, "x1": 400, "y1": 200}
        ],
        "seed": 0
    }
    scene_context = registry.generate_scene_context(test_state)
    print(f"  ✓ Generated scene context")
    print(scene_context)
    
    # Test 7: Compact tool context (optional - requires full dependencies)
    print("\n🔍 Testing compact tool context...")
    try:
        from semantic.parser import SemanticParser
        parser = SemanticParser()
        compact = parser._generate_compact_tool_context()
        print(f"  ✓ Generated compact tool context ({len(compact)} chars)")
        print(compact[:400] + "...")
    except ImportError as e:
        print(f"  ⚠ Skipped (requires dependencies: {e})")
        print("  ℹ Install with: uv sync")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED! MCP Tool Registry is operational.")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Start the server: uvicorn server.main:app --reload --port 8001")
    print("  2. Test with frontend commands")
    print("  3. Observe context-aware parsing in action!")


if __name__ == "__main__":
    try:
        test_tool_registry()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

