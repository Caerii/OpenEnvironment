"""
Integration tests for ReAct agent with real Cerebras API.

These tests require CEREBRAS_API_KEY to be set.
"""

import pytest
import os
import logging
from cerebras.cloud.sdk import Cerebras

RUN_REACT_TESTS = os.environ.get("ENABLE_REACT_TESTS") == "1"

from server.semantic.react_agent_v2 import ReActAgentV2
from server.semantic.tools.executor import ToolExecutor
from server.semantic.tools.schema import get_all_tool_schemas

logger = logging.getLogger(__name__)


# Sample scene for testing
SAMPLE_SCENE = {
    "features": [
        {
            "id": 1,
            "type": "mountain",
            "x": 100,
            "y": 200,
            "radius": 50,
            "height": 0.8,
            "use_noise": True
        },
        {
            "id": 2,
            "type": "valley",
            "x": 300,
            "y": 250,
            "radius": 40,
            "depth": 0.5
        }
    ],
    "semantic_scene": {
        "version": 1,
        "root": {
            "path": "/World",
            "name": "World",
            "data": {},
            "feature_ids": [],
            "children": {}
        },
        "entities": [
            {
                "id": "mountain_1",
                "type": "feature",
                "label": "the peak",
                "keywords": ["mountain", "tall"],
                "description": "1 mountain",
                "feature_refs": [1],
                "metadata": {},
                "created_at": 1000.0,
                "user_intent": "add mountain",
                "relationship_ids": []
            },
            {
                "id": "valley_1",
                "type": "feature",
                "label": "the valley",
                "keywords": ["valley", "low"],
                "description": "1 valley",
                "feature_refs": [2],
                "metadata": {},
                "created_at": 1100.0,
                "user_intent": "add valley",
                "relationship_ids": []
            }
        ],
        "relationships": {
            "relationships": [],
            "next_id": 1
        }
    },
    "seed": 12345,
    "next_id": 3
}


@pytest.fixture
def cerebras_client():
    """Create Cerebras client if API key is available."""
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        pytest.skip("CEREBRAS_API_KEY not set")
    
    return Cerebras(api_key=api_key)


@pytest.fixture
def react_agent(cerebras_client):
    """Create ReAct agent."""
    return ReActAgentV2(cerebras_client, model="llama3.1-8b")


class TestToolSchemas:
    """Test tool schema generation."""
    
    def test_schema_generation(self):
        """Test that tool schemas are generated correctly."""
        executor = ToolExecutor()
        schemas = get_all_tool_schemas(executor.get_tool_functions())
        
        assert len(schemas) > 0, "Should generate at least one schema"
        
        # Check schema structure
        for schema in schemas:
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema
            
            func = schema["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            
            params = func["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
            
            logger.info(f"Schema for {func['name']}: {len(params['properties'])} parameters")
    
    def test_tool_executor(self):
        """Test tool executor registration."""
        executor = ToolExecutor()
        
        assert len(executor.tools) > 0, "Should register tools"
        assert "query_entities" in executor.tools
        assert "calculate_position" in executor.tools
        
        logger.info(f"Registered tools: {list(executor.tools.keys())}")


class TestReActAgent:
    """Test ReAct agent with real API."""
    
    @pytest.mark.skipif(not RUN_REACT_TESTS or not os.environ.get("CEREBRAS_API_KEY"), reason="ReAct tests require ENABLE_REACT_TESTS=1 and API key")
    def test_simple_command(self, react_agent):
        """Test simple command without spatial references."""
        command = "add 2 mountains"
        
        result = react_agent.solve(command, SAMPLE_SCENE)
        
        assert result["success"], f"Should succeed: {result.get('error')}"
        assert len(result["actions"]) > 0, "Should generate actions"
        assert result["iterations"] <= 5, "Should complete within max iterations"
        
        # Check action structure
        for action in result["actions"]:
            assert "kind" in action
            assert "type" in action
            assert action["kind"] == "add"
            assert action["type"] == "mountain"
        
        logger.info(f"Completed in {result['iterations']} iterations with {result['total_tool_calls']} tool calls")
        logger.info(f"Generated {len(result['actions'])} actions")
    
    @pytest.mark.skipif(not RUN_REACT_TESTS or not os.environ.get("CEREBRAS_API_KEY"), reason="ReAct tests require ENABLE_REACT_TESTS=1 and API key")
    def test_spatial_reference(self, react_agent):
        """Test command with spatial reference."""
        command = "add a hill near the peak"
        
        result = react_agent.solve(command, SAMPLE_SCENE)
        
        assert result["success"], f"Should succeed: {result.get('error')}"
        assert len(result["actions"]) > 0, "Should generate actions"
        assert result["total_tool_calls"] > 0, "Should use tools for reference resolution"
        
        # Check that position is reasonable (near mountain at 100, 200)
        action = result["actions"][0]
        assert "x" in action and "y" in action
        assert 50 <= action["x"] <= 150, "Should be near mountain x"
        assert 150 <= action["y"] <= 250, "Should be near mountain y"
        
        logger.info(f"Reasoning trace:")
        for line in result.get("reasoning_trace", []):
            logger.info(f"  {line}")
    
    @pytest.mark.skipif(not RUN_REACT_TESTS or not os.environ.get("CEREBRAS_API_KEY"), reason="ReAct tests require ENABLE_REACT_TESTS=1 and API key")
    def test_between_reference(self, react_agent):
        """Test 'between' spatial reference."""
        command = "add a valley between the peak and the valley"
        
        result = react_agent.solve(command, SAMPLE_SCENE)
        
        assert result["success"], f"Should succeed: {result.get('error')}"
        assert len(result["actions"]) > 0, "Should generate actions"
        assert result["total_tool_calls"] > 0, "Should use tools"
        
        # Check that position is between (100,200) and (300,250)
        action = result["actions"][0]
        assert "x" in action and "y" in action
        # Should be roughly in the middle
        assert 150 <= action["x"] <= 250
        assert 200 <= action["y"] <= 250
        
        logger.info(f"Generated position: ({action['x']}, {action['y']})")
    
    @pytest.mark.skipif(not RUN_REACT_TESTS or not os.environ.get("CEREBRAS_API_KEY"), reason="ReAct tests require ENABLE_REACT_TESTS=1 and API key")
    def test_multiple_features_pattern(self, react_agent):
        """Test command requiring multiple positions in pattern."""
        command = "add 5 hills in a circle around the peak"
        
        result = react_agent.solve(command, SAMPLE_SCENE)
        
        assert result["success"], f"Should succeed: {result.get('error')}"
        assert len(result["actions"]) == 5, "Should generate 5 actions"
        assert result["total_tool_calls"] > 0, "Should use tools"
        
        # Check all actions are add/hill
        for action in result["actions"]:
            assert action["kind"] == "add"
            assert action["type"] == "hill"
            assert "x" in action and "y" in action
        
        logger.info(f"Generated {len(result['actions'])} positions in pattern")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])

