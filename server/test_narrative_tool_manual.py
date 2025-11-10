"""
Manual test for narrative tool - bypasses pytest import issues.

This runs the narrative tool directly and analyzes the output mathematically.
"""

import sys
import json
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

def test_narrative_tool_deep():
    """Deep analytical test of narrative tool output."""
    from semantic.tools.executor import ToolExecutor
    from semantic.tools.narrative_tools import generate_narrative_composition
    
    print("\n" + "="*80)
    print("DEEP NARRATIVE TOOL TEST")
    print("="*80)
    
    # Initialize executor
    executor = ToolExecutor()
    
    print(f"\nTool Registration:")
    print(f"  Total tools: {len(executor.tools)}")
    print(f"  Narrative tool registered: {'generate_narrative_composition' in executor.tools}")
    
    # Create test scene state
    scene_state = {
        "features": [],
        "seed": 42,
        "semantic_scene": {"entities": []},
        "biome": "desert"
    }
    
    # Test commands
    test_commands = [
        "create dramatic mountains",
        "design serene valley",
        "build rugged cliffs",
        "generate beautiful dunes"
    ]
    
    print("\n" + "-"*80)
    print("TESTING COMMANDS:")
    print("-"*80)
    
    for cmd in test_commands:
        print(f"\nCommand: '{cmd}'")
        print("-" * 40)
        
        try:
            # Call tool directly (bypass executor for clearer errors)
            result = generate_narrative_composition(scene_state, cmd)
            
            print(f"SUCCESS: {result['success']}")
            
            if result['success']:
                data = result['data']
                
                # Analyze actions
                actions = data.get('actions', [])
                print(f"  Actions count: {len(actions)}")
                
                if actions:
                    # Mathematical analysis
                    print(f"\n  ACTION ANALYSIS:")
                    
                    # 1. Feature type distribution
                    feature_types = {}
                    for action in actions:
                        ftype = action.get('type', 'unknown')
                        feature_types[ftype] = feature_types.get(ftype, 0) + 1
                    
                    print(f"    Feature types: {feature_types}")
                    
                    # 2. Position analysis (if present)
                    positions = []
                    for action in actions:
                        if 'x' in action and 'y' in action:
                            positions.append((action['x'], action['y']))
                    
                    if positions:
                        print(f"    Positions (x, y):")
                        for i, (x, y) in enumerate(positions):
                            print(f"      [{i}] ({x}, {y})")
                        
                        # Calculate spatial distribution
                        xs = [x for x, y in positions]
                        ys = [y for x, y in positions]
                        
                        avg_x = sum(xs) / len(xs)
                        avg_y = sum(ys) / len(ys)
                        
                        # Calculate spread (standard deviation)
                        import math
                        spread_x = math.sqrt(sum((x - avg_x)**2 for x in xs) / len(xs))
                        spread_y = math.sqrt(sum((y - avg_y)**2 for y in ys) / len(ys))
                        
                        print(f"    Spatial center: ({avg_x:.1f}, {avg_y:.1f})")
                        print(f"    Spatial spread: (_x={spread_x:.1f}, _y={spread_y:.1f})")
                        
                        # Check if positions follow composition rules
                        # (should not all be at same point)
                        if spread_x > 10 or spread_y > 10:
                            print(f"     Good spatial distribution (features are spread out)")
                        else:
                            print(f"      Features are clustered (may be intentional)")
                    
                    # 3. Parameter analysis
                    print(f"\n   PARAMETER ANALYSIS:")
                    for i, action in enumerate(actions):
                        print(f"    Action [{i}]:")
                        print(f"      Type: {action.get('type', 'N/A')}")
                        print(f"      Kind: {action.get('kind', 'N/A')}")
                        
                        # Check modifiers
                        mods = action.get('modifiers', {})
                        if mods:
                            for key, val in mods.items():
                                print(f"      {key}: {val}")
                        
                        # Check position
                        pos = action.get('position', {})
                        if pos:
                            print(f"      Position: {pos}")
                
                # Analyze metadata
                print(f"\n   NARRATIVE METADATA:")
                print(f"    Archetype: {data.get('archetype', 'N/A')}")
                print(f"    Focal type: {data.get('focal_type', 'N/A')}")
                print(f"    Supporting types: {data.get('supporting_types', [])}")
                print(f"    Aesthetic goals: {data.get('aesthetic_goals', [])}")
                print(f"    Feature count: {data.get('feature_count', 0)}")
                print(f"    Golden ratio used: {data.get('golden_ratio_used', False)}")
                print(f"    Rule of thirds used: {data.get('rule_of_thirds_used', False)}")
                
                # Validate composition quality
                print(f"\n   QUALITY CHECKS:")
                
                # Check 1: Has focal point
                has_focal = data.get('focal_type') is not None
                print(f"    Has focal point: {has_focal}")
                
                # Check 2: Has supporting features
                has_supporting = len(data.get('supporting_types', [])) > 0
                print(f"    Has supporting features: {has_supporting}")
                
                # Check 3: Aesthetic goals present
                has_aesthetics = len(data.get('aesthetic_goals', [])) > 0
                print(f"    Has aesthetic goals: {has_aesthetics}")
                
                # Check 4: Reasonable feature count (2-8 for most commands)
                feature_count = data.get('feature_count', 0)
                reasonable_count = 1 <= feature_count <= 10
                print(f"    Reasonable feature count (1-10): {reasonable_count} (actual: {feature_count})")
                
                # Check 5: Actions match feature count
                actions_match = len(actions) == feature_count
                print(f"    Actions match feature count: {actions_match}")
                
                # Overall quality score
                quality_score = sum([
                    has_focal,
                    has_supporting,
                    has_aesthetics,
                    reasonable_count,
                    actions_match
                ]) / 5.0
                
                print(f"\n   OVERALL QUALITY SCORE: {quality_score:.1%}")
                if quality_score >= 0.8:
                    print(f"     EXCELLENT - Tool is working correctly")
                elif quality_score >= 0.6:
                    print(f"      GOOD - Minor issues detected")
                else:
                    print(f"     POOR - Significant issues detected")
                
                # Print narrative story
                narrative = data.get('narrative', '')
                if narrative:
                    print(f"\n   GEOLOGICAL STORY:")
                    print(f"    {narrative}")
            
            else:
                error = result.get('error', 'Unknown error')
                print(f" Error: {error}")
        
        except Exception as e:
            print(f" Exception: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print(" TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_narrative_tool_deep()

